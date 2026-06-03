import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "resources" / "skills"
SKILLS_METADATA = SKILLS_ROOT / "metadata.json"
QUICK_VALIDATE = SKILLS_ROOT / "common" / "pack-skills" / "scripts" / "quick_validate.py"


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
