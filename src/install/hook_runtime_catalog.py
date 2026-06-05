from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from common import fail
from common import parse_toml_file

SUBAGENT_ROLE_NAME_PATTERN = r"^[a-z][a-z0-9_-]*$"
HOOK_SCRIPT_NAME_PATTERN = r"^[A-Za-z0-9_.-]+\.pl$"
SUPPORTED_TOOL_HOOK_EVENTS = ("PreToolUse", "PermissionRequest", "PostToolUse")


def hook_manifest_path(repo_root: Path | None = None) -> Path:
    base = repo_root or Path(__file__).resolve().parents[2]
    return base / "resources" / "hooks" / "scripts" / "lib" / "Codex" / "Hook" / "HookManifest.toml"


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, *, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    items: list[str] = []
    for index, item in enumerate(value):
        items.append(_require_string(item, label=f"{label}[{index}]"))
    if not allow_empty and not items:
        fail(f"{label} must not be empty")
    return items


@lru_cache(maxsize=4)
def load_hook_catalog(catalog_path_value: Path | None = None) -> dict[str, Any]:
    path = hook_manifest_path() if catalog_path_value is None else catalog_path_value
    payload = parse_toml_file(path)
    if payload.get("version") != 1:
        fail(f"{path} must declare version = 1")

    tool_profiles = payload.get("tool_profiles")
    if not isinstance(tool_profiles, list) or not tool_profiles:
        fail(f"{path} must declare a non-empty tool_profiles array")
    roles = payload.get("roles")
    if not isinstance(roles, list) or not roles:
        fail(f"{path} must declare a non-empty roles array")
    subagent_profiles = payload.get("subagent_profiles")
    if not isinstance(subagent_profiles, list) or not subagent_profiles:
        fail(f"{path} must declare a non-empty subagent_profiles array")

    tool_profile_ids: set[str] = set()
    for profile_index, profile in enumerate(tool_profiles):
        if not isinstance(profile, dict):
            fail(f"{path} tool_profiles[{profile_index}] must be an object")
        profile_id = _require_string(profile.get("id"), label=f"{path} tool_profiles[{profile_index}].id")
        matcher = _require_string(profile.get("matcher"), label=f"{path} tool_profiles[{profile_index}].matcher")
        label = _require_string(profile.get("label"), label=f"{path} tool_profiles[{profile_index}].label")
        events = profile.get("events")
        if not isinstance(events, dict):
            fail(f"{path} tool_profiles[{profile_index}].events must be an object")
        if profile_id in tool_profile_ids:
            fail(f"{path} duplicate tool profile id: {profile_id}")
        tool_profile_ids.add(profile_id)
        if re.fullmatch(SUBAGENT_ROLE_NAME_PATTERN, profile_id) is None:
            fail(f"{path} tool_profiles[{profile_index}].id is invalid: {profile_id}")

        normalized_events: dict[str, dict[str, Any]] = {}
        for event_name in SUPPORTED_TOOL_HOOK_EVENTS:
            event_payload = events.get(event_name)
            if not isinstance(event_payload, dict):
                fail(f"{path} tool_profiles[{profile_index}].events.{event_name} must be an object")
            script_name = _require_string(
                event_payload.get("script"),
                label=f"{path} tool_profiles[{profile_index}].events.{event_name}.script",
            )
            timeout = event_payload.get("timeout")
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 600:
                fail(f"{path} tool_profiles[{profile_index}].events.{event_name}.timeout must be an integer between 1 and 600")
            status_message = _require_string(
                event_payload.get("statusMessage"),
                label=f"{path} tool_profiles[{profile_index}].events.{event_name}.statusMessage",
            )
            if "/" in script_name or "\\" in script_name:
                fail(
                    f"{path} tool_profiles[{profile_index}].events.{event_name}.script must be a basename: {script_name}"
                )
            if re.fullmatch(HOOK_SCRIPT_NAME_PATTERN, script_name) is None:
                fail(
                    f"{path} tool_profiles[{profile_index}].events.{event_name}.script must end with .pl: {script_name}"
                )
            normalized_events[event_name] = {
                "script": script_name,
                "timeout": timeout,
                "statusMessage": status_message,
            }

        unknown_events = sorted(set(events) - set(SUPPORTED_TOOL_HOOK_EVENTS))
        if unknown_events:
            fail(f"{path} tool_profiles[{profile_index}] contains unsupported event definitions: {', '.join(unknown_events)}")

        profile["id"] = profile_id
        profile["matcher"] = matcher
        profile["label"] = label
        profile["events"] = normalized_events

    role_names: set[str] = set()
    for role_index, role in enumerate(roles):
        if not isinstance(role, dict):
            fail(f"{path} roles[{role_index}] must be an object")
        name = _require_string(role.get("name"), label=f"{path} roles[{role_index}].name")
        description = _require_string(role.get("description"), label=f"{path} roles[{role_index}].description")
        use_when = _require_string(role.get("use_when"), label=f"{path} roles[{role_index}].use_when")
        if re.fullmatch(SUBAGENT_ROLE_NAME_PATTERN, name) is None:
            fail(f"{path} roles[{role_index}].name is invalid: {name}")
        if name in role_names:
            fail(f"{path} duplicate role name: {name}")
        role_names.add(name)
        role["name"] = name
        role["description"] = description
        role["use_when"] = use_when

    profile_ids: set[str] = set()
    for profile_index, profile in enumerate(subagent_profiles):
        if not isinstance(profile, dict):
            fail(f"{path} subagent_profiles[{profile_index}] must be an object")
        profile_id = _require_string(profile.get("id"), label=f"{path} subagent_profiles[{profile_index}].id")
        matcher = _require_string(profile.get("matcher"), label=f"{path} subagent_profiles[{profile_index}].matcher")
        status_label = _require_string(
            profile.get("status_label"),
            label=f"{path} subagent_profiles[{profile_index}].status_label",
        )
        role_names_for_profile = _require_string_list(
            profile.get("role_names"),
            label=f"{path} subagent_profiles[{profile_index}].role_names",
            allow_empty=True,
        )
        start_script = _require_string(
            profile.get("start_script"),
            label=f"{path} subagent_profiles[{profile_index}].start_script",
        )
        stop_script = _require_string(
            profile.get("stop_script"),
            label=f"{path} subagent_profiles[{profile_index}].stop_script",
        )
        start_lines = _require_string_list(
            profile.get("start_lines"),
            label=f"{path} subagent_profiles[{profile_index}].start_lines",
            allow_empty=True,
        )
        stop_lines = _require_string_list(
            profile.get("stop_lines"),
            label=f"{path} subagent_profiles[{profile_index}].stop_lines",
            allow_empty=True,
        )

        if profile_id in profile_ids:
            fail(f"{path} duplicate subagent profile id: {profile_id}")
        profile_ids.add(profile_id)
        if re.fullmatch(SUBAGENT_ROLE_NAME_PATTERN, profile_id) is None:
            fail(f"{path} subagent_profiles[{profile_index}].id is invalid: {profile_id}")

        for role_name in role_names_for_profile:
            if role_name not in role_names:
                fail(f"{path} subagent_profiles[{profile_index}] references unknown role name: {role_name}")

        for label, script_name in (
            ("start_script", start_script),
            ("stop_script", stop_script),
        ):
            if "/" in script_name or "\\" in script_name:
                fail(f"{path} subagent_profiles[{profile_index}].{label} must be a basename: {script_name}")
            if re.fullmatch(HOOK_SCRIPT_NAME_PATTERN, script_name) is None:
                fail(f"{path} subagent_profiles[{profile_index}].{label} must end with .pl: {script_name}")

        profile["id"] = profile_id
        profile["matcher"] = matcher
        profile["status_label"] = status_label
        profile["role_names"] = role_names_for_profile
        profile["start_script"] = start_script
        profile["stop_script"] = stop_script
        profile["start_lines"] = start_lines
        profile["stop_lines"] = stop_lines

    return payload


def build_tool_hook_groups(
    *,
    event_name: str,
    catalog_path_value: Path | None = None,
) -> list[dict[str, Any]]:
    if event_name not in SUPPORTED_TOOL_HOOK_EVENTS:
        fail(f"unsupported tool hook event: {event_name}")
    catalog = load_hook_catalog(catalog_path_value)
    groups: list[dict[str, Any]] = []
    for profile in catalog["tool_profiles"]:
        event_payload = profile["events"][event_name]
        groups.append(
            {
                "matcher": profile["matcher"],
                "hooks": [
                    {
                        "type": "command",
                        "command": f"perl ${{CODEX_HOME}}/hooks/scripts/{event_payload['script']}",
                        "timeout": event_payload["timeout"],
                        "statusMessage": event_payload["statusMessage"],
                    }
                ],
            }
        )
    return groups


def build_subagent_hook_groups(
    *,
    phase: str,
    catalog_path_value: Path | None = None,
) -> list[dict[str, Any]]:
    if phase not in {"start", "stop"}:
        fail(f"unsupported subagent hook phase: {phase}")
    catalog = load_hook_catalog(catalog_path_value)
    timeout = 20 if phase == "start" else 25
    verb = "Injecting" if phase == "start" else "Checking"
    suffix = "guidance" if phase == "start" else "completion gates"
    script_key = "start_script" if phase == "start" else "stop_script"

    groups: list[dict[str, Any]] = []
    for profile in catalog["subagent_profiles"]:
        groups.append(
            {
                "matcher": profile["matcher"],
                "hooks": [
                    {
                        "type": "command",
                        "command": f"perl ${{CODEX_HOME}}/hooks/scripts/{profile[script_key]}",
                        "timeout": timeout,
                        "statusMessage": f"{verb} {profile['status_label']} subagent {suffix}",
                    }
                ],
            }
        )
    return groups
