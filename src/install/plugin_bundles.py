from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PluginAppSpec:
    name: str
    app_id: str


@dataclass(frozen=True)
class PluginBundleSpec:
    name: str
    plugin_id: str
    enabled: bool
    plugin_version: str | None
    description: str
    homepage: str | None
    repository: str | None
    license_name: str | None
    keywords: list[str]
    author_name: str | None
    author_email: str | None
    author_url: str | None
    hooks_file: str | None
    display_name: str
    short_description: str
    long_description: str | None
    developer_name: str | None
    category: str
    capabilities: list[str]
    default_prompt: list[str]
    brand_color: str | None
    website_url: str | None
    privacy_policy_url: str | None
    terms_of_service_url: str | None
    composer_icon: str | None
    logo: str | None
    screenshots: list[str]
    skills: list[str]
    mcp_servers: dict[str, dict[str, Any]]
    apps: list[PluginAppSpec]

    def interface_capabilities(self) -> list[str]:
        return self.capabilities


def render_runtime_plugin_marketplace(
    marketplace_name: str,
    entries: list[PluginBundleSpec],
) -> str:
    def _marketplace_interface(entry: PluginBundleSpec) -> dict[str, Any]:
        interface: dict[str, Any] = {
            "displayName": entry.display_name,
            "shortDescription": entry.short_description,
            "longDescription": entry.long_description,
            "developerName": entry.developer_name,
            "category": entry.category,
            "capabilities": entry.interface_capabilities(),
            "defaultPrompt": entry.default_prompt or None,
            "brandColor": entry.brand_color,
        }
        website_url = entry.website_url or entry.homepage
        if website_url:
            interface["websiteURL"] = website_url
        if entry.privacy_policy_url:
            interface["privacyPolicyURL"] = entry.privacy_policy_url
        if entry.terms_of_service_url:
            interface["termsOfServiceURL"] = entry.terms_of_service_url
        if entry.composer_icon:
            interface["composerIcon"] = entry.composer_icon
        if entry.logo:
            interface["logo"] = entry.logo
        if entry.screenshots:
            interface["screenshots"] = entry.screenshots
        return interface

    payload = {
        "name": marketplace_name,
        "plugins": [
            {
                "name": entry.name,
                "source": {
                    "source": "local",
                    "path": f"./plugins/cache/{marketplace_name}/{entry.name}/local",
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL" if entry.apps else "ON_USE",
                },
                "category": entry.category,
                "description": entry.description,
                "interface": _marketplace_interface(entry),
            }
            for entry in entries
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_runtime_plugin_manifest(bundle: PluginBundleSpec) -> str:
    interface: dict[str, Any] = {
        "displayName": bundle.display_name,
        "shortDescription": bundle.short_description,
        "category": bundle.category,
        "capabilities": bundle.interface_capabilities(),
        "defaultPrompt": bundle.default_prompt,
    }
    if bundle.long_description:
        interface["longDescription"] = bundle.long_description
    if bundle.developer_name:
        interface["developerName"] = bundle.developer_name
    if bundle.brand_color:
        interface["brandColor"] = bundle.brand_color
    website_url = bundle.website_url or bundle.homepage
    if website_url:
        interface["websiteURL"] = website_url
    if bundle.privacy_policy_url:
        interface["privacyPolicyURL"] = bundle.privacy_policy_url
    if bundle.terms_of_service_url:
        interface["termsOfServiceURL"] = bundle.terms_of_service_url
    if bundle.composer_icon:
        interface["composerIcon"] = bundle.composer_icon
    if bundle.logo:
        interface["logo"] = bundle.logo
    if bundle.default_prompt:
        interface["defaultPrompt"] = bundle.default_prompt
    interface["screenshots"] = bundle.screenshots

    payload: dict[str, Any] = {
        "name": bundle.name,
        "version": bundle.plugin_version or "1.0.0",
        "description": bundle.description,
        "skills": "./skills",
        "interface": interface,
    }
    author: dict[str, Any] = {"name": bundle.author_name or "Codex Setup"}
    if bundle.author_email:
        author["email"] = bundle.author_email
    if bundle.author_url:
        author["url"] = bundle.author_url
    payload["author"] = author
    if bundle.homepage:
        payload["homepage"] = bundle.homepage
    if bundle.repository:
        payload["repository"] = bundle.repository
    if bundle.license_name:
        payload["license"] = bundle.license_name
    if bundle.keywords:
        payload["keywords"] = bundle.keywords
    if bundle.hooks_file:
        payload["hooks"] = bundle.hooks_file
    if bundle.mcp_servers:
        payload["mcpServers"] = "./.mcp.json"
    if bundle.apps:
        payload["apps"] = "./.app.json"
    return json.dumps(payload, indent=2) + "\n"


def render_runtime_plugin_mcp(bundle: PluginBundleSpec) -> str:
    return json.dumps({"mcpServers": bundle.mcp_servers}, indent=2) + "\n"


def render_runtime_plugin_apps(bundle: PluginBundleSpec) -> str:
    return json.dumps({"apps": {app.name: {"id": app.app_id} for app in bundle.apps}}, indent=2) + "\n"
