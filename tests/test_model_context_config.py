import json
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_CATALOG_PATH = REPO_ROOT / "resources" / "home" / "user" / ".models" / "model_catalog.json"
EXAMPLE_CATALOG_PATH = REPO_ROOT / "examples" / "models" / "model_catalog.json"
USER_CONFIG_PATH = REPO_ROOT / "config" / "usr" / "config.toml"


def catalog_contexts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {model["slug"]: model["context_window"] for model in payload["models"]}


def catalog_models(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {model["slug"]: model for model in payload["models"]}


class ModelContextConfigTests(unittest.TestCase):
    def test_runtime_catalog_clamps_gpt_5_5_to_chatgpt_backed_limit(self) -> None:
        models = catalog_models(RUNTIME_CATALOG_PATH)

        self.assertEqual(models["gpt-5.5"]["context_window"], 385_000)
        self.assertEqual(models["gpt-5.5"]["max_context_window"], 385_000)
        self.assertEqual(models["gpt-5.5"]["auto_compact_token_limit"], 340_000)
        self.assertLess(models["gpt-5.5"]["auto_compact_token_limit"], models["gpt-5.5"]["context_window"])

    def test_runtime_catalog_keeps_gpt_5_4_large_window(self) -> None:
        contexts = catalog_contexts(RUNTIME_CATALOG_PATH)
        self.assertEqual(contexts["gpt-5.4"], 1_050_000)

    def test_example_catalog_does_not_downsize_gpt_5_4_models(self) -> None:
        contexts = catalog_contexts(EXAMPLE_CATALOG_PATH)
        self.assertEqual(contexts["gpt-5.4"], 1_050_000)
        self.assertEqual(contexts["gpt-5.4-mini"], 400_000)

    def test_user_config_compacts_below_large_model_context_ceiling(self) -> None:
        payload = tomllib.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
        context_window = payload["model_context_window"]
        compact_limit = payload["model_auto_compact_token_limit"]

        self.assertEqual(context_window, 1_050_000)
        self.assertEqual(compact_limit, 900_000)
        self.assertLess(compact_limit, context_window)
        self.assertLessEqual(compact_limit + 128_000, context_window)


if __name__ == "__main__":
    unittest.main()
