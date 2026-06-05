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

from hook_runtime_catalog import load_hook_catalog  # noqa: E402

EXPECTED_MULTI_AGENT_CONCURRENCY = {
    "analyst.toml": 2,
    "coder.toml": 2,
    "delegator.toml": 3,
    "default.toml": 2,
    "explorer.toml": 2,
    "hunter.toml": 2,
    "integrator.toml": 1,
    "manager.toml": 4,
    "orchestrator.toml": 4,
    "planner.toml": 2,
    "reviewer.toml": 1,
    "synthesizer.toml": 1,
    "tester.toml": 1,
    "worker.toml": 1,
}


class AgentRoleContractsTests(unittest.TestCase):
    def test_manifest_roles_match_agent_configs_and_apps_entries(self) -> None:
        manifest_roles = load_hook_catalog()["roles"]
        expected_role_names = [str(role["name"]) for role in manifest_roles]
        expected_descriptions = {
            str(role["name"]): str(role["description"])
            for role in manifest_roles
        }

        agent_files = sorted(path.stem for path in AGENTS_DIR.glob("*.toml"))
        self.assertEqual(agent_files, sorted(expected_role_names))

        apps_payload = tomllib.loads(APPS_TOML_PATH.read_text(encoding="utf-8"))
        agent_entries = apps_payload.get("agents", {})
        configured_roles = {
            name: entry
            for name, entry in agent_entries.items()
            if isinstance(entry, dict) and isinstance(entry.get("config_file"), str)
        }
        self.assertEqual(sorted(configured_roles), sorted(expected_role_names))
        for role_name, entry in configured_roles.items():
            with self.subTest(role=role_name):
                self.assertEqual(entry.get("description"), expected_descriptions[role_name])
                self.assertEqual(entry.get("config_file"), f"${{CODEX_AGENTS}}/{role_name}.toml")

    def test_all_agent_role_tomls_parse(self) -> None:
        for path in sorted(AGENTS_DIR.glob("*.toml")):
            with self.subTest(path=path.name):
                tomllib.loads(path.read_text(encoding="utf-8"))

    def test_agent_role_tomls_do_not_keep_live_artifact_feature(self) -> None:
        for path in sorted(AGENTS_DIR.glob("*.toml")):
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertNotIn("artifact", payload.get("features", {}))

    def test_agent_role_tomls_define_multi_agent_v2_contracts(self) -> None:
        for path in sorted(AGENTS_DIR.glob("*.toml")):
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            multi_agent_v2 = payload.get("features", {}).get("multi_agent_v2")
            with self.subTest(path=path.name):
                self.assertIsInstance(multi_agent_v2, dict)
                self.assertTrue(multi_agent_v2.get("enabled"))
                self.assertTrue(multi_agent_v2.get("usage_hint_enabled"))
                self.assertEqual(
                    multi_agent_v2.get("max_concurrent_threads_per_session"),
                    EXPECTED_MULTI_AGENT_CONCURRENCY[path.name],
                )
                min_wait = multi_agent_v2.get("min_wait_timeout_ms")
                default_wait = multi_agent_v2.get("default_wait_timeout_ms")
                max_wait = multi_agent_v2.get("max_wait_timeout_ms")
                self.assertIsInstance(min_wait, int)
                self.assertIsInstance(default_wait, int)
                self.assertIsInstance(max_wait, int)
                self.assertLessEqual(min_wait, default_wait)
                self.assertLessEqual(default_wait, max_wait)
                self.assertTrue(str(multi_agent_v2.get("root_agent_usage_hint_text", "")).strip())
                self.assertTrue(str(multi_agent_v2.get("subagent_usage_hint_text", "")).strip())


if __name__ == "__main__":
    unittest.main()
