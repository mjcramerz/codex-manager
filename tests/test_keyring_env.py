import io
import os
import shutil
import subprocess
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
from lib import codex_mcp_token  # noqa: E402
from lib import codex_login  # noqa: E402
from lib.managed_secrets import ManagedSecretsConfig  # noqa: E402
from lib.managed_secrets import ManagedSecretsError  # noqa: E402
from lib.runtime import render_codex_shim  # noqa: E402
import codex_install  # noqa: E402


class ManagedSecretsHelperTests(unittest.TestCase):
    def test_collect_lookup_environment_uses_enabled_url_and_command_env_vars(self) -> None:
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
                        "[mcp_servers.context7]",
                        "CONTEXT7_API_KEY = true",
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
                        "[mcp_servers.context7]",
                        'command = "/usr/bin/context7"',
                        'env_vars = ["CONTEXT7_API_KEY"]',
                        "enabled = true",
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
                    else "context7-secret"
                    if server_name == "context7"
                    else ""
                ),
            ):
                exported = keyring_env.collect_lookup_environment(host_config_path, secrets_path)

        self.assertEqual(
            exported,
            {
                "LINEAR_API_KEY": "linear-secret",
                "CONTEXT7_API_KEY": "context7-secret",
            },
        )

    def test_collect_lookup_environment_skips_disabled_secret_entries(self) -> None:
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
                    ]
                ),
                encoding="utf-8",
            )

            with patch("lib.keyring_env.lookup_managed_secret", return_value="linear-secret") as lookup_mock:
                exported = keyring_env.collect_lookup_environment(host_config_path, secrets_path)

        self.assertEqual(exported, {})
        lookup_mock.assert_not_called()

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

    def test_runtime_mcp_secret_env_map_rejects_command_transport_bearer_token(self) -> None:
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
                keyring_env._runtime_mcp_secret_env_map(host_config_path)

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

    def test_render_codex_shim_always_uses_managed_secret_helper_when_configured(self) -> None:
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
        self.assertNotIn("CODEX_INJECT_SECRETS", rendered)
        self.assertIn("codex-secret-tool-env.py", rendered)
        self.assertNotIn("codex-ensure-tmpfs", rendered)
        self.assertNotIn("--lookup-file", rendered)
        self.assertNotIn("--secret-service", rendered)
        self.assertNotIn('if [ "${codex_arg}" = "--k" ]; then', rendered)

    def test_render_codex_shim_skips_lookup_block_when_unconfigured(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
            wrapper_dir=Path("/data/bin"),
        )
        self.assertNotIn("codex-ensure-tmpfs", rendered)
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

    def test_sync_managed_auth_file_overwrites_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            source_file = repo_root / "auth.toml"
            source_file.write_text(
                'version = 1\nservice = "codex-login"\n\n[codex_login."matthew@gmail.com"]\nCODEX_ACCESS_TOKEN = true\n',
                encoding="utf-8",
            )

            installer = self._make_installer(
                env={"CODEX_ROOT_DIR": str(Path(tmpdir) / "runtime")},
                repo_root=repo_root,
            )
            installer._needs_sudo_write = lambda _path: False

            installed_file = Path(tmpdir) / "runtime" / "lookup" / "auth.toml"
            installed_file.parent.mkdir(parents=True, exist_ok=True)
            installed_file.write_text(
                'version = 1\nservice = "codex-login"\n\n[codex_login."matthew@gmail.com"]\nCODEX_ACCESS_TOKEN = false\n',
                encoding="utf-8",
            )

            codex_install.Installer._sync_managed_auth_file(installer)

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
            self.assertNotIn("alias codex-s=", aliases)
            self.assertNotIn("alias codex-exec-s=", aliases)
            self.assertIn("unalias codex-s", aliases)
            self.assertIn("unalias codex-exec-s", aliases)

    def test_sync_codex_login_wrapper_installs_managed_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            wrapper_dir = root / "wrappers"
            wrapper_dir.mkdir(parents=True)

            installer = self._make_installer(repo_root=REPO_ROOT)
            installer._codex_login_wrapper_source_path = lambda: REPO_ROOT / "src" / "python" / "lib" / "codex_login.py"
            installer._codex_login_wrapper_target = lambda: wrapper_dir / "codex-login"
            installer._copy_file = lambda src, dst, mode=0o755: (
                dst.parent.mkdir(parents=True, exist_ok=True),
                shutil.copy2(src, dst),
                dst.chmod(mode),
            )

            codex_install.Installer._sync_codex_login_wrapper(installer)

            rendered = (wrapper_dir / "codex-login").read_text(encoding="utf-8")
            self.assertIn("# managed by codex installer", rendered)
            self.assertIn('"--with-access-token"', rendered)
            self.assertIn('"logout"', rendered)
            self.assertTrue(os.access(wrapper_dir / "codex-login", os.X_OK))

    def test_sync_managed_secret_env_helper_installs_runtime_lib_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            share_dir = root / "share"
            helper_path = share_dir / "helpers" / "codex-secret-tool-env.py"

            installer = self._make_installer(repo_root=REPO_ROOT)
            installer._managed_secret_env_helper_source_path = lambda: REPO_ROOT / "src" / "python" / "lib" / "keyring_env.py"
            installer._managed_secret_env_helper_target = lambda: helper_path
            installer._managed_secret_runtime_lib_dir = lambda: share_dir / "lib"
            installer._managed_secret_runtime_lib_sources = lambda: [
                (REPO_ROOT / "src" / "python" / "lib" / "__init__.py", share_dir / "lib" / "__init__.py"),
                (REPO_ROOT / "src" / "python" / "lib" / "managed_secrets.py", share_dir / "lib" / "managed_secrets.py"),
                (REPO_ROOT / "src" / "python" / "lib" / "runtime.py", share_dir / "lib" / "runtime.py"),
            ]
            installer._copy_file = lambda src, dst, mode=0o755: (
                dst.parent.mkdir(parents=True, exist_ok=True),
                shutil.copy2(src, dst),
                dst.chmod(mode),
            )
            installer._mkdir_path = lambda path: path.mkdir(parents=True, exist_ok=True)

            codex_install.Installer._sync_managed_secret_env_helper(installer)

            self.assertTrue(helper_path.is_file())
            self.assertTrue((share_dir / "lib" / "__init__.py").is_file())
            self.assertTrue((share_dir / "lib" / "managed_secrets.py").is_file())
            self.assertTrue((share_dir / "lib" / "runtime.py").is_file())

            proc = subprocess.run(
                [sys.executable, str(helper_path), "--help"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("secret-tool-backed Codex environment launcher", proc.stdout)

    def test_sync_codex_mcp_token_wrapper_installs_managed_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            wrapper_dir = root / "wrappers"
            wrapper_dir.mkdir(parents=True)

            installer = self._make_installer(repo_root=REPO_ROOT)
            installer._codex_mcp_token_wrapper_source_path = (
                lambda: REPO_ROOT / "src" / "python" / "lib" / "codex_mcp_token.py"
            )
            installer._codex_mcp_token_wrapper_target = lambda: wrapper_dir / "codex-mcp-token"
            installer._copy_file = lambda src, dst, mode=0o755: (
                dst.parent.mkdir(parents=True, exist_ok=True),
                shutil.copy2(src, dst),
                dst.chmod(mode),
            )

            codex_install.Installer._sync_codex_mcp_token_wrapper(installer)

            rendered = (wrapper_dir / "codex-mcp-token").read_text(encoding="utf-8")
            self.assertIn("Please enable secret first and try again later", rendered)
            self.assertIn("secret-tool", rendered)
            self.assertTrue(os.access(wrapper_dir / "codex-mcp-token", os.X_OK))

    def test_codex_mcp_token_rejects_disabled_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "secrets.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-mcp"',
                        "",
                        "[mcp_servers.jina-ai]",
                        "JINA_API_KEY = false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("sys.stderr", new=io.StringIO()),
            ):
                rc = codex_mcp_token.main(["JINA_API_KEY", "1646558"])

        self.assertEqual(rc, 1)

    def test_codex_mcp_token_stores_enabled_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "secrets.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-mcp"',
                        "",
                        "[mcp_servers.jina-ai]",
                        "JINA_API_KEY = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            lookup_proc = Mock(returncode=0, stdout="existing-token\n", stderr="")
            store_proc = Mock(returncode=0, stdout="", stderr="")
            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_mcp_token.shutil.which", return_value="/usr/bin/secret-tool"),
                patch("lib.codex_mcp_token.subprocess.run", side_effect=[lookup_proc, store_proc]) as run_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_mcp_token.main(["JINA_API_KEY", "1646558"])

        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_count, 2)
        self.assertIn("lookup", run_mock.call_args_list[0].args[0])
        self.assertIn("store", run_mock.call_args_list[1].args[0])

    def test_codex_login_init_stores_enabled_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                        '[codex_login."disabled@example.com"]',
                        "CODEX_ACCESS_TOKEN = false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.secret_tool_available", return_value=True),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch.object(sys.stderr, "isatty", return_value=True),
                patch("lib.codex_login.lookup_login_secret", return_value=""),
                patch("lib.codex_login.getpass.getpass", return_value="token-1") as getpass_mock,
                patch("lib.codex_login.store_login_secret") as store_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--init"])

        self.assertEqual(rc, 0)
        getpass_mock.assert_called_once_with("Enter the Access Token for copilot@jcramer.sbs: ")
        self.assertEqual(store_mock.call_count, 1)
        self.assertEqual(store_mock.call_args.args[1], "copilot@jcramer.sbs")
        self.assertEqual(store_mock.call_args.args[2], "token-1")

    def test_codex_login_init_skips_existing_account_when_user_declines_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.secret_tool_available", return_value=True),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch.object(sys.stderr, "isatty", return_value=True),
                patch("lib.codex_login.lookup_login_secret", return_value="existing-token") as lookup_mock,
                patch("builtins.input", return_value="n") as input_mock,
                patch("lib.codex_login.getpass.getpass") as getpass_mock,
                patch("lib.codex_login.store_login_secret") as store_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--init"])

        self.assertEqual(rc, 0)
        lookup_mock.assert_called_once_with(unittest.mock.ANY, "copilot@jcramer.sbs")
        input_mock.assert_called_once()
        getpass_mock.assert_not_called()
        store_mock.assert_not_called()

    def test_codex_login_init_prompts_before_adding_duplicate_for_existing_account(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.secret_tool_available", return_value=True),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch.object(sys.stderr, "isatty", return_value=True),
                patch("lib.codex_login.lookup_login_secret", return_value="existing-token") as lookup_mock,
                patch("builtins.input", return_value="y") as input_mock,
                patch("lib.codex_login.getpass.getpass", return_value="token-2") as getpass_mock,
                patch("lib.codex_login.store_login_secret") as store_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--init"])

        self.assertEqual(rc, 0)
        lookup_mock.assert_called_once_with(unittest.mock.ANY, "copilot@jcramer.sbs")
        input_mock.assert_called_once()
        getpass_mock.assert_called_once_with("Enter the Access Token for copilot@jcramer.sbs: ")
        store_mock.assert_called_once()
        self.assertEqual(store_mock.call_args.args[1], "copilot@jcramer.sbs")
        self.assertEqual(store_mock.call_args.args[2], "token-2")

    def test_codex_login_list_prints_available_stored_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                        '[codex_login."missing@example.com"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.lookup_login_secret", side_effect=["token-1", ""]),
                patch("sys.stdout", new=io.StringIO()) as stdout,
            ):
                rc = codex_login.main(["--list"])

        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue().strip(), "1) copilot@jcramer.sbs")

    def test_codex_login_reset_all_clears_all_configured_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                        '[codex_login."disabled@example.com"]',
                        "CODEX_ACCESS_TOKEN = false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.secret_tool_available", return_value=True),
                patch("lib.codex_login.clear_login_secret") as clear_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--reset", "all"])

        self.assertEqual(rc, 0)
        self.assertEqual(
            [call.args[1] for call in clear_mock.call_args_list],
            ["copilot@jcramer.sbs", "disabled@example.com"],
        )

    def test_codex_login_reset_specific_account_clears_only_requested_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.secret_tool_available", return_value=True),
                patch("lib.codex_login.clear_login_secret") as clear_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--reset", "matthew@gmail.com"])

        self.assertEqual(rc, 0)
        clear_mock.assert_called_once()
        self.assertEqual(clear_mock.call_args.args[1], "matthew@gmail.com")

    def test_codex_login_selects_stored_account_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                        '[codex_login."matthew@gmail.com"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            logout_proc = Mock(returncode=0, stdout="", stderr="")
            login_proc = Mock(returncode=0, stdout="", stderr="")
            class TtyStringIO(io.StringIO):
                def isatty(self) -> bool:
                    return True
            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch("lib.codex_login.lookup_login_secret", side_effect=["token-a", "token-b"]),
                patch("lib.codex_login._resolve_codex_wrapper", return_value=Path("/data/bin/codex")),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch("builtins.input", return_value="2"),
                patch("lib.codex_login.subprocess.run", side_effect=[logout_proc, login_proc]) as run_mock,
                patch("sys.stdout", new=TtyStringIO()),
            ):
                rc = codex_login.main([])

        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[1].kwargs["input"], "token-b")

    def test_codex_login_init_retries_store_with_bootstrap_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            failed_store = Mock(returncode=1, stdout="", stderr="secret-tool: The name is not activatable")
            successful_store = Mock(returncode=0, stdout="", stderr="")

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch.object(sys.stderr, "isatty", return_value=True),
                patch("lib.codex_login.lookup_login_secret", return_value=""),
                patch("lib.codex_login.getpass.getpass", return_value="token-1"),
                patch(
                    "lib.codex_login.shutil.which",
                    side_effect=lambda name: {
                        "secret-tool": "/usr/bin/secret-tool",
                        "dbus-run-session": "/usr/bin/dbus-run-session",
                        "gnome-keyring-daemon": "/usr/bin/gnome-keyring-daemon",
                    }.get(name),
                ),
                patch("lib.codex_login.subprocess.run", side_effect=[failed_store, successful_store]) as run_mock,
                patch("sys.stdout", new=io.StringIO()),
            ):
                rc = codex_login.main(["--init"])

        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[0].args[0][0], "/usr/bin/secret-tool")
        self.assertEqual(run_mock.call_args_list[1].args[0][0], "/usr/bin/dbus-run-session")
        self.assertEqual(run_mock.call_args_list[1].kwargs["input"], "token-1\n")

    def test_codex_login_init_reports_secret_service_failure_when_bootstrap_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lookup_dir = root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            (lookup_dir / "auth.toml").write_text(
                "\n".join(
                    [
                        "version = 1",
                        'service = "codex-login"',
                        "",
                        '[codex_login."copilot@jcramer.sbs"]',
                        "CODEX_ACCESS_TOKEN = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            failed_store = Mock(returncode=1, stdout="", stderr="secret-tool: The name is not activatable")
            class TtyStringIO(io.StringIO):
                def isatty(self) -> bool:
                    return True

            with (
                patch.dict(os.environ, {"CODEX_ROOT_DIR": str(root)}, clear=False),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch("lib.codex_login.lookup_login_secret", return_value=""),
                patch("lib.codex_login.getpass.getpass", return_value="token-1"),
                patch(
                    "lib.codex_login.shutil.which",
                    side_effect=lambda name: {
                        "secret-tool": "/usr/bin/secret-tool",
                        "dbus-run-session": "/usr/bin/dbus-run-session",
                    }.get(name),
                ),
                patch("lib.codex_login.subprocess.run", return_value=failed_store),
                patch("sys.stdout", new=io.StringIO()),
                patch("sys.stderr", new=TtyStringIO()) as stderr,
            ):
                rc = codex_login.main(["--init"])

        self.assertEqual(rc, 1)
        self.assertIn("ensure a Secret Service is running", stderr.getvalue())

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

    def test_uninstall_preserves_managed_auth_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "runtime"
            system_dir = root / "system"
            user_dir = root / "user"
            share_dir = root / "share"
            mcp_dir = root / "mcp"
            backup_dir = root / "backup"
            home_dir = root / "home"
            agents_dir = root / "agents"
            skills_dir = root / "skills"
            log_dir = root / "logs"
            sqlite_dir = root / "sqlite"
            lookup_dir = codex_root / "lookup"
            lookup_dir.mkdir(parents=True, exist_ok=True)
            managed_auth = lookup_dir / "auth.toml"
            managed_auth.write_text(
                'version = 1\nservice = "codex-login"\n\n[codex_login."matthew@gmail.com"]\nCODEX_ACCESS_TOKEN = true\n',
                encoding="utf-8",
            )
            doomed_file = codex_root / "tmp.txt"
            doomed_file.write_text("remove me\n", encoding="utf-8")

            for path in (system_dir, user_dir, share_dir, mcp_dir, backup_dir, home_dir, agents_dir, skills_dir, log_dir, sqlite_dir):
                path.mkdir(parents=True, exist_ok=True)

            installer = self._make_installer(
                env={
                    "CODEX_ROOT_DIR": str(codex_root),
                    "CODEX_SYSTEM_DIR": str(system_dir),
                    "CODEX_USER_DIR": str(user_dir),
                    "CODEX_SHARE_DIR": str(share_dir),
                    "CODEX_WRAPPER_DIR": str(share_dir / "wrappers"),
                    "CODEX_MCP_DIR": str(mcp_dir),
                    "CODEX_BACKUP_DIR": str(backup_dir),
                },
            )
            installer.runtime_vars = {
                "CODEX_HOME": str(home_dir),
                "CODEX_AGENTS": str(agents_dir),
                "CODEX_SKILLS": str(skills_dir),
                "CODEX_LOG_DIR": str(log_dir),
                "CODEX_SQLITE_HOME": str(sqlite_dir),
            }
            installer._log = lambda _message: None
            installer._backup_install_state = lambda *, flow: None
            installer._stage_mode = lambda: False
            installer._managed_wrapper_targets_for_uninstall = lambda: set()
            installer._path_profile_target = lambda: root / "profile.d" / "codex.sh"
            installer._clear_all_managed_secrets = Mock()
            installer.reset_environment = Mock()
            installer._run_command = lambda args: subprocess.run(args, check=False)

            codex_install.Installer.uninstall(installer)

            self.assertTrue(managed_auth.exists())
            self.assertFalse(doomed_file.exists())
            installer._clear_all_managed_secrets.assert_not_called()
            installer.reset_environment.assert_called_once_with()

    def test_prepare_runtime_refresh_base_does_not_clear_managed_secrets(self) -> None:
        installer = self._make_installer()
        installer._log = lambda _message: None
        installer._backup_install_state = lambda *, flow: None
        installer._ensure_runtime_directories = Mock()
        installer._sync_managed_secrets_file = Mock()
        installer._sync_managed_auth_file = Mock()
        installer._stage_mode = lambda: False
        installer._ensure_enabled_managed_secrets = Mock()
        installer._secure_exec_directories = Mock()
        installer._clear_all_managed_secrets = Mock()

        codex_install.Installer._prepare_runtime_refresh_base(installer, flow="install")

        installer._ensure_enabled_managed_secrets.assert_called_once_with()
        installer._clear_all_managed_secrets.assert_not_called()

    def test_verify_runtime_hook_assets_detects_missing_runtime_driver(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_scripts = REPO_ROOT / "resources" / "hooks" / "scripts"
            source_schemas = REPO_ROOT / "resources" / "hooks" / "schema" / "generated"
            runtime_scripts = root / "home" / ".hooks" / "scripts"
            runtime_schemas = root / "home" / ".hooks" / "schema" / "generated"
            shutil.copytree(source_scripts, runtime_scripts)
            shutil.copytree(source_schemas, runtime_schemas)
            (runtime_scripts / "hook_driver.pl").unlink()

            installer = self._make_installer()
            installer._hooks_source_dir = lambda: source_scripts
            installer._hooks_schema_source_dir = lambda: source_schemas
            installer._runtime_hooks_scripts_dir = lambda: runtime_scripts
            installer._runtime_hooks_schema_dir = lambda: runtime_schemas

            with self.assertRaisesRegex(codex_install.InstallError, "missing runtime hook driver"):
                codex_install.Installer._verify_runtime_hook_assets(installer)

if __name__ == "__main__":
    unittest.main()
