#!/usr/bin/env python3
"""Codex schema helper logic used by installed wrappers.

This tool is installed into CODEX_SHARE_DIR/helpers and invoked via:
- codex-schema-newest
- codex-schema-diff
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any, Callable

OPENAI_CODEX_GIT_URL = "https://github.com/openai/codex.git"
OPENAI_CODEX_SCHEMA_BLOB_URL = (
    "https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json"
)
OPENAI_CODEX_SCHEMA_PATH = "codex-rs/core/config.schema.json"

MAX_SCHEMA_BYTES = 8 * 1024 * 1024
GIT_ATTEMPTS = 3
GIT_CLONE_TIMEOUT_SECONDS = 120
GIT_SPARSE_TIMEOUT_SECONDS = 60
BARE_TOML_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
PLACEHOLDER_SEGMENT_PATTERN = re.compile(r"^<[^>\n\r\x00]+>$")
DYNAMIC_PATH_PLACEHOLDERS: dict[tuple[str, ...], str] = {
    ("agents",): "<role>",
    ("mcp_servers",): "<server>",
    ("model_providers",): "<provider>",
    ("plugins",): "<plugin@marketplace>",
    ("profiles",): "<profile>",
    ("projects",): "<project>",
}


class SchemaToolError(RuntimeError):
    """Domain error for schema helper flows."""


def fail(message: str) -> None:
    raise SchemaToolError(message)


def ensure_safe_absolute_path(label: str, value: str) -> Path:
    if not value:
        fail(f"missing required path value for {label}")
    if "\n" in value or "\r" in value or "\x00" in value:
        fail(f"path {label} contains control characters")
    path = Path(value)
    if not path.is_absolute():
        fail(f"path {label} must be absolute: {value}")
    return path.resolve(strict=False)


def ensure_git_available() -> None:
    if shutil.which("git") is None:
        fail("git is required for schema download but is not installed")


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="codex-schema-",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.chmod(0o644)
    temp_path.replace(path)


def atomic_write_text(path: Path, payload: str) -> None:
    atomic_write_bytes(path, payload.encode("utf-8"))


def ensure_schema_json_bytes(payload: bytes, source: str) -> dict[str, Any]:
    if len(payload) > MAX_SCHEMA_BYTES:
        fail(f"schema payload too large from {source}: {len(payload)} bytes")
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON schema payload from {source}: {exc}")
    if not isinstance(parsed, dict):
        fail(f"schema payload must be a JSON object from {source}")
    return parsed


def load_schema(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"schema file not found: {path}")
    payload = path.read_bytes()
    return ensure_schema_json_bytes(payload, str(path))


def _tar_schema_members(tf: tarfile.TarFile) -> list[tarfile.TarInfo]:
    candidates: list[tarfile.TarInfo] = []
    for member in tf.getmembers():
        if not member.isfile():
            continue
        rel = Path(member.name)
        if rel.name != "config.schema.json":
            continue
        if rel.parent.name != "share":
            continue
        candidates.append(member)
    return candidates


def extract_latest_schema_from_release_package(release_package: Path, latest_path: Path) -> None:
    if not release_package.is_file():
        fail(f"release package not found for schema extraction: {release_package}")
    try:
        with tarfile.open(release_package, "r:*") as tf:
            candidates = _tar_schema_members(tf)
            if not candidates:
                fail(
                    "release package does not contain share/config.schema.json for latest schema extraction"
                )
            if len(candidates) > 1:
                rendered = ", ".join(member.name for member in candidates)
                fail(f"release package contains multiple schema candidates: {rendered}")
            selected = candidates[0]
            file_obj = tf.extractfile(selected)
            if file_obj is None:
                fail(f"unable to read schema member from release package: {selected.name}")
            payload = file_obj.read(MAX_SCHEMA_BYTES + 1)
    except (tarfile.TarError, OSError) as exc:
        fail(f"unable to extract latest schema from release package {release_package}: {exc}")

    ensure_schema_json_bytes(payload, f"{release_package}:{selected.name}")
    atomic_write_bytes(latest_path, payload)


def _run_git(args: list[str], timeout: int) -> None:
    try:
        subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        fail(f"git command timed out ({' '.join(args)}): {exc}")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        fail(
            f"git command failed ({' '.join(args)}), exit code {exc.returncode}"
            + (f": {stderr}" if stderr else "")
        )


def download_newest_schema(newest_path: Path) -> None:
    ensure_git_available()
    last_error = ""
    for attempt in range(1, GIT_ATTEMPTS + 1):
        try:
            with tempfile.TemporaryDirectory(prefix="codex-schema-newest-") as tmp_dir:
                repo_dir = Path(tmp_dir) / "repo"
                _run_git(
                    [
                        "clone",
                        "--depth",
                        "1",
                        "--filter=blob:none",
                        "--sparse",
                        OPENAI_CODEX_GIT_URL,
                        str(repo_dir),
                    ],
                    timeout=GIT_CLONE_TIMEOUT_SECONDS,
                )
                _run_git(
                    [
                        "-C",
                        str(repo_dir),
                        "sparse-checkout",
                        "set",
                        "--no-cone",
                        OPENAI_CODEX_SCHEMA_PATH,
                    ],
                    timeout=GIT_SPARSE_TIMEOUT_SECONDS,
                )
                source = repo_dir / OPENAI_CODEX_SCHEMA_PATH
                if not source.is_file():
                    fail(f"schema file not found in cloned repository: {OPENAI_CODEX_SCHEMA_PATH}")
                payload = source.read_bytes()
                ensure_schema_json_bytes(payload, str(source))
                atomic_write_bytes(newest_path, payload)
                return
        except SchemaToolError as exc:
            last_error = str(exc)
            if attempt < GIT_ATTEMPTS:
                time.sleep(1)
            continue
    fail(f"unable to download newest schema from {OPENAI_CODEX_GIT_URL}: {last_error}")


def resolve_schema_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        fail(f"unsupported schema ref format: {ref}")
    current: Any = root
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or key not in current:
            fail(f"schema ref target not found: {ref}")
        current = current[key]
    if not isinstance(current, dict):
        fail(f"schema ref target must resolve to an object: {ref}")
    return current


def dereference_schema_node(
    root: dict[str, Any],
    node: dict[str, Any],
    active_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    current = dict(node)
    while "$ref" in current:
        ref = current["$ref"]
        if not isinstance(ref, str):
            fail("schema $ref must be a string")
        if ref in active_refs:
            chain = " -> ".join((*active_refs, ref))
            fail(f"schema $ref recursion detected: {chain}")
        target = resolve_schema_ref(root, ref)
        merged = dict(target)
        for key, value in current.items():
            if key != "$ref":
                merged[key] = value
        current = merged
        active_refs = (*active_refs, ref)
    return current


def schema_object_properties(root: dict[str, Any], node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    resolved = dereference_schema_node(root, node)
    props: dict[str, dict[str, Any]] = {}

    all_of = resolved.get("allOf")
    if isinstance(all_of, list):
        for part in all_of:
            if not isinstance(part, dict):
                continue
            nested = schema_object_properties(root, part)
            props.update(nested)

    for variant_key in ("anyOf", "oneOf"):
        variants = resolved.get(variant_key)
        if not isinstance(variants, list):
            continue
        for option in variants:
            if not isinstance(option, dict):
                continue
            candidate = dereference_schema_node(root, option)
            candidate_type = candidate.get("type")
            if candidate_type == "null":
                continue
            has_object_shape = (
                candidate_type == "object"
                or isinstance(candidate.get("properties"), dict)
                or isinstance(candidate.get("allOf"), list)
                or isinstance(candidate.get("anyOf"), list)
                or isinstance(candidate.get("oneOf"), list)
            )
            if has_object_shape:
                props.update(schema_object_properties(root, candidate))

    direct_props = resolved.get("properties")
    if isinstance(direct_props, dict):
        for key, value in direct_props.items():
            if isinstance(key, str) and isinstance(value, dict):
                props[key] = value
    return props


def schema_additional_properties(root: dict[str, Any], node: dict[str, Any]) -> dict[str, Any] | None:
    resolved = dereference_schema_node(root, node)
    candidates: list[dict[str, Any]] = []

    direct = resolved.get("additionalProperties")
    if isinstance(direct, dict):
        candidates.append(direct)

    all_of = resolved.get("allOf")
    if isinstance(all_of, list):
        for part in all_of:
            if not isinstance(part, dict):
                continue
            nested = schema_additional_properties(root, part)
            if isinstance(nested, dict):
                candidates.append(nested)

    for variant_key in ("anyOf", "oneOf"):
        variants = resolved.get(variant_key)
        if not isinstance(variants, list):
            continue
        for option in variants:
            if not isinstance(option, dict):
                continue
            candidate = dereference_schema_node(root, option)
            candidate_type = candidate.get("type")
            if candidate_type == "null":
                continue
            nested = schema_additional_properties(root, candidate)
            if isinstance(nested, dict):
                candidates.append(nested)

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    return {"allOf": candidates}


def schema_example_value(root: dict[str, Any], node: dict[str, Any]) -> Any:
    resolved = dereference_schema_node(root, node)

    for key in ("default", "const"):
        if key in resolved:
            return resolved[key]

    examples = resolved.get("examples")
    if isinstance(examples, list) and examples:
        return examples[0]

    enum_values = resolved.get("enum")
    if isinstance(enum_values, list) and enum_values:
        return enum_values[0]

    for variant_key in ("anyOf", "oneOf"):
        variants = resolved.get(variant_key)
        if not isinstance(variants, list):
            continue
        for option in variants:
            if not isinstance(option, dict):
                continue
            candidate = dereference_schema_node(root, option)
            candidate_type = candidate.get("type")
            if candidate_type == "null":
                continue
            return schema_example_value(root, candidate)

    schema_type = resolved.get("type")
    if isinstance(schema_type, list):
        filtered = [item for item in schema_type if item != "null"]
        schema_type = filtered[0] if filtered else None

    if schema_type == "boolean":
        return False
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0
    if schema_type == "array":
        return []
    if schema_type == "object":
        return {}
    return ""


def placeholder_segment_for_prefix(prefix: tuple[str, ...]) -> str:
    return DYNAMIC_PATH_PLACEHOLDERS.get(prefix, "<name>")


def collect_schema_entries(
    root: dict[str, Any],
    node: dict[str, Any],
    prefix: tuple[str, ...],
    output: dict[tuple[str, ...], Any],
) -> None:
    properties = schema_object_properties(root, node)
    had_nested = False
    if properties:
        had_nested = True
        for key in sorted(properties.keys()):
            if "\n" in key or "\r" in key or "\x00" in key:
                fail(f"schema property name contains control characters: {key!r}")
            collect_schema_entries(root, properties[key], (*prefix, key), output)

    additional_schema = schema_additional_properties(root, node)
    if additional_schema is not None:
        had_nested = True
        collect_schema_entries(
            root,
            additional_schema,
            (*prefix, placeholder_segment_for_prefix(prefix)),
            output,
        )

    if had_nested:
        return

    if not prefix:
        return
    output[prefix] = schema_example_value(root, node)


def toml_key(value: str) -> str:
    if BARE_TOML_KEY_PATTERN.fullmatch(value):
        return value
    return json.dumps(value)


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return json.dumps(value)
    if value is None:
        return '""'
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        rendered = ", ".join(toml_value(item) for item in value)
        return f"[{rendered}]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts: list[str] = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                fail("inline table keys must be strings")
            parts.append(f"{toml_key(key)} = {toml_value(value[key])}")
        return "{ " + ", ".join(parts) + " }"
    return json.dumps(str(value))


def render_entries_as_toml(
    entries: dict[tuple[str, ...], Any], empty_comment: str | None = None
) -> str:
    table_entries: dict[tuple[str, ...], list[tuple[str, Any]]] = {}
    root_entries: list[tuple[str, Any]] = []

    for path, value in sorted(entries.items()):
        if len(path) == 1:
            root_entries.append((path[0], value))
            continue
        table_entries.setdefault(path[:-1], []).append((path[-1], value))

    lines: list[str] = []
    for key, value in root_entries:
        lines.append(f"{toml_key(key)} = {toml_value(value)}")

    for table in sorted(table_entries.keys()):
        if lines:
            lines.append("")
        header = ".".join(toml_key(part) for part in table)
        lines.append(f"[{header}]")
        for key, value in table_entries[table]:
            lines.append(f"{toml_key(key)} = {toml_value(value)}")

    if not lines:
        if empty_comment:
            return f"# {empty_comment}\n"
        return ""
    return "\n".join(lines).rstrip() + "\n"


def schema_paths(schema: dict[str, Any]) -> dict[tuple[str, ...], Any]:
    entries: dict[tuple[str, ...], Any] = {}
    collect_schema_entries(schema, schema, tuple(), entries)
    return entries


def newest_only_entries(
    latest_entries: dict[tuple[str, ...], Any], newest_entries: dict[tuple[str, ...], Any]
) -> dict[tuple[str, ...], Any]:
    return {
        path: newest_entries[path]
        for path in sorted(newest_entries.keys())
        if path not in latest_entries
    }


def load_host_config(config_path: Path) -> tuple[Path, dict[str, Any]]:
    if not config_path.is_file():
        fail(f"host config.toml not found under CODEX_HOME: {config_path}")
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"unable to parse host config TOML {config_path}: {exc}")
    if not isinstance(data, dict):
        fail(f"host config TOML must decode to a table: {config_path}")
    return config_path, data


def toml_paths_from_data(
    value: Any,
    prefix: tuple[str, ...] = (),
    output: dict[tuple[str, ...], Any] | None = None,
) -> dict[tuple[str, ...], Any]:
    if output is None:
        output = {}
    if isinstance(value, dict):
        if prefix and not value:
            output[prefix] = {}
            return output
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                continue
            toml_paths_from_data(value[key], (*prefix, key), output)
        return output
    if prefix:
        output[prefix] = value
    return output


def is_placeholder_segment(value: str) -> bool:
    return bool(PLACEHOLDER_SEGMENT_PATTERN.fullmatch(value))


def config_node_for_prefix(config: dict[str, Any], prefix: tuple[str, ...]) -> Any:
    current: Any = config
    for part in prefix:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def dynamic_identities_for_prefix(config: dict[str, Any], prefix: tuple[str, ...]) -> list[str]:
    current = config_node_for_prefix(config, prefix)
    if not isinstance(current, dict):
        return []
    identities = [
        key
        for key, value in current.items()
        if isinstance(key, str) and isinstance(value, dict)
    ]
    return sorted(set(identities))


def expand_path_with_config(path: tuple[str, ...], config: dict[str, Any]) -> list[tuple[str, ...]]:
    expanded_paths: list[tuple[str, ...]] = [tuple()]
    for segment in path:
        if not is_placeholder_segment(segment):
            expanded_paths = [(*prefix, segment) for prefix in expanded_paths]
            continue
        next_paths: list[tuple[str, ...]] = []
        for prefix in expanded_paths:
            identities = dynamic_identities_for_prefix(config, prefix)
            if identities:
                next_paths.extend([(*prefix, identity) for identity in identities])
            else:
                next_paths.append((*prefix, segment))
        expanded_paths = next_paths
    unique_paths = sorted(set(expanded_paths))
    return unique_paths


def expand_entries_with_config(
    entries: dict[tuple[str, ...], Any], config: dict[str, Any]
) -> dict[tuple[str, ...], Any]:
    expanded: dict[tuple[str, ...], Any] = {}
    for path, value in sorted(entries.items()):
        for expanded_path in expand_path_with_config(path, config):
            expanded[expanded_path] = value
    return expanded


def _ensure_snapshot_file(path: Path, label: str, materialize: Callable[[], None]) -> None:
    if path.is_file():
        try:
            load_schema(path)
            return
        except SchemaToolError:
            pass
    materialize()
    if not path.is_file():
        fail(f"{label} snapshot was not created: {path}")
    load_schema(path)


def ensure_snapshots(
    latest_path: Path,
    newest_path: Path,
    release_package: Path,
) -> None:
    _ensure_snapshot_file(
        latest_path,
        "latest",
        lambda: extract_latest_schema_from_release_package(release_package, latest_path),
    )
    _ensure_snapshot_file(
        newest_path,
        "newest",
        lambda: download_newest_schema(newest_path),
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex schema helper tool")
    parser.add_argument(
        "command",
        choices=("newest", "diff"),
        help="Operation to run",
    )
    parser.add_argument("--schema-root", required=True, help="Absolute schema root directory")
    parser.add_argument("--release-package", required=True, help="Absolute codex release package path")
    parser.add_argument("--host-config", help="Absolute host config.toml path")
    parser.add_argument(
        "--output",
        action="store_true",
        help="Print generated diff/example content (supported only by 'diff')",
    )
    return parser


def run_newest(schema_root: Path) -> int:
    newest_path = schema_root / "newest" / "config.schema.newest.json"
    download_newest_schema(newest_path)
    print(f"[ok] newest schema: {newest_path}")
    return 0


def run_diff(schema_root: Path, release_package: Path, host_config_path: Path, output: bool) -> int:
    latest_path = schema_root / "latest" / "config.schema.latest.json"
    newest_path = schema_root / "newest" / "config.schema.newest.json"
    newest_copy_path = schema_root / "config.schema.json"
    diff_toml_path = schema_root / "config.diff.toml"
    example_toml_path = schema_root / "config.example.toml"

    ensure_snapshots(latest_path, newest_path, release_package)
    latest_schema = load_schema(latest_path)
    newest_schema = load_schema(newest_path)
    host_config_path, host_config = load_host_config(host_config_path)

    newest_payload = newest_path.read_bytes()
    ensure_schema_json_bytes(newest_payload, str(newest_path))
    atomic_write_bytes(newest_copy_path, newest_payload)

    latest_entries = schema_paths(latest_schema)
    newest_entries = schema_paths(newest_schema)
    host_entries = toml_paths_from_data(host_config)

    diff_entries = expand_entries_with_config(
        newest_only_entries(latest_entries, newest_entries),
        host_config,
    )
    diff_toml = render_entries_as_toml(
        diff_entries,
        empty_comment="no keys exist in newest schema that are absent from latest schema",
    )
    example_entries = {
        path: value
        for path, value in expand_entries_with_config(newest_entries, host_config).items()
        if path not in host_entries
    }
    example_toml = render_entries_as_toml(example_entries)

    atomic_write_text(diff_toml_path, diff_toml)
    atomic_write_text(example_toml_path, example_toml)

    if output:
        print("=== config.diff.toml ===")
        sys.stdout.write(diff_toml)
        print("=== config.example.toml ===")
        sys.stdout.write(example_toml)

    print(f"[ok] schema source: {OPENAI_CODEX_GIT_URL}")
    print(f"[ok] blob reference: {OPENAI_CODEX_SCHEMA_BLOB_URL}")
    print(f"[ok] host config: {host_config_path}")
    print(f"[ok] newest schema copy: {newest_copy_path}")
    print(f"[ok] diff output: {diff_toml_path}")
    print(f"[ok] example output: {example_toml_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    schema_root = ensure_safe_absolute_path("schema-root", args.schema_root)
    release_package = ensure_safe_absolute_path("release-package", args.release_package)

    if args.command == "newest":
        if args.output:
            fail("--output is only supported for the 'diff' command")
        return run_newest(schema_root)
    if not args.host_config:
        fail("--host-config is required for the 'diff' command")
    host_config_path = ensure_safe_absolute_path("host-config", args.host_config)
    return run_diff(schema_root, release_package, host_config_path, args.output)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SchemaToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
