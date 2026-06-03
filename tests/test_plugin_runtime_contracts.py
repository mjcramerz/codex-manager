import json
import shutil
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
from plugins import sync_runtime_plugin_bundle  # noqa: E402
from plugins import validate_plugin_skill_metadata  # noqa: E402
from plugin_bundles import render_runtime_plugin_marketplace  # noqa: E402
from plugin_bundles import render_runtime_plugin_manifest  # noqa: E402
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
        self.assertEqual(len(security_labs.default_prompt), 1)
        self.assertEqual(len(security_labs.default_prompt[0]), DEFAULT_PROMPT_MAX_CHARS)
        print_mock.assert_called()
        self.assertTrue(
            any("truncating to fit runtime limit" in call.args[0] for call in print_mock.call_args_list),
        )

    def test_plugin_default_prompt_accepts_list_and_caps_entries(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["security-labs"]["interface"]["default_prompt"] = [
            "one",
            "two",
            "three",
            "four",
        ]

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
        self.assertEqual(security_labs.default_prompt, ["one", "two", "three"])
        self.assertTrue(
            any("exceeds 3 entries" in call.args[0] for call in print_mock.call_args_list),
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

    def test_plugin_skill_dependencies_fail_when_mcp_server_is_missing(self) -> None:
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

            with self.assertRaisesRegex(InstallError, "references unknown MCP server: vercel"):
                rewrite_runtime_plugin_skill_dependencies(
                    runtime_skills_dir,
                    bundle,
                    inventory_payload,
                    apps_payload,
                    dry_run=False,
                )

    def test_runtime_plugin_bundle_sync_reuses_skill_dirs_and_prunes_only_extras(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        bundle = {entry.name: entry for entry in load_plugin_bundles()}["hosting-platforms"]

        class FakeInstaller:
            def __init__(self) -> None:
                self.repo_root = REPO_ROOT
                self.plugins_json_path = PLUGINS_MANIFEST_PATH
                self.effective_plugins_metadata_payload = inventory_payload
                self.mcp_payload = apps_payload
                self.dry_run = False
                self.sync_calls: list[tuple[Path, Path, bool]] = []
                self.removed_paths: list[Path] = []

            def _mkdir_path(self, path: Path) -> None:
                path.mkdir(parents=True, exist_ok=True)

            def _remove_path_force(self, path: Path) -> None:
                self.removed_paths.append(path)
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()

            def _sync_tree(self, src: Path, dst: Path, *, mirror_deletions: bool) -> None:
                self.sync_calls.append((src, dst, mirror_deletions))
                dst.mkdir(parents=True, exist_ok=True)

            def _write_file(self, path: Path, content: str) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_root = Path(tmpdir) / "plugin" / "local"
            runtime_skills_dir = target_root / "skills"
            runtime_skills_dir.mkdir(parents=True)
            obsolete = runtime_skills_dir / "obsolete-skill"
            obsolete.mkdir()
            # Simulate a previously synced desired skill directory.
            (runtime_skills_dir / bundle.skills[0]).mkdir()

            installer = FakeInstaller()
            sync_runtime_plugin_bundle(
                installer,
                REPO_ROOT / "resources" / "plugins" / "skills",
                target_root,
                bundle,
            )

            self.assertEqual(len(installer.sync_calls), len(bundle.skills))
            self.assertTrue(all(mirror_deletions for _, _, mirror_deletions in installer.sync_calls))
            self.assertIn(obsolete, installer.removed_paths)
            self.assertNotIn(runtime_skills_dir / bundle.skills[0], installer.removed_paths)
            self.assertTrue((target_root / ".codex-plugin" / "plugin.json").is_file())

    def test_plugin_manifest_rejects_invalid_brand_color(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["security-labs"]["interface"]["brand_color"] = "purple"

        with self.assertRaisesRegex(InstallError, "must be a #RRGGBB hex color"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_plugin_manifest_rejects_invalid_capability(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["security-labs"]["interface"]["capabilities"] = ["Read", "Launch"]

        with self.assertRaisesRegex(InstallError, "contains unsupported capability: Launch"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_plugin_settings_reject_non_boolean_enabled_payload(self) -> None:
        apps_payload = load_apps_payload()
        apps_payload["plugins"] = dict(apps_payload["plugins"])
        apps_payload["plugins"]["github@codex-local"] = {"enabled": "yes"}
        inventory_payload = load_effective_plugins_inventory()

        with self.assertRaisesRegex(InstallError, "plugin entry must be a boolean or an object with boolean enabled"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_plugin_manifest_fails_when_shared_mcp_server_missing(self) -> None:
        apps_payload = load_apps_payload()
        apps_payload["mcp_servers"] = dict(apps_payload["mcp_servers"])
        apps_payload["mcp_servers"].pop("fetch", None)
        inventory_payload = load_effective_plugins_inventory()

        with self.assertRaisesRegex(InstallError, "shared_mcp references unknown MCP server: fetch"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_plugin_manifest_fails_when_plugin_scoped_mcp_server_missing(self) -> None:
        apps_payload = load_apps_payload()
        apps_payload["mcp_servers"] = dict(apps_payload["mcp_servers"])
        apps_payload["mcp_servers"].pop("vercel", None)
        inventory_payload = load_effective_plugins_inventory()

        with self.assertRaisesRegex(
            InstallError,
            r"plugin\.mcp references unknown MCP server for .*: vercel",
        ):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_current_plugin_manifest_declares_repository_for_every_bundle(self) -> None:
        inventory = load_effective_plugins_inventory()
        for plugin_name, payload in inventory["plugins"].items():
            self.assertTrue(payload.get("repository"), f"{plugin_name} is missing repository")

    def test_current_plugin_manifest_declares_homepage_for_every_bundle(self) -> None:
        inventory = load_effective_plugins_inventory()
        for plugin_name, payload in inventory["plugins"].items():
            self.assertTrue(payload.get("homepage"), f"{plugin_name} is missing homepage")

    def test_rendered_marketplace_includes_optional_interface_urls(self) -> None:
        bundles = load_plugin_bundles()
        marketplace_name = load_effective_plugins_inventory()["marketplace_name"]
        payload = json.loads(render_runtime_plugin_marketplace(marketplace_name, bundles))
        by_name = {entry["name"]: entry for entry in payload["plugins"]}

        linear_interface = by_name["linear"]["interface"]
        self.assertEqual(linear_interface["websiteURL"], "https://linear.app/")
        self.assertEqual(linear_interface["privacyPolicyURL"], "https://linear.app/privacy")
        self.assertEqual(linear_interface["termsOfServiceURL"], "https://linear.app/terms")

    def test_current_app_backed_plugins_are_interactive(self) -> None:
        inventory = load_effective_plugins_inventory()
        for plugin_name, payload in inventory["plugins"].items():
            if payload.get("apps"):
                capabilities = payload["interface"].get("capabilities", [])
                self.assertIn("Interactive", capabilities, f"{plugin_name} must be Interactive when apps are declared")

    def test_plugin_manifest_rejects_blank_app_id(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["linear"]["apps"] = [{"name": "linear", "id": ""}]

        with self.assertRaisesRegex(InstallError, "app id is required for linear: linear"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_plugin_manifest_rejects_apps_without_interactive_capability(self) -> None:
        apps_payload = load_apps_payload()
        inventory_payload = load_effective_plugins_inventory()
        inventory_payload["plugins"]["linear"]["interface"]["capabilities"] = ["Read", "Write"]

        with self.assertRaisesRegex(InstallError, "must include Interactive when apps are declared"):
            plugin_manifest_bundles(
                repo_root=REPO_ROOT,
                plugins_payload=apps_payload,
                plugins_path=APPS_TOML_PATH,
                plugins_metadata_payload=inventory_payload,
                plugins_metadata_path=PLUGINS_MANIFEST_PATH,
                shared_mcp_servers=apps_payload.get("mcp_servers", {}),
                enabled_only=False,
            )

    def test_rendered_marketplace_entries_include_policy_and_category(self) -> None:
        bundles = load_plugin_bundles()
        marketplace_name = load_effective_plugins_inventory()["marketplace_name"]
        payload = json.loads(render_runtime_plugin_marketplace(marketplace_name, bundles))
        first = payload["plugins"][0]
        self.assertEqual(first["policy"]["installation"], "AVAILABLE")
        self.assertIn(first["policy"]["authentication"], {"ON_INSTALL", "ON_USE"})
        self.assertTrue(first["category"])

    def test_rendered_plugin_manifest_preserves_site_facing_interface_metadata(self) -> None:
        bundles = {bundle.name: bundle for bundle in load_plugin_bundles()}
        bundle = bundles["netlify"]

        payload = json.loads(render_runtime_plugin_manifest(bundle))
        interface = payload["interface"]
        self.assertIsInstance(interface["defaultPrompt"], list)
        self.assertGreaterEqual(len(interface["defaultPrompt"]), 1)
        self.assertTrue(interface["websiteURL"].startswith("https://"))
        self.assertTrue(interface["privacyPolicyURL"].startswith("https://"))
        self.assertTrue(interface["termsOfServiceURL"].startswith("https://"))

    def test_current_plugin_manifest_matches_enabled_plugins_config(self) -> None:
        inventory = load_effective_plugins_inventory()
        apps_payload = load_apps_payload()
        manifest_names = set(inventory["plugins"].keys())
        configured_names = {plugin_id.split("@", 1)[0] for plugin_id in apps_payload["plugins"].keys()}
        self.assertEqual(manifest_names, configured_names)

    def test_current_plugin_manifest_mcp_refs_exist_in_apps_config(self) -> None:
        inventory = load_effective_plugins_inventory()
        apps_payload = load_apps_payload()
        mcp_servers = apps_payload.get("mcp_servers", {})
        for plugin_name, payload in inventory["plugins"].items():
            for entry in payload.get("mcp", []):
                if isinstance(entry, str):
                    ref_name = entry
                else:
                    ref_name = entry["name"]
                self.assertIn(ref_name, mcp_servers, f"{plugin_name} references unknown MCP server: {ref_name}")

    def test_current_plugin_skill_metadata_is_valid(self) -> None:
        for metadata_path in sorted((REPO_ROOT / "resources" / "plugins" / "skills").glob("*/metadata.json")):
            validate_plugin_skill_metadata(metadata_path.parent)

    def test_plugin_skill_metadata_rejects_localhost_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "sample-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (skill_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "version": "1.0",
                        "organization": "Codex Setup",
                        "date": "June 3, 2026",
                        "abstract": "Sample skill.",
                        "references": ["https://localhost:8787"],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(InstallError, "must not use localhost URLs"):
                validate_plugin_skill_metadata(skill_dir)

    def test_plugin_skill_metadata_accepts_bundle_relative_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "sample-skill"
            refs_dir = skill_dir / "references"
            refs_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (refs_dir / "latest-sources.md").write_text("source\n", encoding="utf-8")
            (skill_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "version": "1.0",
                        "organization": "Codex Setup",
                        "date": "June 3, 2026",
                        "abstract": "Sample skill.",
                        "references": ["references/latest-sources.md"],
                    }
                ),
                encoding="utf-8",
            )

            validate_plugin_skill_metadata(skill_dir)


if __name__ == "__main__":
    unittest.main()
