import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = REPO_ROOT / "resources" / "home" / "user"
SKILLS_ROOT = REPO_ROOT / "resources" / "skills"
PLUGIN_SKILLS_ROOT = REPO_ROOT / "resources" / "plugins" / "skills"
class RuntimeReferenceContractTests(unittest.TestCase):
    @staticmethod
    def _skill_root_for_markdown(path: Path) -> Path | None:
        relative = path.relative_to(REPO_ROOT)
        parts = relative.parts
        if parts[:2] == ("resources", "skills") and len(parts) >= 4:
            return REPO_ROOT / "resources" / "skills" / parts[2] / parts[3]
        if parts[:3] == ("resources", "plugins", "skills") and len(parts) >= 4:
            return REPO_ROOT / "resources" / "plugins" / "skills" / parts[3]
        return None

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

    def test_skill_and_plugin_markdown_avoid_repo_source_paths(self) -> None:
        roots = [SKILLS_ROOT, PLUGIN_SKILLS_ROOT]
        banned = (
            "resources/home/user",
            "resources/skills",
            "resources/plugins",
            "resources/hooks",
            "config/usr",
            "config/vendor",
            "config/agents",
            "src/install",
            "./.models/",
        )
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                for needle in banned:
                    if needle in text:
                        offenders.append(f"{path}: {needle}")
        self.assertEqual(offenders, [])

    def test_skill_and_plugin_markdown_avoid_bundle_relative_navigation(self) -> None:
        roots = [SKILLS_ROOT, PLUGIN_SKILLS_ROOT]
        token_pattern = re.compile(r"(?:\./|\.\./)[A-Za-z0-9_./-]+/?")
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.md")):
                skill_root = self._skill_root_for_markdown(path)
                if skill_root is None:
                    continue
                skill_root = skill_root.resolve(strict=False)
                text = path.read_text(encoding="utf-8")
                for token in token_pattern.findall(text):
                    candidate = (path.parent / token).resolve(strict=False)
                    try:
                        candidate.relative_to(skill_root)
                    except ValueError:
                        continue
                    if candidate.exists():
                        offenders.append(f"{path}: {token}")
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
