from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from common import ensure_https_url
from common import fail
from common import is_within
from common import parse_json_file
from apps_config import rewrite_runtime_plugin_skill_dependencies
from plugin_bundles import PluginAppSpec
from plugin_bundles import PluginBundleSpec
from plugin_bundles import render_runtime_plugin_apps
from plugin_bundles import render_runtime_plugin_manifest
from plugin_bundles import render_runtime_plugin_marketplace
from plugin_bundles import render_runtime_plugin_mcp

PLUGINS_MANIFEST_VERSION = 2
PLUGINS_METADATA_VERSION = 2
SAFE_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PLUGINS_BUNDLE_PATTERN = SAFE_FILENAME_PATTERN
PLUGINS_MARKETPLACE_PATTERN = SAFE_FILENAME_PATTERN
PLUGINS_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DEFAULT_PLUGIN_VERSION = "1.0.0"
DEFAULT_PROMPT_MAX_CHARS = 128
DEFAULT_PROMPT_MAX_ITEMS = 3
INTERFACE_CAPABILITY_VALUES = {"Interactive", "Read", "Write"}
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
PLUGIN_SKILL_REFERENCE_PLACEHOLDER_MARKERS = ("${", "<", ">", ":fileKey", ":fileName", "{", "}")
PLUGIN_HOOK_EVENTS = frozenset(
    {
        "SessionStart",
        "UserPromptSubmit",
        "PreCompact",
        "PostCompact",
        "Stop",
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "SubagentStart",
        "SubagentStop",
    }
)
PLUGIN_HOOK_GROUP_ALLOWED_KEYS = frozenset({"matcher", "hooks"})
PLUGIN_HOOK_HANDLER_ALLOWED_KEYS = frozenset({"type", "command", "commandWindows", "command_windows", "timeout", "statusMessage"})
PLUGIN_HOOK_HOME_SCRIPT_PATTERN = re.compile(r"\$\{CODEX_HOME\}/\.hooks/scripts/([A-Za-z0-9_.-]+\.pl)\b")


def _warn(message: str) -> None:
    print(f"[warn] {message}")


def local_plugin_bundle_dirs(source_root: Path) -> list[str]:
    if not source_root.is_dir():
        return []
    return sorted(path.name for path in source_root.iterdir() if path.is_dir())


def plugin_manifest_marketplace_name(inventory_payload: dict[str, Any], inventory_path: Path) -> str:
    version = inventory_payload.get("version")
    if version != PLUGINS_MANIFEST_VERSION:
        fail(f"{inventory_path} must declare version = {PLUGINS_MANIFEST_VERSION}")
    marketplace_name = str(inventory_payload.get("marketplace_name", "")).strip()
    if not PLUGINS_MARKETPLACE_PATTERN.fullmatch(marketplace_name):
        fail(f"{inventory_path} must declare a valid marketplace_name")
    return marketplace_name


def plugin_skill_source_path(repo_root: Path, inventory_path: Path, skill_name: str) -> Path:
    if not PLUGINS_SKILL_NAME_PATTERN.fullmatch(skill_name):
        fail(f"{inventory_path} contains invalid skill source: {skill_name}")
    skill_path = repo_root / "resources" / "plugins" / "skills" / skill_name
    if not skill_path.is_dir():
        fail(f"plugin skill source not found for {skill_name}: {skill_path}")
    return skill_path


def plugin_hook_source_path(
    repo_root: Path,
    inventory_path: Path,
    bundle_name: str,
    hooks_file: str,
) -> tuple[str, Path]:
    normalized = _normalize_skill_asset_reference(hooks_file)
    if not normalized:
        fail(
            f"{inventory_path} plugin.hooks for {bundle_name} must be a relative plugin path starting with ./"
        )
    source_root = repo_root / "resources" / "plugins" / "hooks" / bundle_name
    source_path = (source_root / normalized).resolve(strict=False)
    if not is_within(source_path, source_root.resolve(strict=False)):
        fail(f"{inventory_path} plugin.hooks for {bundle_name} escapes resources/plugins/hooks/{bundle_name}")
    if not source_path.is_file():
        fail(f"{inventory_path} plugin.hooks source is missing for {bundle_name}: {source_path}")
    return normalized, source_path


def validate_plugin_hook_file(
    repo_root: Path,
    inventory_path: Path,
    bundle_name: str,
    hooks_path: Path,
) -> None:
    payload = parse_json_file(hooks_path)
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        fail(f"{inventory_path} plugin.hooks for {bundle_name} must define a non-empty hooks object")

    for event_name, groups in hooks.items():
        if event_name not in PLUGIN_HOOK_EVENTS:
            fail(f"{inventory_path} plugin.hooks for {bundle_name} contains unsupported event: {event_name}")
        if not isinstance(groups, list) or not groups:
            fail(f"{inventory_path} plugin.hooks for {bundle_name} event {event_name} must be a non-empty list")
        for group_index, group in enumerate(groups):
            label = f"{inventory_path} plugin.hooks for {bundle_name} {event_name}[{group_index}]"
            if not isinstance(group, dict):
                fail(f"{label} must be an object")
            unknown_group_keys = sorted(set(group) - set(PLUGIN_HOOK_GROUP_ALLOWED_KEYS))
            if unknown_group_keys:
                fail(f"{label} contains unsupported keys: {', '.join(unknown_group_keys)}")
            matcher = group.get("matcher")
            if matcher is not None and (not isinstance(matcher, str) or not matcher.strip()):
                fail(f"{label}.matcher must be a non-empty string when provided")
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                fail(f"{label}.hooks must be a non-empty list")
            for handler_index, handler in enumerate(handlers):
                handler_label = f"{label}.hooks[{handler_index}]"
                if not isinstance(handler, dict):
                    fail(f"{handler_label} must be an object")
                unknown_handler_keys = sorted(set(handler) - set(PLUGIN_HOOK_HANDLER_ALLOWED_KEYS))
                if unknown_handler_keys:
                    fail(f"{handler_label} contains unsupported keys: {', '.join(unknown_handler_keys)}")
                if handler.get("type") != "command":
                    fail(f"{handler_label}.type must be command")
                command = handler.get("command")
                if not isinstance(command, str) or not command.strip():
                    fail(f"{handler_label}.command must be a non-empty string")
                timeout = handler.get("timeout")
                if timeout is not None and (not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 600):
                    fail(f"{handler_label}.timeout must be an integer between 1 and 600")
                status_message = handler.get("statusMessage")
                if status_message is not None and (not isinstance(status_message, str) or not status_message.strip()):
                    fail(f"{handler_label}.statusMessage must be a non-empty string when provided")
                script_match = PLUGIN_HOOK_HOME_SCRIPT_PATTERN.search(command)
                if script_match is not None:
                    script_path = repo_root / "resources" / "hooks" / "scripts" / script_match.group(1)
                    if not script_path.is_file():
                        fail(f"{handler_label}.command references missing installed home hook script: {script_path}")


def validate_plugin_skill_metadata(skill_path: Path) -> None:
    metadata_path = skill_path / "metadata.json"
    payload = parse_json_file(metadata_path)

    _required_string(payload.get("version"), label=f"{metadata_path} version")
    _required_string(payload.get("organization"), label=f"{metadata_path} organization")
    _required_string(payload.get("date"), label=f"{metadata_path} date")
    _required_string(payload.get("abstract"), label=f"{metadata_path} abstract")

    references = _string_list(payload.get("references", []), label=f"{metadata_path} references")
    if not references:
        fail(f"{metadata_path} references must not be empty")

    skill_doc = skill_path / "SKILL.md"
    if not skill_doc.is_file():
        fail(f"plugin skill is missing SKILL.md: {skill_doc}")

    skill_root = skill_path.resolve(strict=False)
    seen: set[str] = set()
    for ref in references:
        if ref in seen:
            fail(f"{metadata_path} references contains duplicate entry: {ref}")
        seen.add(ref)
        if any(ch in ref for ch in ("`", "\r", "\n", "\t")):
            fail(f"{metadata_path} references contains invalid characters: {ref}")
        if "://" in ref:
            ensure_https_url(f"{metadata_path} reference", ref)
            parsed = ref.lower()
            if "localhost" in parsed or "127.0.0.1" in parsed:
                fail(f"{metadata_path} references must not use localhost URLs: {ref}")
            if any(marker in ref for marker in PLUGIN_SKILL_REFERENCE_PLACEHOLDER_MARKERS):
                fail(f"{metadata_path} references must not contain placeholders: {ref}")
            continue

        ref_path = Path(ref)
        if ref_path.is_absolute():
            fail(f"{metadata_path} references must use bundle-relative paths or https URLs: {ref}")
        parts = ref_path.parts
        if not parts or any(part in ("", ".", "..") for part in parts):
            fail(f"{metadata_path} references contains invalid relative path: {ref}")
        candidate = (skill_path / ref_path).resolve(strict=False)
        if not is_within(candidate, skill_root):
            fail(f"{metadata_path} references escapes skill root: {ref}")
        if not candidate.is_file():
            fail(f"{metadata_path} references target is missing: {ref}")


def _normalize_skill_asset_reference(raw_value: str) -> str | None:
    value = raw_value.strip().strip("\"'")
    if not value:
        return None
    if value.startswith("./"):
        value = value[2:]
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    parts = candidate.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return None
    return candidate.as_posix()


def _derive_plugin_interface_assets(
    repo_root: Path,
    inventory_path: Path,
    skills: list[str],
) -> tuple[str | None, str | None]:
    icon_pattern = re.compile(r"^\s*(icon_small|icon_large):\s*(.+?)\s*$")

    for skill_name in skills:
        skill_path = plugin_skill_source_path(repo_root, inventory_path, skill_name)
        openai_yaml = skill_path / "agents" / "openai.yaml"
        if not openai_yaml.is_file():
            continue

        composer_icon: str | None = None
        logo: str | None = None
        for line in openai_yaml.read_text(encoding="utf-8").splitlines():
            match = icon_pattern.match(line)
            if not match:
                continue
            normalized = _normalize_skill_asset_reference(match.group(2))
            if not normalized:
                continue
            if not (skill_path / normalized).is_file():
                continue
            runtime_path = f"./skills/{skill_path.name}/{normalized}"
            if match.group(1) == "icon_small" and composer_icon is None:
                composer_icon = runtime_path
            if match.group(1) == "icon_large" and logo is None:
                logo = runtime_path
        if composer_icon or logo:
            return composer_icon, logo

    return None, None


def _inventory_plugin_tables(inventory_payload: dict[str, Any], inventory_path: Path) -> dict[str, dict[str, Any]]:
    plugins = inventory_payload.get("plugins")
    if not isinstance(plugins, dict) or not plugins:
        fail(f"{inventory_path} must declare a non-empty plugins object")
    entries: dict[str, dict[str, Any]] = {}
    for bundle_name, payload in plugins.items():
        if not isinstance(bundle_name, str) or not PLUGINS_BUNDLE_PATTERN.fullmatch(bundle_name):
            fail(f"{inventory_path} plugin name is invalid: {bundle_name}")
        if not isinstance(payload, dict):
            fail(f"{inventory_path} plugin entry must be an object for {bundle_name}")
        entries[bundle_name] = payload
    return entries


def _inventory_shared_mcp_refs(inventory_payload: dict[str, Any], inventory_path: Path) -> list[str]:
    shared_mcp = inventory_payload.get("shared_mcp", {})
    if shared_mcp in (None, {}):
        return []
    if not isinstance(shared_mcp, dict):
        fail(f"{inventory_path} shared_mcp must be an object")
    refs = shared_mcp.get("refs", [])
    if not isinstance(refs, list):
        fail(f"{inventory_path} shared_mcp.refs must be a list")
    out: list[str] = []
    seen: set[str] = set()
    for raw_ref in refs:
        ref = str(raw_ref).strip()
        if not PLUGINS_BUNDLE_PATTERN.fullmatch(ref):
            fail(f"{inventory_path} shared_mcp ref is invalid: {ref}")
        if ref in seen:
            continue
        seen.add(ref)
        out.append(ref)
    return out


def _user_plugin_settings(
    user_plugins_payload: dict[str, Any],
    user_plugins_path: Path,
    *,
    bundle_names: set[str],
    marketplace_name: str,
) -> dict[str, bool]:
    expected_ids = {f"{bundle_name}@{marketplace_name}" for bundle_name in bundle_names}
    settings: dict[str, bool] = {plugin_id: False for plugin_id in expected_ids}

    plugins_table = user_plugins_payload.get("plugins")
    if plugins_table in (None, {}):
        return settings
    if not isinstance(plugins_table, dict):
        fail(f"{user_plugins_path} plugins must be an object when present")

    configured_ids = {str(plugin_id).strip() for plugin_id in plugins_table.keys()}
    extra = sorted(configured_ids - expected_ids)
    if extra:
        fail(f"{user_plugins_path} declares unknown plugin ids: {', '.join(extra)}")

    for plugin_id, payload in plugins_table.items():
        if plugin_id not in settings:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("enabled"), bool):
            settings[plugin_id] = payload["enabled"]
            continue
        if isinstance(payload, bool):
            settings[plugin_id] = payload
            continue
        fail(f"{user_plugins_path} plugin entry must be a boolean or an object with boolean enabled: {plugin_id}")
    return settings


def _plugin_apps(bundle_name: str, payload: dict[str, Any], inventory_path: Path) -> list[PluginAppSpec]:
    raw_apps = payload.get("apps", [])
    if raw_apps in (None, {}):
        raw_apps = []
    if not isinstance(raw_apps, list):
        fail(f"{inventory_path} plugin.apps must be a list for {bundle_name}")
    apps: list[PluginAppSpec] = []
    seen: set[str] = set()
    for raw_app in raw_apps:
        if isinstance(raw_app, str):
            app_name = raw_app.strip()
            app_id = app_name
        elif isinstance(raw_app, dict):
            app_name = str(raw_app.get("name", "")).strip()
            app_id = str(raw_app.get("id", app_name)).strip()
        else:
            fail(f"{inventory_path} plugin.apps must contain strings or objects for {bundle_name}")
        if not PLUGINS_BUNDLE_PATTERN.fullmatch(app_name):
            fail(f"{inventory_path} app name is invalid for {bundle_name}: {app_name}")
        if not app_id:
            fail(f"{inventory_path} app id is required for {bundle_name}: {app_name}")
        if app_name in seen:
            fail(f"{inventory_path} duplicate app name for {bundle_name}: {app_name}")
        seen.add(app_name)
        apps.append(PluginAppSpec(name=app_name, app_id=app_id))
    return apps


def _plugin_mcp_servers(
    bundle_name: str,
    payload: dict[str, Any],
    inventory_path: Path,
    shared_mcp_servers: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    raw_mcp = payload.get("mcp", [])
    if not isinstance(raw_mcp, list):
        fail(f"{inventory_path} plugin.mcp must be a list for {bundle_name}")

    servers: dict[str, dict[str, Any]] = {}
    for entry in raw_mcp:
        if isinstance(entry, str):
            server_name = entry.strip()
            server = shared_mcp_servers.get(server_name)
            if not isinstance(server, dict):
                fail(f"{inventory_path} plugin.mcp references unknown MCP server for {bundle_name}: {server_name}")
            continue
        elif isinstance(entry, dict):
            server_name = str(entry.get("name", "")).strip()
            payload_copy = dict(entry)
            payload_copy.pop("name", None)
        else:
            fail(f"{inventory_path} plugin.mcp must contain strings or objects for {bundle_name}")

        if not PLUGINS_BUNDLE_PATTERN.fullmatch(server_name):
            fail(f"{inventory_path} MCP server name is invalid for {bundle_name}: {server_name}")
        if server_name in servers:
            fail(f"{inventory_path} duplicate MCP server for {bundle_name}: {server_name}")
        if isinstance(payload_copy.get("url"), str) and payload_copy.get("url"):
            ensure_https_url(f"plugin bundle {bundle_name} MCP server {server_name} url", payload_copy["url"])
        elif isinstance(payload_copy.get("command"), str) and payload_copy.get("command"):
            pass
        else:
            fail(f"{inventory_path} MCP server must define url or command for {bundle_name}: {server_name}")
        payload_copy.pop("enabled", None)
        servers[server_name] = payload_copy
    return servers


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    rendered: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            fail(f"{label} must contain non-empty strings")
        rendered.append(item.strip())
    return rendered


def _required_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be a string")
    rendered = value.strip()
    if not rendered:
        fail(f"{label} is required")
    return rendered


def _required_string_warn_truncate(value: Any, *, label: str, max_length: int) -> str:
    rendered = _required_string(value, label=label)
    if len(rendered) > max_length:
        _warn(f"{label} exceeds {max_length} characters; truncating to fit runtime limit")
        rendered = rendered[:max_length].rstrip()
    return rendered


def _default_prompt_values(value: Any, *, label: str) -> list[str]:
    if value in (None, ""):
        return []

    if isinstance(value, str):
        values = [_required_string_warn_truncate(value, label=label, max_length=DEFAULT_PROMPT_MAX_CHARS)]
    elif isinstance(value, list):
        values = []
        for index, item in enumerate(value):
            values.append(
                _required_string_warn_truncate(
                    item,
                    label=f"{label}[{index}]",
                    max_length=DEFAULT_PROMPT_MAX_CHARS,
                )
            )
    else:
        fail(f"{label} must be a string or a list of strings")

    if len(values) > DEFAULT_PROMPT_MAX_ITEMS:
        _warn(f"{label} exceeds {DEFAULT_PROMPT_MAX_ITEMS} entries; truncating to fit runtime limit")
        values = values[:DEFAULT_PROMPT_MAX_ITEMS]
    return values


def _optional_string(value: Any, *, label: str) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        fail(f"{label} must be a string")
    rendered = value.strip()
    return rendered or None


def _optional_https_url(value: Any, *, label: str) -> str | None:
    rendered = _optional_string(value, label=label)
    if rendered is None:
        return None
    ensure_https_url(label, rendered)
    return rendered


def _required_https_url(value: Any, *, label: str) -> str:
    rendered = _required_string(value, label=label)
    ensure_https_url(label, rendered)
    return rendered


def _optional_hex_color(value: Any, *, label: str) -> str | None:
    rendered = _optional_string(value, label=label)
    if rendered is None:
        return None
    if not HEX_COLOR_PATTERN.fullmatch(rendered):
        fail(f"{label} must be a #RRGGBB hex color")
    return rendered


def plugin_manifest_bundles(
    repo_root: Path,
    plugins_payload: dict[str, Any],
    plugins_path: Path,
    plugins_metadata_payload: dict[str, Any],
    plugins_metadata_path: Path,
    shared_mcp_servers: dict[str, Any],
    *,
    enabled_only: bool,
) -> list[PluginBundleSpec]:
    if not plugins_payload:
        return []
    marketplace_name = plugin_manifest_marketplace_name(plugins_metadata_payload, plugins_metadata_path)
    inventory_entries = _inventory_plugin_tables(plugins_metadata_payload, plugins_metadata_path)
    shared_mcp_refs = _inventory_shared_mcp_refs(plugins_metadata_payload, plugins_metadata_path)
    for server_name in shared_mcp_refs:
        if not isinstance(shared_mcp_servers.get(server_name), dict):
            fail(f"{plugins_metadata_path} shared_mcp references unknown MCP server: {server_name}")
    plugin_settings = _user_plugin_settings(
        plugins_payload,
        plugins_path,
        bundle_names=set(inventory_entries.keys()),
        marketplace_name=marketplace_name,
    )

    seen_skill_names: set[str] = set()
    entries: list[PluginBundleSpec] = []
    for bundle_name, payload in inventory_entries.items():
        name_value = _required_string(
            payload.get("name"),
            label=f"{plugins_metadata_path} plugin.name for {bundle_name}",
        )
        if name_value != bundle_name:
            fail(f"{plugins_metadata_path} plugin.name must match plugin key for {bundle_name}")

        description = _required_string(
            payload.get("description"),
            label=f"{plugins_metadata_path} plugin.description for {bundle_name}",
        )
        category = _required_string(
            payload.get("category"),
            label=f"{plugins_metadata_path} plugin.category for {bundle_name}",
        )

        raw_skills = payload.get("skills", [])
        skills = _string_list(raw_skills, label=f"{plugins_metadata_path} plugin.skills for {bundle_name}")
        for skill_source in skills:
            skill_path = plugin_skill_source_path(repo_root, plugins_metadata_path, skill_source)
            if skill_path.name in seen_skill_names:
                fail(f"{plugins_metadata_path} plugin skill is bundled more than once: {skill_path.name}")
            seen_skill_names.add(skill_path.name)

        author = payload.get("author", {})
        if author in (None, {}):
            author = {}
        if not isinstance(author, dict):
            fail(f"{plugins_metadata_path} plugin.author must be an object for {bundle_name}")

        interface = payload.get("interface", {})
        if not isinstance(interface, dict):
            fail(f"{plugins_metadata_path} plugin.interface must be an object for {bundle_name}")
        derived_composer_icon, derived_logo = _derive_plugin_interface_assets(
            repo_root,
            plugins_metadata_path,
            skills,
        )
        display_name = _required_string(
            interface.get("display_name"),
            label=f"{plugins_metadata_path} plugin.interface.display_name for {bundle_name}",
        )
        short_description = _required_string(
            interface.get("short_description"),
            label=f"{plugins_metadata_path} plugin.interface.short_description for {bundle_name}",
        )
        default_prompt = _default_prompt_values(
            interface.get("default_prompt"),
            label=f"{plugins_metadata_path} plugin.interface.default_prompt for {bundle_name}",
        )
        capabilities = _string_list(interface.get("capabilities", []), label=f"{plugins_metadata_path} plugin.interface.capabilities for {bundle_name}")
        for capability in capabilities:
            if capability not in INTERFACE_CAPABILITY_VALUES:
                fail(
                    f"{plugins_metadata_path} plugin.interface.capabilities for {bundle_name} "
                    f"contains unsupported capability: {capability}"
                )

        apps = _plugin_apps(bundle_name, payload, plugins_metadata_path)
        mcp_servers = _plugin_mcp_servers(
            bundle_name,
            payload,
            plugins_metadata_path,
            shared_mcp_servers,
        )
        if apps and "Interactive" not in capabilities:
            fail(
                f"{plugins_metadata_path} plugin.interface.capabilities for {bundle_name} "
                "must include Interactive when apps are declared"
            )
        if not skills and not apps and not mcp_servers:
            fail(f"{plugins_metadata_path} plugin {bundle_name} must declare at least one of skills, apps, or mcp")

        plugin_id = f"{bundle_name}@{marketplace_name}"
        enabled = plugin_settings[plugin_id]
        if enabled_only and not enabled:
            continue

        hook_file = _optional_string(
            payload.get("hooks"),
            label=f"{plugins_metadata_path} plugin.hooks for {bundle_name}",
        )
        if hook_file is not None:
            normalized_hook_file, source_hook_path = plugin_hook_source_path(
                repo_root,
                plugins_metadata_path,
                bundle_name,
                hook_file,
            )
            validate_plugin_hook_file(
                repo_root,
                plugins_metadata_path,
                bundle_name,
                source_hook_path,
            )
            hook_file = f"./{normalized_hook_file}"

        entries.append(
            PluginBundleSpec(
                name=bundle_name,
                plugin_id=plugin_id,
                enabled=enabled,
                plugin_version=_optional_string(
                    payload.get("plugin_version"),
                    label=f"{plugins_metadata_path} plugin.plugin_version for {bundle_name}",
                )
                or DEFAULT_PLUGIN_VERSION,
                description=description,
                homepage=_required_https_url(
                    payload.get("homepage"),
                    label=f"{plugins_metadata_path} plugin.homepage for {bundle_name}",
                ),
                repository=_required_https_url(
                    payload.get("repository"),
                    label=f"{plugins_metadata_path} plugin.repository for {bundle_name}",
                ),
                license_name=_optional_string(
                    payload.get("license"),
                    label=f"{plugins_metadata_path} plugin.license for {bundle_name}",
                ),
                keywords=_string_list(payload.get("keywords", []), label=f"{plugins_metadata_path} plugin.keywords for {bundle_name}"),
                author_name=_optional_string(
                    author.get("name"),
                    label=f"{plugins_metadata_path} plugin.author.name for {bundle_name}",
                ),
                author_email=_optional_string(
                    author.get("email"),
                    label=f"{plugins_metadata_path} plugin.author.email for {bundle_name}",
                ),
                author_url=_optional_https_url(
                    author.get("url"),
                    label=f"{plugins_metadata_path} plugin.author.url for {bundle_name}",
                ),
                hooks_file=hook_file,
                display_name=display_name,
                short_description=short_description,
                long_description=_optional_string(
                    interface.get("long_description"),
                    label=f"{plugins_metadata_path} plugin.interface.long_description for {bundle_name}",
                ),
                developer_name=_optional_string(
                    interface.get("developer_name"),
                    label=f"{plugins_metadata_path} plugin.interface.developer_name for {bundle_name}",
                ),
                category=category,
                capabilities=capabilities,
                default_prompt=default_prompt,
                brand_color=_optional_hex_color(
                    interface.get("brand_color"),
                    label=f"{plugins_metadata_path} plugin.interface.brand_color for {bundle_name}",
                ),
                website_url=_optional_https_url(
                    interface.get("website_url"),
                    label=f"{plugins_metadata_path} plugin.interface.website_url for {bundle_name}",
                ),
                privacy_policy_url=_optional_https_url(
                    interface.get("privacy_policy_url"),
                    label=f"{plugins_metadata_path} plugin.interface.privacy_policy_url for {bundle_name}",
                ),
                terms_of_service_url=_optional_https_url(
                    interface.get("terms_of_service_url"),
                    label=f"{plugins_metadata_path} plugin.interface.terms_of_service_url for {bundle_name}",
                ),
                composer_icon=_optional_string(
                    interface.get("composer_icon"),
                    label=f"{plugins_metadata_path} plugin.interface.composer_icon for {bundle_name}",
                )
                or derived_composer_icon,
                logo=_optional_string(
                    interface.get("logo"),
                    label=f"{plugins_metadata_path} plugin.interface.logo for {bundle_name}",
                )
                or derived_logo,
                screenshots=_string_list(interface.get("screenshots", []), label=f"{plugins_metadata_path} plugin.interface.screenshots for {bundle_name}") if "screenshots" in interface else [],
                skills=skills,
                mcp_servers=mcp_servers,
                apps=apps,
            )
        )
    return entries


def validate_plugin_bundle_inventory(installer: Any, source_root: Path) -> list[PluginBundleSpec]:
    all_entries = plugin_manifest_bundles(
        repo_root=installer.repo_root,
        plugins_payload=installer.plugins_payload,
        plugins_path=installer.plugins_path,
        plugins_metadata_payload=installer.effective_plugins_metadata_payload,
        plugins_metadata_path=installer.plugins_json_path,
        shared_mcp_servers=installer.mcp_payload.get("mcp_servers", {}),
        enabled_only=False,
    )
    referenced_skill_names = {skill_name for entry in all_entries for skill_name in entry.skills}
    actual_skill_names = set(local_plugin_bundle_dirs(source_root))
    missing = sorted(referenced_skill_names - actual_skill_names)
    extra = sorted(actual_skill_names - referenced_skill_names)
    if missing:
        fail(f"{installer.plugins_json_path} references missing plugin skills: {', '.join(missing)}")
    if extra:
        fail(f"{installer.plugins_json_path} leaves plugin skills unbundled: {', '.join(extra)}")
    for skill_name in sorted(actual_skill_names):
        validate_plugin_skill_metadata(source_root / skill_name)
    return all_entries


def sync_runtime_plugin_bundle(installer: Any, source_root: Path, target_root: Path, bundle: PluginBundleSpec) -> None:
    installer._mkdir_path(target_root)
    plugin_dir = target_root / ".codex-plugin"
    installer._mkdir_path(plugin_dir)
    runtime_skills_dir = target_root / "skills"
    installer._mkdir_path(runtime_skills_dir)
    previous_manifest_path = plugin_dir / "plugin.json"
    previous_hooks_path: Path | None = None
    if previous_manifest_path.is_file():
        try:
            previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous_manifest = {}
        previous_hooks = previous_manifest.get("hooks")
        normalized_previous = _normalize_skill_asset_reference(previous_hooks) if isinstance(previous_hooks, str) else None
        if normalized_previous:
            previous_hooks_path = target_root / normalized_previous

    existing_skill_dirs = {path.name for path in runtime_skills_dir.iterdir() if path.is_dir()} if runtime_skills_dir.exists() else set()
    desired_skill_dirs = {plugin_skill_source_path(installer.repo_root, installer.plugins_json_path, skill_source).name for skill_source in bundle.skills}
    for dirname in sorted(existing_skill_dirs - desired_skill_dirs):
        installer._remove_path_force(runtime_skills_dir / dirname)

    for skill_source in bundle.skills:
        skill_path = plugin_skill_source_path(installer.repo_root, installer.plugins_json_path, skill_source)
        target_skill_dir = runtime_skills_dir / skill_path.name
        installer._sync_tree(skill_path, target_skill_dir, mirror_deletions=True)

    rewrite_runtime_plugin_skill_dependencies(
        runtime_skills_dir,
        bundle,
        installer.effective_plugins_metadata_payload,
        installer.mcp_payload,
        dry_run=installer.dry_run,
    )

    installer._write_file(plugin_dir / "plugin.json", render_runtime_plugin_manifest(bundle))
    if bundle.hooks_file:
        normalized_hooks_path, source_hooks_path = plugin_hook_source_path(
            installer.repo_root,
            installer.plugins_json_path,
            bundle.name,
            bundle.hooks_file,
        )
        if previous_hooks_path is not None and previous_hooks_path != target_root / normalized_hooks_path:
            installer._remove_path_force(previous_hooks_path)
        installer._copy_file(source_hooks_path, target_root / normalized_hooks_path, mode=0o644)
    elif previous_hooks_path is not None:
        installer._remove_path_force(previous_hooks_path)
    if bundle.mcp_servers:
        installer._write_file(target_root / ".mcp.json", render_runtime_plugin_mcp(bundle))
    else:
        installer._remove_path_force(target_root / ".mcp.json")
    if bundle.apps:
        installer._write_file(target_root / ".app.json", render_runtime_plugin_apps(bundle))
    else:
        installer._remove_path_force(target_root / ".app.json")


def sync_local_plugins(installer: Any) -> None:
    source_root = installer._plugins_source_dir()
    runtime_plugins_dir = installer._runtime_plugins_dir()
    runtime_marketplace_path = installer._runtime_plugin_marketplace_path()

    installer._mkdir_path(runtime_plugins_dir)
    installer._mkdir_path(runtime_marketplace_path.parent)
    all_entries = validate_plugin_bundle_inventory(installer, source_root)
    active_entries = [entry for entry in all_entries if entry.enabled]
    marketplace_name = plugin_manifest_marketplace_name(installer.effective_plugins_metadata_payload, installer.plugins_json_path)
    bundle_dirs = {entry.name for entry in active_entries}
    runtime_marketplace_plugins_dir = runtime_plugins_dir / marketplace_name

    installer._mkdir_path(runtime_marketplace_plugins_dir)
    if runtime_marketplace_plugins_dir.exists():
        for child in sorted(runtime_marketplace_plugins_dir.iterdir(), key=lambda item: item.name):
            if child.name not in bundle_dirs:
                installer._remove_path_force(child)

    for bundle in active_entries:
        sync_runtime_plugin_bundle(
            installer,
            source_root,
            runtime_marketplace_plugins_dir / bundle.name / "local",
            bundle,
        )

    installer._write_file(
        runtime_marketplace_path,
        render_runtime_plugin_marketplace(marketplace_name, active_entries),
    )
