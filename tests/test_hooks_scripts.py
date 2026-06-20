import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_DRIVER = REPO_ROOT / "resources" / "hooks" / "scripts" / "hook_driver.pl"
APPS_TOML_PATH = REPO_ROOT / "config" / "usr" / "apps.toml"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from common import parse_toml_file
from tests.hook_table_assertions import assert_expected_inline_hooks


def _prepare_runtime_hook_dir(tmpdir: str) -> tuple[Path, Path]:
    runtime_root = Path(tmpdir)
    rendered_driver_path = runtime_root / "hook_driver.pl"
    rendered_driver_path.write_text(HOOK_DRIVER.read_text(encoding="utf-8"), encoding="utf-8")
    rendered_driver_path.chmod(0o755)

    runtime_lib = runtime_root / "lib"
    shutil.copytree(HOOK_DRIVER.parent / "lib", runtime_lib, dirs_exist_ok=True)
    schema_src = REPO_ROOT / "resources" / "hooks" / "schema"
    shutil.copytree(schema_src, runtime_root / "schema", dirs_exist_ok=True)
    for script in (HOOK_DRIVER.parent).glob("*.pl"):
        if script.name == "hook_driver.pl":
            continue
        target = runtime_root / script.name
        shutil.copy2(script, target)
        target.chmod(0o755)
    return runtime_root, rendered_driver_path


def run_hook(event_name: str, payload: dict, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_root, rendered_driver_path = _prepare_runtime_hook_dir(tmpdir)
        merged_env = dict(os.environ)
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["perl", str(rendered_driver_path), event_name],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            cwd=runtime_root,
            env=merged_env,
        )


def run_hook_wrapper(wrapper_name: str, payload: dict, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_root, _rendered_driver_path = _prepare_runtime_hook_dir(tmpdir)
        merged_env = dict(os.environ)
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["perl", str(runtime_root / wrapper_name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            cwd=runtime_root,
            env=merged_env,
        )


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "checkout", "-qb", "mcr/main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=path, check=True)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_codex_manager_repo(tmpdir: str) -> Path:
    repo = Path(tmpdir) / "codex"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "Makefile", "preflight:\n\t@true\nverify:\n\t@true\n")
    write_file(repo / "src" / "install" / "codex_install.py", "print('ok')\n")
    write_file(repo / "config" / "usr" / "apps.toml", "")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo


def make_codex_repo(tmpdir: str) -> Path:
    repo = Path(tmpdir) / "codex"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "codex-rs" / "Cargo.toml", "[package]\nname = 'codex-workspace'\nversion = '0.0.0'\n")
    write_file(repo / "codex-rs" / "core" / "src" / "codex.rs", "// core\n")
    write_file(repo / "codex-rs" / "tui" / "src" / "main.rs", "// tui\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo


def make_incomplete_codex_manager_repo(tmpdir: str) -> Path:
    repo = Path(tmpdir) / "codex"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "Makefile", "all:\n\t@true\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo


class HookScriptTests(unittest.TestCase):
    maxDiff = None

    def test_hooks_toml_carries_full_runtime_hook_table(self) -> None:
        payload = parse_toml_file(REPO_ROOT / "config" / "usr" / "hooks.toml")
        hooks = payload.get("hooks")
        assert_expected_inline_hooks(self, hooks)

    def test_apps_toml_no_longer_includes_hook_table(self) -> None:
        payload = parse_toml_file(APPS_TOML_PATH)
        self.assertNotIn("hooks", payload)

    def test_runtime_hook_driver_is_repo_sourced_without_manifest_template(self) -> None:
        self.assertFalse((REPO_ROOT / "resources" / "hooks" / "manifest.json").exists())
        driver_text = HOOK_DRIVER.read_text(encoding="utf-8")
        self.assertNotIn("__HOOK_RUNTIME_CONFIG_TEMPLATE__", driver_text)

    def test_session_start_lists_matching_runtime_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "new_driver.py", "print('x')\n")

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Active hook runtime profiles: `codex-manager`", context)
            self.assertIn("Repo role: Codex installer and runtime-configuration source tree.", context)

    def test_session_start_requires_full_match_contract_for_repo_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_incomplete_codex_manager_repo(tmpdir)

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Repository context for `codex`", context)
            self.assertNotIn("Active hook runtime profiles:", context)
            self.assertNotIn("Repo role: Codex installer and runtime-configuration source tree.", context)

    def test_session_start_injects_mirror_and_patch_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            subprocess.run(["git", "checkout", "-qb", "github/mcr/main"], cwd=repo, check=True)
            write_file(repo / "patches" / "release" / "sample.patch", "diff --git a/a b/a\n")

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Mirror refs detected", context)
            self.assertIn("true-sync `mcr/main` from `github/mcr/main`", context)
            self.assertIn("Current branch `github/mcr/main` is a read-only mirror branch.", context)
            self.assertIn("`patches/release/` exists.", context)

    def test_session_start_injects_salsa_packaging_mirror_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            subprocess.run(["git", "branch", "gitlab/mcr/main"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "pristine-tar"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "upstream/0.20.1"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "debian/0.20.1-1"], cwd=repo, check=True)

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Debian Salsa packaging mirror detected", context)
            self.assertIn("`pristine-tar`, `upstream/*`, and `debian/*`", context)
            self.assertIn("Packaging refs preview:", context)

    def test_session_start_includes_environment_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            wrapper_dir = Path(tmpdir) / "bin"
            wrapper_dir.mkdir()
            (wrapper_dir / "docker").write_text(
                "#!/bin/sh\nprintf '%s\\n' 'CONTAINER ID   IMAGE'\n",
                encoding="utf-8",
            )
            (wrapper_dir / "docker").chmod(0o755)

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
                env={"PATH": f"{wrapper_dir}:{os.environ['PATH']}"},
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Local environment signals:", context)
            self.assertIn("Required commands available: `bash`, `make`.", context)
            self.assertIn("Probe `docker ps`: ok (CONTAINER ID   IMAGE).", context)

    def test_resume_injects_generic_worktree_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "tracked.txt", "base\n")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "tracked"], cwd=repo, check=True)
            write_file(repo / "tracked.txt", "base\nchange\n")
            write_file(repo / "new.txt", "new\n")

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "resume",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Worktree summary:", context)
            self.assertIn("unstaged=1", context)
            self.assertIn("untracked=1", context)
            self.assertIn("Changed files preview:", context)
            self.assertIn("tracked.txt", context)
            self.assertNotIn("Manifest-defined focus areas", context)

    def test_startup_omits_transcript_signal_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            transcript_path = Path(tmpdir) / "session.jsonl"
            transcript_path.write_text(
                "Recent warning: {\"timestamp\":\"2026-06-20T01:21:07.638Z\",\"type\":\"session_meta\",\"payload\":{\"base_instructions\":{\"text\":\"<skills_instructions> ### Available skills\"}}}\n"
                "command timed out after 20 seconds\n",
                encoding="utf-8",
            )

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                    "transcript_path": str(transcript_path),
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("Recent recurring signals from the session transcript:", context)
            self.assertNotIn("Available skills", context)

    def test_session_start_does_not_fallback_when_no_change_group_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "README.md", "# temp\n")

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("Current changed areas:", context)
            self.assertNotIn("README", context)

    def test_user_prompt_submit_uses_generic_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "user-prompt-submit",
                {
                    "cwd": str(repo),
                    "prompt": "Audit the hooks manifest and validate the stop hook behavior.",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Review requests should lead with concrete findings", context)
            self.assertIn("Hook wiring stays inline in `config/usr/apps.toml`", context)
            self.assertIn("runtime source of truth", context)
            self.assertIn("python3 -m compileall src tests", context)
            self.assertIn("python3 -m unittest discover -s tests", context)

    def test_user_prompt_submit_includes_shared_multi_agent_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "user-prompt-submit",
                {
                    "cwd": str(repo),
                    "prompt": "Decide when to delegate, which agent to spawn, and when to wait_agent or close_agent for this task.",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Multi-agent orchestration guidance:", context)
            self.assertIn("Multi-agent roles are shared across repos", context)
            self.assertIn("`spawn_agent`", context)
            self.assertIn("`send_input`", context)
            self.assertIn("`wait_agent`", context)
            self.assertIn("`close_agent`", context)
            self.assertIn("`planner`:", context)
            self.assertIn("`delegator`:", context)
            self.assertIn("`orchestrator`:", context)
            self.assertLess(len(context), 1800)

    def test_resume_context_stays_bounded_with_noisy_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            transcript_path = Path(tmpdir) / "session.jsonl"
            giant_warning = "Warning: " + ("x" * 8000)
            transcript_path.write_text(
                "\n".join([
                    giant_warning,
                    giant_warning,
                    "command timed out after 20 seconds",
                    "permission denied while writing file",
                ] * 40),
                encoding="utf-8",
            )

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "resume",
                    "transcript_path": str(transcript_path),
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertLess(len(context), 1800)

    def test_subagent_start_coordination_wrapper_includes_role_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook_wrapper(
                "subagent_start_coordination.pl",
                {
                    "cwd": str(repo),
                    "agent_type": "manager",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Subagent start for `manager`", context)
            self.assertIn("Role profile: `coordination`.", context)
            self.assertIn("Own decomposition, acceptance criteria, and sequencing", context)

    def test_subagent_start_delegation_wrapper_includes_role_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook_wrapper(
                "subagent_start_delegation.pl",
                {
                    "cwd": str(repo),
                    "agent_type": "delegator",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Subagent start for `delegator`", context)
            self.assertIn("Role profile: `delegation`.", context)
            self.assertIn("Select the smallest role that fits each child slice", context)

    def test_subagent_stop_validation_wrapper_includes_role_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "hook_driver.pl", "print('x')\n")

            result = run_hook_wrapper(
                "subagent_stop_validation.pl",
                {
                    "cwd": str(repo),
                    "agent_id": "agent-verify",
                    "agent_type": "tester",
                    "last_assistant_message": "",
                    "stop_hook_active": False,
                },
            )

            outputs = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(outputs), 2)
            context = outputs[0]["systemMessage"]
            self.assertIn("Subagent stop guidance for `tester`", context)
            self.assertIn("Role profile: `validation`.", context)
            self.assertIn("State pass, fail, or untested per check", context)
            self.assertEqual(outputs[-1]["decision"], "block")
            self.assertIn("validation follow-up", outputs[-1]["reason"])

    def test_subagent_stop_synthesis_wrapper_includes_role_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "hook_driver.pl", "print('x')\n")

            result = run_hook_wrapper(
                "subagent_stop_synthesis.pl",
                {
                    "cwd": str(repo),
                    "agent_id": "agent-merge",
                    "agent_type": "synthesizer",
                    "last_assistant_message": "",
                    "stop_hook_active": False,
                },
            )

            outputs = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(outputs), 2)
            context = outputs[0]["systemMessage"]
            self.assertIn("Subagent stop guidance for `synthesizer`", context)
            self.assertIn("Role profile: `synthesis`.", context)
            self.assertIn("Identify which statements come from which child evidence", context)
            self.assertEqual(outputs[-1]["decision"], "block")
            self.assertIn("validation follow-up", outputs[-1]["reason"])

    def test_user_prompt_submit_includes_environment_warnings_for_operational_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            wrapper_dir = Path(tmpdir) / "bin"
            wrapper_dir.mkdir()
            (wrapper_dir / "docker").write_text(
                "#!/bin/sh\nprintf '%s\\n' 'Cannot connect to the Docker daemon' >&2\nexit 1\n",
                encoding="utf-8",
            )
            (wrapper_dir / "docker").chmod(0o755)

            result = run_hook(
                "user-prompt-submit",
                {
                    "cwd": str(repo),
                    "prompt": "Check the docker container build flow and validate the runtime setup.",
                },
                env={"PATH": f"{wrapper_dir}:{os.environ['PATH']}"},
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Local environment signals:", context)
            self.assertIn("Probe `docker ps`: failed (Cannot connect to the Docker daemon).", context)

    def test_user_prompt_submit_mentions_salsa_packaging_mirror_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            subprocess.run(["git", "branch", "gitlab/mcr/main"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "pristine-tar"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "upstream/0.20.1"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "debian/0.20.1-1"], cwd=repo, check=True)

            result = run_hook(
                "user-prompt-submit",
                {
                    "cwd": str(repo),
                    "prompt": "Check the gitlab mirror and packaging refs for rebuild flow.",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Debian Salsa packaging mirror", context)
            self.assertIn("`pristine-tar`, `upstream/*`, and `debian/*`", context)

    def test_pre_tool_use_shell_command_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "pre-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_input": "git reset --hard HEAD",
                },
            )

            self.assertEqual(result.stdout.strip(), "")

    def test_pre_tool_use_shell_structured_payload_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "pre-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_input": {"cmd": "git clean -fd"},
                },
            )

            self.assertEqual(result.stdout.strip(), "")

    def test_wrapper_script_executes_driver_with_vendored_schema_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook_wrapper(
                "session_start.pl",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Repository context for `codex`", context)

    def test_permission_request_shell_command_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "permission-request",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_input": {"network": True},
                },
            )

            self.assertEqual(result.stdout.strip(), "")

    def test_permission_request_generic_tool_uses_fallback_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "permission-request",
                {
                    "cwd": str(repo),
                    "tool_name": "write_stdin",
                    "tool_input": {"chars": "status"},
                },
            )

            payload = json.loads(result.stdout)
            context = payload["systemMessage"]
            self.assertIn("Permission request for `tool call` (`write_stdin`)", context)
            self.assertIn("Keep the scope minimal", context)

    def test_post_tool_use_shell_command_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "post-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_response": "permission denied while writing file",
                },
            )

            self.assertEqual(result.stdout.strip(), "")

    def test_post_tool_use_shell_structured_payload_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "post-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_response": {"stderr": "permission denied while writing file", "rc": 1},
                },
            )

            self.assertEqual(result.stdout.strip(), "")

    def test_generic_post_tool_use_wrapper_noops_for_shell_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook_wrapper(
                "post_tool_use.pl",
                {
                    "cwd": str(repo),
                    "hook_event_name": "PostToolUse",
                    "model": "unknown-model",
                    "permission_mode": "default",
                    "session_id": "session-1",
                    "tool_input": {"cmd": "git status"},
                    "tool_name": "exec_command",
                    "tool_response": "permission denied while writing file",
                    "tool_use_id": "tool-use-1",
                    "transcript_path": None,
                    "turn_id": "turn-1",
                },
            )

            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.returncode, 0)

    def test_generic_mcp_post_tool_use_wrapper_noops_for_specific_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook_wrapper(
                "post_tool_use_mcp.pl",
                {
                    "cwd": str(repo),
                    "hook_event_name": "PostToolUse",
                    "model": "unknown-model",
                    "permission_mode": "default",
                    "session_id": "session-1",
                    "tool_input": {},
                    "tool_name": "mcp__git__status",
                    "tool_response": {"stderr": "failed to query status", "rc": 1},
                    "tool_use_id": "tool-use-1",
                    "transcript_path": None,
                    "turn_id": "turn-1",
                },
            )

            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.returncode, 0)

    def test_pre_compact_uses_system_message_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "pre-compact",
                {
                    "cwd": str(repo),
                },
            )

            payload = json.loads(result.stdout)
            self.assertIn("Pre compact guidance", payload["systemMessage"])
            self.assertNotIn("hookSpecificOutput", payload)

    def test_codex_shape_detection_is_generic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_repo(tmpdir)
            write_file(repo / "codex-rs" / "hooks" / "src" / "schema.rs", "// hook schema\n")

            result = run_hook(
                "session-start",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Active hook runtime profiles: `codex`", context)
            self.assertIn("Repo role: upstream Codex source tree and runtime-contract implementation.", context)

    def test_stop_hook_reentry_stops_instead_of_reblocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "hook_driver.pl", "print('x')\n")

            first = run_hook(
                "stop",
                {
                    "cwd": str(repo),
                    "transcript_path": None,
                    "last_assistant_message": "",
                    "stop_hook_active": False,
                },
            )
            first_payload = json.loads(first.stdout)
            self.assertEqual(first_payload["decision"], "block")
            self.assertIn("python3 -m compileall src tests", first_payload["reason"])
            self.assertIn("local test suite", first_payload["reason"])

            second = run_hook(
                "stop",
                {
                    "cwd": str(repo),
                    "transcript_path": None,
                    "last_assistant_message": "",
                    "stop_hook_active": True,
                },
            )
            second_payload = json.loads(second.stdout)
            self.assertFalse(second_payload["continue"])
            self.assertIn("ending instead of blocking again", second_payload["stopReason"])

    def test_subagent_stop_reuses_stop_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "hook_driver.pl", "print('x')\n")

            result = run_hook(
                "subagent-stop",
                {
                    "cwd": str(repo),
                    "agent_id": "agent-1",
                    "agent_type": "worker",
                    "last_assistant_message": "",
                    "stop_hook_active": False,
                },
            )

            outputs = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(outputs), 2)
            context = outputs[0]["systemMessage"]
            self.assertIn("Subagent stop guidance", context)
            self.assertEqual(outputs[-1]["decision"], "block")
            self.assertIn("validation follow-up", outputs[-1]["reason"])

    def test_subagent_stop_reports_identity_and_missing_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)

            result = run_hook(
                "subagent-stop",
                {
                    "cwd": str(repo),
                    "agent_id": "agent-1",
                    "agent_type": "tester",
                    "last_assistant_message": "",
                    "stop_hook_active": False,
                },
            )

            payload = json.loads(result.stdout)
            context = payload["systemMessage"]
            self.assertIn("Subagent stop guidance for `tester`", context)
            self.assertIn("Agent id: `agent-1`", context)
            self.assertIn("Last assistant message is empty", context)

    def test_subagent_stop_includes_transcript_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            transcript_path = Path(tmpdir) / "agent.jsonl"
            transcript_path.write_text(
                "permission denied while running validation\n"
                "Traceback: test failed\n",
                encoding="utf-8",
            )

            result = run_hook(
                "subagent-stop",
                {
                    "cwd": str(repo),
                    "agent_id": "agent-2",
                    "agent_type": "worker",
                    "agent_transcript_path": str(transcript_path),
                    "last_assistant_message": "Could not run tests because permission denied.",
                    "stop_hook_active": False,
                },
            )

            payload = json.loads(result.stdout)
            context = payload["systemMessage"]
            self.assertIn("Subagent transcript signals:", context)
            self.assertIn("permission or sandbox denials", context)
            self.assertIn("test failures", context)

    def test_stop_hook_allows_explicit_skip_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_codex_manager_repo(tmpdir)
            write_file(repo / "resources" / "hooks" / "scripts" / "hook_driver.pl", "print('x')\n")

            result = run_hook(
                "stop",
                {
                    "cwd": str(repo),
                    "transcript_path": None,
                    "last_assistant_message": "I could not run the home sync because this environment blocked execution.",
                    "stop_hook_active": True,
                },
            )
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
