import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "src" / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lib.runtime import derive_runtime_globals_from_env  # noqa: E402
from lib.runtime import render_shell_path_profile  # noqa: E402


ENV_SCRIPT = REPO_ROOT / "src" / "python" / "lib" / "codex_env.sh"


class ShellPathProfileRenderTests(unittest.TestCase):
    def test_derive_runtime_globals_omits_codex_tmpdir(self) -> None:
        rendered = derive_runtime_globals_from_env(
            {
                "CODEX_ROOT_DIR": "/data/codex",
                "CODEX_USER_DIR": "/data/codex/usr",
            }
        )

        self.assertEqual(
            rendered,
            {
                "CODEX_HOME": "/data/codex/usr/home",
                "CODEX_AGENTS": "/data/codex/usr/agents",
                "CODEX_SKILLS": "/data/codex/usr/skills",
                "CODEX_LOG_DIR": "/data/codex/log",
            },
        )

    def test_render_shell_path_profile_exports_globals_and_path_entries(self) -> None:
        rendered = render_shell_path_profile(
            Path("/data/codex/share"),
            Path("/data/bin"),
            {
                "CODEX_AGENTS": "/data/codex/usr/agents",
                "CODEX_HOME": "/data/codex/usr/home",
                "CODEX_SKILLS": "/data/codex/usr/skills",
            },
            guard_user="mcramer",
        )

        self.assertIn('codex_target_user="mcramer"', rendered)
        self.assertIn('export CODEX_HOME="/data/codex/usr/home"', rendered)
        self.assertIn('export CODEX_AGENTS="/data/codex/usr/agents"', rendered)
        self.assertIn('export CODEX_SKILLS="/data/codex/usr/skills"', rendered)
        self.assertIn('"/data/bin"', rendered)
        self.assertIn('"/data/codex/share/helpers"', rendered)
        self.assertIn('codex-wrapper-aliases.sh', rendered)
        self.assertNotIn('"/data/codex/share/shims"', rendered)


class CodexEnvHookTests(unittest.TestCase):
    def _run_env_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(ENV_SCRIPT), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_hook_installs_managed_blocks_in_bashrc_and_zshrc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            user_home = Path(tmpdir) / "home"
            user_home.mkdir(parents=True, exist_ok=True)
            profile_path = Path(tmpdir) / "profile.d" / "50-codex-user-env.sh"

            result = self._run_env_script(
                "hook",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            bashrc = (user_home / ".bashrc").read_text(encoding="utf-8")
            zshrc = (user_home / ".zshrc").read_text(encoding="utf-8")
            profile = (user_home / ".profile").read_text(encoding="utf-8")

            source_line = f'. "{profile_path}"'
            self.assertIn(source_line, bashrc)
            self.assertIn(source_line, zshrc)
            self.assertIn(source_line, profile)
            self.assertIn("# managed by codex installer", profile)
            self.assertNotIn("# >>> codex-shell-hook >>>", profile)
            self.assertIn('bash-completion/completions/codex', bashrc)
            self.assertNotIn('bash-completion/completions/codex', zshrc)

    def test_hook_installs_clean_profile_source_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            user_home = Path(tmpdir) / "home"
            user_home.mkdir(parents=True, exist_ok=True)
            profile_path = Path(tmpdir) / "profile.d" / "50-codex-user-env.sh"
            profile = user_home / ".profile"
            profile.write_text("export PATH=/usr/bin\n", encoding="utf-8")

            result = self._run_env_script(
                "hook",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            rendered = profile.read_text(encoding="utf-8")
            self.assertIn('export PATH=/usr/bin\n\n# managed by codex installer\n', rendered)
            self.assertNotIn("# >>> codex-shell-hook >>>", rendered)

    def test_verify_requires_managed_zshrc_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            user_home = Path(tmpdir) / "home"
            user_home.mkdir(parents=True, exist_ok=True)
            profile_path = Path(tmpdir) / "profile.d" / "50-codex-user-env.sh"

            install_result = self._run_env_script(
                "hook",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)

            (user_home / ".zshrc").unlink()

            verify_result = self._run_env_script(
                "hook",
                "--verify",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )

            self.assertNotEqual(verify_result.returncode, 0)
            self.assertIn("missing shell rc file", verify_result.stderr)
            self.assertIn(".zshrc", verify_result.stderr)

    def test_unhook_removes_managed_blocks_from_zshrc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            user_home = Path(tmpdir) / "home"
            user_home.mkdir(parents=True, exist_ok=True)
            profile_dir = Path(tmpdir) / "profile.d"
            profile_dir.mkdir(parents=True, exist_ok=True)
            profile_path = profile_dir / "50-codex-user-env.sh"
            profile_path.write_text("# managed by codex installer\n", encoding="utf-8")

            install_result = self._run_env_script(
                "hook",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)

            unhook_result = self._run_env_script(
                "unhook",
                "--user-home",
                str(user_home),
                "--profile-path",
                str(profile_path),
            )

            self.assertEqual(unhook_result.returncode, 0, msg=unhook_result.stderr)
            self.assertFalse(profile_path.exists())
            zshrc = (user_home / ".zshrc").read_text(encoding="utf-8")
            self.assertNotIn("# >>> codex-shell-hook >>>", zshrc)
            profile = (user_home / ".profile").read_text(encoding="utf-8")
            self.assertNotIn("# managed by codex installer", profile)


if __name__ == "__main__":
    unittest.main()
