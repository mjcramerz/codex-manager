import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = REPO_ROOT / "resources" / "home" / "user"


class RuntimePackStructureContractTests(unittest.TestCase):
    def test_governing_files_have_purpose_and_navigation(self) -> None:
        files = [
            HOME_ROOT / "AGENTS.md",
            HOME_ROOT / "INDEX.md",
            HOME_ROOT / "docs" / "OVERVIEW.md",
            HOME_ROOT / "index" / "OVERVIEW.md",
            HOME_ROOT / "index" / "core" / "overview.md",
            HOME_ROOT / "index" / "domains" / "overview.md",
            HOME_ROOT / "index" / "pack" / "overview.md",
            HOME_ROOT / "plans" / "OVERVIEW.md",
            HOME_ROOT / "plans" / "frameworks" / "overview.md",
            HOME_ROOT / "plans" / "workflows" / "overview.md",
            HOME_ROOT / "plans" / "skills" / "overview.md",
            HOME_ROOT / "docs" / "workflows" / "overview.md",
            HOME_ROOT / "rules" / "OVERVIEW.md",
            HOME_ROOT / "snippets" / "OVERVIEW.md",
            HOME_ROOT / "templates" / "OVERVIEW.md",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("Purpose:", text, path)
            if path.name.endswith(".md") and path != HOME_ROOT / "AGENTS.md":
                self.assertIn("## Navigation", text, path)

    def test_legacy_unix_entrypoint_is_removed(self) -> None:
        self.assertFalse((HOME_ROOT / "UNIX.md").exists())

    def test_governing_docs_avoid_tool_specific_or_stale_contract_language(self) -> None:
        files = [
            HOME_ROOT / "AGENTS.md",
            HOME_ROOT / "INDEX.md",
            HOME_ROOT / "docs" / "OVERVIEW.md",
            HOME_ROOT / "index" / "OVERVIEW.md",
            HOME_ROOT / "index" / "core" / "overview.md",
            HOME_ROOT / "index" / "domains" / "overview.md",
            HOME_ROOT / "index" / "pack" / "overview.md",
            HOME_ROOT / "plans" / "OVERVIEW.md",
            HOME_ROOT / "docs" / "workflows" / "overview.md",
            HOME_ROOT / "docs" / "workflows" / "agent-orchestration.md",
            HOME_ROOT / "index" / "core" / "agent-orchestration.md",
            HOME_ROOT / "rules" / "OVERVIEW.md",
            HOME_ROOT / "snippets" / "OVERVIEW.md",
            HOME_ROOT / "templates" / "OVERVIEW.md",
        ]
        banned = (
            "spawn_agent",
            "send_input",
            "close_agent",
            "$CODEX_HOME/rollouts",
            "runtime materialized content",
            "runtime-only materialized content",
        )
        for path in files:
            text = path.read_text(encoding="utf-8")
            for needle in banned:
                self.assertNotIn(needle, text, f"{path} still contains {needle!r}")
