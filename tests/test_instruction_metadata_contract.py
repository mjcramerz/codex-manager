import json
import re
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "usr" / "config.toml"
MEMORY_PATH = REPO_ROOT / "config" / "usr" / "memory.toml"
DEFAULT_METADATA_PATH = REPO_ROOT / "resources" / "instructions" / "default" / "metadata.json"
AGENTS_METADATA_PATH = REPO_ROOT / "resources" / "instructions" / "agents" / "metadata.json"
PROFILES_METADATA_PATH = REPO_ROOT / "resources" / "instructions" / "profiles" / "metadata.json"
INSTRUCTIONS_ROOT = REPO_ROOT / "resources" / "instructions"
AGENT_CONFIG_DIR = REPO_ROOT / "config" / "agents"
PROFILE_CONFIG_DIR = REPO_ROOT / "config" / "profiles"
LEGACY_METADATA_PATH = REPO_ROOT / "resources" / "instructions" / "metadata.json"
DEVELOPER_INSTRUCTIONS_PATTERN = re.compile(r'developer_instructions\s*=\s*"""\n?(.*?)\n?"""', re.S)


class InstructionMetadataContractTests(unittest.TestCase):
    @staticmethod
    def _flatten_paths(value: dict, prefix: tuple[str, ...] = ()) -> dict[str, str]:
        flattened: dict[str, str] = {}
        for key, item in value.items():
            if isinstance(item, dict):
                flattened.update(
                    InstructionMetadataContractTests._flatten_paths(item, (*prefix, key))
                )
                continue
            if isinstance(item, str):
                flattened[".".join((*prefix, key))] = item
        return flattened

    @staticmethod
    def _manifest_entries(payload: dict) -> list[tuple[str, dict]]:
        return [
            (group["name"], entry)
            for group in payload["groups"]
            for entry in group.get("entries", [])
        ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.memory = tomllib.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        cls.default_metadata = json.loads(DEFAULT_METADATA_PATH.read_text(encoding="utf-8"))
        cls.default_entries = cls._manifest_entries(cls.default_metadata)

        cls.profiles_metadata = json.loads(PROFILES_METADATA_PATH.read_text(encoding="utf-8"))
        cls.profile_entries = cls._manifest_entries(cls.profiles_metadata)

        cls.agents_metadata = json.loads(AGENTS_METADATA_PATH.read_text(encoding="utf-8"))
        cls.agent_entries = cls._manifest_entries(cls.agents_metadata)

    def test_legacy_root_manifest_is_removed(self) -> None:
        self.assertFalse(LEGACY_METADATA_PATH.exists())

    def test_default_manifest_keys_match_active_instruction_overrides(self) -> None:
        expected = {
            "model_catalog_json",
            "model_instructions_file",
            "experimental_compact_prompt_file",
        }
        expected |= set(
            self._flatten_paths(
                {"instruction_overrides": self.config.get("instruction_overrides", {})}
            ).keys()
        )
        expected |= {
            f"memories.{key}"
            for key in self.memory.get("memories", {})
            if key.endswith("_instructions_file")
        }
        actual = {entry["config_key"] for _, entry in self.default_entries if entry.get("config_key")}
        self.assertEqual(actual, expected)

    def test_default_manifest_source_files_exist(self) -> None:
        missing = []
        for group_name, entry in self.default_entries:
            source_group = entry.get("source_group", group_name)
            source_path = INSTRUCTIONS_ROOT / source_group / entry["file"]
            if not source_path.is_file():
                missing.append(str(source_path.relative_to(REPO_ROOT)))
        self.assertEqual(missing, [])

    def test_default_manifest_disable_paths_match_config_values(self) -> None:
        expected = {
            "model_catalog_json": self.config["model_catalog_json"],
            "model_instructions_file": self.config["model_instructions_file"],
            "experimental_compact_prompt_file": self.config["experimental_compact_prompt_file"],
        }
        expected.update(
            self._flatten_paths(
                {"instruction_overrides": self.config.get("instruction_overrides", {})}
            )
        )
        expected.update(
            {
                f"memories.{key}": value
                for key, value in self.memory.get("memories", {}).items()
                if key.endswith("_instructions_file")
            }
        )
        actual = {
            entry["config_key"]: entry["default_disable_path"]
            for _, entry in self.default_entries
            if entry.get("config_key")
        }
        self.assertEqual(actual, expected)

    def test_default_asset_only_entries_use_expected_runtime_targets(self) -> None:
        actual = {
            entry["name"]: entry["default_disable_path"]
            for _, entry in self.default_entries
            if not entry.get("config_key")
        }
        self.assertEqual(
            actual,
            {
                "review_catalog_asset": "$CODEX_HOME/.models/review_catalog.json",
                "cyber_catalog_asset": "$CODEX_HOME/.models/cyber_catalog.json",
            },
        )

    def test_profile_manifest_entries_match_profile_config_values(self) -> None:
        expected: dict[tuple[str, str], str] = {}
        for path in sorted(PROFILE_CONFIG_DIR.glob("*.toml")):
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            expected[(path.name, "model_catalog_json")] = payload["model_catalog_json"]
            expected[(path.name, "model_instructions_file")] = payload["model_instructions_file"]
            expected[(path.name, "instruction_overrides.models.base_instructions_file")] = payload[
                "instruction_overrides"
            ]["models"]["base_instructions_file"]

        actual = {}
        for _, entry in self.profile_entries:
            key = entry.get("config_key")
            if not key:
                continue
            config_file = entry["config_file"]
            value = entry["default_enable_path"] if entry.get("enabled", True) else entry["default_disable_path"]
            actual[(config_file, key)] = value
        self.assertEqual(actual, expected)

    def test_profile_manifest_source_files_exist(self) -> None:
        missing = []
        for group_name, entry in self.profile_entries:
            source_group = entry.get("source_group", group_name)
            source_path = INSTRUCTIONS_ROOT / source_group / entry["file"]
            if not source_path.is_file():
                missing.append(str(source_path.relative_to(REPO_ROOT)))
        self.assertEqual(missing, [])

    def test_agent_manifest_entries_match_role_instruction_sources(self) -> None:
        expected = {}
        for path in sorted(AGENT_CONFIG_DIR.glob("*.toml")):
            text = path.read_text(encoding="utf-8")
            match = DEVELOPER_INSTRUCTIONS_PATTERN.search(text)
            self.assertIsNotNone(match, f"missing developer_instructions block in {path}")
            assert match is not None
            expected[(path.name, "developer_instructions")] = match.group(1).strip("\n")

        actual = {}
        for group_name, entry in self.agent_entries:
            source_group = entry.get("source_group", group_name)
            source_path = INSTRUCTIONS_ROOT / source_group / entry["file"]
            actual[(entry["config_file"], entry["config_key"])] = source_path.read_text(
                encoding="utf-8"
            ).strip("\n")
        self.assertEqual(actual, expected)

    def test_agent_manifest_source_files_exist(self) -> None:
        missing = []
        for group_name, entry in self.agent_entries:
            source_group = entry.get("source_group", group_name)
            source_path = INSTRUCTIONS_ROOT / source_group / entry["file"]
            if not source_path.is_file():
                missing.append(str(source_path.relative_to(REPO_ROOT)))
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
