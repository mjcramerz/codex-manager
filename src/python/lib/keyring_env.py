#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

from lib.managed_secrets import ManagedSecretsError
from lib.managed_secrets import SECRETS_FILENAME
from lib.managed_secrets import KEY_PATTERN
from lib.managed_secrets import SERVER_NAME_PATTERN
from lib.managed_secrets import lookup_managed_secret
from lib.managed_secrets import parse_managed_secrets_file
from lib.runtime import RuntimeRenderError
from lib.runtime import derive_runtime_globals_from_env


class KeyringEnvError(RuntimeError):
    """Raised when secret-tool-backed env export cannot proceed safely."""


def fail(message: str) -> None:
    raise KeyringEnvError(message)


def strip_inline_comment(line: str) -> str:
    out: list[str] = []
    in_single = False
    in_double = False
    prev = ""
    for ch in line:
        if ch == "'" and not in_double and prev != "\\":
            in_single = not in_single
        elif ch == '"' and not in_single and prev != "\\":
            in_double = not in_double
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
        prev = ch
    return "".join(out).strip()


def parse_repo_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        fail(f"missing env file: {path}")

    parsed: dict[str, str] = {}
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            fail(f"invalid env assignment at {path}:{idx}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = strip_inline_comment(value).strip()
        if not KEY_PATTERN.fullmatch(key):
            fail(f"invalid env key at {path}:{idx}: {key}")
        if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
            value = value[1:-1]
        parsed[key] = value
    return parsed


def secrets_config_from_env_file(path: Path) -> Path:
    env = parse_repo_env_file(path)
    root_dir = env.get("CODEX_ROOT_DIR", "").strip()
    if not root_dir:
        fail(f"missing CODEX_ROOT_DIR in {path}")
    if "\n" in root_dir or "\r" in root_dir:
        fail(f"invalid CODEX_ROOT_DIR in {path}")
    return Path(root_dir) / "lookup" / SECRETS_FILENAME


def host_config_from_env_file(path: Path) -> Path:
    env = parse_repo_env_file(path)
    try:
        runtime_env = derive_runtime_globals_from_env(env)
    except RuntimeRenderError as exc:
        fail(str(exc))
    home_dir = runtime_env.get("CODEX_HOME", "").strip()
    if not home_dir:
        fail(f"missing CODEX_USER_DIR in {path}")
    host_config_path = Path(home_dir) / "config.toml"
    if not host_config_path.is_absolute():
        fail(f"derived host config path is not absolute: {host_config_path}")
    return host_config_path


def resolve_secrets_config(
    *,
    secrets_file: str | None,
    env_file: str | None,
) -> Path:
    resolved_secrets_file: Path | None = Path(secrets_file) if secrets_file else None
    if env_file:
        env_secrets_file = secrets_config_from_env_file(Path(env_file))
        if resolved_secrets_file is None:
            resolved_secrets_file = env_secrets_file
    if resolved_secrets_file is None:
        fail("managed secrets file path is required")
    return resolved_secrets_file


def resolve_host_config(
    *,
    host_config: str | None,
    env_file: str | None,
) -> Path:
    resolved_host_config: Path | None = Path(host_config) if host_config else None
    if env_file:
        env_host_config = host_config_from_env_file(Path(env_file))
        if resolved_host_config is None:
            resolved_host_config = env_host_config
    if resolved_host_config is None:
        fail("host config path is required")
    if not resolved_host_config.is_absolute():
        fail("host config path must be absolute")
    return resolved_host_config


def _normalize_secret_value(key: str, value: str, *, source: str) -> str:
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        fail(f"{source} for {key} must be single-line")
    return normalized


def _lookup_env_secret(key: str) -> str:
    value = os.environ.get(key, "")
    if not value:
        return ""
    return _normalize_secret_value(key, value, source="environment value")


def _runtime_mcp_bearer_env_map(path: Path) -> dict[str, str]:
    if not path.is_file():
        fail(f"missing host config: {path}")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"invalid host config {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must be a TOML object")

    raw_mcp_servers = payload.get("mcp_servers")
    if raw_mcp_servers in (None, {}):
        return {}
    if not isinstance(raw_mcp_servers, dict):
        fail(f"{path} mcp_servers must be an object")

    exported: dict[str, str] = {}
    for server_name, raw_server in raw_mcp_servers.items():
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            fail(f"{path} contains invalid mcp server name: {server_name}")
        if not isinstance(raw_server, dict):
            fail(f"{path} mcp_servers.{server_name} must be an object")
        enabled_value = raw_server.get("enabled")
        if enabled_value is not None and not isinstance(enabled_value, bool):
            fail(f"{path} mcp_servers.{server_name}.enabled must be boolean")
        if enabled_value is not True:
            continue
        token_key = raw_server.get("bearer_token_env_var")
        if token_key is None:
            continue
        if not isinstance(token_key, str):
            fail(f"{path} mcp_servers.{server_name}.bearer_token_env_var must be a string")
        normalized_key = token_key.strip()
        if not KEY_PATTERN.fullmatch(normalized_key):
            fail(f"{path} mcp_servers.{server_name}.bearer_token_env_var must be an env var name")
        exported[server_name] = normalized_key
    return exported


def collect_lookup_environment(host_config_path: Path, secrets_path: Path) -> dict[str, str]:
    try:
        config = parse_managed_secrets_file(secrets_path)
    except ManagedSecretsError as exc:
        fail(str(exc))

    exported: dict[str, str] = {}
    for server_name, key in _runtime_mcp_bearer_env_map(host_config_path).items():
        value = _lookup_env_secret(key)
        if not value:
            try:
                value = lookup_managed_secret(config, server_name).strip()
            except ManagedSecretsError as exc:
                fail(str(exc))
        if value:
            exported[key] = value
    return exported


def lookup_exec(binary: str, args: list[str], secrets_file: Path, host_config_path: Path) -> int:
    env = dict(os.environ)
    env.update(collect_lookup_environment(host_config_path, secrets_file))
    filtered_args = list(args)
    if filtered_args[:1] == ["--"]:
        filtered_args = filtered_args[1:]
    filtered_args = [arg for arg in filtered_args if arg != "--k"]
    os.execvpe(binary, [binary, *filtered_args], env)
    return 0


def lookup_shell(secrets_file: Path, host_config_path: Path, shell: str | None) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        fail("interactive managed secret export requires a terminal")
    env = dict(os.environ)
    env.update(collect_lookup_environment(host_config_path, secrets_file))
    shell_path = (shell or os.environ.get("SHELL") or "/bin/bash").strip()
    if not shell_path.startswith("/"):
        shell_path = "/bin/bash"
    os.execvpe(shell_path, [shell_path, "-i"], env)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="secret-tool-backed Codex environment launcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    shell_parser = subparsers.add_parser("shell")
    shell_parser.add_argument(
        "--env-file",
        help="Repo .env file used to locate the installed managed secrets config",
    )
    shell_parser.add_argument(
        "--secrets-file",
        help=f"Absolute path to {SECRETS_FILENAME}",
    )
    shell_parser.add_argument(
        "--host-config",
        help="Absolute path to the installed CODEX_HOME/config.toml",
    )
    shell_parser.add_argument("--shell", help="Interactive shell path to exec")

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("--binary", required=True, help="Absolute binary path to exec")
    exec_parser.add_argument(
        "--secrets-file",
        required=True,
        help=f"Absolute path to {SECRETS_FILENAME}",
    )
    exec_parser.add_argument(
        "--host-config",
        required=True,
        help="Absolute path to the installed CODEX_HOME/config.toml",
    )
    exec_parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "shell":
            secrets_file = resolve_secrets_config(
                secrets_file=args.secrets_file,
                env_file=args.env_file,
            )
            host_config = resolve_host_config(
                host_config=args.host_config,
                env_file=args.env_file,
            )
            return lookup_shell(secrets_file, host_config, args.shell)
        if args.command == "exec":
            if not args.binary.startswith("/"):
                fail("--binary must be an absolute path")
            return lookup_exec(
                args.binary,
                args.args,
                Path(args.secrets_file),
                resolve_host_config(host_config=args.host_config, env_file=None),
            )
        fail(f"unsupported command: {args.command}")
    except KeyringEnvError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
