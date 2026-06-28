from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from typing import Callable

from common import fail

SKILLS_MANIFEST_LABEL = "resources/skills/metadata.json"
VENDOR_MCP_LABEL = "config/vendor/mcp.toml"


def render_mcp_command_line(command: str, args: list[str]) -> str:
    tokens = [command] + args
    for token in tokens:
        if "\n" in token or "\r" in token:
            fail(f"mcp command token contains control characters: {token}")
    return " ".join(tokens)


def iter_skill_groups(skills_payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups = skills_payload.get("groups")
    if not isinstance(groups, list) or not groups:
        fail(f"{SKILLS_MANIFEST_LABEL} missing groups definitions")
    return [group for group in groups if isinstance(group, dict)]


def role_tools_from_skills(skills_payload: dict[str, Any], role_name: str) -> list[str]:
    role_table = skills_payload.get("roles")
    if not isinstance(role_table, dict):
        fail(f"{SKILLS_MANIFEST_LABEL} missing roles definitions")
    role = role_table.get(role_name)
    if not isinstance(role, dict):
        fail(f"role not found in {SKILLS_MANIFEST_LABEL}: {role_name}")
    tools = role.get("tools")
    if not isinstance(tools, list) or not tools:
        fail(f"role {role_name} has no tools configured")
    out: list[str] = []
    for raw in tools:
        if not isinstance(raw, str) or not raw.strip():
            fail(f"role {role_name} contains invalid tool entry")
        out.append(raw.strip())
    return out


def render_dependency_block(role_tools: list[str], mcp_servers: dict[str, Any]) -> str:
    lines = ["dependencies:"]
    tool_lines: list[str] = []
    for tool in role_tools:
        server = mcp_servers.get(tool)
        if not isinstance(server, dict):
            continue
        entry_lines = [
            "  - type: mcp",
            f"    value: {tool}",
            f"    description: {tool} MCP server",
        ]
        if isinstance(server.get("url"), str) and server.get("url"):
            entry_lines.append("    transport: streamable_http")
            entry_lines.append(f"    url: {server['url']}")
        elif isinstance(server.get("command"), str) and server.get("command"):
            args = server.get("args", [])
            if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
                continue
            cmd_line = render_mcp_command_line(server["command"], args)
            entry_lines.append("    transport: stdio")
            entry_lines.append(f"    command: {cmd_line}")
        else:
            continue
        tool_lines.extend(entry_lines)
    if not tool_lines:
        lines.append("  tools: []")
        return "\n".join(lines) + "\n"
    lines.append("  tools:")
    lines.extend(tool_lines)
    return "\n".join(lines) + "\n"


def rewrite_openai_yaml_dependencies(
    path: Path,
    dependency_block: str,
    dry_run: bool,
    write_file: Callable[[Path, str], None] | None = None,
) -> None:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    def is_top_level_key(line: str) -> bool:
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", line))

    dep_index = next((idx for idx, line in enumerate(lines) if line.strip() == "dependencies:"), -1)
    policy_index = next((idx for idx, line in enumerate(lines) if line.strip() == "policy:"), -1)

    block_lines = dependency_block.rstrip("\n").splitlines()

    if dep_index >= 0:
        end_index = len(lines)
        for idx in range(dep_index + 1, len(lines)):
            if is_top_level_key(lines[idx]):
                end_index = idx
                break
        new_lines = lines[:dep_index] + block_lines + lines[end_index:]
    elif policy_index >= 0:
        new_lines = lines[:policy_index] + block_lines + [""] + lines[policy_index:]
    else:
        if lines and lines[-1].strip():
            lines.append("")
        new_lines = lines + block_lines

    rendered = "\n".join(new_lines).rstrip() + "\n"
    if rendered == raw:
        return
    if dry_run:
        print(f"[dry-run] update dependencies in {path}")
        return
    if write_file is not None:
        write_file(path, rendered)
        return
    path.write_text(rendered, encoding="utf-8")


def validate_openai_yaml_mcp_dependencies(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    dep_index = next((idx for idx, line in enumerate(lines) if line.strip() == "dependencies:"), -1)
    if dep_index < 0:
        return

    def is_top_level_key(line: str) -> bool:
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", line))

    end_index = len(lines)
    for idx in range(dep_index + 1, len(lines)):
        if is_top_level_key(lines[idx]):
            end_index = idx
            break

    current: dict[str, str] = {}

    def validate_current(item: dict[str, str]) -> None:
        if not item or item.get("type", "").lower() != "mcp":
            return
        value = item.get("value", "").strip()
        if not value:
            fail(f"{path} MCP dependency is missing value")
        transport = item.get("transport", "").strip().lower()
        if not transport:
            fail(f"{path} MCP dependency {value} is missing transport")
        if transport == "streamable_http":
            if not item.get("url", "").strip():
                fail(f"{path} MCP dependency {value} is missing url")
            return
        if transport == "stdio":
            if not item.get("command", "").strip():
                fail(f"{path} MCP dependency {value} is missing command")
            return
        fail(f"{path} MCP dependency {value} uses unsupported transport: {transport}")

    for line in lines[dep_index + 1 : end_index]:
        stripped = line.strip()
        type_match = re.match(r"^-\s*type:\s*(.+)$", stripped)
        if type_match:
            validate_current(current)
            current = {"type": type_match.group(1).strip().strip("\"'")}
            continue
        field_match = re.match(r"^(value|description|transport|command|url):\s*(.+)$", stripped)
        if field_match:
            current[field_match.group(1)] = field_match.group(2).strip().strip("\"'")

    validate_current(current)
