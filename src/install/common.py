from __future__ import annotations

import json
import re
import tomllib
import urllib.parse
from pathlib import Path
from typing import Any

KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
PLACEHOLDER_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}|\$([A-Z0-9_]+)")
UNRESOLVED_CODEX_PLACEHOLDER_PATTERN = re.compile(r"\$\{CODEX_[A-Z0-9_]+\}|\$CODEX_[A-Z0-9_]+")
SHA256_PATTERN = re.compile(r"^[A-Fa-f0-9]{64}$")


class InstallError(RuntimeError):
    """Domain error."""


def fail(message: str) -> None:
    raise InstallError(message)


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


def parse_env_file(path: Path) -> dict[str, str]:
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
        value = strip_inline_comment(value)
        if not KEY_PATTERN.fullmatch(key):
            fail(f"invalid env key at {path}:{idx}: {key}")
        value = value.strip()
        if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
            value = value[1:-1]
        if "${" in value or "$(" in value or "`" in value:
            fail(f"fallback/expansion is not allowed in .env ({key} at line {idx})")
        parsed[key] = value
    return parsed


def parse_toml_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing TOML file: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"invalid TOML at {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"invalid TOML payload shape at {path}")
    return data


def parse_json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing JSON file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"invalid JSON payload shape at {path}")
    return data


def parse_variable_table(
    payload: dict[str, Any],
    *,
    path_label: str,
    table_name: str,
    item_label: str,
) -> dict[str, str]:
    table = payload.get(table_name)
    if not isinstance(table, dict):
        fail(f"{path_label} must contain [{table_name}]")

    parsed: dict[str, str] = {}
    for key, value in table.items():
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
            fail(f"invalid {item_label} key in {path_label}: {key}")
        if not isinstance(value, str):
            fail(f"{item_label} value must be string: {key}")
        parsed[key] = value.strip()
    return parsed


def normalize_path(value: str) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def ensure_safe_absolute_path(label: str, value: str) -> Path:
    if not value:
        fail(f"missing required path value for {label}")
    if "\n" in value or "\r" in value:
        fail(f"path {label} contains control characters")
    if any(ch.isspace() for ch in value):
        fail(f"path {label} contains whitespace: {value}")
    path = Path(value)
    if not path.is_absolute():
        fail(f"path {label} must be absolute: {value}")
    return normalize_path(value)


def ensure_safe_shell_export_value(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        fail(f"missing required shell export value for {label}")
    if any(ch in cleaned for ch in ("\x00", "\n", "\r", '"')):
        fail(f"shell export {label} contains unsupported characters")
    return cleaned


def ensure_sha256(label: str, value: str) -> None:
    if not SHA256_PATTERN.fullmatch(value):
        fail(f"{label} must be 64 hex characters")


def ensure_https_url(label: str, value: str) -> None:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        fail(f"{label} must use https")


def ensure_gitlab_url(label: str, value: str) -> None:
    parsed = urllib.parse.urlparse(value)
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        fail(f"{label} must use https")
    if not host:
        fail(f"{label} must include a host")
    normalized = host.lower()
    if normalized != "gitlab.com" and not normalized.endswith(".gitlab.com"):
        fail(f"{label} must point to GitLab: {value}")


def resolve_placeholders(value: str, variables: dict[str, str], context: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2) or ""
        resolved = variables.get(key, "").strip()
        if not resolved:
            fail(f"unresolved placeholder {key} in {context}")
        return resolved

    rendered = PLACEHOLDER_PATTERN.sub(repl, value)
    if "$" in rendered:
        fail(f"unresolved variable token remains in {context}: {rendered}")
    return rendered


def resolve_object_placeholders(value: Any, variables: dict[str, str], context: str) -> Any:
    if isinstance(value, str):
        return resolve_placeholders(value, variables, context)
    if isinstance(value, list):
        return [resolve_object_placeholders(item, variables, context) for item in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            out[key] = resolve_object_placeholders(item, variables, f"{context}.{key}")
        return out
    return value


def replace_known_placeholders_in_text(text: str, variables: dict[str, str]) -> str:
    rendered = text
    for key in sorted(variables.keys(), key=len, reverse=True):
        value = variables[key]
        rendered = rendered.replace(f"${{{key}}}", value)
        rendered = rendered.replace(f"${key}", value)
    return rendered


def replace_known_placeholders_in_object(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        return replace_known_placeholders_in_text(value, variables)
    if isinstance(value, list):
        return [replace_known_placeholders_in_object(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: replace_known_placeholders_in_object(item, variables) for key, item in value.items()}
    return value


def _first_unresolved_codex_placeholder_in_object(value: Any) -> str | None:
    if isinstance(value, str):
        match = UNRESOLVED_CODEX_PLACEHOLDER_PATTERN.search(value)
        return match.group(0) if match else None
    if isinstance(value, list):
        for item in value:
            match = _first_unresolved_codex_placeholder_in_object(item)
            if match:
                return match
        return None
    if isinstance(value, dict):
        for item in value.values():
            match = _first_unresolved_codex_placeholder_in_object(item)
            if match:
                return match
        return None
    return None


def _toml_multiline_string_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    length = len(text)
    idx = 0
    state = "normal"
    span_start = 0

    while idx < length:
        if state == "normal":
            if text[idx] == "#":
                state = "comment"
                idx += 1
                continue
            if text.startswith('"""', idx):
                state = "multi_basic"
                span_start = idx
                idx += 3
                continue
            if text.startswith("'''", idx):
                state = "multi_literal"
                span_start = idx
                idx += 3
                continue
            if text[idx] == '"':
                state = "basic"
                idx += 1
                continue
            if text[idx] == "'":
                state = "literal"
                idx += 1
                continue
            idx += 1
            continue

        if state == "comment":
            if text[idx] == "\n":
                state = "normal"
            idx += 1
            continue

        if state == "basic":
            if text[idx] == "\\":
                idx += 2
                continue
            if text[idx] == '"':
                state = "normal"
            idx += 1
            continue

        if state == "literal":
            if text[idx] == "'":
                state = "normal"
            idx += 1
            continue

        if state == "multi_basic":
            if text.startswith('"""', idx):
                backslashes = 0
                cursor = idx - 1
                while cursor >= 0 and text[cursor] == "\\":
                    backslashes += 1
                    cursor -= 1
                if backslashes % 2 == 0:
                    idx += 3
                    spans.append((span_start, idx))
                    state = "normal"
                    continue
            idx += 1
            continue

        if state == "multi_literal":
            if text.startswith("'''", idx):
                idx += 3
                spans.append((span_start, idx))
                state = "normal"
                continue
            idx += 1
            continue

    return spans


def _replace_known_placeholders_outside_toml_multiline_strings(text: str, variables: dict[str, str]) -> str:
    spans = _toml_multiline_string_spans(text)
    if not spans:
        return replace_known_placeholders_in_text(text, variables)

    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        parts.append(replace_known_placeholders_in_text(text[cursor:start], variables))
        parts.append(text[start:end])
        cursor = end
    parts.append(replace_known_placeholders_in_text(text[cursor:], variables))
    return "".join(parts)


def _first_unresolved_codex_placeholder_outside_toml_multiline_strings(text: str) -> str | None:
    spans = _toml_multiline_string_spans(text)
    if not spans:
        match = UNRESOLVED_CODEX_PLACEHOLDER_PATTERN.search(text)
        return match.group(0) if match else None

    cursor = 0
    for start, end in spans:
        match = UNRESOLVED_CODEX_PLACEHOLDER_PATTERN.search(text[cursor:start])
        if match:
            return match.group(0)
        cursor = end
    match = UNRESOLVED_CODEX_PLACEHOLDER_PATTERN.search(text[cursor:])
    return match.group(0) if match else None


def toml_key(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value
    return json.dumps(value)


def toml_value(value: Any, indent: int = 0) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:
            fail("NaN is not supported in generated TOML")
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        inner_indent = " " * (indent + 2)
        closing_indent = " " * indent
        rendered = [f"{inner_indent}{toml_value(item, indent + 2)}," for item in value]
        return "[\n" + "\n".join(rendered) + "\n" + f"{closing_indent}]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts: list[str] = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                fail("inline table keys must be strings")
            parts.append(f"{toml_key(key)} = {toml_value(value[key], indent)}")
        return "{ " + ", ".join(parts) + " }"
    fail(f"unsupported TOML value type: {type(value)!r}")
