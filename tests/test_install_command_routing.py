import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

import codex_install  # noqa: E402
from common import resolve_placeholders  # noqa: E402


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

    def test_build_src_uses_source_build_helpers_without_installer(self) -> None:
        args = types.SimpleNamespace(command="build-src", dry_run=False, compiled_dir="src/misc/compiled")
        settings = object()
        with (
            patch.object(codex_install, "parse_args", return_value=args),
            patch.object(codex_install, "ensure_non_root_user"),
            patch.object(codex_install, "load_source_build_environment", return_value={"CODEX_SOURCE_REPO_URL": "https://example.invalid/repo.git", "CODEX_SOURCE_BUILD_ROOT": "/tmp/build", "CODEX_SOURCE_CACHE_ROOT": "/tmp/cache"}),
            patch.object(codex_install, "load_source_build_settings", return_value=settings),
            patch.object(codex_install, "build_from_settings") as build_from_settings,
            patch.object(codex_install, "Installer", autospec=True) as installer_cls,
        ):
            build_from_settings.return_value = types.SimpleNamespace(output_dir=Path("/tmp/build/output"))
            rc = codex_install.run()

        self.assertEqual(rc, 0)
        installer_cls.assert_not_called()
        build_from_settings.assert_called_once_with(settings)

    def test_build_install_runs_validate_then_build_install(self) -> None:
        installer = self._run_command("build-install")
        installer.validate.assert_called_once_with()
        installer.compile.assert_called_once()
        installer.build_install.assert_called_once_with(installer.compile.return_value)

    def test_build_install_uses_source_build_environment_overrides(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = {
            "CODEX_SOURCE_BUILD_ROOT": "/tmp/from-installer/build",
            "CODEX_SHARE_DIR": "/tmp/share",
        }
        installer.repo_root = Path("/tmp/repo")
        installer.dry_run = True
        with (
            patch.object(codex_install, "load_source_build_environment", return_value={"CODEX_SOURCE_BUILD_ROOT": "/tmp/from-process/build"}),
            patch.object(codex_install, "load_source_build_settings") as load_source_build_settings,
        ):
            load_source_build_settings.return_value = types.SimpleNamespace(
                repo_url="https://github.com/imjcramer/codex.git",
                output_dir=Path("/tmp/from-process/build/output"),
            )
            codex_install.Installer.build_install(installer, types.SimpleNamespace(config_toml=Path("/tmp/config.toml")))

        load_source_build_settings.assert_called_once()
        merged_env = load_source_build_settings.call_args.args[0]
        self.assertEqual(merged_env["CODEX_SOURCE_BUILD_ROOT"], "/tmp/from-process/build")

    def test_build_install_runs_full_source_backed_install_flow(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = {"CODEX_SHARE_DIR": "/tmp/share"}
        installer.repo_root = Path("/tmp/repo")
        installer.dry_run = False
        installer._log = lambda _message: None
        artifacts = types.SimpleNamespace(config_toml=Path("/tmp/config.toml"))
        settings = types.SimpleNamespace(output_dir=Path("/tmp/build/output"))
        build_result = types.SimpleNamespace(output_dir=Path("/tmp/build/output"))
        calls: list[str] = []

        for name in (
            "_backup_install_state",
            "_ensure_runtime_directories",
            "_ensure_lookup_secret_service_file",
            "_secure_exec_directories",
            "apply_home_bundle",
            "apply_admin",
            "setup_environment",
            "_sync_tmpfs_helper",
            "mount_runtime_tmpfs",
            "_install_runtime_binary_wrappers",
        ):
            setattr(installer, name, Mock(side_effect=lambda *args, _name=name, **kwargs: calls.append(_name)))
        installer._install_source_build_binary = Mock(
            side_effect=lambda output_dir: calls.append("_install_source_build_binary") or ["codex"]
        )

        with (
            patch.object(codex_install, "load_source_build_environment", return_value={}),
            patch.object(codex_install, "load_source_build_settings", return_value=settings),
            patch.object(codex_install, "build_if_missing", return_value=build_result) as build_if_missing,
        ):
            codex_install.Installer.build_install(installer, artifacts)

        build_if_missing.assert_called_once_with(settings)
        self.assertEqual(
            calls,
            [
                "_backup_install_state",
                "_ensure_runtime_directories",
                "_ensure_lookup_secret_service_file",
                "_secure_exec_directories",
                "apply_home_bundle",
                "apply_admin",
                "setup_environment",
                "_sync_tmpfs_helper",
                "mount_runtime_tmpfs",
                "_install_source_build_binary",
                "_install_runtime_binary_wrappers",
            ],
        )
        installer.apply_admin.assert_called_once_with(artifacts)
        installer._install_source_build_binary.assert_called_once_with(build_result.output_dir)
        installer._install_runtime_binary_wrappers.assert_called_once_with(["codex"])


class InstallConfigToleranceTests(unittest.TestCase):
    def test_resolve_placeholders_allows_literal_regex_dollar(self) -> None:
        rendered = resolve_placeholders("^(startup|resume)$", {}, "config/usr/apps.toml.hooks.SessionStart.matcher")
        self.assertEqual(rendered, "^(startup|resume)$")

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
                    "instruction_overrides.tools.missing_key": "./missing.md",
                    "instruction_overrides.tools.apply_patch_instructions_file": "./present.md",
                },
            ),
            patch("builtins.print") as print_mock,
        ):
            rendered = installer._apply_instruction_file_overrides(
                "[instruction_overrides.tools]\napply_patch_instructions_file = \"./before.md\"\n"
            )

        self.assertIn('apply_patch_instructions_file = "./present.md"', rendered)
        self.assertNotIn("missing_key =", rendered)
        print_mock.assert_called_once_with(
            "[warn] instruction metadata references config keys left unset in the rendered user config: "
            "`instruction_overrides.tools.missing_key`; continuing without those overrides"
        )

    def test_instruction_override_rewrites_nested_dotted_key(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer._warnings_emitted = set()
        with patch.object(
            installer,
            "_instruction_file_overrides",
            return_value={
                "instruction_overrides.tools.apply_patch_instructions_file": "./after.md",
            },
        ):
            rendered = installer._apply_instruction_file_overrides(
                "\n".join(
                    [
                        '[instruction_overrides.tools]',
                        'apply_patch_instructions_file = "./before.md"',
                        "",
                    ]
                )
            )

        self.assertIn('apply_patch_instructions_file = "./after.md"', rendered)


if __name__ == "__main__":
    unittest.main()
