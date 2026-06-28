import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "resources" / "skills"
SKILLS_METADATA = SKILLS_ROOT / "metadata.json"
QUICK_VALIDATE = SKILLS_ROOT / "common" / "pack-skills" / "scripts" / "quick_validate.py"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from common import InstallError  # noqa: E402
from skills import render_dependency_block  # noqa: E402
from skills import rewrite_openai_yaml_dependencies  # noqa: E402
from skills import validate_openai_yaml_mcp_dependencies  # noqa: E402


def load_quick_validate_module():
    spec = importlib.util.spec_from_file_location("pack_skills_quick_validate", QUICK_VALIDATE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load validator module from {QUICK_VALIDATE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillCatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quick_validate = load_quick_validate_module()
        cls.skills_payload = json.loads(SKILLS_METADATA.read_text(encoding="utf-8"))

    def test_all_listed_skills_have_required_support_files(self) -> None:
        required_rel_paths = [
            "SKILL.md",
            "metadata.json",
            "agents/openai.yaml",
            "assets/icon-32.png",
            "assets/icon-128.png",
            "rules/framework.md",
            "rules/rules.md",
            "references/latest-sources.md",
            "scripts/skill_helper.py",
        ]

        for entries in self.skills_payload["skills"].values():
            for entry in entries:
                skill_dir = SKILLS_ROOT / entry["skill_path"]
                self.assertTrue(skill_dir.is_dir(), f"missing skill dir: {skill_dir}")
                for rel in required_rel_paths:
                    self.assertTrue((skill_dir / rel).exists(), f"{skill_dir} missing {rel}")

    def test_all_listed_skills_pass_quick_validation(self) -> None:
        for entries in self.skills_payload["skills"].values():
            for entry in entries:
                skill_dir = SKILLS_ROOT / entry["skill_path"]
                valid, message = self.quick_validate.validate_skill(skill_dir)
                self.assertTrue(valid, f"{skill_dir} failed validation: {message}")

    def test_all_skill_directories_are_listed_once_in_metadata(self) -> None:
        listed = []
        for entries in self.skills_payload["skills"].values():
            for entry in entries:
                listed.append(entry["skill_path"])

        discovered = sorted(
            f"{group.name}/{skill.name}"
            for group in SKILLS_ROOT.iterdir()
            if group.is_dir()
            for skill in group.iterdir()
            if skill.is_dir()
        )
        self.assertEqual(sorted(listed), discovered)
        self.assertEqual(len(listed), len(set(listed)))

    def test_rewrite_openai_yaml_dependencies_preserves_non_tool_sections(self) -> None:
        source = """interface:
  display_name: Demo

dependencies:
  files:
  - type: local
    value: ./README.md
  tools:
  - type: mcp
    value: old
    description: old MCP server
    transport: stdio
    command: old-command
  apps:
  - github

policy:
  allow_implicit_invocation: true
"""
        dependency_block = render_dependency_block(
            ["filesystem"],
            {
                "filesystem": {
                    "command": "bash",
                    "args": ["-lc", "printf ok"],
                }
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "openai.yaml"
            path.write_text(source, encoding="utf-8")

            rewrite_openai_yaml_dependencies(path, dependency_block, dry_run=False)
            rendered = path.read_text(encoding="utf-8")

            self.assertIn("files:", rendered)
            self.assertIn("value: ./README.md", rendered)
            self.assertIn("apps:", rendered)
            self.assertIn("- github", rendered)
            self.assertIn("value: filesystem", rendered)
            self.assertNotIn("value: old", rendered)

            validate_openai_yaml_mcp_dependencies(path)

    def test_render_dependency_block_requires_known_server(self) -> None:
        with self.assertRaisesRegex(InstallError, "missing MCP server definition"):
            render_dependency_block(["filesystem"], {})

    def test_render_dependency_block_accepts_command_server_without_args(self) -> None:
        rendered = render_dependency_block(
            ["filesystem"],
            {
                "filesystem": {
                    "command": "bash",
                }
            },
        )

        self.assertIn("transport: stdio", rendered)
        self.assertIn("command: bash", rendered)
