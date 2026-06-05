from __future__ import annotations

from typing import Any
from unittest import TestCase

from hooks_builder import EXPECTED_HOOK_LAYOUT, SUPPORTED_HOOK_EVENTS


def _assert_hook_command_matches(testcase: TestCase, actual_command: object, expected_command: str, event_name: str) -> None:
    testcase.assertIsInstance(actual_command, str, event_name)
    if actual_command == expected_command:
        return
    expected_suffix = expected_command.split("${CODEX_HOME}", 1)[-1]
    testcase.assertTrue(
        isinstance(actual_command, str) and actual_command.startswith("perl ") and actual_command.endswith(expected_suffix),
        f"{event_name} command drift: {actual_command!r} != {expected_command!r}",
    )


def assert_expected_inline_hooks(testcase: TestCase, hooks: dict[str, Any]) -> None:
    testcase.assertIsInstance(hooks, dict)
    testcase.assertEqual(set(hooks), set(SUPPORTED_HOOK_EVENTS))

    for event_name, expected_groups in EXPECTED_HOOK_LAYOUT.items():
        groups = hooks[event_name]
        testcase.assertEqual(len(groups), len(expected_groups), event_name)
        for group, expected_group in zip(groups, expected_groups, strict=True):
            testcase.assertEqual(group.get("matcher"), expected_group.matcher)
            handlers = group.get("hooks", [])
            testcase.assertEqual(len(handlers), 1, event_name)
            testcase.assertIsInstance(handlers[0], dict, event_name)
            testcase.assertEqual(handlers[0].get("type"), "command", event_name)
            _assert_hook_command_matches(testcase, handlers[0].get("command"), expected_group.handler.command, event_name)
            testcase.assertEqual(handlers[0].get("timeout"), expected_group.handler.timeout, event_name)
            testcase.assertEqual(handlers[0].get("statusMessage"), expected_group.handler.status_message, event_name)
