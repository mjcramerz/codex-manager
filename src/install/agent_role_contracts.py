from __future__ import annotations

from pathlib import Path
from typing import Any

from common import fail
from common import parse_toml_file
from hook_runtime_catalog import load_hook_catalog


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value.strip()


def _configured_agent_entries(apps_payload: dict[str, Any], *, path_label: str) -> dict[str, dict[str, Any]]:
    agents_table = apps_payload.get("agents")
    if not isinstance(agents_table, dict):
        fail(f"{path_label} must define an [agents] table")
    return {
        str(name): entry
        for name, entry in agents_table.items()
        if isinstance(entry, dict)
    }


def validate_agent_role_contracts(
    agents_dir: Path,
    apps_path: Path,
    *,
    apps_payload: dict[str, Any] | None = None,
    catalog: dict[str, Any] | None = None,
) -> None:
    if not agents_dir.is_dir():
        fail(f"missing agent config directory: {agents_dir}")
    catalog_payload = load_hook_catalog() if catalog is None else catalog
    roles = catalog_payload.get("roles")
    if not isinstance(roles, list) or not roles:
        fail("hook runtime catalog must declare roles")

    expected_role_names = sorted(_require_non_empty_string(role.get("name"), label="hook runtime catalog role name") for role in roles)
    agent_paths = sorted(path for path in agents_dir.glob("*.toml") if path.is_file())
    actual_role_names = sorted(path.stem for path in agent_paths)
    if actual_role_names != expected_role_names:
        missing = sorted(set(expected_role_names) - set(actual_role_names))
        unexpected = sorted(set(actual_role_names) - set(expected_role_names))
        details: list[str] = []
        if missing:
            details.append(f"missing role TOMLs: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected role TOMLs: {', '.join(unexpected)}")
        fail(f"{agents_dir} is out of sync with hook runtime roles ({'; '.join(details)})")

    resolved_apps_payload = parse_toml_file(apps_path) if apps_payload is None else apps_payload
    configured_roles = _configured_agent_entries(resolved_apps_payload, path_label=str(apps_path))
    actual_configured_role_names = sorted(configured_roles)
    if actual_configured_role_names != expected_role_names:
        missing = sorted(set(expected_role_names) - set(actual_configured_role_names))
        unexpected = sorted(set(actual_configured_role_names) - set(expected_role_names))
        details = []
        if missing:
            details.append(f"missing agent entries: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected agent entries: {', '.join(unexpected)}")
        fail(f"{apps_path} [agents] entries are out of sync with hook runtime roles ({'; '.join(details)})")
