import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from apps_config import REQUIRED_SHARED_MCP_REFS  # noqa: E402
from apps_config import effective_plugins_inventory_payload  # noqa: E402
from apps_config import rewrite_runtime_plugin_skill_dependencies  # noqa: E402
from common import InstallError  # noqa: E402
from common import parse_json_file  # noqa: E402
from common import parse_toml_file  # noqa: E402
from plugins import DEFAULT_PROMPT_MAX_CHARS  # noqa: E402
from plugins import plugin_manifest_bundles  # noqa: E402
from skills import role_tools_from_skills  # noqa: E402


PLUGINS_MANIFEST_PATH = REPO_ROOT / "resources" / "plugins" / "manifest.json"
APPS_TOML_PATH = REPO_ROOT / "config" / "usr" / "apps.toml"
SKILLS_METADATA_PATH = REPO_ROOT / "resources" / "skills" / "metadata.json"
REQUIRED_GLOBAL_MCP = set(REQUIRED_SHARED_MCP_REFS)


def load_effective_plugins_inventory() -> dict:
    return effective_plugins_inventory_payload(
        parse_json_file(PLUGINS_MANIFEST_PATH),
        PLUGINS_MANIFEST_PATH,
    )


def load_apps_payload() -> dict:
    return parse_toml_file(APPS_TOML_PATH)


def load_plugin_bundles():
    apps_payload = load_apps_payload()
    inventory_payload = load_effective_plugins_inventory()
    return plugin_manifest_bundles(
        repo_root=REPO_ROOT,
        plugins_payload=apps_payload,
        plugins_path=APPS_TOML_PATH,
        plugins_metadata_payload=inventory_payload,
        plugins_metadata_path=PLUGINS_MANIFEST_PATH,
        shared_mcp_servers=apps_payload.get("mcp_servers", {}),
        enabled_only=False,
    )


def dependency_values(path: Path) -> set[str]:
    values: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("value:"):
            values.add(stripped.split(":", 1)[1].strip().strip("\"'"))
    return values


class PluginRuntimeContractsTests(unittest.TestCase):
    def test_current_plugins_inventory_declares_required_global_shared_mcp_refs(self) -> None:
        inventory = load_effective_plugins_inventory()
        self.assertTrue(REQUIRED_GLOBAL_MCP.issubset(set(inventory["shared_mcp"]["refs"])))

    def test_effective_plugins_inventory_warns_when_required_global_shared_mcp_refs_missing(self) -> None:
        inventory = parse_json_file(PLUGINS_MANIFEST_PATH)
        inventory["shared_mcp"]["refs"] = ["filesystem", "git"]

        with patch("builtins.print") as print_mock:
            rendered = effective_plugins_inventory_payload(inventory, PLUGINS_MANIFEST_PATH)

        self.assertEqual(rendered["shared_mcp"]["refs"], ["filesystem", "git"])
        print_mock.assert_called_once()
        self.assertIn("missing required global MCP servers", print_mock.call_args.args[0])

    def test_plugin_default_prompt_warns_and_truncates_over_limit(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["security-labs"]["interface"]["default_prompt"] = "x" * (DEFAULT_PROMPT_MAX_CHARS + 1)

        with patch("builtins.print") as print_mock:
            bundles = plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )
        security_labs = {bundle.name: bundle for bundle in bundles}["security-labs"]
        self.assertEqual(len(security_labs.default_prompt), DEFAULT_PROMPT_MAX_CHARS)
        print_mock.assert_called()
        self.assertTrue(
            any("truncating to fit runtime limit" in call.args[0] for call in print_mock.call_args_list),
        )

    def test_skill_roles_include_required_global_mcp_servers(self) -> None:
        skills_payload = parse_json_file(SKILLS_METADATA_PATH)
        for role_name in ("common", "audit"):
            role_tools = set(role_tools_from_skills(skills_payload, role_name))
            self.assertTrue(
                REQUIRED_GLOBAL_MCP.issubset(role_tools),
                f"{role_name} role is missing required global MCP servers",
            )

    def test_plugin_bundles_do_not_emit_global_mcp_servers(self) -> None:
        bundles = load_plugin_bundles()
        for bundle in bundles:
            self.assertTrue(
                REQUIRED_GLOBAL_MCP.isdisjoint(bundle.mcp_servers.keys()),
                f"{bundle.name} emitted global MCP servers in plugin bundle metadata",
            )
        scoped_servers = {bundle.name: sorted(bundle.mcp_servers) for bundle in bundles if bundle.mcp_servers}
        self.assertEqual(scoped_servers, {})

    def test_plugin_skill_dependencies_include_global_and_plugin_scoped_mcp(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        bundles = {bundle.name: bundle for bundle in load_plugin_bundles()}
        bundle = bundles["hosting-platforms"]

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_skills_dir = Path(tmpdir)
            for skill_name in bundle.skills:
                openai_yaml = runtime_skills_dir / skill_name / "agents" / "openai.yaml"
                openai_yaml.parent.mkdir(parents=True, exist_ok=True)
                openai_yaml.write_text("name: test\npolicy:\n  mode: safe\n", encoding="utf-8")

            rewrite_runtime_plugin_skill_dependencies(
                runtime_skills_dir,
                bundle,
                inventory_payload,
                apps_payload,
                dry_run=False,
            )

            rendered_values = dependency_values(runtime_skills_dir / bundle.skills[0] / "agents" / "openai.yaml")
            expected_values = REQUIRED_GLOBAL_MCP | {"render", "vercel"}
            self.assertTrue(expected_values.issubset(rendered_values))

    def test_plugin_skill_dependencies_warn_when_mcp_server_is_missing(self) -> None:
        apps_payload = load_apps_payload()
        apps_payload["mcp_servers"] = dict(apps_payload["mcp_servers"])
        apps_payload["mcp_servers"].pop("vercel", None)
        inventory_payload = load_effective_plugins_inventory()
        bundles = {bundle.name: bundle for bundle in load_plugin_bundles()}
        bundle = bundles["hosting-platforms"]

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_skills_dir = Path(tmpdir)
            for skill_name in bundle.skills:
                openai_yaml = runtime_skills_dir / skill_name / "agents" / "openai.yaml"
                openai_yaml.parent.mkdir(parents=True, exist_ok=True)
                openai_yaml.write_text("name: test\npolicy:\n  mode: safe\n", encoding="utf-8")

            with patch("builtins.print") as print_mock:
                rewrite_runtime_plugin_skill_dependencies(
                    runtime_skills_dir,
                    bundle,
                    inventory_payload,
                    apps_payload,
                    dry_run=False,
                )

            rendered_values = dependency_values(runtime_skills_dir / bundle.skills[0] / "agents" / "openai.yaml")
            self.assertIn("render", rendered_values)
            self.assertNotIn("vercel", rendered_values)
            print_mock.assert_called()
            self.assertTrue(
                any("references unknown MCP server: vercel" in call.args[0] for call in print_mock.call_args_list),
            )


if __name__ == "__main__":
    unittest.main()
