from __future__ import annotations

from dataclasses import dataclass
import re
import tomllib
from pathlib import Path
from typing import Any

from common import fail
from hook_runtime_catalog import build_tool_hook_groups
from hook_runtime_catalog import SUPPORTED_TOOL_HOOK_EVENTS
from hook_runtime_catalog import load_hook_catalog


@dataclass(frozen=True)
class HookGroupSpec:
    matcher: str | None
    script_name: str


def _subagent_group_specs(phase: str) -> tuple[HookGroupSpec, ...]:
    catalog = load_hook_catalog()
    script_key = "start_script" if phase == "start" else "stop_script"
    return tuple(
        HookGroupSpec(
            matcher=str(profile["matcher"]),
            script_name=str(profile[script_key]),
        )
        for profile in catalog["subagent_profiles"]
    )


def _tool_group_specs(event_name: str) -> tuple[HookGroupSpec, ...]:
    return tuple(
        HookGroupSpec(
            matcher=str(group["matcher"]),
            script_name=str(group["hooks"][0]["command"]).rsplit("/", 1)[-1],
        )
        for group in build_tool_hook_groups(event_name=event_name)
    )


EXPECTED_HOOK_LAYOUT: dict[str, tuple[HookGroupSpec, ...]] = {
    "SessionStart": (HookGroupSpec(matcher="^(startup|resume|clear|compact)$", script_name="session_start.pl"),),
    "UserPromptSubmit": (HookGroupSpec(matcher=None, script_name="user_prompt_submit.pl"),),
    "PreToolUse": _tool_group_specs("PreToolUse"),
    "PermissionRequest": _tool_group_specs("PermissionRequest"),
    "PostToolUse": _tool_group_specs("PostToolUse"),
    "PreCompact": (HookGroupSpec(matcher=None, script_name="pre_compact.pl"),),
    "PostCompact": (HookGroupSpec(matcher=None, script_name="post_compact.pl"),),
    "SubagentStart": _subagent_group_specs("start"),
    "SubagentStop": _subagent_group_specs("stop"),
    "Stop": (HookGroupSpec(matcher=None, script_name="stop.pl"),),
}

SUPPORTED_HOOK_EVENTS = frozenset(EXPECTED_HOOK_LAYOUT)
TOOL_MATCHER_EVENTS = frozenset(SUPPORTED_TOOL_HOOK_EVENTS)
SUBAGENT_MATCHER_EVENTS = frozenset({"SubagentStart", "SubagentStop"})
MATCHER_UNSUPPORTED_EVENTS = frozenset({"UserPromptSubmit", "Stop"})
HOOK_SCRIPT_COMMAND_PATTERN = re.compile(r"\$\{CODEX_HOME\}/hooks/scripts/([A-Za-z0-9_.-]+\.pl)\b")


def _load_apps_payload(apps_path: Path) -> dict[str, Any]:
    if not apps_path.is_file():
        fail(f"missing TOML file: {apps_path}")
    try:
        payload = tomllib.loads(apps_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"invalid TOML at {apps_path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"invalid TOML payload shape at {apps_path}")
    return payload


def _hooks_table(payload: dict[str, Any], *, path_label: str) -> dict[str, Any]:
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        fail(f"{path_label} must define a non-empty [hooks] table")
    missing = sorted(set(SUPPORTED_HOOK_EVENTS) - set(hooks))
    if missing:
        fail(f"{path_label} is missing supported hook events: {', '.join(missing)}")
    unknown = sorted(set(hooks) - SUPPORTED_HOOK_EVENTS)
    if unknown:
        fail(f"{path_label} contains unsupported hook events: {', '.join(unknown)}")
    return hooks


def load_inline_hooks_config(apps_path: Path) -> dict[str, Any]:
    payload = _load_apps_payload(apps_path)
    return _hooks_table(payload, path_label=str(apps_path))


def _script_name_from_command(command: str) -> str | None:
    script_match = HOOK_SCRIPT_COMMAND_PATTERN.search(command)
    if script_match is None:
        return None
    return script_match.group(1)


def _validate_expected_group_layout(
    *,
    path_label: str,
    event_name: str,
    group_index: int,
    group: dict[str, Any],
    expected_group: HookGroupSpec,
) -> None:
    group_label = f"{path_label} hooks.{event_name}[{group_index}]"
    matcher = group.get("matcher")
    if expected_group.matcher is None:
        if matcher is not None:
            fail(f"{group_label}.matcher is not supported for {event_name}")
    elif matcher != expected_group.matcher:
        fail(
            f"{group_label}.matcher must be `{expected_group.matcher}` "
            f"to keep the inline hook layout aligned with the runtime contract"
        )

    handlers = group.get("hooks")
    if not isinstance(handlers, list):
        return
    script_names = {
        script_name
        for handler in handlers
        if isinstance(handler, dict)
        for script_name in [_script_name_from_command(str(handler.get('command', '')))]
        if script_name is not None
    }
    if expected_group.script_name not in script_names:
        fail(
            f"{group_label}.hooks must include `{expected_group.script_name}` "
            f"to keep the inline hook layout aligned with the runtime contract"
        )


def validate_inline_hooks_config(
    apps_path: Path,
    scripts_dir: Path,
    *,
    hooks_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_label = str(apps_path)
    hooks = _hooks_table({"hooks": hooks_payload} if hooks_payload is not None else _load_apps_payload(apps_path), path_label=path_label)
    if not scripts_dir.is_dir():
        fail(f"missing hook scripts directory: {scripts_dir}")

    for event_name in sorted(hooks):
        groups = hooks[event_name]
        if not isinstance(groups, list) or not groups:
            fail(f"{path_label} hooks.{event_name} must be a non-empty array of matcher groups")
        expected_groups = EXPECTED_HOOK_LAYOUT[event_name]
        if len(groups) != len(expected_groups):
            fail(
                f"{path_label} hooks.{event_name} must define exactly {len(expected_groups)} matcher group(s) "
                f"to stay aligned with the runtime contract"
            )

        for group_index, group in enumerate(groups):
            group_label = f"{path_label} hooks.{event_name}[{group_index}]"
            if not isinstance(group, dict):
                fail(f"{group_label} must be a table")
            matcher = group.get("matcher")
            if event_name in TOOL_MATCHER_EVENTS | SUBAGENT_MATCHER_EVENTS:
                if not isinstance(matcher, str) or not matcher.strip():
                    fail(f"{group_label}.matcher must be a non-empty string")
            elif event_name in MATCHER_UNSUPPORTED_EVENTS:
                if matcher is not None:
                    fail(f"{group_label}.matcher is not supported for {event_name}")
            elif matcher is not None and (not isinstance(matcher, str) or not matcher.strip()):
                fail(f"{group_label}.matcher must be a non-empty string when provided")

            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                fail(f"{group_label}.hooks must be a non-empty array")

            for handler_index, handler in enumerate(handlers):
                handler_label = f"{group_label}.hooks[{handler_index}]"
                if not isinstance(handler, dict):
                    fail(f"{handler_label} must be a table")
                if handler.get("type") != "command":
                    fail(f"{handler_label}.type must be command")
                command = handler.get("command")
                if not isinstance(command, str) or not command.strip():
                    fail(f"{handler_label}.command must be a non-empty string")
                if "hooks.json" in command:
                    fail(f"{handler_label}.command must not reference hooks.json")
                script_match = HOOK_SCRIPT_COMMAND_PATTERN.search(command)
                if script_match is not None:
                    script_path = scripts_dir / script_match.group(1)
                    if not script_path.is_file():
                        fail(f"{handler_label}.command references a missing hook script: {script_path}")
                timeout = handler.get("timeout")
                if timeout is not None and (not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 600):
                    fail(f"{handler_label}.timeout must be an integer between 1 and 600 seconds")
                status_message = handler.get("statusMessage")
                if status_message is not None and (not isinstance(status_message, str) or not status_message.strip()):
                    fail(f"{handler_label}.statusMessage must be a non-empty string when provided")

            _validate_expected_group_layout(
                path_label=path_label,
                event_name=event_name,
                group_index=group_index,
                group=group,
                expected_group=expected_groups[group_index],
            )

    return hooks
