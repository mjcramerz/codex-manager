from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any
from typing import Callable

from common import fail

SKILLS_MANIFEST_LABEL = "resources/skills/metadata.json"
VENDOR_MCP_LABEL = "config/vendor/mcp.toml"
TOP_LEVEL_YAML_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$")
DEPENDENCY_CHILD_KEY = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_]*)\s*:(?:\s*(.*))?$")


def render_mcp_command_line(command: str, args: list[str]) -> str:
    tokens = [command] + args
    for token in tokens:
        if "\n" in token or "\r" in token:
            fail(f"mcp command token contains control characters: {token}")
    return shlex.join(tokens)


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
    seen_tools: set[str] = set()
    for tool in role_tools:
        if tool in seen_tools:
            fail(f"duplicate MCP dependency requested for skill role: {tool}")
        seen_tools.add(tool)
        server = mcp_servers.get(tool)
        if not isinstance(server, dict):
            fail(f"missing MCP server definition for skill dependency: {tool}")
        entry_lines = [
            "  - type: mcp",
            f"    value: {tool}",
            f"    description: {tool} MCP server",
        ]
        url = server.get("url")
        command = server.get("command")
        if isinstance(url, str) and url.strip():
            entry_lines.append("    transport: streamable_http")
            entry_lines.append(f"    url: {url.strip()}")
        elif isinstance(command, str) and command.strip():
            args = server.get("args", [])
            if args in (None, {}):
                args = []
            if not isinstance(args, list) or not all(isinstance(item, str) and item for item in args):
                fail(f"MCP server {tool} has invalid args; expected a list of non-empty strings")
            cmd_line = render_mcp_command_line(command.strip(), args)
            entry_lines.append("    transport: stdio")
            entry_lines.append(f"    command: {cmd_line}")
        else:
            fail(f"MCP server {tool} must define either url or command for skill dependencies")
        tool_lines.extend(entry_lines)
    if not tool_lines:
        lines.append("  tools: []")
        return "\n".join(lines) + "\n"
    lines.append("  tools:")
    lines.extend(tool_lines)
    return "\n".join(lines) + "\n"


def _find_top_level_block(lines: list[str], key: str) -> tuple[int, int]:
    start = next((idx for idx, line in enumerate(lines) if line.strip() == f"{key}:"), -1)
    if start < 0:
        return -1, -1
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if TOP_LEVEL_YAML_KEY.match(lines[idx]):
            end = idx
            break
    return start, end


def _find_dependency_tools_block(lines: list[str], dependencies_start: int, dependencies_end: int) -> tuple[int, int]:
    for idx in range(dependencies_start + 1, dependencies_end):
        match = DEPENDENCY_CHILD_KEY.match(lines[idx])
        if match is None or match.group(1) != "tools":
            continue
        end = dependencies_end
        for inner_idx in range(idx + 1, dependencies_end):
            if DEPENDENCY_CHILD_KEY.match(lines[inner_idx]):
                end = inner_idx
                break
        return idx, end
    return -1, -1


def _dependency_tools_lines(dependency_block: str) -> list[str]:
    block_lines = dependency_block.rstrip("\n").splitlines()
    if not block_lines or block_lines[0].strip() != "dependencies:":
        fail("dependency block must start with `dependencies:`")
    if len(block_lines) < 2 or DEPENDENCY_CHILD_KEY.match(block_lines[1]) is None:
        fail("dependency block must define `dependencies.tools`")
    child_match = DEPENDENCY_CHILD_KEY.match(block_lines[1])
    if child_match is None or child_match.group(1) != "tools":
        fail("dependency block must define `dependencies.tools` first")
    return block_lines[1:]


def rewrite_openai_yaml_dependencies(
    path: Path,
    dependency_block: str,
    dry_run: bool,
    write_file: Callable[[Path, str], None] | None = None,
) -> None:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    dep_index, dep_end_index = _find_top_level_block(lines, "dependencies")
    policy_index, _policy_end_index = _find_top_level_block(lines, "policy")
    block_lines = dependency_block.rstrip("\n").splitlines()
    tools_lines = _dependency_tools_lines(dependency_block)

    if dep_index >= 0:
        tools_start, tools_end = _find_dependency_tools_block(lines, dep_index, dep_end_index)
        if tools_start >= 0:
            new_lines = lines[:tools_start] + tools_lines + lines[tools_end:]
        else:
            new_lines = lines[: dep_index + 1] + tools_lines + lines[dep_index + 1 :]
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
    dep_index, dep_end_index = _find_top_level_block(lines, "dependencies")
    if dep_index < 0:
        return

    tools_index, tools_end_index = _find_dependency_tools_block(lines, dep_index, dep_end_index)
    if tools_index < 0:
        return

    tools_match = DEPENDENCY_CHILD_KEY.match(lines[tools_index])
    if tools_match is None:
        fail(f"{path} dependencies.tools block is malformed")
    inline_value = (tools_match.group(2) or "").strip()
    if inline_value:
        if inline_value != "[]":
            fail(f"{path} dependencies.tools must use `[]` or a block list")
        return

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

    for line in lines[tools_index + 1 : tools_end_index]:
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
