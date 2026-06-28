#!/usr/bin/env python3
# managed by codex installer
from __future__ import annotations

import getpass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Sequence

import tomllib

PYCACHE_PREFIX = "/tmp/codex-pycache"
_pycache_target = Path(os.environ.get("PYTHONPYCACHEPREFIX", "").strip() or PYCACHE_PREFIX)
if not _pycache_target.is_absolute():
    _pycache_target = Path(PYCACHE_PREFIX)
try:
    _pycache_target.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
else:
    os.environ["PYTHONPYCACHEPREFIX"] = str(_pycache_target)
    sys.pycache_prefix = str(_pycache_target)

DEFAULT_CODEX_ROOT = "/data/codex"
AUTH_FILENAME = "auth.toml"
LOGIN_ENV_KEY = "CODEX_ACCESS_TOKEN"
LOGIN_ACCOUNT_PATTERN = re.compile(r"^[^\s\x00\r\n]+$")
LOGIN_SECRET_NAME_PREFIX = "codex_login."
LOGIN_SECRET_LABEL_PREFIX = "Codex login token"
SECRET_TOOL_TIMEOUT_SECONDS = 20
SECRET_TOOL_RETRY_ERROR_MARKERS = (
    "the name is not activatable",
    "cannot autolaunch dbus",
    "could not connect",
    "no such interface",
    "operation not permitted",
)


class CodexLoginAuthConfig:
    def __init__(self, service: str, accounts: dict[str, bool]) -> None:
        self.service = service
        self.accounts = accounts

    def enabled_accounts(self) -> list[str]:
        return [name for name in sorted(self.accounts) if self.accounts[name]]


class CodexLoginError(RuntimeError):
    """Raised when the managed codex-login wrapper cannot complete safely."""


def fail(message: str) -> None:
    raise CodexLoginError(message)


def _resolve_codex_wrapper(script_path: Path) -> Path:
    codex_wrapper = script_path.resolve(strict=False).with_name("codex")
    if not codex_wrapper.is_file():
        fail(f"missing codex wrapper: {codex_wrapper}")
    if not os.access(codex_wrapper, os.X_OK):
        fail(f"codex wrapper is not executable: {codex_wrapper}")
    return codex_wrapper


def _normalize_access_token(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        fail(f"{LOGIN_ENV_KEY} cannot be empty")
    if any(ch.isspace() for ch in normalized):
        fail(f"{LOGIN_ENV_KEY} must not contain whitespace")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        fail(f"{LOGIN_ENV_KEY} must not contain control characters")
    return normalized


def _normalize_account_name(value: str) -> str:
    normalized = value.strip()
    if not LOGIN_ACCOUNT_PATTERN.fullmatch(normalized):
        fail(f"invalid login account name: {value}")
    return normalized


def _login_lookup_name(account_name: str) -> str:
    return f"{LOGIN_SECRET_NAME_PREFIX}{_normalize_account_name(account_name)}"


def _parse_login_auth_file(path: Path) -> CodexLoginAuthConfig:
    if not path.is_file():
        fail(f"missing login auth file: {path}")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"invalid login auth file {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must be a TOML object")

    if payload.get("version", 1) != 1:
        fail(f"{path} must declare version = 1")

    service = payload.get("service")
    if not isinstance(service, str) or not service.strip():
        fail(f"{path} must declare service = \"...\"")

    raw_accounts = payload.get("codex_login", {})
    if raw_accounts in (None, {}):
        return CodexLoginAuthConfig(service=service.strip(), accounts={})
    if not isinstance(raw_accounts, dict):
        fail(f"{path} codex_login must be an object")

    parsed_accounts: dict[str, bool] = {}
    for account_name, raw_table in raw_accounts.items():
        normalized_name = _normalize_account_name(str(account_name))
        if not isinstance(raw_table, dict) or not raw_table:
            fail(f"{path} codex_login.{normalized_name} must be a non-empty table")
        if set(raw_table.keys()) != {LOGIN_ENV_KEY}:
            fail(f"{path} codex_login.{normalized_name} must declare only {LOGIN_ENV_KEY}")
        enabled = raw_table.get(LOGIN_ENV_KEY)
        if not isinstance(enabled, bool):
            fail(f"{path} codex_login.{normalized_name}.{LOGIN_ENV_KEY} must be boolean")
        parsed_accounts[normalized_name] = enabled
    return CodexLoginAuthConfig(service=service.strip(), accounts=parsed_accounts)


def _secret_tool_available() -> bool:
    return bool(shutil.which("secret-tool"))


def _secret_tool_binary() -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        fail("secret-tool is required but unavailable")
    return binary


def _should_retry_secret_tool(details: str) -> bool:
    normalized = details.strip().lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in SECRET_TOOL_RETRY_ERROR_MARKERS)


def _run_secret_tool(
    args: list[str],
    *,
    timeout_label: str,
    failure_label: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    binary = _secret_tool_binary()
    command = [binary, *args]
    try:
        proc = subprocess.run(
            command,
            check=False,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool {timeout_label} timed out for {failure_label}")
    except FileNotFoundError as exc:
        fail(f"secret-tool {timeout_label} failed for {failure_label}: {exc}")

    details = proc.stderr.strip() or proc.stdout.strip()
    if proc.returncode == 0 or not _should_retry_secret_tool(details):
        return proc

    dbus_run_session = shutil.which("dbus-run-session")
    gnome_keyring_daemon = shutil.which("gnome-keyring-daemon")
    if not dbus_run_session or not gnome_keyring_daemon:
        return proc

    bootstrap_script = (
        "set -eu\n"
        "eval \"$(gnome-keyring-daemon --start --components=secrets 2>/dev/null)\"\n"
        "exec \"$@\"\n"
    )
    retry_command = [
        dbus_run_session,
        "--",
        "sh",
        "-lc",
        bootstrap_script,
        "sh",
        *command,
    ]
    try:
        return subprocess.run(
            retry_command,
            check=False,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool {timeout_label} timed out for {failure_label}")
    except FileNotFoundError as exc:
        fail(f"secret-tool {timeout_label} failed for {failure_label}: {exc}")


def _lookup_login_secret(config: CodexLoginAuthConfig, account_name: str) -> str:
    lookup_name = _login_lookup_name(account_name)
    proc = _run_secret_tool(
        ["lookup", "service", config.service, "name", lookup_name],
        timeout_label="lookup",
        failure_label=lookup_name,
    )
    if proc.returncode != 0:
        return ""
    return _normalize_access_token(proc.stdout)


def _store_login_secret(config: CodexLoginAuthConfig, account_name: str, token: str) -> None:
    lookup_name = _login_lookup_name(account_name)
    normalized = _normalize_access_token(token)
    proc = _run_secret_tool(
        [
            "store",
            f"--label={LOGIN_SECRET_LABEL_PREFIX}: {lookup_name} ({LOGIN_ENV_KEY})",
            "service",
            config.service,
            "name",
            lookup_name,
        ],
        timeout_label="store",
        failure_label=lookup_name,
        input_text=normalized + "\n",
    )
    if proc.returncode != 0:
        details = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        if _should_retry_secret_tool(details):
            details += "; ensure a Secret Service is running or install gnome-keyring-daemon for retry bootstrap"
        fail(f"secret-tool store failed for {lookup_name}: {details}")


def _clear_login_secret(config: CodexLoginAuthConfig, account_name: str) -> None:
    lookup_name = _login_lookup_name(account_name)
    proc = _run_secret_tool(
        ["clear", "service", config.service, "name", lookup_name],
        timeout_label="clear",
        failure_label=lookup_name,
    )
    if proc.returncode == 0:
        return
    if proc.returncode == 1 and not lookup_login_secret(config, account_name):
        return

    details = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
    fail(f"secret-tool clear failed for {lookup_name}: {details}")


parse_login_auth_file = _parse_login_auth_file
secret_tool_available = _secret_tool_available
lookup_login_secret = _lookup_login_secret
store_login_secret = _store_login_secret
clear_login_secret = _clear_login_secret


def _installed_auth_path() -> Path:
    root_dir = os.environ.get("CODEX_ROOT_DIR", "").strip() or DEFAULT_CODEX_ROOT
    if any(ch in root_dir for ch in ("\x00", "\n", "\r")):
        fail("CODEX_ROOT_DIR contains unsupported characters")
    path = Path(root_dir)
    if not path.is_absolute():
        fail("CODEX_ROOT_DIR must be absolute")
    return path / "lookup" / AUTH_FILENAME


def _load_auth_config() -> CodexLoginAuthConfig:
    return parse_login_auth_file(_installed_auth_path())


def _load_access_token() -> str:
    env_value = os.environ.get(LOGIN_ENV_KEY, "")
    if env_value:
        return _normalize_access_token(env_value)

    if not sys.stdin.isatty() or not sys.stderr.isatty():
        fail(f"interactive terminal required unless {LOGIN_ENV_KEY} is already set")

    return _normalize_access_token(getpass.getpass("Codex Access Token: "))


def _stored_login_choices(config: CodexLoginAuthConfig) -> list[tuple[str, str]]:
    choices: list[tuple[str, str]] = []
    for account_name in config.enabled_accounts():
        token = lookup_login_secret(config, account_name)
        if token:
            choices.append((account_name, token))
    return choices


def _list_stored_logins(config: CodexLoginAuthConfig) -> int:
    choices = _stored_login_choices(config)
    for idx, (account_name, _token) in enumerate(choices, start=1):
        print(f"{idx}) {account_name}")
    return len(choices)


def _select_login_choice(choices: Sequence[tuple[str, str]]) -> tuple[str, str]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        fail("interactive terminal required to select a stored Codex login")
    if not choices:
        fail("no stored Codex login choices available")

    while True:
        for idx, (account_name, _token) in enumerate(choices, start=1):
            print(f"{idx}) {account_name}")
        selection = input("Select login: ").strip()
        if not selection.isdigit():
            print("[warn] enter the number of the login to use")
            continue
        selected_index = int(selection)
        if selected_index < 1 or selected_index > len(choices):
            print("[warn] selection is out of range")
            continue
        return choices[selected_index - 1]


def _should_store_additional_login_token(account_name: str, has_existing_token: bool) -> bool:
    if not has_existing_token:
        return True

    while True:
        response = input(
            f"An Access Token is already stored for {account_name}. "
            "Add another token for this account? [y/N]: "
        ).strip().lower()
        if response in ("", "n", "no", "s", "skip"):
            return False
        if response in ("y", "yes"):
            return True
        print("[warn] enter 'y' to add another token or press Enter to skip")


def _init_stored_logins(config: CodexLoginAuthConfig) -> int:
    enabled_accounts = config.enabled_accounts()
    if not enabled_accounts:
        fail("no enabled codex_login accounts found in auth.toml")
    if not secret_tool_available():
        fail("secret-tool is required but unavailable")
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        fail("interactive terminal required for codex-login --init")

    stored = 0
    for account_name in enabled_accounts:
        if not _should_store_additional_login_token(
            account_name,
            has_existing_token=bool(lookup_login_secret(config, account_name)),
        ):
            continue
        while True:
            token = getpass.getpass(f"Enter the Access Token for {account_name}: ").strip()
            if token.lower() == "s":
                break
            if not token:
                print("[warn] token cannot be empty; enter a value or 's' to skip")
                continue
            store_login_secret(config, account_name, token)
            stored += 1
            break
    return stored


def _reset_stored_logins(config: CodexLoginAuthConfig, reset_target: str) -> int:
    if not secret_tool_available():
        fail("secret-tool is required but unavailable")

    normalized_target = reset_target.strip().lower()
    if normalized_target == "all":
        account_names = sorted(config.accounts)
    else:
        account_names = [_normalize_account_name(reset_target)]

    cleared = 0
    for account_name in account_names:
        clear_login_secret(config, account_name)
        cleared += 1
    return cleared


def _login_with_token(codex_wrapper: Path, token: str) -> int:
    child_env = dict(os.environ)
    child_env.pop(LOGIN_ENV_KEY, None)

    os.umask(0o077)
    subprocess.run(
        [str(codex_wrapper), "logout"],
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=child_env,
    )
    proc = subprocess.run(
        [str(codex_wrapper), "login", "--with-access-token"],
        check=False,
        input=token,
        text=True,
        env=child_env,
    )
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args == ["--init"]:
            config = _load_auth_config()
            stored = _init_stored_logins(config)
            print(f"Stored {stored} Codex login token(s)")
            return 0
        if args == ["--list"]:
            config = _load_auth_config()
            _list_stored_logins(config)
            return 0
        if len(args) == 2 and args[0] == "--reset":
            config = _load_auth_config()
            cleared = _reset_stored_logins(config, args[1])
            print(f"Cleared {cleared} Codex login token entr{'y' if cleared == 1 else 'ies'}")
            return 0
        if args:
            fail("usage: codex-login [--init | --list | --reset all | --reset <account>]")

        codex_wrapper = _resolve_codex_wrapper(Path(__file__))
        config = _load_auth_config()
        choices = _stored_login_choices(config)
        if choices:
            _account_name, token = _select_login_choice(choices)
        else:
            token = _load_access_token()
        return _login_with_token(codex_wrapper, token)
    except CodexLoginError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
