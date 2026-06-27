from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


AUTH_FILENAME = "auth.toml"
LOGIN_ENV_KEY = "CODEX_ACCESS_TOKEN"
LOGIN_ACCOUNT_PATTERN = re.compile(r"^[^\s\x00\r\n]+$")
LOGIN_SECRET_NAME_PREFIX = "codex_login."
LOGIN_SECRET_LABEL_PREFIX = "Codex login token"
SECRET_TOOL_TIMEOUT_SECONDS = 20


class CodexLoginAuthError(RuntimeError):
    """Raised when login auth parsing or secret-tool operations fail."""


@dataclass(frozen=True)
class CodexLoginAuthConfig:
    service: str
    accounts: dict[str, bool]

    def enabled_accounts(self) -> list[str]:
        return [name for name in sorted(self.accounts) if self.accounts[name]]


def fail(message: str) -> None:
    raise CodexLoginAuthError(message)


def _normalize_service(value: str, *, source: str) -> str:
    normalized = value.strip()
    if not normalized:
        fail(f"{source} must be a non-empty string")
    if any(ch in normalized for ch in ("\x00", "\n", "\r")):
        fail(f"{source} must not contain control characters")
    return normalized


def normalize_account_name(value: str, *, source: str) -> str:
    normalized = value.strip()
    if not LOGIN_ACCOUNT_PATTERN.fullmatch(normalized):
        fail(f"{source} contains invalid account name: {value}")
    return normalized


def normalize_access_token(value: str, *, source: str) -> str:
    normalized = value.strip()
    if not normalized:
        fail(f"{source} token cannot be empty")
    if any(ch.isspace() for ch in normalized):
        fail(f"{source} token must not contain whitespace")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        fail(f"{source} token must not contain control characters")
    return normalized


def login_lookup_name(account_name: str) -> str:
    normalized = normalize_account_name(account_name, source="login account")
    return f"{LOGIN_SECRET_NAME_PREFIX}{normalized}"


def parse_login_auth_file(path: Path) -> CodexLoginAuthConfig:
    if not path.is_file():
        fail(f"missing login auth file: {path}")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"invalid login auth file {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must be a TOML object")

    version = payload.get("version", 1)
    if version != 1:
        fail(f"{path} must declare version = 1")

    service = payload.get("service")
    if not isinstance(service, str):
        fail(f"{path} must declare service = \"...\"")
    normalized_service = _normalize_service(service, source=f"{path} service")

    raw_accounts = payload.get("codex_login", {})
    if raw_accounts in (None, {}):
        return CodexLoginAuthConfig(service=normalized_service, accounts={})
    if not isinstance(raw_accounts, dict):
        fail(f"{path} codex_login must be an object")

    parsed_accounts: dict[str, bool] = {}
    for account_name, raw_table in raw_accounts.items():
        normalized_name = normalize_account_name(str(account_name), source=f"{path} codex_login")
        if not isinstance(raw_table, dict) or not raw_table:
            fail(f"{path} codex_login.{normalized_name} must be a non-empty table")
        if set(raw_table.keys()) != {LOGIN_ENV_KEY}:
            fail(f"{path} codex_login.{normalized_name} must declare only {LOGIN_ENV_KEY}")
        enabled = raw_table.get(LOGIN_ENV_KEY)
        if not isinstance(enabled, bool):
            fail(f"{path} codex_login.{normalized_name}.{LOGIN_ENV_KEY} must be boolean")
        if normalized_name in parsed_accounts:
            fail(f"{path} reuses login account name: {normalized_name}")
        parsed_accounts[normalized_name] = enabled

    return CodexLoginAuthConfig(service=normalized_service, accounts=parsed_accounts)


def secret_tool_available() -> bool:
    return bool(shutil.which("secret-tool"))


def _secret_tool_binary() -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        fail("secret-tool is required but unavailable")
    return binary


def lookup_login_secret(config: CodexLoginAuthConfig, account_name: str) -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        return ""
    lookup_name = login_lookup_name(account_name)
    try:
        proc = subprocess.run(
            [binary, "lookup", "service", config.service, "name", lookup_name],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool lookup timed out for {lookup_name}")
    except FileNotFoundError as exc:
        fail(f"secret-tool lookup failed for {lookup_name}: {exc}")
    if proc.returncode != 0:
        return ""
    return normalize_access_token(proc.stdout, source=lookup_name)


def store_login_secret(config: CodexLoginAuthConfig, account_name: str, token: str) -> None:
    lookup_name = login_lookup_name(account_name)
    normalized_token = normalize_access_token(token, source=lookup_name)
    try:
        proc = subprocess.run(
            [
                _secret_tool_binary(),
                "store",
                f"--label={LOGIN_SECRET_LABEL_PREFIX}: {lookup_name} ({LOGIN_ENV_KEY})",
                "service",
                config.service,
                "name",
                lookup_name,
            ],
            check=False,
            input=normalized_token + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool store timed out for {lookup_name}")
    if proc.returncode != 0:
        details = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        fail(f"secret-tool store failed for {lookup_name}: {details}")
