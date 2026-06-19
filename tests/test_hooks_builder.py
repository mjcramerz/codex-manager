import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from common import InstallError  # noqa: E402
from common import parse_toml_file  # noqa: E402
from hooks_builder import validate_hooks_config  # noqa: E402
from tests.hook_table_assertions import assert_expected_inline_hooks  # noqa: E402


HOOKS_TOML_PATH = REPO_ROOT / "config" / "usr" / "hooks.toml"
HOOK_SCRIPTS_DIR = REPO_ROOT / "resources" / "hooks" / "scripts"


def _hooks_payload() -> dict:
    hooks_payload = parse_toml_file(HOOKS_TOML_PATH)
    hooks = hooks_payload.get("hooks")
    if not isinstance(hooks, dict):
        raise AssertionError("hooks payload is missing a hooks table")
    return hooks


class HookBuilderTests(unittest.TestCase):
    def test_validate_hooks_config_accepts_repo_layout(self) -> None:
        hooks = validate_hooks_config(
            HOOKS_TOML_PATH,
            HOOK_SCRIPTS_DIR,
            hooks_payload=_hooks_payload(),
        )
        assert_expected_inline_hooks(self, hooks)

    def test_validate_hooks_config_rejects_tool_matcher_drift(self) -> None:
        hooks = copy.deepcopy(_hooks_payload())
        hooks["PreToolUse"][0]["matcher"] = "^shell$"

        with self.assertRaisesRegex(InstallError, r"hooks\.PreToolUse\[0\]\.matcher must be"):
            validate_hooks_config(HOOKS_TOML_PATH, HOOK_SCRIPTS_DIR, hooks_payload=hooks)

    def test_validate_hooks_config_rejects_subagent_command_drift(self) -> None:
        hooks = copy.deepcopy(_hooks_payload())
        hooks["SubagentStop"][0]["hooks"][0]["command"] = "perl ${CODEX_HOME}/hooks/scripts/subagent_stop.pl"

        with self.assertRaisesRegex(InstallError, r"hooks\.SubagentStop\[0\]\.hooks\[0\]\.command must be"):
            validate_hooks_config(HOOKS_TOML_PATH, HOOK_SCRIPTS_DIR, hooks_payload=hooks)

    def test_validate_hooks_config_rejects_timeout_drift(self) -> None:
        hooks = copy.deepcopy(_hooks_payload())
        hooks["PostToolUse"][1]["hooks"][0]["timeout"] = 99

        with self.assertRaisesRegex(InstallError, r"hooks\.PostToolUse\[1\]\.hooks\[0\]\.timeout must be"):
            validate_hooks_config(HOOKS_TOML_PATH, HOOK_SCRIPTS_DIR, hooks_payload=hooks)
