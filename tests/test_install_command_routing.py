import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

import codex_install  # noqa: E402


class InstallCommandRoutingTests(unittest.TestCase):
    def _run_command(self, command: str) -> object:
        args = types.SimpleNamespace(command=command, dry_run=False, compiled_dir="src/misc/compiled")
        with (
            patch.object(codex_install, "parse_args", return_value=args),
            patch.object(codex_install, "ensure_non_root_user"),
            patch.object(codex_install, "Installer", autospec=True) as installer_cls,
        ):
            rc = codex_install.run()
        self.assertEqual(rc, 0)
        installer = installer_cls.return_value
        installer.load.assert_called_once_with()
        return installer

    def test_nuke_does_not_run_full_validate(self) -> None:
        installer = self._run_command("nuke")
        installer.validate.assert_not_called()
        installer.uninstall.assert_called_once_with()

    def test_home_still_runs_full_validate(self) -> None:
        installer = self._run_command("home")
        installer.validate.assert_called_once_with()
        installer.apply_home_bundle.assert_called_once_with()


class InstallConfigToleranceTests(unittest.TestCase):
    def test_home_bundle_keeps_plugins_hooks_and_skills(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        with (
            patch.object(installer, "apply_home") as apply_home,
            patch.object(installer, "apply_apps") as apply_apps,
            patch.object(installer, "apply_skills") as apply_skills,
        ):
            codex_install.Installer.apply_home_bundle(installer)

        apply_home.assert_called_once_with()
        apply_apps.assert_called_once_with()
        apply_skills.assert_called_once_with()

    def test_parse_launch_env_table_allows_missing_table(self) -> None:
        parsed = codex_install.parse_launch_env_table(
            {},
            path_label="config/usr/env.toml",
            variables={},
        )
        self.assertEqual(parsed, {})

    def test_instruction_override_missing_key_warns_without_blocking(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer._warnings_emitted = set()
        with (
            patch.object(
                installer,
                "_instruction_file_overrides",
                return_value={
                    "missing_key": "./missing.md",
                    "present_key": "./present.md",
                },
            ),
            patch("builtins.print") as print_mock,
        ):
            rendered = installer._apply_instruction_file_overrides(
                "[prompt_overrides]\npresent_key = \"./before.md\"\n"
            )

        self.assertIn('present_key = "./present.md"', rendered)
        self.assertNotIn("missing_key =", rendered)
        print_mock.assert_called_once_with(
            "[warn] instruction metadata references config keys left unset in the rendered user config: "
            "`missing_key`; continuing without those overrides"
        )


if __name__ == "__main__":
    unittest.main()
