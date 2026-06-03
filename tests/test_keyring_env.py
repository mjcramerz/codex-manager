import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "src" / "python"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from lib import keyring_env  # noqa: E402
from lib.runtime import render_codex_shim  # noqa: E402
import codex_install  # noqa: E402


class LookupSecretServiceTests(unittest.TestCase):
    def test_parse_lookup_file_skips_comments_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "lookup-secret-service.env"
            path.write_text(
                "\n# comment\nLINEAR_API_KEY\n\nLINEAR_API_KEY\nCLOUDFLARE_API_TOKEN\n",
                encoding="utf-8",
            )

            parsed = keyring_env.parse_lookup_file(path)

        self.assertEqual(parsed, ["LINEAR_API_KEY", "CLOUDFLARE_API_TOKEN"])

    def test_parse_lookup_file_rejects_invalid_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "lookup-secret-service.env"
            path.write_text("not-valid\n", encoding="utf-8")

            with self.assertRaisesRegex(keyring_env.KeyringEnvError, "invalid key name"):
                keyring_env.parse_lookup_file(path)

    def test_collect_lookup_environment_uses_bws_and_filters_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lookup_path = Path(tmpdir) / "lookup-secret-service.env"
            lookup_path.write_text("LINEAR_API_KEY\nFIGMA_OAUTH_TOKEN\n", encoding="utf-8")

            calls: list[list[str]] = []

            def fake_run(
                args: list[str],
                check: bool,
                stdout: int,
                stderr: int,
                text: bool,
                timeout: int | None = None,
            ) -> subprocess.CompletedProcess[str]:
                calls.append(args)
                if args[:5] == ["/usr/bin/kwallet-query", "--read-password", "BWS_PROJECT_ID", "--folder", "Passwords"]:
                    account = args[2]
                    if account == "BWS_PROJECT_ID":
                        return subprocess.CompletedProcess(args, 0, stdout="project-id\n", stderr="")
                if args[:5] == ["/usr/bin/kwallet-query", "--read-password", "BWS_ACCESS_TOKEN", "--folder", "Passwords"]:
                    account = args[2]
                    if account == "BWS_ACCESS_TOKEN":
                        return subprocess.CompletedProcess(args, 0, stdout="access-token\n", stderr="")
                if args[:5] == ["/usr/bin/bws", "--access-token", "access-token", "run", "--no-inherit-env"]:
                    stdout_payload = (
                        "LINEAR_API_KEY=linear-secret\n"
                        "UNRELATED=ignore-me\n"
                    )
                    return subprocess.CompletedProcess(args, 0, stdout=stdout_payload, stderr="")
                return subprocess.CompletedProcess(args, 1, stdout="", stderr="error")

            with (
                patch(
                    "lib.keyring_env.shutil.which",
                    side_effect=lambda name: "/usr/bin/kwallet-query" if name == "kwallet-query" else "/usr/bin/bws",
                ),
                patch("lib.keyring_env.subprocess.run", side_effect=fake_run),
            ):
                exported = keyring_env.collect_lookup_environment(lookup_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "linear-secret"})
        self.assertTrue(any(call[:3] == ["/usr/bin/bws", "--access-token", "access-token"] for call in calls))

    def test_collect_lookup_environment_falls_back_to_environment_when_kwallet_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lookup_path = Path(tmpdir) / "lookup-secret-service.env"
            lookup_path.write_text("LINEAR_API_KEY\n", encoding="utf-8")

            def fake_run(
                args: list[str],
                check: bool,
                stdout: int,
                stderr: int,
                text: bool,
                timeout: int | None = None,
            ) -> subprocess.CompletedProcess[str]:
                if args[:5] == ["/usr/bin/bws", "--access-token", "env-token", "run", "--no-inherit-env"]:
                    return subprocess.CompletedProcess(args, 0, stdout="LINEAR_API_KEY=linear-secret\n", stderr="")
                return subprocess.CompletedProcess(args, 1, stdout="", stderr="unexpected")

            with (
                patch(
                    "lib.keyring_env.shutil.which",
                    side_effect=lambda name: None if name == "kwallet-query" else "/usr/bin/bws",
                ),
                patch("lib.keyring_env.subprocess.run", side_effect=fake_run),
                patch.dict(os.environ, {"BWS_PROJECT_ID": "env-project", "BWS_ACCESS_TOKEN": "env-token"}, clear=False),
            ):
                exported = keyring_env.collect_lookup_environment(lookup_path)

        self.assertEqual(exported, {"LINEAR_API_KEY": "linear-secret"})

    def test_lookup_config_from_env_file_uses_codex_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "CODEX_ROOT_DIR=/data/codex\n",
                encoding="utf-8",
            )

            lookup_path = keyring_env.lookup_config_from_env_file(env_path)

        self.assertEqual(lookup_path, Path("/data/codex/lookup/lookup-secret-service.env"))

    def test_lookup_shell_execs_interactive_shell(self) -> None:
        with (
            patch("lib.keyring_env.collect_lookup_environment", return_value={"LINEAR_API_KEY": "linear-secret"}),
            patch("os.execvpe") as execvpe,
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
        ):
            rc = keyring_env.lookup_shell(
                Path("/data/codex/lookup/lookup-secret-service.env"),
                "/bin/bash",
            )

        self.assertEqual(rc, 0)
        execvpe.assert_called_once()
        path, argv, env = execvpe.call_args.args
        self.assertEqual(path, "/bin/bash")
        self.assertEqual(argv, ["/bin/bash", "-i"])
        self.assertEqual(env["LINEAR_API_KEY"], "linear-secret")

    def test_render_codex_shim_supports_k_flag(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
            lookup_secret_service_path=Path("/data/codex/lookup/lookup-secret-service.env"),
            lookup_helper_path=Path("/data/codex/share/helpers/codex-bws-env.py"),
        )

        self.assertIn('--lookup-file "/data/codex/lookup/lookup-secret-service.env"', rendered)
        self.assertNotIn("--secret-service", rendered)
        self.assertIn("codex-bws-env.py", rendered)
        self.assertIn('if [ "${codex_arg}" = "--k" ]; then', rendered)

    def test_render_codex_shim_skips_lookup_block_when_unconfigured(self) -> None:
        rendered = render_codex_shim(
            Path("/data/codex/share/bin/codex"),
            share_dir=Path("/data/codex/share"),
        )
        self.assertNotIn("--lookup-file", rendered)
        self.assertNotIn("--secret-service", rendered)


class InstallerLookupSecretServiceTests(unittest.TestCase):
    def _make_installer(self, env: dict[str, str] | None = None) -> codex_install.Installer:
        installer = codex_install.Installer.__new__(codex_install.Installer)
        installer.env = env or {}
        installer._release_credentials_cache = None
        installer._keyring_secret_cache = {}
        installer._log = lambda _message: None
        return installer

    def test_ensure_lookup_secret_service_file_creates_missing_file_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            source_file = repo_root / "lookup-secret-service.env"
            source_file.write_text("LINEAR_API_KEY\n", encoding="utf-8")

            installer = codex_install.Installer.__new__(codex_install.Installer)
            installer.env = {"CODEX_ROOT_DIR": str(Path(tmpdir) / "runtime")}
            installer.repo_root = repo_root
            installer.dry_run = False

            codex_install.Installer._ensure_lookup_secret_service_file(installer)
            installed_file = Path(tmpdir) / "runtime" / "lookup" / "lookup-secret-service.env"
            self.assertTrue(installed_file.is_file())
            self.assertEqual(installed_file.read_text(encoding="utf-8"), "LINEAR_API_KEY\n")

            installed_file.write_text("CUSTOM_TOKEN\n", encoding="utf-8")
            codex_install.Installer._ensure_lookup_secret_service_file(installer)
            self.assertEqual(installed_file.read_text(encoding="utf-8"), "CUSTOM_TOKEN\n")

    def test_resolve_release_credentials_prefers_bws_cli_kwallet(self) -> None:
        installer = self._make_installer(
            {
                "GL_DEPLOY_RELEASE_USERNAME": "env-user",
                "GL_DEPLOY_RELEASE_TOKEN": "env-token",
            }
        )
        calls: list[list[str]] = []

        def fake_run(
            args: list[str],
            check: bool,
            stdout: int,
            stderr: int,
            text: bool,
            timeout: int | None = None,
        ) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            if args[:5] == ["/usr/bin/kwallet-query", "--read-password", "BWS_PROJECT_ID", "--folder", "Passwords"]:
                account = args[2]
                if account == "BWS_PROJECT_ID":
                    return subprocess.CompletedProcess(args, 0, stdout="project-id\n", stderr="")
            if args[:5] == ["/usr/bin/kwallet-query", "--read-password", "BWS_ACCESS_TOKEN", "--folder", "Passwords"]:
                account = args[2]
                if account == "BWS_ACCESS_TOKEN":
                    return subprocess.CompletedProcess(args, 0, stdout="access-token\n", stderr="")
            if args[:5] == ["/usr/bin/bws", "--access-token", "access-token", "run", "--no-inherit-env"]:
                stdout_payload = (
                    "GL_DEPLOY_RELEASE_USERNAME=bws-user\n"
                    "GL_DEPLOY_RELEASE_TOKEN=bws-token\n"
                )
                return subprocess.CompletedProcess(args, 0, stdout=stdout_payload, stderr="")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="error")

        with (
            patch.object(installer, "_resolve_bws_binary", return_value=Path("/usr/bin/bws")),
            patch(
                "codex_install.shutil.which",
                side_effect=lambda name: "/usr/bin/kwallet-query" if name == "kwallet-query" else None,
            ),
            patch("codex_install.subprocess.run", side_effect=fake_run),
        ):
            credentials = codex_install.Installer._resolve_release_credentials(installer)

        self.assertEqual(credentials, ("bws-user", "bws-token"))
        self.assertTrue(any(call[:2] == ["/usr/bin/kwallet-query", "--read-password"] for call in calls))
        self.assertTrue(any(call[:5] == ["/usr/bin/bws", "--access-token", "access-token", "run", "--no-inherit-env"] for call in calls))

    def test_resolve_release_credentials_falls_back_to_environment_when_kwallet_missing(self) -> None:
        installer = self._make_installer(
            {
                "GL_DEPLOY_RELEASE_USERNAME": "env-user",
                "GL_DEPLOY_RELEASE_TOKEN": "env-token",
            }
        )
        calls: list[list[str]] = []

        def fake_run(
            args: list[str],
            check: bool,
            stdout: int,
            stderr: int,
            text: bool,
            timeout: int | None = None,
        ) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            if args[:5] == ["/usr/bin/bws", "--access-token", "env-token", "run", "--no-inherit-env"]:
                stdout_payload = (
                    "GL_DEPLOY_RELEASE_USERNAME=bws-user\n"
                    "GL_DEPLOY_RELEASE_TOKEN=bws-token\n"
                )
                return subprocess.CompletedProcess(args, 0, stdout=stdout_payload, stderr="")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="error")

        with (
            patch.object(installer, "_resolve_bws_binary", return_value=Path("/usr/bin/bws")),
            patch("codex_install.shutil.which", side_effect=lambda name: None if name == "kwallet-query" else None),
            patch("codex_install.subprocess.run", side_effect=fake_run),
            patch.dict(os.environ, {"BWS_PROJECT_ID": "env-project", "BWS_ACCESS_TOKEN": "env-token"}, clear=False),
        ):
            credentials = codex_install.Installer._resolve_release_credentials(installer)

        self.assertEqual(credentials, ("bws-user", "bws-token"))
        self.assertTrue(any(call[:5] == ["/usr/bin/bws", "--access-token", "env-token", "run", "--no-inherit-env"] for call in calls))

    def test_resolve_release_credentials_prompts_when_kwallet_and_environment_missing(self) -> None:
        installer = self._make_installer()
        calls: list[list[str]] = []

        def fake_run(
            args: list[str],
            check: bool,
            stdout: int,
            stderr: int,
            text: bool,
            timeout: int | None = None,
        ) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            if args[:5] == ["/usr/bin/bws", "--access-token", "prompt-token", "run", "--no-inherit-env"]:
                stdout_payload = (
                    "GL_DEPLOY_RELEASE_USERNAME=bws-user\n"
                    "GL_DEPLOY_RELEASE_TOKEN=bws-token\n"
                )
                return subprocess.CompletedProcess(args, 0, stdout=stdout_payload, stderr="")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="error")

        with (
            patch.object(installer, "_resolve_bws_binary", return_value=Path("/usr/bin/bws")),
            patch.object(
                installer,
                "_prompt_bws_account_value",
                side_effect=["prompt-project", "prompt-token"],
            ) as prompt_mock,
            patch("codex_install.shutil.which", side_effect=lambda name: None if name == "kwallet-query" else None),
            patch("codex_install.subprocess.run", side_effect=fake_run),
            patch.dict(os.environ, {}, clear=True),
        ):
            credentials = codex_install.Installer._resolve_release_credentials(installer)

        self.assertEqual(credentials, ("bws-user", "bws-token"))
        self.assertEqual(prompt_mock.call_args_list[0].args, ("BWS_PROJECT_ID",))
        self.assertEqual(prompt_mock.call_args_list[1].args, ("BWS_ACCESS_TOKEN",))

    def test_resolve_release_credentials_rejects_partial_bws_cli_kwallet_or_env(self) -> None:
        installer = self._make_installer()

        def fake_run(
            args: list[str],
            check: bool,
            stdout: int,
            stderr: int,
            text: bool,
            timeout: int | None = None,
        ) -> subprocess.CompletedProcess[str]:
            if args[:5] == ["/usr/bin/kwallet-query", "--read-password", "BWS_PROJECT_ID", "--folder", "Passwords"]:
                account = args[2]
                if account == "BWS_PROJECT_ID":
                    return subprocess.CompletedProcess(args, 0, stdout="project-id\n", stderr="")
                return subprocess.CompletedProcess(args, 1, stdout="", stderr="missing")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="unexpected")

        with (
            patch("codex_install.shutil.which", side_effect=lambda name: "/usr/bin/kwallet-query" if name == "kwallet-query" else None),
            patch("codex_install.subprocess.run", side_effect=fake_run),
        ):
            with self.assertRaisesRegex(
                codex_install.InstallError,
                "bws-cli kwallet/env bootstrap must contain both BWS_PROJECT_ID and BWS_ACCESS_TOKEN",
            ):
                codex_install.Installer._resolve_release_credentials(installer)


if __name__ == "__main__":
    unittest.main()
