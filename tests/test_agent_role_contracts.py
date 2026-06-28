import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "config" / "agents"
APPS_TOML_PATH = REPO_ROOT / "config" / "usr" / "apps.toml"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from common import InstallError  # noqa: E402
from hook_runtime_catalog import load_hook_catalog  # noqa: E402
from agent_role_contracts import validate_agent_role_contracts  # noqa: E402

class AgentRoleContractsTests(unittest.TestCase):
    def test_validate_agent_role_contracts_accepts_repo_layout(self) -> None:
        validate_agent_role_contracts(AGENTS_DIR, APPS_TOML_PATH)

    def test_validate_agent_role_contracts_rejects_missing_role_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            copied_agents_dir = Path(tmpdir) / "agents"
            shutil.copytree(AGENTS_DIR, copied_agents_dir)
            (copied_agents_dir / "manager.toml").unlink()

            with self.assertRaisesRegex(InstallError, r"missing role TOMLs: manager"):
                validate_agent_role_contracts(copied_agents_dir, APPS_TOML_PATH)

    def test_manifest_roles_match_agent_configs_and_apps_entries(self) -> None:
        manifest_roles = load_hook_catalog()["roles"]
        expected_role_names = [str(role["name"]) for role in manifest_roles]

        agent_files = sorted(path.stem for path in AGENTS_DIR.glob("*.toml"))
        self.assertEqual(agent_files, sorted(expected_role_names))

        apps_payload = tomllib.loads(APPS_TOML_PATH.read_text(encoding="utf-8"))
        agent_entries = apps_payload.get("agents", {})
        configured_roles = {
            name: entry
            for name, entry in agent_entries.items()
            if isinstance(entry, dict)
        }
        self.assertEqual(sorted(configured_roles), sorted(expected_role_names))

    def test_all_agent_role_tomls_parse(self) -> None:
        for path in sorted(AGENTS_DIR.glob("*.toml")):
            with self.subTest(path=path.name):
                tomllib.loads(path.read_text(encoding="utf-8"))

    def test_runtime_skill_roots_use_single_flat_codex_skills_path(self) -> None:
        apps_payload = tomllib.loads(APPS_TOML_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            apps_payload.get("skills", {}).get("config"),
            [{"enabled": True, "path": "${CODEX_SKILLS}"}],
        )

        for path in sorted(AGENTS_DIR.glob("*.toml")):
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertEqual(
                    payload.get("skills", {}).get("config"),
                    [{"enabled": True, "path": "${CODEX_SKILLS}"}],
                )


if __name__ == "__main__":
    unittest.main()
