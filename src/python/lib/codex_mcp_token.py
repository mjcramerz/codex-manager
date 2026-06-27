#!/usr/bin/env python3
# managed by codex installer
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
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

KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DEFAULT_CODEX_ROOT = "/data/codex"
SECRETS_FILENAME = "secrets.toml"
SECRET_NAME_PREFIX = "mcp_servers."
SECRET_TOOL_LABEL_PREFIX = "Codex managed secret"
SECRET_TOOL_TIMEOUT_SECONDS = 20


class CodexMcpTokenError(RuntimeError):
    """Raised when managed MCP token rotation cannot proceed safely."""


def fail(message: str) -> None:
    raise CodexMcpTokenError(message)


def _normalize_token(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        fail("token must be non-empty")
    if any(ch.isspace() for ch in normalized):
        fail("token must not contain whitespace")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        fail("token must not contain control characters")
    return normalized


def _installed_secrets_path() -> Path:
    root_dir = os.environ.get("CODEX_ROOT_DIR", "").strip() or DEFAULT_CODEX_ROOT
    if any(ch in root_dir for ch in ("\x00", "\n", "\r")):
        fail("CODEX_ROOT_DIR contains unsupported characters")
    path = Path(root_dir)
    if not path.is_absolute():
        fail("CODEX_ROOT_DIR must be absolute")
    return path / "lookup" / SECRETS_FILENAME


def _load_enabled_secret_map(path: Path) -> tuple[str, dict[str, tuple[str, bool]]]:
    if not path.is_file():
        fail(f"missing managed secrets file: {path}")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"invalid managed secrets file {path}: {exc}")

    if payload.get("version", 1) != 1:
        fail(f"{path} must declare version = 1")
    service = payload.get("service")
    if not isinstance(service, str) or not service.strip():
        fail(f"{path} must declare service = \"...\"")

    raw_servers = payload.get("mcp_servers")
    if not isinstance(raw_servers, dict) or not raw_servers:
        fail(f"{path} must declare a non-empty [mcp_servers] table")

    env_map: dict[str, tuple[str, bool]] = {}
    for server_name, raw_table in raw_servers.items():
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            fail(f"{path} contains invalid mcp server name: {server_name}")
        if not isinstance(raw_table, dict) or not raw_table:
            fail(f"{path} mcp_servers.{server_name} must be a non-empty table")
        for env_key, enabled in raw_table.items():
            if not isinstance(env_key, str) or not KEY_PATTERN.fullmatch(env_key):
                fail(f"{path} mcp_servers.{server_name} contains invalid env key: {env_key}")
            if not isinstance(enabled, bool):
                fail(f"{path} mcp_servers.{server_name}.{env_key} must be boolean")
            if env_key in env_map:
                fail(f"{path} reuses env key {env_key}")
            env_map[env_key] = (server_name, enabled)
    return service.strip(), env_map


def _lookup_name(server_name: str) -> str:
    if not SERVER_NAME_PATTERN.fullmatch(server_name):
        fail(f"invalid managed secret server name: {server_name}")
    return f"{SECRET_NAME_PREFIX}{server_name}"


def _secret_tool_binary() -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        fail("secret-tool is required but unavailable")
    return binary


def _secret_exists(binary: str, service: str, server_name: str) -> bool:
    try:
        proc = subprocess.run(
            [binary, "lookup", "service", service, "name", _lookup_name(server_name)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool lookup timed out for {_lookup_name(server_name)}")
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _store_secret(binary: str, service: str, server_name: str, env_key: str, token: str) -> None:
    lookup_name = _lookup_name(server_name)
    try:
        proc = subprocess.run(
            [
                binary,
                "store",
                f"--label={SECRET_TOOL_LABEL_PREFIX}: {lookup_name} ({env_key})",
                "service",
                service,
                "name",
                lookup_name,
            ],
            check=False,
            input=token + "\n",
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(args) != 2:
            fail("usage: codex-mcp-token <SECRET_NAME> <TOKEN>")

        secret_name, raw_token = args
        if not KEY_PATTERN.fullmatch(secret_name):
            fail(f"invalid secret name: {secret_name}")
        token = _normalize_token(raw_token)

        secrets_path = _installed_secrets_path()
        service, env_map = _load_enabled_secret_map(secrets_path)
        if secret_name not in env_map:
            fail(f"managed MCP secret is not configured: {secret_name}")

        server_name, enabled = env_map[secret_name]
        if not enabled:
            fail("Please enable secret first and try again later")

        binary = _secret_tool_binary()
        existed = _secret_exists(binary, service, server_name)
        _store_secret(binary, service, server_name, secret_name, token)
        print(f"{'Updated' if existed else 'Stored'} managed MCP token for {secret_name}")
        return 0
    except CodexMcpTokenError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
