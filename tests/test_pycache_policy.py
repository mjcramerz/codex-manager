import os
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYCACHE_PREFIX = "/tmp/codex-pycache"


class PycachePolicyTests(unittest.TestCase):
    def _clean_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.pop("PYTHONPYCACHEPREFIX", None)
        return env

    def _managed_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPYCACHEPREFIX"] = DEFAULT_PYCACHE_PREFIX
        return env

    def _assert_no_repo_pycache(self) -> None:
        pycache_dirs = sorted(
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("__pycache__")
            if path.is_dir()
        )
        self.assertEqual(pycache_dirs, [], f"repo contains unexpected __pycache__ dirs: {pycache_dirs}")

    def test_repo_config_exports_pycache_prefix(self) -> None:
        vars_payload = tomllib.loads((REPO_ROOT / "vars.toml").read_text(encoding="utf-8"))
        env_payload = tomllib.loads((REPO_ROOT / "config" / "usr" / "env.toml").read_text(encoding="utf-8"))

        self.assertNotIn("PYTHONPYCACHEPREFIX", vars_payload["global_variables"])
        self.assertEqual(env_payload["launch_env"]["PYTHONPYCACHEPREFIX"], DEFAULT_PYCACHE_PREFIX)
        self._assert_no_repo_pycache()

    def test_direct_python_entrypoints_do_not_create_repo_pycache(self) -> None:
        commands = (
            [sys.executable, "src/install/codex_install.py", "--help"],
            [sys.executable, "src/misc/codex_schema_tool.py", "--help"],
            [sys.executable, "src/python/lib/keyring_env.py", "--help"],
        )
        for command in commands:
            with self.subTest(command=command[1]):
                proc = subprocess.run(
                    command,
                    check=False,
                    cwd=REPO_ROOT,
                    env=self._clean_env(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                self._assert_no_repo_pycache()

    def test_unittest_package_entrypoint_respects_managed_pycache_env(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "tests.test_shell_env"],
            check=False,
            cwd=REPO_ROOT,
            env=self._managed_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self._assert_no_repo_pycache()


if __name__ == "__main__":
    unittest.main()
