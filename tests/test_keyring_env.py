import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "src" / "python"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from lib import keyring_env  # noqa: E402
from lib.managed_secrets import ManagedSecretsConfig  # noqa: E402
from lib.managed_secrets import ManagedSecretsError  # noqa: E402
from lib.runtime import render_codex_shim  # noqa: E402
import codex_install  # noqa: E402


class ManagedSecretsHelperTests(unittest.TestCase):
    def test_collect_lookup_environment_uses_host_config_bearer_env_vars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_path = Path(tmpdir) / "secrets.toml"
            host_config_path = Path(tmpdir) / "config.toml"
            secrets_path.write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-mcp"',
                        "",
                        "[mcp_servers.linear]",
                        "LINEAR_API_KEY = false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            host_config_path.write_text(
                "\n".join(
                    [
                        "[mcp_servers.linear]",
                        'url = "https://mcp.linear.app/mcp"',
                        "enabled = true",
                        'bearer_token_env_var = "LINEAR_API_KEY"',
                        "",
                        "[mcp_servers.vercel]",
                        'url = "https://mcp.vercel.com"',
                        "enabled = false",
                        'bearer_token_env_var = "VERCEL_API_TOKEN"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch(
                "lib.keyring_env.lookup_managed_secret",
                side_effect=lambda config, server_name: (
                    "linear-secret"
                    if server_name == "linear"
                    else "vercel-secret"
                    if server_name == "vercel"
                    else ""
                ),
            ):
                exported = keyring_env.collect_lookup_environment(host_config_path, secrets_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "linear-secret"})

    def test_collect_lookup_environment_prefers_existing_environment_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_path = Path(tmpdir) / "secrets.toml"
            host_config_path = Path(tmpdir) / "config.toml"
            secrets_path.write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-mcp"',
                        "",
                        "[mcp_servers.linear]",
                        "LINEAR_API_KEY = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            host_config_path.write_text(
                "\n".join(
                    [
                        "[mcp_servers.linear]",
                        'url = "https://mcp.linear.app/mcp"',
                        "enabled = true",
                        'bearer_token_env_var = "LINEAR_API_KEY"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch("lib.keyring_env.lookup_managed_secret", return_value="keyring-secret"),
                patch.dict(os.environ, {"LINEAR_API_KEY": "env-secret"}, clear=False),
            ):
                exported = keyring_env.collect_lookup_environment(host_config_path, secrets_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "env-secret"})

    def test_runtime_mcp_bearer_env_map_rejects_command_transport(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            host_config_path = Path(tmpdir) / "config.toml"
            host_config_path.write_text(
                "\n".join(
                    [
                        "[mcp_servers.context7]",
                        'command = "/usr/bin/context7"',
                        "enabled = true",
                        'bearer_token_env_var = "CONTEXT7_API_KEY"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                keyring_env.KeyringEnvError,
                "uses command transport and must not declare bearer_token_env_var",
            ):
                keyring_env._runtime_mcp_bearer_env_map(host_config_path)

    def test_secrets_config_from_env_file_uses_codex_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("CODEX_ROOT_DIR=/data/codex\n", encoding="utf-8")

            secrets_path = keyring_env.secrets_config_from_env_file(env_path)

        self.assertEqual(secrets_path, Path("/data/codex/lookup/secrets.toml"))

    def test_host_config_from_env_file_uses_codex_user_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "CODEX_ROOT_DIR=/data/codex",
                        "CODEX_USER_DIR=/data/codex/user",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            host_config_path = keyring_env.host_config_from_env_file(env_path)

        self.assertEqual(host_config_path, Path("/data/codex/user/home/config.toml"))

    def test_lookup_shell_execs_interactive_shell(self) -> None:
        with (
            patch("lib.keyring_env.collect_lookup_environment", return_value={"LINEAR_API_KEY": "linear-secret"}),
            patch("os.execvpe") as execvpe,
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
        ):
            rc = keyring_env.lookup_shell(
                Path("/data/codex/lookup/secrets.toml"),
                Path("/data/codex/home/config.toml"),
                "/bin/bash",
            )

        self.assertEqual(rc, 0)
        execvpe.assert_called_once()
        path, argv, env = execvpe.call_args.args
        self.assertEqual(path, "/bin/bash")
        self.assertEqual(argv, ["/bin/bash", "-i"])
        self.assertEqual(env["LINEAR_API_KEY"], "linear-secret")

    def test_lookup_exec_strips_helper_delimiter_and_preserves_user_args(self) -> None:
        with (
            patch("lib.keyring_env.collect_lookup_environment", return_value={}),
            patch("os.execvpe") as execvpe,
        ):
            rc = keyring_env.lookup_exec(
                "/bin/echo",
                ["--", "--", "--foo"],
                Path("/data/codex/lookup/secrets.toml"),
                Path("/data/codex/home/config.toml"),
            )

        self.assertEqual(rc, 0)
        execvpe.assert_called_once_with(
            "/bin/echo",
            ["/bin/echo", "--", "--foo"],
            unittest.mock.ANY,
        )

    def test_render_codex_shim_uses_env_gated_managed_secret_helper(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
            wrapper_dir=Path("/data/bin"),
            managed_secrets_path=Path("/data/codex/lookup/secrets.toml"),
            managed_secret_helper_path=Path("/data/codex/share/helpers/codex-secret-tool-env.py"),
            host_config_path=Path("/data/codex/home/config.toml"),
        )

        self.assertIn("/data/codex/share/bin/codex", rendered)
        self.assertIn('"/data/bin"', rendered)
        self.assertNotIn('"/data/codex/share/shims"', rendered)
        self.assertIn('--secrets-file "/data/codex/lookup/secrets.toml"', rendered)
        self.assertIn('--host-config "/data/codex/home/config.toml"', rendered)
        self.assertIn('if [ -n "${CODEX_INJECT_SECRETS:-}" ]; then', rendered)
        self.assertIn("codex-secret-tool-env.py", rendered)
        self.assertNotIn("--lookup-file", rendered)
        self.assertNotIn("--secret-service", rendered)
        self.assertNotIn('if [ "${codex_arg}" = "--k" ]; then', rendered)

    def test_render_codex_shim_skips_lookup_block_when_unconfigured(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
            wrapper_dir=Path("/data/bin"),
        )
        self.assertNotIn("--secrets-file", rendered)
        self.assertNotIn("--lookup-file", rendered)


class InstallerManagedSecretsTests(unittest.TestCase):
    def _make_installer(
        self,
        *,
        env: dict[str, str] | None = None,
        secrets_config: ManagedSecretsConfig | None = None,
        repo_root: Path | None = None,
    ) -> codex_install.Installer:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = env or {}
        installer.secrets_config = secrets_config
        installer.repo_root = repo_root or Path("/tmp/repo")
        installer.env_path = installer.repo_root / ".env"
        installer.dry_run = False
        installer._log = lambda _message: None
        installer._warn_once = Mock()
        return installer

    def test_prompt_managed_secret_value_uses_visible_input(self) -> None:
        installer = self._make_installer()

        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch("builtins.input", return_value=" visible-secret ") as input_mock,
        ):
            value = codex_install.Installer._prompt_managed_secret_value(
                installer,
                server_name="vercel",
                key="VERCEL_API_TOKEN",
            )

        self.assertEqual(value, "visible-secret")
        input_mock.assert_called_once_with(
            "Enter VERCEL_API_TOKEN for mcp_servers.vercel (or 's' to skip): "
        )

    def test_prompt_managed_secret_value_skips_on_s(self) -> None:
        installer = self._make_installer()

        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch("builtins.input", return_value="s"),
        ):
            value = codex_install.Installer._prompt_managed_secret_value(
                installer,
                server_name="vercel",
                key="VERCEL_API_TOKEN",
            )

        self.assertIsNone(value)

    def test_prompt_managed_secret_value_retries_on_empty_input(self) -> None:
        installer = self._make_installer()

        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch("builtins.input", side_effect=["", " retry-secret "]) as input_mock,
            patch("builtins.print") as print_mock,
        ):
            value = codex_install.Installer._prompt_managed_secret_value(
                installer,
                server_name="vercel",
                key="VERCEL_API_TOKEN",
            )

        self.assertEqual(value, "retry-secret")
        self.assertEqual(input_mock.call_count, 2)
        print_mock.assert_called_once_with(
            "[warn] VERCEL_API_TOKEN cannot be empty; enter a value or 's' to skip"
        )

    def test_repo_secrets_file_tracks_vendor_mcp_token_servers(self) -> None:
        installer = codex_install.Installer(repo_root=REPO_ROOT, dry_run=True)
        installer.load()
        installer._validate_managed_secrets_config()

    def test_sync_managed_secrets_file_overwrites_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            source_file = repo_root / "secrets.toml"
            source_file.write_text(
                'version = 1\nservice = "codex-mcp"\n\n[mcp_servers.linear]\nLINEAR_API_KEY = true\n',
                encoding="utf-8",
            )

            installer = self._make_installer(
                env={"CODEX_ROOT_DIR": str(Path(tmpdir) / "runtime")},
                repo_root=repo_root,
            )
            installer._needs_sudo_write = lambda _path: False

            installed_file = Path(tmpdir) / "runtime" / "lookup" / "secrets.toml"
            installed_file.parent.mkdir(parents=True, exist_ok=True)
            installed_file.write_text(
                'version = 1\nservice = "codex-mcp"\n\n[mcp_servers.linear]\nLINEAR_API_KEY = false\n',
                encoding="utf-8",
            )

            codex_install.Installer._sync_managed_secrets_file(installer)

            self.assertEqual(installed_file.read_text(encoding="utf-8"), source_file.read_text(encoding="utf-8"))

    def test_sync_release_shims_writes_single_wrapper_and_alias_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            share_dir = root / "share"
            wrapper_dir = root / "wrappers"
            (share_dir / "bin").mkdir(parents=True)
            wrapper_dir.mkdir(parents=True)
            (share_dir / "bin" / "codex").write_text("#!/bin/sh\n", encoding="utf-8")
            (share_dir / "bin" / "codex-exec").write_text("#!/bin/sh\n", encoding="utf-8")

            installer = self._make_installer()
            installer.launch_env = {}
            installer._share_dir = lambda: share_dir
            installer._wrapper_dir = lambda: wrapper_dir
            installer._managed_secrets_path = lambda: root / "lookup" / "secrets.toml"
            installer._managed_secret_env_helper_target = lambda: share_dir / "helpers" / "codex-secret-tool-env.py"
            installer._home_config_path = lambda: root / "home" / "config.toml"
            installer._wrapper_aliases_target = lambda: share_dir / "helpers" / "codex-wrapper-aliases.sh"
            installer._write_file = lambda path, content, mode=0o755: (
                path.parent.mkdir(parents=True, exist_ok=True),
                path.write_text(content, encoding="utf-8"),
                path.chmod(mode),
            )

            codex_install.Installer._sync_release_shims(installer, ["codex", "codex-exec"])
            codex_install.Installer._sync_wrapper_aliases(installer, ["codex", "codex-exec"])

            self.assertTrue((wrapper_dir / "codex").is_file())
            self.assertTrue((wrapper_dir / "codex-exec").is_file())
            self.assertFalse((wrapper_dir / "codex-s").exists())
            self.assertFalse((wrapper_dir / "codex-exec-s").exists())
            self.assertIn(
                "codex-secret-tool-env.py",
                (wrapper_dir / "codex").read_text(encoding="utf-8"),
            )
            aliases = (share_dir / "helpers" / "codex-wrapper-aliases.sh").read_text(encoding="utf-8")
            self.assertIn("alias codex-s='CODEX_INJECT_SECRETS=1 command codex'", aliases)
            self.assertIn("alias codex-exec-s='CODEX_INJECT_SECRETS=1 command codex-exec'", aliases)

    def test_ensure_enabled_managed_secrets_prompts_and_stores_missing_values(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
                service="codex-mcp",
                mcp_servers={
                    "vercel": {"VERCEL_API_TOKEN": True},
                    "linear": {"LINEAR_API_KEY": False},
                }
            )
        )

        with (
            patch("codex_install.secret_tool_available", return_value=True),
            patch("codex_install.lookup_managed_secret", return_value=""),
            patch.object(installer, "_prompt_managed_secret_value", return_value="vercel-secret") as prompt_mock,
            patch("codex_install.store_managed_secret") as store_mock,
        ):
            codex_install.Installer._ensure_enabled_managed_secrets(installer)

        prompt_mock.assert_called_once_with(server_name="vercel", key="VERCEL_API_TOKEN")
        store_mock.assert_called_once_with(
            installer.secrets_config,
            "vercel",
            "vercel-secret",
            env_key="VERCEL_API_TOKEN",
        )

    def test_ensure_enabled_managed_secrets_skips_missing_noninteractive_values(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
                service="codex-mcp",
                mcp_servers={"vercel": {"VERCEL_API_TOKEN": True}},
            )
        )

        with (
            patch("codex_install.secret_tool_available", return_value=True),
            patch("codex_install.lookup_managed_secret", return_value=""),
            patch.object(installer, "_prompt_managed_secret_value", return_value=None) as prompt_mock,
            patch("codex_install.store_managed_secret") as store_mock,
        ):
            codex_install.Installer._ensure_enabled_managed_secrets(installer)

        prompt_mock.assert_called_once_with(server_name="vercel", key="VERCEL_API_TOKEN")
        store_mock.assert_not_called()

    def test_clear_all_managed_secrets_clears_defined_keys_even_when_disabled(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
                service="codex-mcp",
                mcp_servers={
                    "cloudflare-api": {"CLOUDFLARE_API_TOKEN": False},
                    "vercel": {"VERCEL_API_TOKEN": True},
                }
            )
        )

        with (
            patch("codex_install.secret_tool_available", return_value=True),
            patch("codex_install.clear_managed_secret") as clear_mock,
        ):
            codex_install.Installer._clear_all_managed_secrets(installer)

        self.assertEqual(clear_mock.call_args_list[0].args, (installer.secrets_config, "cloudflare-api"))
        self.assertEqual(clear_mock.call_args_list[1].args, (installer.secrets_config, "vercel"))

    def test_clear_all_managed_secrets_warns_when_secret_tool_is_unavailable(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
                service="codex-mcp",
                mcp_servers={"vercel": {"VERCEL_API_TOKEN": True}},
            )
        )

        with patch("codex_install.secret_tool_available", return_value=False):
            codex_install.Installer._clear_all_managed_secrets(installer)

        installer._warn_once.assert_called_once_with(
            "secret-tool is unavailable; skipping managed MCP credential cleanup during uninstall"
        )

    def test_clear_all_managed_secrets_warns_and_continues_on_clear_failure(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
                service="codex-mcp",
                mcp_servers={
                    "linear": {"LINEAR_API_KEY": False},
                    "vercel": {"VERCEL_API_TOKEN": True},
                },
            )
        )

        with (
            patch("codex_install.secret_tool_available", return_value=True),
            patch(
                "codex_install.clear_managed_secret",
                side_effect=[ManagedSecretsError("secret-tool clear failed for mcp_servers.linear: exit code 1"), None],
            ) as clear_mock,
        ):
            codex_install.Installer._clear_all_managed_secrets(installer)

        self.assertEqual(clear_mock.call_count, 2)
        installer._warn_once.assert_called_once_with(
            "secret-tool clear failed for mcp_servers.linear: exit code 1; continuing uninstall without removing that keyring entry"
        )

if __name__ == "__main__":
    unittest.main()
