#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
LOOKUP_SECRET_SERVICE_FILENAME = "lookup-secret-service.env"
BWS_PROJECT_ID_KEY = "BWS_PROJECT_ID"
BWS_ACCESS_TOKEN_KEY = "BWS_ACCESS_TOKEN"
BWS_ENV_TIMEOUT_SECONDS = 90
KWALLET_QUERY_TIMEOUT_SECONDS = 15
BWS_KWALLET_NAME = "bws-cli"
BWS_KWALLET_FOLDER = "Passwords"


class KeyringEnvError(RuntimeError):
    """Raised when KWallet6-backed env export cannot proceed safely."""


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


def lookup_config_from_env_file(path: Path) -> Path:
    env = parse_repo_env_file(path)
    root_dir = env.get("CODEX_ROOT_DIR", "").strip()
    if not root_dir:
        fail(f"missing CODEX_ROOT_DIR in {path}")
    if "\n" in root_dir or "\r" in root_dir:
        fail(f"invalid CODEX_ROOT_DIR in {path}")
    return Path(root_dir) / "lookup" / LOOKUP_SECRET_SERVICE_FILENAME


def resolve_lookup_config(
    *,
    lookup_file: str | None,
    env_file: str | None,
) -> Path:
    resolved_lookup_file: Path | None = Path(lookup_file) if lookup_file else None
    if env_file:
        env_lookup_file = lookup_config_from_env_file(Path(env_file))
        if resolved_lookup_file is None:
            resolved_lookup_file = env_lookup_file
    if resolved_lookup_file is None:
        fail("lookup secret service file path is required")
    return resolved_lookup_file


def parse_lookup_file(path: Path) -> list[str]:
    if not path.is_file():
        fail(f"lookup secret service file is missing: {path}")

    keys: list[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not KEY_PATTERN.fullmatch(stripped):
            fail(f"invalid key name at {path}:{idx}: {stripped}")
        if stripped in seen:
            continue
        seen.add(stripped)
        keys.append(stripped)
    if not keys:
        fail(f"lookup secret service file is empty: {path}; add one env var name per line before continuing")
    return keys


def _normalize_secret_value(key: str, value: str, *, source: str) -> str:
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        fail(f"{source} for {key} must be single-line")
    return normalized


def lookup_secret(key: str) -> str:
    kwallet_query = shutil.which("kwallet-query")
    if not kwallet_query:
        return ""
    try:
        proc = subprocess.run(
            [
                kwallet_query,
                "--read-password",
                key,
                "--folder",
                BWS_KWALLET_FOLDER,
                BWS_KWALLET_NAME,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=KWALLET_QUERY_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        fail(f"required command is unavailable: {exc}")
    except subprocess.TimeoutExpired:
        fail("kwallet-query timed out while retrieving BWS bootstrap credentials")
    if proc.returncode != 0:
        return ""
    return _normalize_secret_value(key, proc.stdout, source="kwallet entry")


def _lookup_env_secret(key: str) -> str:
    value = os.environ.get(key, "")
    if not value:
        return ""
    return _normalize_secret_value(key, value, source="environment value")


def lookup_bws_credentials() -> tuple[str, str]:
    project_id = lookup_secret(BWS_PROJECT_ID_KEY).strip() or _lookup_env_secret(BWS_PROJECT_ID_KEY)
    access_token = lookup_secret(BWS_ACCESS_TOKEN_KEY).strip() or _lookup_env_secret(BWS_ACCESS_TOKEN_KEY)
    if not project_id:
        fail(f"missing {BWS_PROJECT_ID_KEY} in kwallet6 wallet {BWS_KWALLET_NAME} and environment")
    if not access_token:
        fail(f"missing {BWS_ACCESS_TOKEN_KEY} in kwallet6 wallet {BWS_KWALLET_NAME} and environment")
    return project_id, access_token


def _parse_env_output(raw_output: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in raw_output.splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        key = key.strip()
        if not KEY_PATTERN.fullmatch(key):
            continue
        if "\n" in value or "\r" in value:
            fail(f"resolved secret for {key} must be single-line")
        parsed[key] = value
    return parsed


def _bws_env(secret_names: list[str], *, project_id: str, access_token: str) -> dict[str, str]:
    bws_binary = shutil.which("bws")
    if not bws_binary:
        fail("required command is unavailable: bws")
    try:
        proc = subprocess.run(
            [
                bws_binary,
                "--access-token",
                access_token,
                "run",
                "--no-inherit-env",
                "--project-id",
                project_id,
                "--",
                "/usr/bin/env",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=BWS_ENV_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        fail(f"required command is unavailable: {exc}")
    except subprocess.TimeoutExpired:
        fail("bws run timed out while retrieving lookup secrets")
    if proc.returncode != 0:
        fail("bws run failed while retrieving lookup secrets")

    exported: dict[str, str] = {}
    available = _parse_env_output(proc.stdout)
    for name in secret_names:
        value = available.get(name, "").strip()
        if not value:
            continue
        if "\n" in value or "\r" in value:
            fail(f"resolved secret for {name} must be single-line")
        exported[name] = value
    return exported


def collect_lookup_environment(path: Path) -> dict[str, str]:
    lookup_keys = parse_lookup_file(path)
    project_id, access_token = lookup_bws_credentials()
    return _bws_env(lookup_keys, project_id=project_id, access_token=access_token)


def lookup_exec(binary: str, args: list[str], lookup_file: Path) -> int:
    env = dict(os.environ)
    env.update(collect_lookup_environment(lookup_file))
    filtered_args = [arg for arg in args if arg != "--k"]
    os.execvpe(binary, [binary, *filtered_args], env)
    return 0


def lookup_shell(lookup_file: Path, shell: str | None) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        fail("interactive lookup export requires a terminal")
    env = dict(os.environ)
    env.update(collect_lookup_environment(lookup_file))
    shell_path = (shell or os.environ.get("SHELL") or "/bin/bash").strip()
    if not shell_path.startswith("/"):
        shell_path = "/bin/bash"
    os.execvpe(shell_path, [shell_path, "-i"], env)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KWallet6-backed Codex environment launcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    shell_parser = subparsers.add_parser("shell")
    shell_parser.add_argument(
        "--env-file",
        help="Path to repo .env for CODEX_ROOT_DIR lookup",
    )
    shell_parser.add_argument("--lookup-file", help="Absolute path to lookup-secret-service.env")
    shell_parser.add_argument("--shell", help="Interactive shell to launch")

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("--lookup-file", required=True, help="Absolute path to lookup-secret-service.env")
    exec_parser.add_argument("--binary", required=True, help="Executable to launch after env injection")
    exec_parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    if args.command == "shell":
        lookup_file = resolve_lookup_config(
            lookup_file=args.lookup_file,
            env_file=args.env_file,
        )
        return lookup_shell(lookup_file, args.shell)
    if args.command == "exec":
        lookup_file = resolve_lookup_config(
            lookup_file=args.lookup_file,
            env_file=None,
        )
        remainder = list(args.args)
        if remainder and remainder[0] == "--":
            remainder = remainder[1:]
        return lookup_exec(args.binary, remainder, lookup_file)
    fail(f"unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except KeyringEnvError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
