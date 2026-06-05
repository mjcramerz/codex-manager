import sys
import tomllib
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
from tests.hook_table_assertions import assert_expected_inline_hooks  # noqa: E402


class InstallCommandRoutingTests(unittest.TestCase):
    def _run_command(self, command: str, *, dry_run: bool = False) -> object:
        args = types.SimpleNamespace(command=command, dry_run=dry_run, compiled_dir="src/misc/compiled")
        with (
            patch.object(codex_install, "parse_args", return_value=args),
            patch.object(codex_install, "ensure_non_root_user"),
            patch.object(codex_install, "Installer", autospec=True) as installer_cls,
        ):
            if dry_run and command in {"install", "build-install"}:
                installer_cls.return_value._resolved_stage_root.return_value = codex_install.DRY_RUN_STAGE_ROOT
            rc = codex_install.run()
        self.assertEqual(rc, 0)
        installer = installer_cls.return_value
        installer.load.assert_called_once_with()
        return installer, installer_cls

    def test_nuke_does_not_run_full_validate(self) -> None:
        installer, _installer_cls = self._run_command("nuke")
        installer.validate.assert_not_called()
        installer.uninstall.assert_called_once_with()

    def test_uninstall_alias_does_not_run_full_validate(self) -> None:
        installer, _installer_cls = self._run_command("uninstall")
        installer.validate.assert_not_called()
        installer.uninstall.assert_called_once_with()

    def test_home_still_runs_full_validate(self) -> None:
        installer, _installer_cls = self._run_command("home")
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
        installer, _installer_cls = self._run_command("build-install")
        installer.validate.assert_called_once_with()
        installer.compile.assert_called_once()
        installer.build_install.assert_called_once_with(installer.compile.return_value)

    def test_update_runs_validate_then_apply_update(self) -> None:
        installer, _installer_cls = self._run_command("update")
        installer.validate.assert_called_once_with()
        installer.compile.assert_called_once()
        installer.apply_update.assert_called_once_with(installer.compile.return_value)

    def test_install_dry_run_uses_staged_installer_root(self) -> None:
        _installer, installer_cls = self._run_command("install", dry_run=True)
        installer_cls.assert_called_once()
        self.assertEqual(installer_cls.call_args.kwargs["dry_run"], False)
        self.assertEqual(installer_cls.call_args.kwargs["stage_root"], codex_install.DRY_RUN_STAGE_ROOT)

    def test_build_install_dry_run_uses_staged_installer_root(self) -> None:
        _installer, installer_cls = self._run_command("build-install", dry_run=True)
        installer_cls.assert_called_once()
        self.assertEqual(installer_cls.call_args.kwargs["dry_run"], False)
        self.assertEqual(installer_cls.call_args.kwargs["stage_root"], codex_install.DRY_RUN_STAGE_ROOT)

    def test_build_install_uses_source_build_environment_overrides(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = {
            "CODEX_SOURCE_BUILD_ROOT": "/tmp/from-installer/build",
            "CODEX_SHARE_DIR": "/tmp/share",
        }
        installer.stage_root = None
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

    def test_build_install_stage_mode_rewrites_source_build_roots(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = {"CODEX_SHARE_DIR": "/tmp/share"}
        installer.stage_root = Path("/data/dryrun/codex")
        installer.repo_root = Path("/tmp/repo")
        installer.dry_run = True
        with (
            patch.object(codex_install, "load_source_build_environment", return_value={"CODEX_SOURCE_BUILD_ROOT": "/tmp/from-process/build"}),
            patch.object(codex_install, "load_source_build_settings") as load_source_build_settings,
        ):
            load_source_build_settings.return_value = types.SimpleNamespace(
                repo_url="https://github.com/imjcramer/codex.git",
                output_dir=Path("/data/dryrun/codex/source-build/output"),
            )
            codex_install.Installer.build_install(installer, types.SimpleNamespace(config_toml=Path("/tmp/config.toml")))

        load_source_build_settings.assert_called_once()
        merged_env = load_source_build_settings.call_args.args[0]
        self.assertEqual(merged_env["CODEX_SOURCE_BUILD_ROOT"], "/data/dryrun/codex/source-build/build")
        self.assertEqual(merged_env["CODEX_SOURCE_CACHE_ROOT"], "/data/dryrun/codex/source-build/cache")
        self.assertEqual(merged_env["CODEX_SOURCE_OUTPUT_DIR"], "/data/dryrun/codex/source-build/output")
        self.assertEqual(merged_env["CODEX_SOURCE_CHECKOUT_DIR"], "/data/dryrun/codex/source-build/checkout")

    def test_build_install_runs_full_source_backed_install_flow(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = {"CODEX_SHARE_DIR": "/tmp/share"}
        installer.stage_root = None
        installer.repo_root = Path("/tmp/repo")
        installer.dry_run = False
        installer._log = lambda _message: None
        artifacts = types.SimpleNamespace(config_toml=Path("/tmp/config.toml"))
        settings = types.SimpleNamespace(output_dir=Path("/tmp/build/output"))
        build_result = types.SimpleNamespace(output_dir=Path("/tmp/build/output"))
        calls: list[str] = []

        for name in ("_prepare_runtime_install_state", "_install_runtime_binary_wrappers"):
            setattr(installer, name, Mock(side_effect=lambda *args, _name=name, **kwargs: calls.append(_name)))
        installer._install_source_build_binary = Mock(
            side_effect=lambda output_dir: calls.append("_install_source_build_binary") or ["codex"]
        )

        with (
            patch.object(codex_install, "load_source_build_environment", return_value={}),
            patch.object(codex_install, "load_source_build_settings", return_value=settings),
            patch.object(codex_install, "build_from_settings", return_value=build_result) as build_from_settings,
        ):
            codex_install.Installer.build_install(installer, artifacts)

        build_from_settings.assert_called_once_with(settings)
        self.assertEqual(
            calls,
            [
                "_prepare_runtime_install_state",
                "_install_source_build_binary",
                "_install_runtime_binary_wrappers",
            ],
        )
        installer._prepare_runtime_install_state.assert_called_once_with(artifacts, flow="install")
        installer._install_source_build_binary.assert_called_once_with(build_result.output_dir)
        installer._install_runtime_binary_wrappers.assert_called_once_with(["codex"])


class InstallConfigToleranceTests(unittest.TestCase):
    def test_resolve_placeholders_allows_literal_regex_dollar(self) -> None:
        rendered = resolve_placeholders("^(startup|resume|clear|compact)$", {}, "config/usr/apps.toml.hooks.SessionStart.matcher")
        self.assertEqual(rendered, "^(startup|resume|clear|compact)$")

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

    def test_home_config_render_merges_full_apps_hooks_table(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.repo_root = REPO_ROOT
        installer.repo_layout = codex_install.RepoLayout.from_repo_root(REPO_ROOT)
        installer._warnings_emitted = set()
        installer._warn_once = lambda _message: None
        installer.plugins_payload = codex_install.parse_toml_file(installer.repo_layout.user_apps_path)

        env = codex_install.parse_env_file(REPO_ROOT / ".env")
        vars_payload = codex_install.parse_toml_file(REPO_ROOT / "vars.toml")
        global_vars = codex_install.parse_variable_table(
            vars_payload,
            path_label="vars.toml",
            table_name="global_variables",
            item_label="global variable",
        )
        runtime_vars = codex_install.derive_runtime_globals_from_env(env)
        sqlite_home = global_vars.get("CODEX_SQLITE_HOME", "").strip()
        if sqlite_home:
            runtime_vars["CODEX_SQLITE_HOME"] = sqlite_home
        installer.variables = dict(env)
        installer.variables.update(runtime_vars)

        with patch.object(installer, "_instruction_file_overrides", return_value={}):
            rendered = installer._render_user_config_toml("", Path(runtime_vars["CODEX_HOME"]) / "config.toml")

        payload = tomllib.loads(rendered)
        hooks = payload.get("hooks")
        assert_expected_inline_hooks(self, hooks)

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

    def test_stage_setup_environment_writes_activation_script_only(self) -> None:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.stage_root = Path("/data/dryrun/codex")
        installer.global_vars = {"CODEX_HOME": "/data/dryrun/codex/usr/home"}
        installer.launch_env = {"TMPDIR": "/data/dryrun/codex/tmp"}
        installer._log = lambda _message: None
        installer._install_stage_environment_exports = Mock()
        installer._sync_global_environment = Mock()

        codex_install.Installer.setup_environment(installer)

        installer._install_stage_environment_exports.assert_called_once_with()
        installer._sync_global_environment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
