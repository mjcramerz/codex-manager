import json
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "usr" / "config.toml"
MEMORY_PATH = REPO_ROOT / "config" / "usr" / "memory.toml"
METADATA_PATH = REPO_ROOT / "resources" / "instructions" / "metadata.json"
INSTRUCTIONS_ROOT = REPO_ROOT / "resources" / "instructions"


class InstructionMetadataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.memory = tomllib.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        cls.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        cls.entries = [
            (group["name"], entry)
            for group in cls.metadata["groups"]
            for entry in group.get("entries", [])
        ]

    def test_manifest_keys_match_active_instruction_overrides(self) -> None:
        expected = {"model_instructions_file"}
        expected |= set(self.config.get("instruction_overrides", {}).keys())
        expected |= {
            key
            for key in self.memory.get("memories", {})
            if key.endswith("_instructions_file")
        }
        actual = {entry["config_key"] for _, entry in self.entries}
        self.assertEqual(actual, expected)

    def test_manifest_source_files_exist(self) -> None:
        missing = []
        for group_name, entry in self.entries:
            source_group = entry.get("source_group", group_name)
            source_path = INSTRUCTIONS_ROOT / source_group / entry["file"]
            if not source_path.is_file():
                missing.append(str(source_path.relative_to(REPO_ROOT)))
        self.assertEqual(missing, [])

    def test_default_disable_paths_match_config_values(self) -> None:
        expected = {"model_instructions_file": self.config["model_instructions_file"]}
        expected.update(self.config.get("instruction_overrides", {}))
        expected.update(
            {
                key: value
                for key, value in self.memory.get("memories", {}).items()
                if key.endswith("_instructions_file")
            }
        )
        actual = {
            entry["config_key"]: entry["default_disable_path"]
            for _, entry in self.entries
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
