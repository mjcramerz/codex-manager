from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from common import fail

HOOKS_MANIFEST_VERSION = 1
REPO_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
COMMAND_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+_.-]*$")
PLACEHOLDER_PATTERN = re.compile(r"\{([a-z_]+)\}")
ALLOWED_TEMPLATE_TOKENS = frozenset(
    {
        "changed_areas_csv",
        "changed_files_preview",
        "current_branch",
        "profile_ids_csv",
        "repo_id",
        "repo_name",
        "repo_root",
        "runtime_hooks_dir",
        "runtime_hooks_driver_path",
    }
)
DEFAULT_RUNTIME = {
    "session_start": {
        "timeout": 20,
        "status_message": "Injecting repository, manifest, and environment context",
    },
    "user_prompt_submit": {
        "timeout": 20,
        "status_message": "Injecting prompt-aware manifest and validation context",
    },
    "stop": {
        "timeout": 25,
        "status_message": "Checking manifest-driven repository and validation gates",
    },
}
HOOK_DRIVER_CONFIG_PLACEHOLDER = '"__HOOK_RUNTIME_CONFIG_TEMPLATE__"'


def _strip_hash_comments(text: str) -> str:
    rendered: list[str] = []
    in_string = False
    escaped = False
    idx = 0
    length = len(text)

    while idx < length:
        ch = text[idx]
        if in_string:
            rendered.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            idx += 1
            continue

        if ch == '"':
            in_string = True
            rendered.append(ch)
            idx += 1
            continue

        if ch == "#":
            while idx < length and text[idx] not in "\r\n":
                idx += 1
            continue

        rendered.append(ch)
        idx += 1

    return "".join(rendered)


def _parse_hooks_manifest_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing JSON file: {path}")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"invalid JSON at {path}: {exc}")
    try:
        data = json.loads(_strip_hash_comments(raw))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON at {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"invalid JSON payload shape at {path}")
    return data


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be a string")
    rendered = value.strip()
    if not rendered:
        fail(f"{label} must not be empty")
    return rendered


def _require_non_negative_timeout(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        fail(f"{label} must be an integer")
    if value < 1 or value > 600:
        fail(f"{label} must be between 1 and 600 seconds")
    return value


def _validate_relative_path(value: str, label: str) -> str:
    path = Path(value)
    if path.is_absolute():
        fail(f"{label} must be relative: {value}")
    if any(part == ".." for part in path.parts):
        fail(f"{label} must not contain '..': {value}")
    if value.startswith("./"):
        fail(f"{label} must not start with './': {value}")
    return value


def _validate_placeholders(text: str, label: str) -> None:
    for token in PLACEHOLDER_PATTERN.findall(text):
        if token not in ALLOWED_TEMPLATE_TOKENS:
            fail(f"{label} uses unsupported placeholder {{{token}}}")


def _require_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    rendered: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        rendered_item = _require_string(item, item_label)
        rendered.append(rendered_item)
    if not allow_empty and not rendered:
        fail(f"{label} must not be empty")
    return rendered


def _validate_regex_list(patterns: list[str], label: str) -> None:
    for index, pattern in enumerate(patterns):
        try:
            re.compile(pattern)
        except re.error as exc:
            fail(f"{label}[{index}] is not a valid regular expression: {exc}")


def _validate_environment_block(value: Any, label: str) -> None:
    if value is None:
        return
    block = _require_object(value, label)
    required_commands = _require_string_list(
        block.get("required_commands", []),
        f"{label}.required_commands",
        allow_empty=True,
    )
    optional_commands = _require_string_list(
        block.get("optional_commands", []),
        f"{label}.optional_commands",
        allow_empty=True,
    )
    for index, item in enumerate(required_commands + optional_commands):
        if not COMMAND_NAME_PATTERN.fullmatch(item):
            fail(f"{label} contains invalid command name at index {index}: {item}")

    probes = block.get("optional_probes", [])
    if probes is None:
        probes = []
    if not isinstance(probes, list):
        fail(f"{label}.optional_probes must be a list")
    for index, probe in enumerate(probes):
        probe_label = f"{label}.optional_probes[{index}]"
        probe_obj = _require_object(probe, probe_label)
        _require_string(probe_obj.get("label"), f"{probe_label}.label")
        command = probe_obj.get("command")
        if not isinstance(command, list) or not command:
            fail(f"{probe_label}.command must be a non-empty list")
        for item_index, part in enumerate(command):
            part_label = f"{probe_label}.command[{item_index}]"
            rendered = _require_string(part, part_label)
            if item_index == 0 and not COMMAND_NAME_PATTERN.fullmatch(rendered):
                fail(f"{part_label} is not a valid command name: {rendered}")


def _validate_focus_areas(value: Any, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        item_obj = _require_object(item, item_label)
        _require_string(item_obj.get("label"), f"{item_label}.label")
        path_globs = _require_string_list(item_obj.get("path_globs"), f"{item_label}.path_globs")
        for pattern_index, pattern in enumerate(path_globs):
            _validate_relative_path(pattern, f"{item_label}.path_globs[{pattern_index}]")


def _validate_runtime_section(manifest_path: Path, payload: dict[str, Any]) -> None:
    runtime = payload.get("runtime")
    if runtime is None:
        return
    runtime_obj = _require_object(runtime, f"{manifest_path}.runtime")
    for event_name in ("session_start", "user_prompt_submit", "stop"):
        event = runtime_obj.get(event_name)
        if event is None:
            continue
        event_obj = _require_object(event, f"{manifest_path}.runtime.{event_name}")
        if "timeout" in event_obj:
            _require_non_negative_timeout(event_obj["timeout"], f"{manifest_path}.runtime.{event_name}.timeout")
        if "status_message" in event_obj:
            _require_string(event_obj["status_message"], f"{manifest_path}.runtime.{event_name}.status_message")


def _validate_session_start_block(value: Any, label: str) -> None:
    if value is None:
        return
    block = _require_object(value, label)
    for field_name in ("startup_context", "resume_context"):
        lines = _require_string_list(block.get(field_name, []), f"{label}.{field_name}", allow_empty=True)
        for index, line in enumerate(lines):
            _validate_placeholders(line, f"{label}.{field_name}[{index}]")


def _validate_prompt_submit_block(value: Any, label: str) -> None:
    if value is None:
        return
    block = _require_object(value, label)
    rules = block.get("rules", [])
    if not isinstance(rules, list):
        fail(f"{label}.rules must be a list")
    for index, rule in enumerate(rules):
        rule_label = f"{label}.rules[{index}]"
        rule_obj = _require_object(rule, rule_label)
        patterns = _require_string_list(rule_obj.get("patterns"), f"{rule_label}.patterns")
        _validate_regex_list(patterns, f"{rule_label}.patterns")
        lines = _require_string_list(rule_obj.get("lines"), f"{rule_label}.lines")
        for line_index, line in enumerate(lines):
            _validate_placeholders(line, f"{rule_label}.lines[{line_index}]")


def _validate_stop_block(value: Any, label: str) -> None:
    if value is None:
        return
    block = _require_object(value, label)
    rules = block.get("rules", [])
    if not isinstance(rules, list):
        fail(f"{label}.rules must be a list")
    for index, rule in enumerate(rules):
        rule_label = f"{label}.rules[{index}]"
        rule_obj = _require_object(rule, rule_label)
        rule_id = _require_string(rule_obj.get("id"), f"{rule_label}.id")
        if not REPO_ID_PATTERN.fullmatch(rule_id):
            fail(f"{rule_label}.id is invalid: {rule_id}")
        changed_path_globs = _require_string_list(
            rule_obj.get("changed_path_globs", []),
            f"{rule_label}.changed_path_globs",
            allow_empty=True,
        )
        for path_index, value in enumerate(changed_path_globs):
            _validate_relative_path(value, f"{rule_label}.changed_path_globs[{path_index}]")
        branch_matches_any = _require_string_list(
            rule_obj.get("branch_matches_any", []),
            f"{rule_label}.branch_matches_any",
            allow_empty=True,
        )
        _validate_regex_list(branch_matches_any, f"{rule_label}.branch_matches_any")
        when_has_mirror_refs = rule_obj.get("when_has_mirror_refs")
        if when_has_mirror_refs is not None and not isinstance(when_has_mirror_refs, bool):
            fail(f"{rule_label}.when_has_mirror_refs must be boolean when provided")
        require_all_patterns = _require_string_list(
            rule_obj.get("require_all_patterns", []),
            f"{rule_label}.require_all_patterns",
            allow_empty=True,
        )
        require_any_patterns = _require_string_list(
            rule_obj.get("require_any_patterns", []),
            f"{rule_label}.require_any_patterns",
            allow_empty=True,
        )
        forbid_any_patterns = _require_string_list(
            rule_obj.get("forbid_any_patterns", []),
            f"{rule_label}.forbid_any_patterns",
            allow_empty=True,
        )
        if not changed_path_globs and not branch_matches_any and when_has_mirror_refs is None:
            fail(f"{rule_label} must define at least one trigger condition")
        _validate_regex_list(require_all_patterns, f"{rule_label}.require_all_patterns")
        _validate_regex_list(require_any_patterns, f"{rule_label}.require_any_patterns")
        _validate_regex_list(forbid_any_patterns, f"{rule_label}.forbid_any_patterns")
        message = _require_string(rule_obj.get("message"), f"{rule_label}.message")
        _validate_placeholders(message, f"{rule_label}.message")


def _configured_agent_roles(manifest_path: Path) -> set[str]:
    repo_root = manifest_path.resolve().parents[2]
    apps_path = repo_root / "config" / "usr" / "apps.toml"
    agents_dir = repo_root / "config" / "agents"
    try:
        apps_payload = tomllib.loads(apps_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"invalid agent config at {apps_path}: {exc}")
    agents_table = apps_payload.get("agents")
    if not isinstance(agents_table, dict):
        fail(f"{apps_path} must define [agents]")
    roles_from_apps = {
        key
        for key, value in agents_table.items()
        if isinstance(value, dict) and isinstance(value.get("config_file"), str)
    }
    roles_from_files = {path.stem for path in agents_dir.glob("*.toml")}
    if roles_from_apps != roles_from_files:
        fail(
            f"agent role mismatch between {apps_path} and {agents_dir}: "
            f"apps={sorted(roles_from_apps)} files={sorted(roles_from_files)}"
        )
    return roles_from_apps


def _validate_multi_agent_block(value: Any, label: str, *, manifest_path: Path) -> None:
    if value is None:
        return
    block = _require_object(value, label)
    trigger_patterns = _require_string_list(block.get("trigger_patterns"), f"{label}.trigger_patterns")
    _validate_regex_list(trigger_patterns, f"{label}.trigger_patterns")
    shared_lines = _require_string_list(block.get("shared_lines"), f"{label}.shared_lines", allow_empty=True)
    for index, line in enumerate(shared_lines):
        _validate_placeholders(line, f"{label}.shared_lines[{index}]")
    roles = block.get("roles")
    if not isinstance(roles, list) or not roles:
        fail(f"{label}.roles must be a non-empty list")
    configured_roles = _configured_agent_roles(manifest_path)
    seen_roles: set[str] = set()
    for index, role in enumerate(roles):
        role_label = f"{label}.roles[{index}]"
        role_obj = _require_object(role, role_label)
        name = _require_string(role_obj.get("name"), f"{role_label}.name")
        if name in seen_roles:
            fail(f"{label} contains duplicate role name: {name}")
        seen_roles.add(name)
        if name not in configured_roles:
            fail(f"{role_label}.name is not a configured agent role: {name}")
        _require_string(role_obj.get("description"), f"{role_label}.description")
        _require_string(role_obj.get("use_when"), f"{role_label}.use_when")
    if seen_roles != configured_roles:
        fail(
            f"{label}.roles must cover configured agent roles exactly: "
            f"expected={sorted(configured_roles)} got={sorted(seen_roles)}"
        )


def validate_hooks_manifest(manifest_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    version = payload.get("version")
    if version != HOOKS_MANIFEST_VERSION:
        fail(
            f"{manifest_path} version must be {HOOKS_MANIFEST_VERSION}, got {version!r}"
        )

    _validate_runtime_section(manifest_path, payload)
    _validate_environment_block(payload.get("environment"), f"{manifest_path}.environment")
    _validate_focus_areas(payload.get("focus_areas"), f"{manifest_path}.focus_areas")
    _validate_session_start_block(payload.get("session_start"), f"{manifest_path}.session_start")
    _validate_prompt_submit_block(payload.get("user_prompt_submit"), f"{manifest_path}.user_prompt_submit")
    _validate_stop_block(payload.get("stop"), f"{manifest_path}.stop")
    _validate_multi_agent_block(payload.get("multi_agent"), f"{manifest_path}.multi_agent", manifest_path=manifest_path)

    repos = payload.get("repos")
    if not isinstance(repos, list) or not repos:
        fail(f"{manifest_path}.repos must be a non-empty list")

    seen_repo_ids: set[str] = set()
    for index, repo in enumerate(repos):
        repo_label = f"{manifest_path}.repos[{index}]"
        repo_obj = _require_object(repo, repo_label)
        repo_id = _require_string(repo_obj.get("id"), f"{repo_label}.id")
        if not REPO_ID_PATTERN.fullmatch(repo_id):
            fail(f"{repo_label}.id is invalid: {repo_id}")
        if repo_id in seen_repo_ids:
            fail(f"{manifest_path} contains duplicate repo id: {repo_id}")
        seen_repo_ids.add(repo_id)

        if "display_name" in repo_obj:
            _require_string(repo_obj["display_name"], f"{repo_label}.display_name")

        match = _require_object(repo_obj.get("match"), f"{repo_label}.match")
        repo_names = _require_string_list(match.get("repo_names", []), f"{repo_label}.match.repo_names", allow_empty=True)
        all_of_paths = _require_string_list(match.get("all_of_paths", []), f"{repo_label}.match.all_of_paths", allow_empty=True)
        any_of_paths = _require_string_list(match.get("any_of_paths", []), f"{repo_label}.match.any_of_paths", allow_empty=True)
        if not repo_names and not all_of_paths and not any_of_paths:
            fail(f"{repo_label}.match must define repo_names, all_of_paths, or any_of_paths")
        for path_index, value in enumerate(all_of_paths):
            _validate_relative_path(value, f"{repo_label}.match.all_of_paths[{path_index}]")
        for path_index, value in enumerate(any_of_paths):
            _validate_relative_path(value, f"{repo_label}.match.any_of_paths[{path_index}]")
        for repo_name in repo_names:
            if "/" in repo_name or "\\" in repo_name:
                fail(f"{repo_label}.match.repo_names must be basenames: {repo_name}")

        _validate_environment_block(repo_obj.get("environment"), f"{repo_label}.environment")
        _validate_focus_areas(repo_obj.get("focus_areas"), f"{repo_label}.focus_areas")
        _validate_session_start_block(repo_obj.get("session_start"), f"{repo_label}.session_start")
        _validate_prompt_submit_block(repo_obj.get("user_prompt_submit"), f"{repo_label}.user_prompt_submit")
        _validate_stop_block(repo_obj.get("stop"), f"{repo_label}.stop")

    return payload


def load_hooks_manifest(manifest_path: Path) -> dict[str, Any]:
    payload = _parse_hooks_manifest_file(manifest_path)
    return validate_hooks_manifest(manifest_path, payload)


def _runtime_event_settings(manifest: dict[str, Any], event_name: str) -> dict[str, Any]:
    settings = dict(DEFAULT_RUNTIME[event_name])
    runtime = manifest.get("runtime", {})
    if isinstance(runtime, dict):
        event = runtime.get(event_name, {})
        if isinstance(event, dict):
            settings.update(event)
    return settings


def render_hooks_json(manifest: dict[str, Any]) -> str:
    session_start = _runtime_event_settings(manifest, "session_start")
    user_prompt_submit = _runtime_event_settings(manifest, "user_prompt_submit")
    stop = _runtime_event_settings(manifest, "stop")

    payload = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "^(startup|resume)$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 \"$CODEX_HOME/hooks/scripts/hook_driver.py\" session-start",
                            "timeout": session_start["timeout"],
                            "statusMessage": session_start["status_message"],
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 \"$CODEX_HOME/hooks/scripts/hook_driver.py\" user-prompt-submit",
                            "timeout": user_prompt_submit["timeout"],
                            "statusMessage": user_prompt_submit["status_message"],
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 \"$CODEX_HOME/hooks/scripts/hook_driver.py\" stop",
                            "timeout": stop["timeout"],
                            "statusMessage": stop["status_message"],
                        }
                    ],
                }
            ],
        }
    }
    return json.dumps(payload, indent=2) + "\n"


def render_hooks_json_from_manifest_path(manifest_path: Path) -> str:
    manifest = load_hooks_manifest(manifest_path)
    return render_hooks_json(manifest)


def render_runtime_config_json(manifest: dict[str, Any]) -> str:
    payload = {
        "version": manifest["version"],
        "multi_agent": manifest.get("multi_agent", {}),
        "environment": manifest.get("environment", {}),
        "focus_areas": manifest.get("focus_areas", []),
        "session_start": manifest.get("session_start", {}),
        "user_prompt_submit": manifest.get("user_prompt_submit", {}),
        "stop": manifest.get("stop", {}),
        "repos": manifest.get("repos", []),
    }
    return json.dumps(payload, indent=2) + "\n"


def render_hook_driver(manifest: dict[str, Any], template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    runtime_json = json.dumps(json.loads(render_runtime_config_json(manifest)), indent=2)
    if HOOK_DRIVER_CONFIG_PLACEHOLDER not in template:
        fail(f"{template_path} is missing the hook driver config placeholder")
    return template.replace(HOOK_DRIVER_CONFIG_PLACEHOLDER, json.dumps(runtime_json), 1)


def render_hook_driver_from_manifest_path(manifest_path: Path, template_path: Path) -> str:
    manifest = load_hooks_manifest(manifest_path)
    return render_hook_driver(manifest, template_path)
