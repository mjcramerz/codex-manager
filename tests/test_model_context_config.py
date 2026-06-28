import json
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DEFAULT_CATALOG_PATH = REPO_ROOT / "resources" / "home" / "user" / ".models" / "default_catalog.json"
RUNTIME_REVIEW_CATALOG_PATH = REPO_ROOT / "resources" / "home" / "user" / ".models" / "review_catalog.json"
RUNTIME_CYBER_CATALOG_PATH = REPO_ROOT / "resources" / "home" / "user" / ".models" / "cyber_catalog.json"
USER_CONFIG_PATH = REPO_ROOT / "config" / "usr" / "config.toml"
PROFILE_CONFIG_DIR = REPO_ROOT / "config" / "profiles"


def catalog_models(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {model["slug"]: model for model in payload["models"]}


class ModelContextConfigTests(unittest.TestCase):
    def test_runtime_default_catalog_contains_requested_models_only(self) -> None:
        models = catalog_models(RUNTIME_DEFAULT_CATALOG_PATH)

        self.assertEqual(
            list(models.keys()),
            [
                "gpt-5.6-sol",
                "gpt-5.6-terra",
                "gpt-5.6-luna",
                "gpt-5.5",
                "gpt-5.4",
                "gpt-5.4-mini",
                "gpt-5.3-codex-spark",
            ],
        )

    def test_runtime_default_catalog_keeps_requested_context_windows(self) -> None:
        models = catalog_models(RUNTIME_DEFAULT_CATALOG_PATH)

        self.assertEqual(models["gpt-5.6-sol"]["context_window"], 385_000)
        self.assertEqual(models["gpt-5.6-terra"]["context_window"], 385_000)
        self.assertEqual(models["gpt-5.6-luna"]["context_window"], 385_000)
        self.assertEqual(models["gpt-5.5"]["context_window"], 385_000)
        self.assertEqual(models["gpt-5.4"]["context_window"], 1_050_000)
        self.assertEqual(models["gpt-5.4-mini"]["context_window"], 400_000)
        self.assertEqual(models["gpt-5.3-codex-spark"]["context_window"], 272_000)

    def test_runtime_profile_catalogs_are_curated(self) -> None:
        review_models = catalog_models(RUNTIME_REVIEW_CATALOG_PATH)
        cyber_models = catalog_models(RUNTIME_CYBER_CATALOG_PATH)

        self.assertEqual(list(review_models.keys()), ["gpt-5.4"])
        self.assertEqual(list(cyber_models.keys()), ["gpt-5.5-cyber"])

    def test_user_config_points_at_default_catalog(self) -> None:
        payload = tomllib.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["model_catalog_json"], "$CODEX_HOME/.models/default_catalog.json")

    def test_profile_configs_parse_and_target_expected_catalogs(self) -> None:
        expected = {
            "agents.config.toml": ("gpt-5.6-sol", "$CODEX_HOME/.models/default_catalog.json"),
            "cyber.config.toml": ("gpt-5.5-cyber", "$CODEX_HOME/.models/cyber_catalog.json"),
            "debug.config.toml": ("gpt-5.6-terra", "$CODEX_HOME/.models/default_catalog.json"),
            "default.config.toml": ("gpt-5.5", "$CODEX_HOME/.models/default_catalog.json"),
            "fast.config.toml": ("gpt-5.4-mini", "$CODEX_HOME/.models/default_catalog.json"),
            "review.config.toml": ("gpt-5.4", "$CODEX_HOME/.models/review_catalog.json"),
            "spark.config.toml": ("gpt-5.3-codex-spark", "$CODEX_HOME/.models/default_catalog.json"),
            "test.config.toml": ("gpt-5.6-luna", "$CODEX_HOME/.models/default_catalog.json"),
        }

        self.assertEqual(sorted(path.name for path in PROFILE_CONFIG_DIR.glob("*.toml")), sorted(expected))

        for name, (model_slug, catalog_path) in expected.items():
            payload = tomllib.loads((PROFILE_CONFIG_DIR / name).read_text(encoding="utf-8"))
            self.assertNotIn("profile", payload)
            self.assertEqual(payload["model"], model_slug)
            self.assertEqual(payload["model_catalog_json"], catalog_path)
            self.assertIn("instruction_overrides", payload)
            self.assertIn("models", payload["instruction_overrides"])


if __name__ == "__main__":
    unittest.main()
