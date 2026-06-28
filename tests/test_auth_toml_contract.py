import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTH_TOML = REPO_ROOT / "auth.toml"
REQUIRED_EMAILS = [
    "copilot@jcramer.sbs",
    "tolvis.nicko@jcramer.sbs",
    "sven.tumba@jcramer.sbs",
    "johlsan@jcramer.sbs",
    "nerikes.allhanda@jcramer.sbs",
    "thor.lundh@jcramer.xyz",
    "nikke@jcramer.sbs",
    "oskar@jcramer.sbs",
    "goran.silkesqvist@jcramer.sbs",
    "livarnix@jcramer.sbs",
    "narnia85@jcramer.xyz",
    "oai@jcramer.xyz",
    "ozzi@jcramer.sbs",
    "ralf.edstrom@jcramer.sbs",
    "tobjorn.ikke@jcramer.sbs",
    "trixien@jcramer.sbs",
]


class AuthTomlContractTests(unittest.TestCase):
    def test_auth_toml_has_no_comments(self) -> None:
        text = AUTH_TOML.read_text(encoding="utf-8")
        self.assertNotIn("#", text)

    def test_required_accounts_exist_and_are_enabled(self) -> None:
        payload = tomllib.loads(AUTH_TOML.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("version"), 1)
        self.assertEqual(payload.get("service"), "codex-login")
        accounts = payload.get("codex_login", {})
        self.assertIsInstance(accounts, dict)

        self.assertEqual(sorted(accounts), sorted(REQUIRED_EMAILS))
        for email in REQUIRED_EMAILS:
            with self.subTest(email=email):
                self.assertEqual(accounts[email], {"CODEX_ACCESS_TOKEN": True})
