from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from common import fail

SUPPORTED_HOOK_EVENTS = frozenset(
    {
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "PreCompact",
        "PostCompact",
        "SessionStart",
        "SubagentStart",
        "SubagentStop",
        "UserPromptSubmit",
        "Stop",
    }
)
TOOL_MATCHER_EVENTS = frozenset({"PreToolUse", "PermissionRequest", "PostToolUse"})
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
    unknown = sorted(set(hooks) - SUPPORTED_HOOK_EVENTS)
    if unknown:
        fail(f"{path_label} contains unsupported hook events: {', '.join(unknown)}")
    return hooks


def load_inline_hooks_config(apps_path: Path) -> dict[str, Any]:
    payload = _load_apps_payload(apps_path)
    return _hooks_table(payload, path_label=str(apps_path))


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
        if event_name in TOOL_MATCHER_EVENTS and len(groups) < 3:
            fail(f"{path_label} hooks.{event_name} must define separate shell, edit, and MCP matcher groups")

        for group_index, group in enumerate(groups):
            group_label = f"{path_label} hooks.{event_name}[{group_index}]"
            if not isinstance(group, dict):
                fail(f"{group_label} must be a table")
            matcher = group.get("matcher")
            if event_name in TOOL_MATCHER_EVENTS:
                if not isinstance(matcher, str) or not matcher.strip():
                    fail(f"{group_label}.matcher must be a non-empty string")
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

    return hooks
