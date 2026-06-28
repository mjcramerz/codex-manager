from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common import ensure_safe_absolute_path


@dataclass(frozen=True)
class RepoLayout:
    repo_root: Path
    config_dir: Path
    profiles_config_dir: Path
    agents_config_dir: Path
    vendor_dir: Path
    user_dir: Path
    resources_dir: Path
    home_dir: Path
    home_user_dir: Path
    hooks_dir: Path
    hooks_scripts_dir: Path
    hooks_manifest_path: Path
    instructions_dir: Path
    instructions_default_metadata_path: Path
    instructions_agents_metadata_path: Path
    instructions_profiles_metadata_path: Path
    skills_dir: Path
    skills_metadata_path: Path
    plugins_dir: Path
    plugins_inventory_path: Path
    plugins_skills_dir: Path
    vendor_config_path: Path
    vendor_providers_path: Path
    vendor_pref_path: Path
    vendor_policy_path: Path
    vendor_mcp_path: Path
    vendor_requirements_path: Path
    user_config_path: Path
    user_features_path: Path
    user_memory_path: Path
    user_pref_path: Path
    user_env_path: Path
    user_apps_path: Path
    user_policy_path: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> "RepoLayout":
        config_dir = repo_root / "config"
        profiles_config_dir = config_dir / "profiles"
        agents_config_dir = config_dir / "agents"
        vendor_dir = config_dir / "vendor"
        user_dir = config_dir / "usr"
        resources_dir = repo_root / "resources"
        home_dir = resources_dir / "home"
        hooks_dir = resources_dir / "hooks"
        instructions_dir = resources_dir / "instructions"
        skills_dir = resources_dir / "skills"
        plugins_dir = resources_dir / "plugins"
        return cls(
            repo_root=repo_root,
            config_dir=config_dir,
            profiles_config_dir=profiles_config_dir,
            agents_config_dir=agents_config_dir,
            vendor_dir=vendor_dir,
            user_dir=user_dir,
            resources_dir=resources_dir,
            home_dir=home_dir,
            home_user_dir=home_dir / "user",
            hooks_dir=hooks_dir,
            hooks_scripts_dir=hooks_dir / "scripts",
            hooks_manifest_path=hooks_dir / "hooks.json",
            instructions_dir=instructions_dir,
            instructions_default_metadata_path=instructions_dir / "default" / "metadata.json",
            instructions_agents_metadata_path=instructions_dir / "agents" / "metadata.json",
            instructions_profiles_metadata_path=instructions_dir / "profiles" / "metadata.json",
            skills_dir=skills_dir,
            skills_metadata_path=skills_dir / "metadata.json",
            plugins_dir=plugins_dir,
            plugins_inventory_path=plugins_dir / "manifest.json",
            plugins_skills_dir=plugins_dir / "skills",
            vendor_config_path=vendor_dir / "config.toml",
            vendor_providers_path=vendor_dir / "providers.toml",
            vendor_pref_path=vendor_dir / "pref.toml",
            vendor_policy_path=vendor_dir / "policy.toml",
            vendor_mcp_path=vendor_dir / "mcp.toml",
            vendor_requirements_path=vendor_dir / "requirements.toml",
            user_config_path=user_dir / "config.toml",
            user_features_path=user_dir / "features.toml",
            user_memory_path=user_dir / "memory.toml",
            user_pref_path=user_dir / "pref.toml",
            user_env_path=user_dir / "env.toml",
            user_apps_path=user_dir / "apps.toml",
            user_policy_path=user_dir / "policy.toml",
        )


@dataclass(frozen=True)
class RuntimeLayout:
    home_dir: Path
    home_config_path: Path
    hooks_dir: Path
    hooks_config_path: Path
    agents_dir: Path
    agent_skills_path: Path
    skills_dir: Path
    system_dir: Path
    system_config_path: Path
    system_requirements_path: Path
    system_skills_dir: Path
    instructions_dir: Path
    plugin_cache_dir: Path
    plugin_marketplace_dir: Path
    plugin_marketplace_path: Path

    @classmethod
    def from_env(cls, env: dict[str, str], runtime_vars: dict[str, str]) -> "RuntimeLayout":
        home_dir = ensure_safe_absolute_path("CODEX_HOME", runtime_vars["CODEX_HOME"])
        agents_dir = ensure_safe_absolute_path("CODEX_AGENTS", runtime_vars["CODEX_AGENTS"])
        skills_dir = ensure_safe_absolute_path("CODEX_SKILLS", runtime_vars["CODEX_SKILLS"])
        system_dir = ensure_safe_absolute_path("CODEX_SYSTEM_DIR", env["CODEX_SYSTEM_DIR"])
        return cls(
            home_dir=home_dir,
            home_config_path=home_dir / "config.toml",
            hooks_dir=home_dir / ".hooks",
            hooks_config_path=home_dir / "hooks.json",
            agents_dir=agents_dir,
            agent_skills_path=home_dir / ".agents" / "skills",
            skills_dir=skills_dir,
            system_dir=system_dir,
            system_config_path=system_dir / "config.toml",
            system_requirements_path=system_dir / "requirements.toml",
            system_skills_dir=system_dir / "skills",
            instructions_dir=ensure_safe_absolute_path("CODEX_USER_DIR", env["CODEX_USER_DIR"]) / "instructions",
            plugin_cache_dir=home_dir / "plugins" / "cache",
            plugin_marketplace_dir=home_dir / ".agents" / "plugins",
            plugin_marketplace_path=home_dir / ".agents" / "plugins" / "marketplace.json",
        )
