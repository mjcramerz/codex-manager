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
from lib.runtime import render_codex_shim  # noqa: E402
import codex_install  # noqa: E402


class ManagedSecretsHelperTests(unittest.TestCase):
    def test_collect_lookup_environment_uses_secret_tool_for_enabled_keys_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_path = Path(tmpdir) / "secrets.toml"
            secrets_path.write_text(
                "\n".join(
                    [
                        "version = 1",
                        "",
                        "[mcp_servers.linear]",
                        "LINEAR_API_KEY = true",
                        "",
                        "[mcp_servers.vercel]",
                        "VERCEL_API_TOKEN = false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch(
                "lib.keyring_env.lookup_managed_secret",
                side_effect=lambda key: "linear-secret" if key == "LINEAR_API_KEY" else "",
            ):
                exported = keyring_env.collect_lookup_environment(secrets_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "linear-secret"})

    def test_collect_lookup_environment_prefers_existing_environment_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_path = Path(tmpdir) / "secrets.toml"
            secrets_path.write_text(
                "\n".join(
                    [
                        "version = 1",
                        "",
                        "[mcp_servers.linear]",
                        "LINEAR_API_KEY = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch("lib.keyring_env.lookup_managed_secret", return_value="keyring-secret"),
                patch.dict(os.environ, {"LINEAR_API_KEY": "env-secret"}, clear=False),
            ):
                exported = keyring_env.collect_lookup_environment(secrets_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "env-secret"})

    def test_secrets_config_from_env_file_uses_codex_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("CODEX_ROOT_DIR=/data/codex\n", encoding="utf-8")

            secrets_path = keyring_env.secrets_config_from_env_file(env_path)

        self.assertEqual(secrets_path, Path("/data/codex/lookup/secrets.toml"))

    def test_lookup_shell_execs_interactive_shell(self) -> None:
        with (
            patch("lib.keyring_env.collect_lookup_environment", return_value={"LINEAR_API_KEY": "linear-secret"}),
            patch("os.execvpe") as execvpe,
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
        ):
            rc = keyring_env.lookup_shell(
                Path("/data/codex/lookup/secrets.toml"),
                "/bin/bash",
            )

        self.assertEqual(rc, 0)
        execvpe.assert_called_once()
        path, argv, env = execvpe.call_args.args
        self.assertEqual(path, "/bin/bash")
        self.assertEqual(argv, ["/bin/bash", "-i"])
        self.assertEqual(env["LINEAR_API_KEY"], "linear-secret")

    def test_render_codex_shim_uses_managed_secret_helper(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
            wrapper_dir=Path("/data/bin"),
            managed_secrets_path=Path("/data/codex/lookup/secrets.toml"),
            managed_secret_helper_path=Path("/data/codex/share/helpers/codex-secret-tool-env.py"),
        )

        self.assertIn("/data/codex/share/bin/codex", rendered)
        self.assertIn('"/data/bin"', rendered)
        self.assertNotIn('"/data/codex/share/shims"', rendered)
        self.assertIn('--secrets-file "/data/codex/lookup/secrets.toml"', rendered)
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
        installer._release_credentials_cache = None
        installer._log = lambda _message: None
        installer._warn_once = Mock()
        return installer

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
                "version = 1\n\n[mcp_servers.linear]\nLINEAR_API_KEY = true\n",
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
                "version = 1\n\n[mcp_servers.linear]\nLINEAR_API_KEY = false\n",
                encoding="utf-8",
            )

            codex_install.Installer._sync_managed_secrets_file(installer)

            self.assertEqual(installed_file.read_text(encoding="utf-8"), source_file.read_text(encoding="utf-8"))

    def test_ensure_enabled_managed_secrets_prompts_and_stores_missing_values(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(
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
        store_mock.assert_called_once_with("VERCEL_API_TOKEN", "vercel-secret")

    def test_ensure_enabled_managed_secrets_skips_missing_noninteractive_values(self) -> None:
        installer = self._make_installer(
            secrets_config=ManagedSecretsConfig(mcp_servers={"vercel": {"VERCEL_API_TOKEN": True}})
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

        self.assertEqual(clear_mock.call_args_list[0].args, ("CLOUDFLARE_API_TOKEN",))
        self.assertEqual(clear_mock.call_args_list[1].args, ("VERCEL_API_TOKEN",))

    def test_resolve_release_credentials_prefers_env_file_values(self) -> None:
        installer = self._make_installer(
            env={
                "GL_DEPLOY_RELEASE_USERNAME": "env-user",
                "GL_DEPLOY_RELEASE_TOKEN": "env-token",
            }
        )

        credentials = codex_install.Installer._resolve_release_credentials(installer)

        self.assertEqual(credentials, ("env-user", "env-token"))

    def test_resolve_release_credentials_falls_back_to_process_environment(self) -> None:
        installer = self._make_installer(
            env={
                "GL_DEPLOY_RELEASE_USERNAME": "",
                "GL_DEPLOY_RELEASE_TOKEN": "",
            }
        )

        with patch.dict(
            os.environ,
            {
                "GL_DEPLOY_RELEASE_USERNAME": "process-user",
                "GL_DEPLOY_RELEASE_TOKEN": "process-token",
            },
            clear=False,
        ):
            credentials = codex_install.Installer._resolve_release_credentials(installer)

        self.assertEqual(credentials, ("process-user", "process-token"))

    def test_resolve_release_credentials_rejects_partial_values(self) -> None:
        installer = self._make_installer(
            env={
                "GL_DEPLOY_RELEASE_USERNAME": "env-user",
                "GL_DEPLOY_RELEASE_TOKEN": "",
            }
        )

        with self.assertRaisesRegex(
            codex_install.InstallError,
            "must define both GL_DEPLOY_RELEASE_USERNAME and GL_DEPLOY_RELEASE_TOKEN",
        ):
            codex_install.Installer._resolve_release_credentials(installer)


if __name__ == "__main__":
    unittest.main()
