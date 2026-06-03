from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from common import _first_unresolved_codex_placeholder_in_object
from common import ensure_https_url
from common import fail
from common import replace_known_placeholders_in_object
from skills import render_dependency_block
from skills import rewrite_openai_yaml_dependencies

PLUGIN_INVENTORY_LABEL = "resources/plugins/manifest.json"
PLUGIN_INVENTORY_VERSION = 2
PLUGIN_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
REQUIRED_SHARED_MCP_REFS = (
    "context7",
    "fetch",
    "filesystem",
    "git",
    "linear",
    "sequential_thinking",
)


def _warn(message: str) -> None:
    print(f"[warn] {message}")


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    rendered: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            fail(f"{label} must contain non-empty strings")
        rendered.append(item.strip())
    return rendered


def _apps_list(value: Any, *, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    rendered: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            name = item.strip()
            app_id = name
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            app_id = str(item.get("id", name)).strip()
        else:
            fail(f"{label} entries must be strings or objects")
        if not PLUGIN_KEY_PATTERN.fullmatch(name):
            fail(f"{label} app name is invalid: {name}")
        if not app_id:
            fail(f"{label} app id is required for {name}")
        if name in seen:
            fail(f"{label} duplicate app name: {name}")
        seen.add(name)
        rendered.append({"name": name, "id": app_id})
    return rendered


def _mcp_list(value: Any, *, label: str) -> list[str | dict[str, Any]]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    rendered: list[str | dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            name = item.strip()
            if not PLUGIN_KEY_PATTERN.fullmatch(name):
                fail(f"{label} MCP server name is invalid: {name}")
            if name in seen:
                fail(f"{label} duplicate MCP server: {name}")
            seen.add(name)
            rendered.append(name)
            continue
        if not isinstance(item, dict):
            fail(f"{label} entries must be strings or objects")

        name = str(item.get("name", "")).strip()
        if not PLUGIN_KEY_PATTERN.fullmatch(name):
            fail(f"{label} MCP server name is invalid: {name}")
        if name in seen:
            fail(f"{label} duplicate MCP server: {name}")
        seen.add(name)

        payload = copy.deepcopy(item)
        payload["name"] = name
        url = payload.get("url")
        command = payload.get("command")
        if isinstance(url, str) and url.strip():
            payload["url"] = url.strip()
            ensure_https_url(f"{label} MCP server {name} url", payload["url"])
        elif isinstance(command, str) and command.strip():
            payload["command"] = command.strip()
            args = payload.get("args", [])
            if args in (None, {}):
                args = []
            if not isinstance(args, list):
                fail(f"{label} MCP server {name} args must be a list")
            normalized_args: list[str] = []
            for arg in args:
                if not isinstance(arg, str) or not arg.strip():
                    fail(f"{label} MCP server {name} args must contain non-empty strings")
                normalized_args.append(arg.strip())
            payload["args"] = normalized_args
        else:
            fail(f"{label} MCP server {name} must define url or command")
        rendered.append(payload)
    return rendered


def _plugin_mcp_name(value: str | dict[str, Any], *, label: str) -> str:
    if isinstance(value, str):
        name = value.strip()
    elif isinstance(value, dict):
        name = str(value.get("name", "")).strip()
    else:
        fail(f"{label} entries must be strings or objects")
    if not PLUGIN_KEY_PATTERN.fullmatch(name):
        fail(f"{label} MCP server name is invalid: {name}")
    return name


def effective_plugins_inventory_payload(
    base_inventory_payload: dict[str, Any],
    inventory_path: Path,
    *,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(base_inventory_payload, dict) or not base_inventory_payload:
        fail(f"{inventory_path} must be a non-empty object")
    if base_inventory_payload.get("version") != PLUGIN_INVENTORY_VERSION:
        fail(f"{inventory_path} must declare version = {PLUGIN_INVENTORY_VERSION}")
    plugins_table = base_inventory_payload.get("plugins")
    if not isinstance(plugins_table, dict) or not plugins_table:
        fail(f"{inventory_path} must declare a non-empty plugins object")

    rendered = copy.deepcopy(base_inventory_payload)
    if variables:
        rendered = replace_known_placeholders_in_object(rendered, variables)
        unresolved = _first_unresolved_codex_placeholder_in_object(rendered)
        if unresolved:
            fail(f"{inventory_path} contains unresolved CODEX_* placeholder: {unresolved}")
    shared_mcp = rendered.get("shared_mcp", {})
    if shared_mcp in (None, {}):
        rendered["shared_mcp"] = {"refs": []}
    elif not isinstance(shared_mcp, dict):
        fail(f"{inventory_path} shared_mcp must be an object")
    else:
        rendered["shared_mcp"] = {
            "refs": _string_list(shared_mcp.get("refs", []), label=f"{inventory_path} shared_mcp.refs")
        }
    missing_shared_refs = sorted(set(REQUIRED_SHARED_MCP_REFS) - set(rendered["shared_mcp"]["refs"]))
    if missing_shared_refs:
        _warn(f"{inventory_path} shared_mcp.refs is missing required global MCP servers: {', '.join(missing_shared_refs)}")

    for key, value in rendered["plugins"].items():
        if not isinstance(key, str) or not PLUGIN_KEY_PATTERN.fullmatch(key):
            fail(f"{inventory_path} plugin key is invalid: {key}")
        if not isinstance(value, dict):
            fail(f"{inventory_path} plugin entry must be an object for {key}")
        value["keywords"] = _string_list(value.get("keywords"), label=f"{inventory_path} plugin.{key}.keywords")
        value["skills"] = _string_list(value.get("skills"), label=f"{inventory_path} plugin.{key}.skills")
        value["apps"] = _apps_list(value.get("apps"), label=f"{inventory_path} plugin.{key}.apps")
        value["mcp"] = _mcp_list(value.get("mcp"), label=f"{inventory_path} plugin.{key}.mcp")
        shared_refs = set(rendered["shared_mcp"]["refs"])
        for entry in value["mcp"]:
            entry_name = _plugin_mcp_name(entry, label=f"{inventory_path} plugin.{key}.mcp")
            if entry_name in shared_refs:
                fail(f"{inventory_path} plugin.{key}.mcp duplicates shared MCP server: {entry_name}")
    return rendered


def rewrite_runtime_plugin_skill_dependencies(
    runtime_skills_dir: Path,
    bundle: Any,
    inventory_payload: dict[str, Any],
    mcp_payload: dict[str, Any],
    *,
    dry_run: bool,
) -> None:
    shared_refs = list(inventory_payload.get("shared_mcp", {}).get("refs", []))
    plugins_table = inventory_payload.get("plugins")
    if not isinstance(plugins_table, dict):
        fail(f"{PLUGIN_INVENTORY_LABEL} is missing plugins object")
    plugin_entry = plugins_table.get(bundle.name)
    if plugin_entry is None:
        fail(f"{PLUGIN_INVENTORY_LABEL} is missing plugin entry for {bundle.name}")
    plugin_mcp = list(plugin_entry["mcp"])
    mcp_servers = mcp_payload.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        fail("vendor MCP payload is missing mcp_servers")

    effective_mcp_servers = dict(mcp_servers)
    tools: list[str] = []
    seen: set[str] = set()
    label = f"{PLUGIN_INVENTORY_LABEL} plugin.{bundle.name}.mcp"
    for raw_tool in [*shared_refs, *plugin_mcp]:
        tool_name = _plugin_mcp_name(raw_tool, label=label)
        if tool_name in seen:
            fail(f"{label} duplicate MCP server: {tool_name}")
        seen.add(tool_name)
        if isinstance(raw_tool, str):
            server = mcp_servers.get(tool_name)
            if not isinstance(server, dict):
                fail(f"{label} references unknown MCP server: {tool_name}")
            effective_mcp_servers[tool_name] = dict(server)
        else:
            server = copy.deepcopy(raw_tool)
            server.pop("name", None)
            effective_mcp_servers[tool_name] = server
        tools.append(tool_name)
    dependency_block = render_dependency_block(tools, effective_mcp_servers)

    for skill_name in bundle.skills:
        skill_path = runtime_skills_dir / skill_name / "agents" / "openai.yaml"
        if not skill_path.is_file():
            continue
        rewrite_openai_yaml_dependencies(skill_path, dependency_block, dry_run)
