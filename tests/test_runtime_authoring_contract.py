import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = REPO_ROOT / "resources" / "home" / "user"


class RuntimeAuthoringContractTests(unittest.TestCase):
    def test_non_template_docs_and_plans_avoid_weak_placeholder_text(self) -> None:
        banned = (
            "<short task statement>",
            "<command or check>",
            "<feature>",
            "<acceptance criteria>",
            "<files/modules likely to change>",
            "<schemas/contracts affected>",
            "<correctness/security/perf risks>",
            "<hot path modules>",
            "<benchmarks or load tests>",
            "<codex-source-repo>",
            "<repo>/scripts/release",
        )
        roots = [HOME_ROOT / "docs", HOME_ROOT / "plans"]
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                for needle in banned:
                    if needle in text:
                        offenders.append(f"{path}: {needle}")
        self.assertEqual(offenders, [])
