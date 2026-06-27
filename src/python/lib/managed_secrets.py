from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECRETS_FILENAME = "secrets.toml"
KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
SECRET_NAME_PREFIX = "mcp_servers."
SECRET_TOOL_TIMEOUT_SECONDS = 20
SECRET_TOOL_LABEL_PREFIX = "Codex managed secret"


class ManagedSecretsError(RuntimeError):
    """Raised when managed secret parsing or secret-tool operations fail."""


@dataclass(frozen=True)
class ManagedSecretsConfig:
    service: str
    mcp_servers: dict[str, dict[str, bool]]

    def configured_server_env_map(self) -> dict[str, str]:
        configured: dict[str, str] = {}
        for server_name in sorted(self.mcp_servers):
            keys = sorted(self.mcp_servers[server_name])
            if len(keys) != 1:
                fail(f"managed secret config for {server_name} must declare exactly one env key")
            configured[server_name] = keys[0]
        return configured

    def enabled_server_env_map(self) -> dict[str, str]:
        enabled: dict[str, str] = {}
        for server_name, key in self.configured_server_env_map().items():
            if self.mcp_servers[server_name][key]:
                enabled[server_name] = key
        return enabled

    def enabled_runtime_env_keys(self) -> list[str]:
        return sorted(self.enabled_server_env_map().values())

    def all_env_keys(self) -> list[str]:
        return sorted(self.configured_server_env_map().values())

    def all_server_names(self) -> list[str]:
        return sorted(self.mcp_servers)


def fail(message: str) -> None:
    raise ManagedSecretsError(message)


def _normalize_secret_value(key: str, value: str, *, source: str) -> str:
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        fail(f"{source} for {key} must be single-line")
    return normalized


def _normalize_secret_service(value: str, *, source: str) -> str:
    normalized = value.strip()
    if not normalized:
        fail(f"{source} must be a non-empty string")
    if any(ch in normalized for ch in ("\x00", "\n", "\r")):
        fail(f"{source} must not contain control characters")
    return normalized


def managed_secret_lookup_name(server_name: str) -> str:
    if not SERVER_NAME_PATTERN.fullmatch(server_name):
        fail(f"invalid managed secret server name: {server_name}")
    return f"{SECRET_NAME_PREFIX}{server_name}"


def parse_managed_secrets_file(path: Path) -> ManagedSecretsConfig:
    if not path.is_file():
        fail(f"missing managed secrets file: {path}")

    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"invalid managed secrets file {path}: {exc}")

    if not isinstance(payload, dict):
        fail(f"{path} must be a TOML object")

    version = payload.get("version", 1)
    if version != 1:
        fail(f"{path} must declare version = 1")

    service = payload.get("service")
    if not isinstance(service, str):
        fail(f"{path} must declare service = \"...\"")
    normalized_service = _normalize_secret_service(service, source=f"{path} service")

    raw_mcp_servers = payload.get("mcp_servers")
    if not isinstance(raw_mcp_servers, dict) or not raw_mcp_servers:
        fail(f"{path} must declare a non-empty [mcp_servers] table")

    parsed_servers: dict[str, dict[str, bool]] = {}
    seen_keys: dict[str, str] = {}
    for server_name, raw_table in raw_mcp_servers.items():
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            fail(f"{path} contains invalid mcp server name: {server_name}")
        if not isinstance(raw_table, dict) or not raw_table:
            fail(f"{path} mcp_servers.{server_name} must be a non-empty table")
        parsed_table: dict[str, bool] = {}
        for key, value in raw_table.items():
            if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
                fail(f"{path} mcp_servers.{server_name} contains invalid env key: {key}")
            if not isinstance(value, bool):
                fail(f"{path} mcp_servers.{server_name}.{key} must be boolean")
            existing_server = seen_keys.get(key)
            if existing_server is not None:
                fail(
                    f"{path} reuses env key {key} across "
                    f"mcp_servers.{existing_server} and mcp_servers.{server_name}"
                )
            seen_keys[key] = server_name
            parsed_table[key] = value
        if len(parsed_table) != 1:
            fail(f"{path} mcp_servers.{server_name} must declare exactly one env key")
        parsed_servers[server_name] = parsed_table

    return ManagedSecretsConfig(service=normalized_service, mcp_servers=parsed_servers)


def _normalized_env_var_list(
    raw_env_vars: Any,
    *,
    path_label: str,
    server_name: str,
) -> tuple[str, ...]:
    if raw_env_vars in (None, []):
        return ()
    if not isinstance(raw_env_vars, list):
        fail(f"{path_label} mcp_servers.{server_name}.env_vars must be a list")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in raw_env_vars:
        if not isinstance(value, str):
            fail(f"{path_label} mcp_servers.{server_name}.env_vars entries must be strings")
        key = value.strip()
        if not KEY_PATTERN.fullmatch(key):
            fail(f"{path_label} mcp_servers.{server_name}.env_vars contains invalid env key: {value}")
        if key in seen:
            fail(f"{path_label} mcp_servers.{server_name}.env_vars reuses env key {key}")
        seen.add(key)
        normalized.append(key)
    return tuple(normalized)


def managed_secret_mcp_env_map(
    payload: dict[str, Any],
    *,
    path_label: str,
    enabled_only: bool = False,
) -> dict[str, str]:
    if not isinstance(payload, dict):
        fail(f"{path_label} must be a TOML object")

    raw_mcp_servers = payload.get("mcp_servers")
    if raw_mcp_servers in (None, {}):
        return {}
    if not isinstance(raw_mcp_servers, dict):
        fail(f"{path_label} mcp_servers must be an object")

    exported: dict[str, str] = {}
    seen_keys: dict[str, str] = {}
    for server_name, raw_server in raw_mcp_servers.items():
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            fail(f"{path_label} contains invalid mcp server name: {server_name}")
        if not isinstance(raw_server, dict):
            fail(f"{path_label} mcp_servers.{server_name} must be an object")

        token_key = raw_server.get("bearer_token_env_var")
        if token_key is None:
            continue
        if not isinstance(token_key, str):
            fail(f"{path_label} mcp_servers.{server_name}.bearer_token_env_var must be a string")
        normalized_key = token_key.strip()
        if not KEY_PATTERN.fullmatch(normalized_key):
            fail(f"{path_label} mcp_servers.{server_name}.bearer_token_env_var must be an env var name")

        enabled_value = raw_server.get("enabled")
        if enabled_value is not None and not isinstance(enabled_value, bool):
            fail(f"{path_label} mcp_servers.{server_name}.enabled must be boolean")

        command_value = raw_server.get("command")
        if isinstance(command_value, str) and command_value.strip():
            fail(
                f"{path_label} mcp_servers.{server_name} uses command transport and must not declare "
                "bearer_token_env_var; use env_vars instead"
            )

        url_value = raw_server.get("url")
        if not isinstance(url_value, str) or not url_value.strip():
            fail(
                f"{path_label} mcp_servers.{server_name} bearer_token_env_var requires a non-empty url transport"
            )

        existing_server = seen_keys.get(normalized_key)
        if existing_server is not None:
            fail(
                f"{path_label} reuses env key {normalized_key} across "
                f"mcp_servers.{existing_server} and mcp_servers.{server_name}"
            )
        seen_keys[normalized_key] = server_name

        if enabled_only and enabled_value is not True:
            continue

        exported[server_name] = normalized_key
    return exported


def managed_secret_supported_mcp_env_map(
    payload: dict[str, Any],
    *,
    path_label: str,
    enabled_only: bool = False,
) -> dict[str, tuple[str, ...]]:
    if not isinstance(payload, dict):
        fail(f"{path_label} must be a TOML object")

    raw_mcp_servers = payload.get("mcp_servers")
    if raw_mcp_servers in (None, {}):
        return {}
    if not isinstance(raw_mcp_servers, dict):
        fail(f"{path_label} mcp_servers must be an object")

    supported: dict[str, tuple[str, ...]] = {}
    for server_name, raw_server in raw_mcp_servers.items():
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            fail(f"{path_label} contains invalid mcp server name: {server_name}")
        if not isinstance(raw_server, dict):
            fail(f"{path_label} mcp_servers.{server_name} must be an object")

        enabled_value = raw_server.get("enabled")
        if enabled_value is not None and not isinstance(enabled_value, bool):
            fail(f"{path_label} mcp_servers.{server_name}.enabled must be boolean")
        if enabled_only and enabled_value is not True:
            continue

        command_value = raw_server.get("command")
        if isinstance(command_value, str) and command_value.strip():
            token_key = raw_server.get("bearer_token_env_var")
            if token_key is not None:
                fail(
                    f"{path_label} mcp_servers.{server_name} uses command transport and must not declare "
                    "bearer_token_env_var; use env_vars instead"
                )
            env_keys = _normalized_env_var_list(raw_server.get("env_vars"), path_label=path_label, server_name=server_name)
            if env_keys:
                supported[server_name] = env_keys
            continue

        env_keys: list[str] = []
        token_key = raw_server.get("bearer_token_env_var")
        if token_key is not None:
            if not isinstance(token_key, str):
                fail(f"{path_label} mcp_servers.{server_name}.bearer_token_env_var must be a string")
            normalized_key = token_key.strip()
            if not KEY_PATTERN.fullmatch(normalized_key):
                fail(f"{path_label} mcp_servers.{server_name}.bearer_token_env_var must be an env var name")
            url_value = raw_server.get("url")
            if not isinstance(url_value, str) or not url_value.strip():
                fail(
                    f"{path_label} mcp_servers.{server_name} bearer_token_env_var requires a non-empty url transport"
                )
            env_keys.append(normalized_key)

        if env_keys:
            supported[server_name] = tuple(env_keys)
    return supported


def secret_tool_available() -> bool:
    return bool(shutil.which("secret-tool"))


def _secret_tool_binary() -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        fail("secret-tool is required for managed secrets but is unavailable")
    return binary


def _secret_tool_attributes(service: str, server_name: str) -> list[str]:
    lookup_name = managed_secret_lookup_name(server_name)
    return [
        "service",
        _normalize_secret_service(service, source="managed secret service"),
        "name",
        lookup_name,
    ]


def lookup_managed_secret(config: ManagedSecretsConfig, server_name: str) -> str:
    binary = shutil.which("secret-tool")
    if not binary:
        return ""
    lookup_name = managed_secret_lookup_name(server_name)
    try:
        proc = subprocess.run(
            [binary, "lookup", *_secret_tool_attributes(config.service, server_name)],
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
    return _normalize_secret_value(lookup_name, proc.stdout, source="secret-tool lookup")


def store_managed_secret(
    config: ManagedSecretsConfig,
    server_name: str,
    value: str,
    *,
    env_key: str | None = None,
) -> None:
    lookup_name = managed_secret_lookup_name(server_name)
    normalized = _normalize_secret_value(lookup_name, value, source="managed secret value")
    label = f"{SECRET_TOOL_LABEL_PREFIX}: {lookup_name}"
    if env_key is not None:
        if not KEY_PATTERN.fullmatch(env_key):
            fail(f"invalid env key for managed secret store: {env_key}")
        label = f"{label} ({env_key})"
    try:
        proc = subprocess.run(
            [
                _secret_tool_binary(),
                "store",
                f"--label={label}",
                *_secret_tool_attributes(config.service, server_name),
            ],
            check=False,
            input=normalized + "\n",
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


def clear_managed_secret(config: ManagedSecretsConfig, server_name: str) -> None:
    lookup_name = managed_secret_lookup_name(server_name)
    try:
        proc = subprocess.run(
            [_secret_tool_binary(), "clear", *_secret_tool_attributes(config.service, server_name)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=SECRET_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fail(f"secret-tool clear timed out for {lookup_name}")
    if proc.returncode == 0:
        return

    if proc.returncode == 1:
        existing_value = lookup_managed_secret(config, server_name).strip()
        if not existing_value:
            return

    details = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
    fail(f"secret-tool clear failed for {lookup_name}: {details}")
