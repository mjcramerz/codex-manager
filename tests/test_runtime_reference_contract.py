import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = REPO_ROOT / "resources" / "home" / "user"
SKILLS_ROOT = REPO_ROOT / "resources" / "skills"
PLUGIN_SKILLS_ROOT = REPO_ROOT / "resources" / "plugins" / "skills"


class RuntimeReferenceContractTests(unittest.TestCase):
    def test_no_dead_prompt_library_paths(self) -> None:
        roots = [HOME_ROOT, SKILLS_ROOT, PLUGIN_SKILLS_ROOT]
        banned = (
            "$CODEX_HOME/prompts/",
            "$CODEX_HOME/.prompt/OVERVIEW.md",
            "$CODEX_HOME/docs/index",
        )
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                for needle in banned:
                    if needle in text:
                        offenders.append(f"{path}: {needle}")
        self.assertEqual(offenders, [])

    def test_no_wrong_runtime_skill_root_paths(self) -> None:
        roots = [SKILLS_ROOT, PLUGIN_SKILLS_ROOT]
        banned = (
            "$CODEX_HOME/skills/",
            "$CODEX_SKILLS/GIT/",
            "$CODEX_SKILLS/NOTE/",
        )
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                for needle in banned:
                    if needle in text:
                        offenders.append(f"{path}: {needle}")
        self.assertEqual(offenders, [])
