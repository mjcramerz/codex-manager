from __future__ import annotations

from pathlib import Path

from common import _replace_known_placeholders_outside_toml_multiline_strings
from common import fail
from layout import RepoLayout

CONFIG_FRAGMENT_PLACEHOLDERS = frozenset(
    {
        "CODEX_MCP_DIR",
        "CODEX_SQLITE_HOME",
        "CODEX_LOG_DIR",
        "CODEX_TMPDIR",
        "CODEX_AGENTS",
        "CODEX_SKILLS",
    }
)


def _config_fragment_variables(variables: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in variables.items()
        if key in CONFIG_FRAGMENT_PLACEHOLDERS
    }


def _render_fragment_text(path: Path, variables: dict[str, str]) -> str:
    if not path.is_file():
        fail(f"missing config fragment: {path}")
    raw = path.read_text(encoding="utf-8")
    return _replace_known_placeholders_outside_toml_multiline_strings(
        raw,
        _config_fragment_variables(variables),
    )


def _append_fragment(document: str, fragment: str) -> str:
    if not document:
        return fragment
    document = document.rstrip("\n")
    fragment = fragment.lstrip("\n")
    return document + "\n\n" + fragment


def _vendor_fragment_paths(layout: RepoLayout) -> list[Path]:
    return [
        layout.vendor_config_path,
        layout.vendor_providers_path,
        layout.vendor_pref_path,
        layout.vendor_mcp_path,
        layout.vendor_policy_path,
    ]


def _user_fragment_paths(layout: RepoLayout) -> list[Path]:
    return [
        layout.user_config_path,
        layout.user_pref_path,
        layout.user_features_path,
        layout.user_memory_path,
        layout.user_apps_path,
        layout.user_policy_path,
    ]


def compile_vendor_config(layout: RepoLayout, variables: dict[str, str]) -> str:
    rendered = ""
    for path in _vendor_fragment_paths(layout):
        rendered = _append_fragment(rendered, _render_fragment_text(path, variables))
    if rendered and not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def compile_home_config(
    layout: RepoLayout,
    variables: dict[str, str],
    instruction_overrides: dict[str, str],
) -> str:
    del instruction_overrides
    rendered = ""
    for path in _user_fragment_paths(layout):
        rendered = _append_fragment(rendered, _render_fragment_text(path, variables))
    if rendered and not rendered.endswith("\n"):
        rendered += "\n"
    return rendered
