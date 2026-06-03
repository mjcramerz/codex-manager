#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TRANSCRIPT_TAIL_BYTES = 120_000
RUNTIME_CONFIG_JSON = "__HOOK_RUNTIME_CONFIG_TEMPLATE__"
SKIP_RATIONALE_PATTERN = re.compile(
    r"\b("
    r"could not run|couldn't run|unable to run|did not run|didn't run|"
    r"skipped|cannot run|can't run|not run|not executed|permission boundary|"
    r"permission denied|requires approval|sandbox|tool unavailable|command not found|"
    r"not installed|missing dependency|out of scope"
    r")\b",
    re.IGNORECASE,
)


def _run_command(args: list[str], *, cwd: Path | None = None, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def _emit_context(event_name: str, context: str | None, system_message: str | None = None) -> None:
    payload: dict[str, Any] = {"continue": True}
    if system_message:
        payload["systemMessage"] = system_message
    if context:
        payload["hookSpecificOutput"] = {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    if len(payload) > 1:
        _emit(payload)


def _emit_stop(stop_reason: str) -> None:
    _emit({"continue": False, "stopReason": stop_reason})


def _emit_block(reason: str) -> None:
    _emit({"continue": True, "decision": "block", "reason": reason})


def _load_input() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("hook input must be a JSON object")
    return payload


def _load_runtime_config() -> dict[str, Any]:
    if RUNTIME_CONFIG_JSON == "__HOOK_RUNTIME_CONFIG_TEMPLATE__":
        raise RuntimeError("hook driver template was not rendered by the home/install/upgrade flow")
    payload = json.loads(RUNTIME_CONFIG_JSON)
    if not isinstance(payload, dict):
        raise ValueError("embedded hook runtime config must be a JSON object")
    repos = payload.get("repos")
    if not isinstance(repos, list):
        raise ValueError("embedded hook runtime config must contain a repos list")
    return payload


def _git_root(cwd: str | None) -> Path | None:
    if not cwd:
        return None
    result = _run_command(["git", "-C", cwd, "rev-parse", "--show-toplevel"], timeout=8)
    if result.returncode != 0:
        return None
    rendered = result.stdout.strip()
    return Path(rendered).resolve(strict=False) if rendered else None


def _current_branch(repo_root: Path) -> str:
    branch = _run_command(
        ["git", "-C", str(repo_root), "symbolic-ref", "--quiet", "--short", "HEAD"],
        timeout=8,
    )
    rendered = branch.stdout.strip()
    if branch.returncode == 0 and rendered:
        return rendered
    detached = _run_command(
        ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
        timeout=8,
    )
    return detached.stdout.strip() or "detached"


def _list_refs(repo_root: Path) -> list[str]:
    result = _run_command(
        [
            "git",
            "-C",
            str(repo_root),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
            "refs/remotes",
        ],
        timeout=10,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _list_mirror_refs(repo_root: Path) -> list[str]:
    return [
        ref
        for ref in _list_refs(repo_root)
        if ref.startswith(("github/", "gitlab/", "origin/github/", "origin/gitlab/"))
    ]


def _preferred_mirror_main_branch(repo_root: Path) -> str:
    mirror_refs = set(_list_mirror_refs(repo_root))
    for candidate in (
        "github/mcr/main",
        "gitlab/mcr/main",
        "origin/github/mcr/main",
        "origin/gitlab/mcr/main",
    ):
        if candidate in mirror_refs:
            return candidate.removeprefix("origin/")
    return ""


def _list_changed_files(repo_root: Path) -> list[str]:
    result = _run_command(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        timeout=12,
    )
    if result.returncode != 0:
        return []
    return _parse_changed_files(result.stdout.splitlines())


def _git_status_lines(repo_root: Path) -> list[str]:
    result = _run_command(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        timeout=12,
    )
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _parse_changed_files(lines: list[str]) -> list[str]:
    changed: list[str] = []
    for raw_line in lines:
        if len(raw_line) < 4:
            continue
        path = raw_line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip()
        if path:
            changed.append(path)
    return changed


def _summarize_worktree(repo_root: Path) -> dict[str, Any]:
    counts = {
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
        "deleted": 0,
        "renamed": 0,
        "conflicts": 0,
    }
    preview: list[str] = []
    for raw_line in _git_status_lines(repo_root):
        if len(raw_line) < 4:
            continue
        x = raw_line[0]
        y = raw_line[1]
        path = raw_line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip()
        if path and path not in preview:
            preview.append(path)
        if x == "?" and y == "?":
            counts["untracked"] += 1
            continue
        if x not in {" ", "?"}:
            counts["staged"] += 1
        if y not in {" ", "?"}:
            counts["unstaged"] += 1
        if x == "D" or y == "D":
            counts["deleted"] += 1
        if x == "R" or y == "R":
            counts["renamed"] += 1
        if "U" in {x, y} or (x == "A" and y == "A") or (x == "D" and y == "D"):
            counts["conflicts"] += 1
    counts["preview"] = preview[:6]
    return counts


def _preview_paths(paths: list[str], *, limit: int = 4) -> str:
    if not paths:
        return "none"
    unique = list(dict.fromkeys(paths))
    return ", ".join(unique[:limit])


def _focus_areas(manifest: dict[str, Any], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for container in (manifest, *profiles):
        raw_groups = container.get("focus_areas", [])
        if not isinstance(raw_groups, list):
            continue
        for item in raw_groups:
            if isinstance(item, dict):
                groups.append(item)
    return groups


def _detect_changed_areas(
    changed_files: list[str],
    manifest: dict[str, Any],
    profiles: list[dict[str, Any]],
) -> list[str]:
    groups = _focus_areas(manifest, profiles)
    areas: list[str] = []
    for path in changed_files:
        if path.startswith("resources/home/user/") or path.startswith(".git/") or path.endswith(".jsonl"):
            continue
        area = ""
        for group in groups:
            name = str(group.get("label", "")).strip()
            patterns = [str(item) for item in group.get("path_globs", []) if str(item).strip()]
            if name and patterns and _matches_globs(path, patterns):
                area = name
                break
        if area and area not in areas:
            areas.append(area)
    return areas


def _join_sections(sections: list[str]) -> str:
    rendered = [section.strip() for section in sections if section and section.strip()]
    return "\n\n".join(rendered)


def _format_template(text: str, values: dict[str, str]) -> str:
    return text.format(**values)


def _format_lines(lines: list[str], values: dict[str, str]) -> list[str]:
    return [_format_template(line, values) for line in lines]


def _repo_matches(match_block: dict[str, Any], repo_root: Path) -> bool:
    repo_name = repo_root.name
    repo_names = match_block.get("repo_names", [])
    all_of_paths = match_block.get("all_of_paths", [])
    any_of_paths = match_block.get("any_of_paths", [])

    if repo_names and repo_name not in repo_names:
        return False
    if all_of_paths and any(not (repo_root / relative).exists() for relative in all_of_paths):
        return False
    if any_of_paths and all(not (repo_root / relative).exists() for relative in any_of_paths):
        return False
    return True


def _find_repo_profiles(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for repo in manifest.get("repos", []):
        match_block = repo.get("match", {})
        if isinstance(match_block, dict) and _repo_matches(match_block, repo_root):
            matched.append(repo)
    return matched


def _manifest_environment(
    manifest: dict[str, Any],
    profiles: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    required: list[str] = []
    optional: list[str] = []
    probes: list[dict[str, Any]] = []
    for block in [manifest.get("environment", {}), *[profile.get("environment", {}) for profile in profiles]]:
        if not isinstance(block, dict):
            continue
        for name in block.get("required_commands", []):
            if name not in required:
                required.append(name)
        for name in block.get("optional_commands", []):
            if name not in optional:
                optional.append(name)
        for probe in block.get("optional_probes", []):
            if probe not in probes:
                probes.append(probe)
    return required, optional, probes


def _environment_message(manifest: dict[str, Any], profiles: list[dict[str, Any]]) -> str | None:
    required, optional, probes = _manifest_environment(manifest, profiles)
    missing: list[str] = []
    unavailable: list[str] = []

    for command_name in required:
        if shutil.which(command_name) is None:
            missing.append(command_name)

    for command_name in optional:
        if shutil.which(command_name) is None:
            unavailable.append(command_name)

    for probe in probes:
        label = str(probe.get("label", "")).strip()
        command = probe.get("command", [])
        if not label or not isinstance(command, list) or not command:
            continue
        executable = str(command[0])
        if shutil.which(executable) is None:
            unavailable.append(label)
            continue
        result = _run_command([str(part) for part in command], timeout=8)
        if result.returncode != 0:
            unavailable.append(label)

    if not missing and not unavailable:
        return None

    parts = ["Prereq check:"]
    if missing:
        parts.append(f"missing {' '.join(missing)}")
    if unavailable:
        parts.append(f"unavailable {' '.join(unavailable)}")
    return "; ".join(parts)


def _has_patch_release_dir(repo_root: Path) -> bool:
    return (repo_root / "patches" / "release").is_dir()


def _manifest_block_entries(
    manifest: dict[str, Any],
    profiles: list[dict[str, Any]],
    block_name: str,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for container in (manifest, *profiles):
        block = container.get(block_name, {})
        if isinstance(block, dict):
            entries.append(block)
    return entries


def _multi_agent_context(manifest: dict[str, Any], prompt: str) -> str | None:
    block = manifest.get("multi_agent")
    if not isinstance(block, dict):
        return None
    trigger_patterns = [str(item) for item in block.get("trigger_patterns", []) if str(item).strip()]
    if not trigger_patterns or not _prompt_matches(prompt, trigger_patterns):
        return None
    sections: list[str] = []
    shared_lines = [str(item) for item in block.get("shared_lines", []) if str(item).strip()]
    if shared_lines:
        sections.append("\n".join(shared_lines))
    roles = block.get("roles", [])
    rendered_roles: list[str] = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        name = str(role.get("name", "")).strip()
        description = str(role.get("description", "")).strip()
        use_when = str(role.get("use_when", "")).strip()
        if not name or not description or not use_when:
            continue
        rendered_roles.append(f"- `{name}`: {description} Use when: {use_when}")
    if rendered_roles:
        sections.append("Available agent roles:\n" + "\n".join(rendered_roles))
    return _join_sections(sections)


def _session_start_context(manifest: dict[str, Any], payload: dict[str, Any]) -> str | None:
    repo_root = _git_root(str(payload.get("cwd") or ""))
    if repo_root is None:
        return None

    profiles = _find_repo_profiles(manifest, repo_root)
    current_branch = _current_branch(repo_root)
    mirror_refs = _list_mirror_refs(repo_root)
    mirror_main_branch = _preferred_mirror_main_branch(repo_root)
    changed_files = _list_changed_files(repo_root)
    worktree = _summarize_worktree(repo_root)
    changed_areas = _detect_changed_areas(changed_files, manifest, profiles)
    profile_ids = [str(profile.get("id", "")).strip() for profile in profiles if str(profile.get("id", "")).strip()]
    profile_id = profile_ids[0] if profile_ids else ""
    values = {
        "changed_areas_csv": ", ".join(changed_areas) if changed_areas else "none",
        "changed_files_preview": _preview_paths(changed_files),
        "current_branch": current_branch,
        "profile_ids_csv": ", ".join(profile_ids) if profile_ids else "none",
        "repo_id": profile_id or repo_root.name,
        "repo_name": repo_root.name,
        "repo_root": str(repo_root),
        "runtime_hooks_dir": "$CODEX_HOME/hooks",
        "runtime_hooks_driver_path": "$CODEX_HOME/hooks/scripts/hook_driver.py",
    }
    sections: list[str] = []

    summary_lines = [
        f"Repository context for `{repo_root.name}`:",
        f"- Repo root: `{repo_root}`",
        f"- Current branch: `{current_branch}`",
    ]
    if (repo_root / "AGENTS.md").is_file():
        summary_lines.append(
            "- Root instructions: follow the repo-root `AGENTS.md`, plus any deeper `AGENTS.md` files under touched paths."
        )
    if profile_ids:
        summary_lines.append(
            f"- Active generated hook profiles: `{', '.join(profile_ids)}` from `$CODEX_HOME/hooks/scripts/hook_driver.py`."
        )
    if mirror_refs:
        summary_lines.append(
            f"- Mirror refs detected (`github/*` or `gitlab/*`). Treat those branches as read-only mirrors and true-sync `mcr/main` from `{mirror_main_branch or 'github/mcr/main or gitlab/mcr/main'}`, then `mcr/staging` from `mcr/main`, then `mcr/release` from `mcr/staging`, preserving only protected paths."
        )
    if current_branch.startswith(("github/", "gitlab/")):
        summary_lines.append(f"- Current branch `{current_branch}` is a read-only mirror branch.")
    if (repo_root / "patches" / "release").is_dir():
        summary_lines.append(
            "- `patches/release/` exists. Keep local patch work check-only with commands such as `git apply --check`, `scripts/release/check_release_patches.sh HEAD`, `git mcr-fork-check`, or `git mcr-fork-test`."
        )
    if changed_areas:
        summary_lines.append("- Current changed areas:")
        summary_lines.extend(f"- `{area}`" for area in changed_areas)
    if str(payload.get("source") or "").strip().lower() == "resume" and changed_files:
        worktree_bits: list[str] = []
        for label in ("staged", "unstaged", "untracked", "deleted", "renamed", "conflicts"):
            value = int(worktree.get(label, 0))
            if value > 0:
                worktree_bits.append(f"{label}={value}")
        if worktree_bits:
            summary_lines.append("- Worktree summary: " + ", ".join(worktree_bits))
        preview = worktree.get("preview", []) or []
        if preview:
            summary_lines.append(f"- Changed files preview: `{_preview_paths(list(preview))}`")
    sections.append("\n".join(summary_lines))

    source_name = str(payload.get("source") or "").strip().lower()
    for index, block in enumerate(_manifest_block_entries(manifest, profiles, "session_start")):
        if source_name == "resume":
            lines = _format_lines(list(block.get("resume_context", [])), values)
        else:
            lines = _format_lines(list(block.get("startup_context", [])), values)
        if lines:
            header = "Hook pack context:" if index == 0 else f"Repository profile `{values['repo_id']}`:"
            sections.append("\n".join([header, *[f"- {line}" for line in lines]]))

    return _join_sections(sections)


def _prompt_matches(prompt: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in patterns)


def _user_prompt_context(manifest: dict[str, Any], payload: dict[str, Any]) -> str | None:
    prompt = str(payload.get("prompt") or "").strip()
    repo_root = _git_root(str(payload.get("cwd") or ""))
    if not prompt or repo_root is None:
        return None

    profiles = _find_repo_profiles(manifest, repo_root)
    primary_profile = profiles[0] if profiles else None
    changed_files = _list_changed_files(repo_root)
    changed_areas = _detect_changed_areas(changed_files, manifest, profiles)
    profile_ids = [str(profile.get("id", "")).strip() for profile in profiles if str(profile.get("id", "")).strip()]
    values = {
        "changed_areas_csv": ", ".join(changed_areas) if changed_areas else "none",
        "changed_files_preview": _preview_paths(changed_files),
        "current_branch": _current_branch(repo_root),
        "profile_ids_csv": ", ".join(profile_ids) if profile_ids else "none",
        "repo_id": str(primary_profile.get("id", repo_root.name)) if primary_profile else repo_root.name,
        "repo_name": repo_root.name,
        "repo_root": str(repo_root),
        "runtime_hooks_dir": "$CODEX_HOME/hooks",
        "runtime_hooks_driver_path": "$CODEX_HOME/hooks/scripts/hook_driver.py",
    }

    sections: list[str] = []

    multi_agent_context = _multi_agent_context(manifest, prompt)
    if multi_agent_context:
        sections.append(multi_agent_context)

    if re.search(r"\b(review|audit)\b", prompt, re.IGNORECASE):
        sections.append(
            "Review requests should lead with concrete findings ordered by severity, supported by file and line evidence plus explicit residual risks."
        )

    if re.search(r"\b(hook|hooks|manifest|sessionstart|userpromptsubmit|stop hook)\b", prompt, re.IGNORECASE):
        hook_lines = [
            "Codex hooks expose exactly `SessionStart`, `UserPromptSubmit`, and `Stop` through `$CODEX_HOME/hooks.json`.",
            "Only `SessionStart` uses the matcher regex from `hooks.json`; `UserPromptSubmit` and `Stop` must self-filter inside the hook command.",
            "Stop input includes `stop_hook_active` and `last_assistant_message`. `decision: block` requires a non-empty `reason`.",
        ]
        sections.append("\n".join(hook_lines))

    if re.search(r"\b(github|gitlab|mirror|patch|patches|release|mcr/)\b", prompt, re.IGNORECASE):
        mirror_patch_lines: list[str] = []
        mirror_main_branch = _preferred_mirror_main_branch(repo_root)
        if _list_mirror_refs(repo_root):
            mirror_patch_lines.append(
                f"Mirror refs are present. Treat `github/*` and `gitlab/*` branches as read-only mirrors; true-sync `mcr/main` from `{mirror_main_branch or 'github/mcr/main or gitlab/mcr/main'}`, then promote `mcr/staging` and `mcr/release` with the same protected-path contract."
            )
        if _has_patch_release_dir(repo_root):
            mirror_patch_lines.append(
                "`patches/release/` exists. Keep local patch work check-only with commands such as `git apply --check`, `scripts/release/check_release_patches.sh HEAD`, `git mcr-fork-check`, or `git mcr-fork-test`."
            )
        if mirror_patch_lines:
            sections.append("\n".join(mirror_patch_lines))

    for block in _manifest_block_entries(manifest, profiles, "user_prompt_submit"):
        for rule in block.get("rules", []):
            if not isinstance(rule, dict):
                continue
            patterns = [str(item) for item in rule.get("patterns", []) if str(item).strip()]
            if not patterns or not _prompt_matches(prompt, patterns):
                continue
            lines = [str(line) for line in rule.get("lines", []) if str(line).strip()]
            if not lines:
                continue
            rendered = _format_lines(lines, values)
            sections.append("\n".join(rendered))

    return _join_sections(sections)


def _read_transcript_tail(transcript_path: str | None) -> str:
    if not transcript_path:
        return ""
    path = Path(transcript_path)
    if not path.is_file():
        return ""
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(size - TRANSCRIPT_TAIL_BYTES, 0))
        return handle.read().decode("utf-8", errors="replace")


def _collect_validation_evidence(payload: dict[str, Any]) -> str:
    last_assistant_message = str(payload.get("last_assistant_message") or "").strip()
    transcript_tail = _read_transcript_tail(payload.get("transcript_path"))
    parts = [last_assistant_message, transcript_tail]
    return "\n".join(part for part in parts if part)


def _has_skip_rationale(text: str) -> bool:
    return bool(text and SKIP_RATIONALE_PATTERN.search(text))


def _has_all_evidence(text: str, patterns: list[str]) -> bool:
    return all(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _has_any_evidence(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _matches_globs(path: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, glob) for glob in globs)


def _collect_generic_validation_issues(
    repo_root: Path,
    changed_files: list[str],
    evidence: str,
    current_branch: str,
    mirror_refs: list[str],
) -> list[str]:
    issues: list[str] = []
    patch_files = [
        path
        for path in changed_files
        if path.endswith(".patch") or path.startswith("patches/release/")
    ]

    if current_branch.startswith(("github/", "gitlab/")) and changed_files:
        issues.append(
            f"Current branch `{current_branch}` is a read-only mirror; move authored work to a non-mirror branch before finishing. Changed files: {_preview_paths(changed_files)}."
        )

    if (_has_patch_release_dir(repo_root) or patch_files) and not _has_any_evidence(
        evidence,
        [
            r"\bgit mcr-fork-(check|test)\b",
            r"\bscripts/release/check_release_patches\.sh\b",
            r"\bgit apply( --verbose)? --check\b",
        ],
    ):
        issues.append(
            f"Patch-release repo shape detected ({_preview_paths(patch_files) if patch_files else 'patches/release/'}). Keep local patch work check-only with `git apply --check`, `scripts/release/check_release_patches.sh HEAD`, `git mcr-fork-check`, or `git mcr-fork-test`."
        )

    if (_has_patch_release_dir(repo_root) or patch_files) and re.search(
        r"(?:^|\n).*?\bgit\s+apply\b(?![^\n]*--check)",
        evidence,
        re.IGNORECASE,
    ):
        issues.append("Transcript evidence shows `git apply` without `--check`; local patch application is disallowed here.")

    python_files = [path for path in changed_files if path.endswith(".py")]
    shell_files = [path for path in changed_files if path.endswith((".sh", ".bash", ".zsh"))]
    json_files = [path for path in changed_files if path.endswith(".json")]
    toml_files = [path for path in changed_files if path.endswith(".toml")]
    yaml_files = [path for path in changed_files if path.endswith((".yaml", ".yml"))]

    if python_files and not _has_any_evidence(
        evidence,
        [r"\bpython3? -m (py_compile|compileall|pytest|unittest)\b", r"\bpytest\b"],
    ):
        issues.append(
            f"Python changes ({_preview_paths(python_files)}) need `python3 -m py_compile <file>` or a targeted unittest/pytest command."
        )
    if shell_files and not _has_any_evidence(
        evidence,
        [r"\bshellcheck\b", r"\bbash -n\b", r"\bzsh -n\b", r"\b(sh|dash) -n\b"],
    ):
        issues.append(
            f"Shell changes ({_preview_paths(shell_files)}) need `bash -n` and/or `shellcheck` coverage."
        )
    if json_files and not _has_any_evidence(
        evidence,
        [r"\bpython3? -m json\.tool\b", r"\bjq \."],
    ):
        issues.append(
            f"JSON changes ({_preview_paths(json_files)}) need `python3 -m json.tool` or `jq .` validation."
        )
    if toml_files and not _has_any_evidence(evidence, [r"\btomllib\b", r"\btaplo\b"]):
        issues.append(
            f"TOML changes ({_preview_paths(toml_files)}) need a `tomllib` parse, `taplo`, or equivalent validation."
        )
    if yaml_files and not _has_any_evidence(evidence, [r"\byamllint\b"]):
        issues.append(
            f"YAML changes ({_preview_paths(yaml_files)}) need `yamllint` or equivalent validation."
        )

    return issues


def _collect_stop_rule_issues(
    manifest: dict[str, Any],
    profiles: list[dict[str, Any]],
    changed_files: list[str],
    evidence: str,
    values: dict[str, str],
    current_branch: str,
    mirror_refs_present: bool,
) -> list[str]:
    issues: list[str] = []
    for block in _manifest_block_entries(manifest, profiles, "stop"):
        for rule in block.get("rules", []):
            if not isinstance(rule, dict):
                continue
            globs = [str(item) for item in rule.get("changed_path_globs", []) if str(item).strip()]
            matched_paths = changed_files if not globs else [path for path in changed_files if _matches_globs(path, globs)]
            if globs and not matched_paths:
                continue

            branch_patterns = [str(item) for item in rule.get("branch_matches_any", []) if str(item).strip()]
            if branch_patterns and not _has_any_evidence(current_branch, branch_patterns):
                continue

            when_has_mirror_refs = rule.get("when_has_mirror_refs")
            if when_has_mirror_refs is not None and bool(when_has_mirror_refs) != mirror_refs_present:
                continue

            rendered_values = dict(values)
            rendered_values["changed_files_preview"] = _preview_paths(matched_paths)
            rendered_values["changed_areas_csv"] = ", ".join(_detect_changed_areas(matched_paths, manifest, profiles)) or "none"

            message = _format_template(str(rule.get("message", "")).strip(), rendered_values)
            forbidden_patterns = [str(item) for item in rule.get("forbid_any_patterns", []) if str(item).strip()]
            if forbidden_patterns and _has_any_evidence(evidence, forbidden_patterns):
                issues.append(message)
                continue

            evidence_all = [str(item) for item in rule.get("require_all_patterns", []) if str(item).strip()]
            evidence_any = [str(item) for item in rule.get("require_any_patterns", []) if str(item).strip()]
            if not evidence_all and not evidence_any and not forbidden_patterns:
                issues.append(message)
                continue
            all_ok = True if not evidence_all else _has_all_evidence(evidence, evidence_all)
            any_ok = True if not evidence_any else _has_any_evidence(evidence, evidence_any)
            if all_ok and any_ok:
                continue
            if evidence_all or evidence_any:
                issues.append(message)
    return issues


def _stop_handler(manifest: dict[str, Any], payload: dict[str, Any]) -> None:
    repo_root = _git_root(str(payload.get("cwd") or ""))
    if repo_root is None:
        return

    changed_files = _list_changed_files(repo_root)
    if not changed_files:
        return

    profiles = _find_repo_profiles(manifest, repo_root)
    primary_profile = profiles[0] if profiles else None
    evidence = _collect_validation_evidence(payload)
    current_branch = _current_branch(repo_root)
    mirror_refs = _list_mirror_refs(repo_root)
    mirror_refs_present = bool(mirror_refs)
    values = {
        "changed_areas_csv": ", ".join(_detect_changed_areas(changed_files, manifest, profiles)) or "none",
        "changed_files_preview": _preview_paths(changed_files),
        "current_branch": current_branch,
        "profile_ids_csv": ", ".join(
            str(profile.get("id", "")).strip()
            for profile in profiles
            if str(profile.get("id", "")).strip()
        ) or "none",
        "repo_id": str(primary_profile.get("id", repo_root.name)) if primary_profile else repo_root.name,
        "repo_name": repo_root.name,
        "repo_root": str(repo_root),
        "runtime_hooks_dir": "$CODEX_HOME/hooks",
        "runtime_hooks_driver_path": "$CODEX_HOME/hooks/scripts/hook_driver.py",
    }

    issues = _collect_generic_validation_issues(
        repo_root,
        changed_files,
        evidence,
        current_branch,
        mirror_refs,
    )
    issues.extend(_collect_stop_rule_issues(
        manifest,
        profiles,
        changed_files,
        evidence,
        values,
        current_branch,
        mirror_refs_present,
    ))

    if not issues or _has_skip_rationale(evidence):
        return

    stop_hook_active = bool(payload.get("stop_hook_active"))
    if stop_hook_active:
        stop_reason = "Stop hook follow-up is still unresolved, so the turn is ending instead of blocking again:"
        stop_reason += "".join(f"\n- {issue}" for issue in issues)
        _emit_stop(stop_reason)
        return

    reason = "Repository and validation follow-up is required before this turn can finish:"
    reason += "".join(f"\n- {issue}" for issue in issues)
    reason += "\n- Run the missing checks now, or explain concretely why they could not be run in this environment before ending the turn."
    _emit_block(reason)


def _main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"session-start", "user-prompt-submit", "stop"}:
        raise SystemExit("usage: hook_driver.py {session-start|user-prompt-submit|stop}")

    event = sys.argv[1]
    payload = _load_input()
    manifest = _load_runtime_config()

    if event == "session-start":
        repo_root = _git_root(str(payload.get("cwd") or ""))
        profiles = _find_repo_profiles(manifest, repo_root) if repo_root else []
        _emit_context(
            "SessionStart",
            _session_start_context(manifest, payload),
            _environment_message(manifest, profiles),
        )
        return 0

    if event == "user-prompt-submit":
        _emit_context("UserPromptSubmit", _user_prompt_context(manifest, payload))
        return 0

    _stop_handler(manifest, payload)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except Exception as exc:  # pragma: no cover - defensive fallback for runtime hook safety
        _emit({"continue": True, "systemMessage": f"Hook driver error: {exc}"})
        raise SystemExit(0)
