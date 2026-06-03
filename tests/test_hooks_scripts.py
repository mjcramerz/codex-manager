import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_DRIVER = REPO_ROOT / "resources" / "hooks" / "scripts" / "hook_driver.pl"
MANIFEST_PATH = REPO_ROOT / "resources" / "hooks" / "manifest.json"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from hooks_builder import render_hook_driver_from_manifest_path  # noqa: E402
from hooks_builder import render_hooks_json_from_manifest_path  # noqa: E402


def _prepare_runtime_hook_dir(tmpdir: str) -> tuple[Path, Path]:
    runtime_root = Path(tmpdir)
    rendered_driver_path = runtime_root / "hook_driver.pl"
    rendered_driver_path.write_text(
        render_hook_driver_from_manifest_path(MANIFEST_PATH, HOOK_DRIVER),
        encoding="utf-8",
    )
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


def run_hook(event_name: str, payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_root, rendered_driver_path = _prepare_runtime_hook_dir(tmpdir)
        return subprocess.run(
            ["perl", str(rendered_driver_path), event_name],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            cwd=runtime_root,
        )


def run_hook_wrapper(wrapper_name: str, payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_root, _rendered_driver_path = _prepare_runtime_hook_dir(tmpdir)
        return subprocess.run(
            ["perl", str(runtime_root / wrapper_name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            cwd=runtime_root,
        )


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "checkout", "-qb", "mcr/main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=path, check=True)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_c0d3x_repo(tmpdir: str) -> Path:
    repo = Path(tmpdir) / "c0d3x"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "Makefile", "preflight:\n\t@true\nverify:\n\t@true\n")
    write_file(repo / "src" / "install" / "codex_install.py", "print('ok')\n")
    write_file(repo / "config" / "usr" / "apps.toml", "")
    write_file(repo / "resources" / "hooks" / "manifest.json", "{}\n")
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


class HookScriptTests(unittest.TestCase):
    maxDiff = None

    def test_manifest_supports_hash_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text(
                """{
  "version": 1,
  "runtime": {
    "session_start": { "timeout": 20, "status_message": "x" },
    "user_prompt_submit": { "timeout": 20, "status_message": "y" },
    "stop": { "timeout": 25, "status_message": "z" }
  },
  "repos": [
    # real comment
    {
      "id": "demo",
      "display_name": "demo",
      "match": {
        "repo_names": ["demo"],
        "all_of_paths": ["a"],
        "any_of_paths": []
      }
    }
  ]
}
""",
                encoding="utf-8",
            )
            payload = json.loads(render_hooks_json_from_manifest_path(manifest_path))
            self.assertEqual(set(payload["hooks"]), {"SessionStart", "UserPromptSubmit", "Stop"})

    def test_manifest_renders_runtime_hooks_json(self) -> None:
        payload = json.loads(render_hooks_json_from_manifest_path(MANIFEST_PATH))
        self.assertEqual(set(payload["hooks"]), {"SessionStart", "UserPromptSubmit", "Stop"})
        session_start = payload["hooks"]["SessionStart"][0]["hooks"][0]
        self.assertEqual(
            session_start["command"],
            'perl "$CODEX_HOME/hooks/scripts/session_start.pl"',
        )
        self.assertEqual(session_start["timeout"], 20)

    def test_session_start_lists_matching_manifest_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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
            self.assertIn("Active generated hook profiles: `codex-manager`", context)
            self.assertIn("Repo role: Codex installer and runtime-configuration source tree.", context)

    def test_session_start_injects_mirror_and_patch_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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

    def test_resume_injects_generic_worktree_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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

    def test_session_start_does_not_fallback_when_no_change_group_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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
            repo = make_c0d3x_repo(tmpdir)

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
            self.assertIn("Codex hooks expose exactly `SessionStart`, `UserPromptSubmit`, and `Stop`", context)
            self.assertIn("python3 -m compileall -q src tests", context)
            self.assertIn("python3 -m unittest discover -s tests", context)

    def test_user_prompt_submit_includes_shared_multi_agent_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

            result = run_hook(
                "user-prompt-submit",
                {
                    "cwd": str(repo),
                    "prompt": "Decide when to delegate and which agent to spawn for this task.",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Multi-agent roles are shared across repos", context)
            self.assertIn("`manager`:", context)
            self.assertIn("`explorer`:", context)
            self.assertIn("`tester`:", context)

    def test_pre_tool_use_blocks_destructive_git_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

            result = run_hook(
                "pre-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_input": "git reset --hard HEAD",
                },
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("destructive `git reset --hard` path", payload["reason"])

    def test_wrapper_script_executes_driver_with_vendored_schema_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

            result = run_hook_wrapper(
                "session_start.pl",
                {
                    "cwd": str(repo),
                    "source": "startup",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Repository context for `c0d3x`", context)

    def test_permission_request_adds_scope_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

            result = run_hook(
                "permission-request",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_input": {"network": True},
                },
            )

            payload = json.loads(result.stdout)
            context = payload["systemMessage"]
            self.assertIn("Permission request for `exec_command`", context)
            self.assertIn("Keep the scope minimal", context)

    def test_post_tool_use_emits_failure_follow_up_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

            result = run_hook(
                "post-tool-use",
                {
                    "cwd": str(repo),
                    "tool_name": "exec_command",
                    "tool_response": "permission denied while writing file",
                },
            )

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Post-tool follow-up for `exec_command`", context)
            self.assertIn("failure or warning signal", context)

    def test_pre_compact_uses_system_message_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)

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
            self.assertIn("Active generated hook profiles: `codex`", context)
            self.assertIn("Repo role: upstream Codex source tree and runtime-contract implementation.", context)

    def test_stop_hook_reentry_stops_instead_of_reblocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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
            self.assertIn("python3 -m compileall -q src tests", first_payload["reason"])
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
            repo = make_c0d3x_repo(tmpdir)
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

    def test_stop_hook_allows_explicit_skip_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_c0d3x_repo(tmpdir)
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
