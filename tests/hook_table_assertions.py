from __future__ import annotations

from typing import Any
from unittest import TestCase

from hooks_builder import EXPECTED_HOOK_LAYOUT, SUPPORTED_HOOK_EVENTS


def assert_expected_inline_hooks(testcase: TestCase, hooks: dict[str, Any]) -> None:
    testcase.assertIsInstance(hooks, dict)
    testcase.assertEqual(set(hooks), set(SUPPORTED_HOOK_EVENTS))

    for event_name, expected_groups in EXPECTED_HOOK_LAYOUT.items():
        groups = hooks[event_name]
        testcase.assertEqual(len(groups), len(expected_groups), event_name)
        for group, expected_group in zip(groups, expected_groups, strict=True):
            testcase.assertEqual(group.get("matcher"), expected_group.matcher)
            commands = [
                handler.get("command")
                for handler in group.get("hooks", [])
                if isinstance(handler, dict)
            ]
            testcase.assertTrue(
                any(isinstance(command, str) and expected_group.script_name in command for command in commands),
                f"{event_name} missing {expected_group.script_name}",
            )
