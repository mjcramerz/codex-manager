import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = REPO_ROOT / "resources" / "home" / "user"


class RuntimePackDocsContractTests(unittest.TestCase):
    def test_create_prompts_doc_exists(self) -> None:
        self.assertTrue((HOME_ROOT / "docs" / "create-prompts.md").is_file())

    def test_prompt_files_start_with_short_comment(self) -> None:
        prompt_dir = HOME_ROOT / ".prompt"
        prompt_files = sorted(path for path in prompt_dir.glob("*.md"))
        self.assertGreaterEqual(len(prompt_files), 5)
        for path in prompt_files:
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(first_line.startswith("<!-- ") and first_line.endswith(" -->"), path)

    def test_only_create_prompts_doc_references_prompt_files(self) -> None:
        prompt_refs = []
        roots = [
            HOME_ROOT / "AGENTS.md",
            HOME_ROOT / "INDEX.md",
            HOME_ROOT / "docs",
            HOME_ROOT / "index",
            HOME_ROOT / "plans",
            HOME_ROOT / "templates",
        ]
        for root in roots:
            paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                if "$CODEX_HOME/.prompt/" in text or ".prompt/" in text:
                    if path != HOME_ROOT / "docs" / "create-prompts.md":
                        prompt_refs.append(str(path))
        self.assertEqual(prompt_refs, [])

    def test_no_stale_runtime_paths_in_docs_index_and_plans(self) -> None:
        disallowed = (
            "$CODEX_HOME/prompts",
            "$CODEX_HOME/docs/runbooks",
            "$CODEX_HOME/rollouts",
            "$CODEX_SKILLS/OVERVIEW.md",
            "$CODEX_HOME/.models/OVERVIEW.md",
            "$CODEX_HOME/.models/instructions/model.md",
            "$CODEX_HOME/.models/instructions/compact.md",
            "codex-setup implementation notes",
            "spawn_agent",
            "send_input",
            "close_agent",
            "$CODEX_HOME/UNIX.md",
        )

        roots = [
            HOME_ROOT / "AGENTS.md",
            HOME_ROOT / "INDEX.md",
            HOME_ROOT / "docs",
            HOME_ROOT / "index",
            HOME_ROOT / "plans",
        ]

        for root in roots:
            paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                for needle in disallowed:
                    self.assertNotIn(needle, text, f"{path} still contains stale reference {needle!r}")

    def test_home_docs_do_not_hardcode_workspace_paths(self) -> None:
        roots = [
            HOME_ROOT / "AGENTS.md",
            HOME_ROOT / "INDEX.md",
            HOME_ROOT / "docs",
            HOME_ROOT / "index",
            HOME_ROOT / "plans",
            HOME_ROOT / "templates",
            HOME_ROOT / "snippets",
        ]
        banned = (
            "/var/local/virt/containerd",
            "/data/workspace",
            "/data/codex/usr/home",
        )
        for root in roots:
            paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                for needle in banned:
                    self.assertNotIn(needle, text, f"{path} hardcodes workspace path {needle!r}")

    def test_manifest_has_current_runtime_paths(self) -> None:
        manifest = (HOME_ROOT / "index" / "manifest.yml").read_text(encoding="utf-8")
        self.assertNotIn("$CODEX_HOME/prompts", manifest)
        self.assertNotIn("$CODEX_HOME/.models/OVERVIEW.md", manifest)
        self.assertIn("$CODEX_HOME/docs/create-prompts.md", manifest)
        self.assertIn("$CODEX_HOME/.models/model_catalog.json", manifest)
        self.assertIn("$CODEX_HOME/.models/instructions/models/base.md", manifest)
        self.assertIn("$CODEX_HOME/.models/instructions/compact/prompt.md", manifest)
