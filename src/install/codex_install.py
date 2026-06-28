#!/usr/bin/env python3
"""Codex installer.

This installer compiles runtime outputs from repository configuration:
- .env
- vars.toml
- config/vendor/*
- config/usr/*
- resources/*/metadata.json
- resources/plugins/manifest.json
- resources/hooks/*
"""

from __future__ import annotations

import argparse
import copy
import filecmp
import getpass
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SRC = Path(__file__).resolve().parent
PYTHON_SRC = REPO_ROOT / "src" / "python"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lib.pycache_bootstrap import bootstrap_pycache_prefix

bootstrap_pycache_prefix()

from common import InstallError
from common import _first_unresolved_codex_placeholder_outside_toml_multiline_strings
from common import _replace_known_placeholders_outside_toml_multiline_strings
from common import _toml_multiline_string_spans
from common import ensure_gitlab_url
from common import ensure_safe_absolute_path
from common import ensure_safe_shell_export_value
from common import ensure_sha256
from common import fail
from common import is_within
from common import normalize_path
from common import parse_env_file
from common import parse_json_file
from common import parse_toml_file
from common import parse_variable_table
from common import replace_known_placeholders_in_text
from common import resolve_object_placeholders
from common import resolve_placeholders
from common import toml_key
from common import toml_value
from config_merge import compile_vendor_config
from hooks_builder import validate_hooks_config
from layout import RepoLayout
from layout import RuntimeLayout
from plugin_bundles import PluginBundleSpec
from plugin_bundles import render_runtime_plugin_marketplace
from plugin_bundles import runtime_marketplace_source_path
from apps_config import effective_plugins_inventory_payload
from agent_role_contracts import validate_agent_role_contracts
from lib.fs_ops import needs_sudo_remove, needs_sudo_write
from lib.managed_secrets import ManagedSecretsConfig
from lib.managed_secrets import ManagedSecretsError
from lib.managed_secrets import SECRETS_FILENAME
from lib.managed_secrets import clear_managed_secret
from lib.managed_secrets import lookup_managed_secret
from lib.managed_secrets import managed_secret_mcp_env_map
from lib.managed_secrets import managed_secret_supported_mcp_env_map
from lib.managed_secrets import parse_managed_secrets_file
from lib.managed_secrets import secret_tool_available
from lib.managed_secrets import store_managed_secret
from lib.codex_login_auth import AUTH_FILENAME
from lib.codex_login_auth import CodexLoginAuthError
from lib.codex_login_auth import parse_login_auth_file
from lib.release_assets import ReleaseAssetError, discover_release_binaries
from lib.runtime import (
    RuntimeRenderError,
    derive_runtime_globals_from_env,
    render_codex_shim,
    render_shell_export_block,
    render_shell_path_profile,
    render_wrapper_aliases,
)
from lib.tar_utils import ArchiveSafetyError, safe_extractall
from plugins import PLUGINS_BUNDLE_PATTERN
from plugins import PLUGINS_MANIFEST_VERSION
from plugins import PLUGINS_MARKETPLACE_PATTERN
from plugins import local_plugin_bundle_dirs
from plugins import plugin_manifest_bundles
from plugins import plugin_manifest_marketplace_name
from plugins import plugin_skill_source_path
from plugins import sync_local_plugins
from plugins import sync_runtime_plugin_bundle
from plugins import validate_plugin_bundle_inventory
from skills import render_dependency_block
from skills import iter_skill_groups
from skills import rewrite_openai_yaml_dependencies
from skills import role_tools_from_skills
from skills import runtime_skill_roles_by_dirname
from skills import validate_openai_yaml_mcp_dependencies
from source_build import SourceBuildError
from source_build import build_from_settings
from source_build import load_source_build_environment
from source_build import load_source_build_settings

ENV_REQUIRED = (
    "CODEX_ROOT_DIR",
    "CODEX_SYSTEM_DIR",
    "CODEX_USER_DIR",
    "CODEX_SHARE_DIR",
    "CODEX_WRAPPER_DIR",
    "CODEX_MCP_DIR",
    "CODEX_BACKUP_DIR",
    "CODEX_DOWNLOAD_URL",
    "CODEX_DOWNLOAD_SHA",
    "CODEX_DOWNLOAD_PKG",
    "CODEX_INSTALL_DEBIAN_PACKAGES",
)

ENV_ROOT_KEYS = (
    "CODEX_ROOT_DIR",
    "CODEX_SYSTEM_DIR",
    "CODEX_USER_DIR",
    "CODEX_SHARE_DIR",
    "CODEX_MCP_DIR",
    "CODEX_BACKUP_DIR",
)

RUNTIME_REQUIRED = (
    "CODEX_HOME",
    "CODEX_AGENTS",
    "CODEX_SKILLS",
    "CODEX_LOG_DIR",
    "CODEX_SQLITE_HOME",
)
GLOBAL_EXPORT_REQUIRED = (
    "CODEX_HOME",
    "CODEX_AGENTS",
    "CODEX_SKILLS",
    "CODEX_SQLITE_HOME",
    "CODEX_LOG_DIR",
)
GLOBAL_EXPORT_PATH_KEYS = GLOBAL_EXPORT_REQUIRED
WRAPPER_ALIASES_FILENAME = "codex-wrapper-aliases.sh"
CODEX_LOGIN_WRAPPER_NAME = "codex-login"
CODEX_MCP_TOKEN_WRAPPER_NAME = "codex-mcp-token"
DEBIAN_PACKAGE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")

SCHEMA_TOOL_SOURCE_FILENAME = "codex_schema_tool.py"
SCHEMA_HELPER_COMMANDS = {
    "codex-schema-newest": "newest",
    "codex-schema-diff": "diff",
}
SCHEMA_HELPER_NAMES = tuple(SCHEMA_HELPER_COMMANDS.keys())
RELEASE_SCHEMA_FILENAME = "config.schema.json"
ENV_PROFILE_FILENAME = "50-codex-user-env.sh"
SHELL_COMPLETION_TARGETS = {
    "bash": Path(".local") / "share" / "bash-completion" / "completions" / "codex",
}

HOME_RUNTIME_PRESERVE_DIRS = ("memories", "sessions", "shell_snapshots")
HOME_RUNTIME_PRESERVE_FILES = (
    ".credentials.json",
    ".personality_migration",
    "history.jsonl",
    "session_index.jsonl",
    "version.json",
)
HOME_FILTER_PRESERVE_DIRS = (*HOME_RUNTIME_PRESERVE_DIRS, "tmp", ".agents", "plugins")
HOME_FILTER_PRESERVE_FILES = (*HOME_RUNTIME_PRESERVE_FILES, "auth.json")
BACKUP_ACCOUNT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9]{8}$")
BACKUP_UNKNOWN_ACCOUNT_KEY = "unknown"
BACKUP_SOURCE_KEY_TO_LABEL = (
    ("CODEX_SQLITE_HOME", "sqlite"),
    ("CODEX_HOME", "home"),
    ("CODEX_SKILLS", "skills"),
    ("CODEX_AGENTS", "agents"),
)
HOME_BACKUP_EXCLUDE_ROOT_CHILDREN = frozenset({"tmp"})
INSTRUCTIONS_MANIFEST_FILENAME = "metadata.json"
USER_APPS_FILENAME = "apps.toml"
PLUGINS_METADATA_FILENAME = "manifest.json"
INSTRUCTIONS_GROUP_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
INSTRUCTIONS_ENTRY_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
INSTRUCTIONS_ENTRY_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
INSTRUCTIONS_ALLOWED_SUFFIXES = {".json", ".lark", ".md", ".xml"}
VERSION_PATTERN = re.compile(r"([0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)*(?:-[A-Za-z0-9._]+)*)")
ENV_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
DRY_RUN_STAGE_ROOT = Path("/data/dryrun/codex")
DRY_RUN_STAGE_ACTIVATE_FILENAME = "activate-codex-env.sh"
STAGE_SOURCE_BUILD_ROOT_KEY = "CODEX_SOURCE_BUILD_ROOT"
STAGE_SOURCE_CACHE_ROOT_KEY = "CODEX_SOURCE_CACHE_ROOT"
STAGE_SOURCE_OUTPUT_DIR_KEY = "CODEX_SOURCE_OUTPUT_DIR"
STAGE_SOURCE_CHECKOUT_DIR_KEY = "CODEX_SOURCE_CHECKOUT_DIR"


def resolve_dry_run_stage_root() -> Path:
    raw = os.environ.get("CODEX_DRY_RUN_STAGE_ROOT", "").strip()
    if not raw:
        return DRY_RUN_STAGE_ROOT
    return ensure_safe_absolute_path("CODEX_DRY_RUN_STAGE_ROOT", raw)


def parse_launch_env_table(
    payload: dict[str, Any],
    *,
    path_label: str,
    variables: dict[str, str],
) -> dict[str, str]:
    table = payload.get("launch_env")
    if table is None:
        return {}
    if not isinstance(table, dict):
        fail(f"{path_label} [launch_env] must be an object")

    parsed: dict[str, str] = {}
    for key, value in table.items():
        if not isinstance(key, str) or not ENV_KEY_PATTERN.fullmatch(key):
            fail(f"invalid launch env key in {path_label}: {key}")
        if not isinstance(value, str):
            fail(f"launch env value must be string in {path_label}: {key}")
        parsed[key] = resolve_placeholders(value.strip(), variables, f"{path_label}.launch_env.{key}")
    return parsed


def ensure_non_root_user() -> None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        fail("run installer as a regular user; it will prompt for sudo only when needed")


@dataclass
class CompiledArtifacts:
    config_toml: Path


class Installer:
    def __init__(self, repo_root: Path, dry_run: bool, *, stage_root: Path | None = None) -> None:
        self.repo_root = repo_root
        self.repo_layout = RepoLayout.from_repo_root(repo_root)
        self.runtime_layout: RuntimeLayout | None = None
        self.dry_run = dry_run
        self.stage_root = stage_root.resolve(strict=False) if stage_root is not None else None
        self.user_home = Path.home()

        self.env_path = repo_root / ".env"
        self.vars_path = repo_root / "vars.toml"
        self.mcp_path = self.repo_layout.vendor_mcp_path
        self.skills_path = self.repo_layout.skills_metadata_path
        self.plugins_path = self.repo_layout.user_apps_path
        self.plugins_json_path = self.repo_layout.plugins_inventory_path
        self.user_env_path = self.repo_layout.user_env_path
        self.sandbox_path = self.repo_layout.user_policy_path
        self.config_path = self.repo_layout.vendor_config_path
        self.requirements_path = self.repo_layout.vendor_requirements_path

        self.env: dict[str, str] = {}
        self.runtime_vars: dict[str, str] = {}
        self.global_vars: dict[str, str] = {}
        self.launch_env: dict[str, str] = {}
        self.variables: dict[str, str] = {}
        self.mcp_payload: dict[str, Any] = {}
        self.skills_payload: dict[str, Any] = {}
        self.plugins_payload: dict[str, Any] = {}
        self.plugins_metadata_payload: dict[str, Any] = {}
        self.effective_plugins_metadata_payload: dict[str, Any] = {}
        self.secrets_config: ManagedSecretsConfig | None = None
        self.allowed_roots: list[Path] = []
        self._keyring_secret_cache: dict[str, str] = {}
        self._warnings_emitted: set[str] = set()

    def _stage_mode(self) -> bool:
        return getattr(self, "stage_root", None) is not None

    def _resolved_stage_root(self) -> Path:
        stage_root = getattr(self, "stage_root", None)
        if stage_root is None:
            fail("staged dry-run root is not configured")
        return stage_root

    def _stage_env_overrides(self) -> dict[str, str]:
        root = self._resolved_stage_root()
        return {
            "CODEX_ROOT_DIR": str(root),
            "CODEX_SYSTEM_DIR": str(root / "etc" / "codex"),
            "CODEX_USER_DIR": str(root / "usr"),
            "CODEX_SHARE_DIR": str(root / "share"),
            "CODEX_WRAPPER_DIR": str(root / "bin"),
            "CODEX_MCP_DIR": str(root / "mcp"),
            "CODEX_BACKUP_DIR": str(root / "backup"),
        }

    def _stage_sqlite_home(self) -> Path:
        return self._resolved_stage_root() / "sqlite"

    def _stage_activation_path(self) -> Path:
        return self._resolved_stage_root() / DRY_RUN_STAGE_ACTIVATE_FILENAME

    def _stage_source_build_overrides(self) -> dict[str, str]:
        root = self._resolved_stage_root() / "source-build"
        return {
            STAGE_SOURCE_BUILD_ROOT_KEY: str(root / "build"),
            STAGE_SOURCE_CACHE_ROOT_KEY: str(root / "cache"),
            STAGE_SOURCE_OUTPUT_DIR_KEY: str(root / "output"),
            STAGE_SOURCE_CHECKOUT_DIR_KEY: str(root / "checkout"),
        }

    def _configure_stage_process_home(self) -> None:
        stage_root = self._resolved_stage_root()
        process_home = stage_root / "process-home"
        for path in (
            process_home,
            process_home / ".cargo",
            process_home / ".rustup",
            process_home / ".cache",
            process_home / ".config",
            process_home / ".local" / "state",
        ):
            self._mkdir_path(path)
        os.environ["HOME"] = str(process_home)
        os.environ["CARGO_HOME"] = str(process_home / ".cargo")
        os.environ["RUSTUP_HOME"] = str(process_home / ".rustup")
        os.environ["XDG_CACHE_HOME"] = str(process_home / ".cache")
        os.environ["XDG_CONFIG_HOME"] = str(process_home / ".config")
        os.environ["XDG_STATE_HOME"] = str(process_home / ".local" / "state")

    def load(self) -> None:
        self.env = parse_env_file(self.env_path)
        if self._stage_mode():
            self.env.update(self._stage_env_overrides())
        vars_payload = parse_toml_file(self.vars_path)
        mcp_payload_raw = parse_toml_file(self.mcp_path)
        self.skills_payload = parse_json_file(self.skills_path)
        self.plugins_payload = parse_toml_file(self.plugins_path) if self.plugins_path.is_file() else {}
        if self.plugins_json_path.is_file():
            try:
                self.plugins_metadata_payload = json.loads(self.plugins_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                fail(f"invalid {self.plugins_json_path}: {exc}")
        else:
            self.plugins_metadata_payload = {}

        parsed_globals = parse_variable_table(
            vars_payload,
            path_label="vars.toml",
            table_name="global_variables",
            item_label="global variable",
        )
        if "session_variables" in vars_payload:
            fail("vars.toml [session_variables] has been replaced by config/usr/env.toml [launch_env]")

        try:
            self.runtime_vars = derive_runtime_globals_from_env(self.env)
        except RuntimeRenderError as exc:
            fail(str(exc))
        if self._stage_mode():
            self.runtime_vars["CODEX_SQLITE_HOME"] = str(self._stage_sqlite_home())
            self.global_vars = dict(parsed_globals)
            for key in GLOBAL_EXPORT_PATH_KEYS:
                self.global_vars[key] = self.runtime_vars[key]
        else:
            self.global_vars = dict(parsed_globals)
            sqlite_home = self.global_vars.get("CODEX_SQLITE_HOME", "").strip()
            if sqlite_home:
                self.runtime_vars["CODEX_SQLITE_HOME"] = sqlite_home

        self.runtime_layout = RuntimeLayout.from_env(self.env, self.runtime_vars)
        if self._stage_mode():
            self._configure_stage_process_home()
        self.variables = dict(self.env)
        self.variables.update(self.runtime_vars)
        self.effective_plugins_metadata_payload = effective_plugins_inventory_payload(
            self.plugins_metadata_payload,
            self.plugins_json_path,
            variables=self.variables,
        )
        try:
            self.secrets_config = parse_managed_secrets_file(self._managed_secrets_source_path())
        except ManagedSecretsError as exc:
            fail(str(exc))
        user_env_payload = parse_toml_file(self.user_env_path)
        if "launch_env" not in user_env_payload:
            self._warn_once(f"{self.user_env_path} does not define [launch_env]; continuing with no launch_env exports")
        self.launch_env = parse_launch_env_table(
            user_env_payload,
            path_label="config/usr/env.toml",
            variables=self.variables,
        )

        self.mcp_payload = resolve_object_placeholders(mcp_payload_raw, self.variables, "config/vendor/mcp.toml")

    def _validate_repo_layout(self) -> None:
        required_paths = (
            self.repo_layout.vendor_config_path,
            self.repo_layout.vendor_providers_path,
            self.repo_layout.vendor_pref_path,
            self.repo_layout.vendor_policy_path,
            self.repo_layout.vendor_mcp_path,
            self.repo_layout.vendor_requirements_path,
            self.repo_layout.profiles_config_dir,
            self.repo_layout.agents_config_dir,
            self.repo_layout.user_config_path,
            self.repo_layout.user_features_path,
            self.repo_layout.user_memory_path,
            self.repo_layout.user_pref_path,
            self.repo_layout.user_env_path,
            self.repo_layout.user_apps_path,
            self.repo_layout.user_policy_path,
            self.repo_layout.home_user_dir,
            self.repo_layout.hooks_dir,
            self.repo_layout.hooks_scripts_dir,
            self.repo_layout.hooks_manifest_path,
            self.repo_layout.hooks_dir / "schema" / "generated",
            self._hooks_runtime_config_source_path(),
            self.repo_layout.instructions_dir,
            self.repo_layout.instructions_default_metadata_path,
            self.repo_layout.instructions_agents_metadata_path,
            self.repo_layout.instructions_profiles_metadata_path,
            self.repo_layout.skills_dir,
            self.repo_layout.skills_metadata_path,
            self.repo_layout.plugins_inventory_path,
            self.repo_layout.plugins_skills_dir,
            self._managed_secrets_source_path(),
            self._managed_auth_source_path(),
        )
        for path in required_paths:
            if not path.exists():
                fail(f"missing required source path: {path}")
        for blocked_name in ("etc", "usr", "local"):
            blocked_path = self.repo_root / blocked_name
            if blocked_path.exists():
                fail(f"unexpected source path must not exist after rollout: {blocked_path}")

    def validate(self) -> None:
        for key in ENV_REQUIRED:
            value = self.env.get(key, "").strip()
            if not value:
                fail(f"missing required .env key: {key}")

        for key in ENV_ROOT_KEYS:
            ensure_safe_absolute_path(key, self.env[key])
        wrapper_dir = ensure_safe_absolute_path("CODEX_WRAPPER_DIR", self.env["CODEX_WRAPPER_DIR"])
        if wrapper_dir == Path("/"):
            fail("CODEX_WRAPPER_DIR must not be /")
        self._configured_install_packages()

        ensure_sha256("CODEX_DOWNLOAD_SHA", self.env["CODEX_DOWNLOAD_SHA"])
        ensure_gitlab_url("CODEX_DOWNLOAD_URL", self.env["CODEX_DOWNLOAD_URL"])

        self.allowed_roots = [ensure_safe_absolute_path(key, self.env[key]) for key in ENV_ROOT_KEYS]

        for key in RUNTIME_REQUIRED:
            if not self.runtime_vars.get(key, "").strip():
                fail(f"missing required runtime path derived from .env: {key}")

        for key in GLOBAL_EXPORT_REQUIRED:
            if not self.global_vars.get(key, "").strip():
                fail(f"missing required exported global variable in vars.toml: {key}")

        sqlite_home = ensure_safe_absolute_path("CODEX_SQLITE_HOME", self.runtime_vars["CODEX_SQLITE_HOME"])
        expected_sqlite_home = self._default_sqlite_home()
        if sqlite_home != expected_sqlite_home:
            fail(f"CODEX_SQLITE_HOME must be {expected_sqlite_home}")

        for key, value in self.runtime_vars.items():
            path = ensure_safe_absolute_path(f"runtime.{key}", value)
            if not any(is_within(path, root) for root in self.allowed_roots):
                fail(f"runtime path {key} is outside .env roots: {value}")

        for key in GLOBAL_EXPORT_PATH_KEYS:
            path = ensure_safe_absolute_path(f"global_variables.{key}", self.global_vars[key])
            if not any(is_within(path, root) for root in self.allowed_roots):
                fail(f"global path {key} is outside .env roots: {self.global_vars[key]}")
            runtime_value = self.runtime_vars.get(key, "").strip()
            if runtime_value and normalize_path(runtime_value) != path:
                fail(f"vars.toml {key} must match the path derived from .env")

        for key, value in self.global_vars.items():
            if key in GLOBAL_EXPORT_PATH_KEYS:
                continue
            ensure_safe_shell_export_value(f"global_variables.{key}", value)
        for key, value in self.launch_env.items():
            if key in self.runtime_vars:
                fail(f"launch_env {key} cannot override installer-managed runtime variables")
            if key in self.global_vars:
                fail(f"launch_env {key} cannot override vars.toml [global_variables]")
            ensure_safe_shell_export_value(f"launch_env.{key}", value)

        groups = iter_skill_groups(self.skills_payload)
        if not groups:
            fail("resources/skills/metadata.json must declare at least one skill group")

        for group in groups:
            if not bool(group.get("enabled", True)):
                continue
            role_name = str(group.get("role", "")).strip()
            if not role_name:
                fail("group entry missing role in resources/skills/metadata.json")

        self._plugin_manifest_bundles(enabled_only=True)
        validate_plugin_bundle_inventory(self, self.repo_layout.plugins_skills_dir)
        if self.sandbox_path.is_file():
            parse_toml_file(self.sandbox_path)
        validate_hooks_config(
            self._hooks_config_source_path(),
            self._hooks_source_dir(),
        )
        validate_agent_role_contracts(self.repo_layout.agents_config_dir, self.repo_layout.user_apps_path)
        self._validate_managed_secrets_config()
        self._validate_home_mcp_managed_secret_config()
        self._validate_login_auth_config()
        self._validate_repo_layout()
        self._render_user_config_toml("", self._home_config_path())

    def _expected_managed_secret_mcp_map(self) -> dict[str, str]:
        try:
            return managed_secret_mcp_env_map(self.mcp_payload, path_label="config/vendor/mcp.toml")
        except ManagedSecretsError as exc:
            fail(str(exc))

    def _supported_managed_secret_mcp_env_map(
        self,
        payload: dict[str, Any],
        *,
        path_label: str,
    ) -> dict[str, tuple[str, ...]]:
        try:
            return managed_secret_supported_mcp_env_map(payload, path_label=path_label)
        except ManagedSecretsError as exc:
            fail(str(exc))

    def _validate_managed_secrets_config(self) -> None:
        config = self.secrets_config
        if config is None:
            fail("managed secrets config is not loaded")

        required = self._expected_managed_secret_mcp_map()
        supported = self._supported_managed_secret_mcp_env_map(
            self.mcp_payload,
            path_label="config/vendor/mcp.toml",
        )
        actual = config.mcp_servers
        required_servers = set(required)
        supported_servers = set(supported)
        actual_servers = set(actual)
        if not required_servers.issubset(actual_servers) or not actual_servers.issubset(supported_servers):
            missing = sorted(required_servers - actual_servers)
            unexpected = sorted(actual_servers - supported_servers)
            details: list[str] = []
            if missing:
                details.append(f"missing servers: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected servers: {', '.join(unexpected)}")
            fail(f"{self._managed_secrets_source_path()} is out of sync with config/vendor/mcp.toml ({'; '.join(details)})")

        seen_keys: dict[str, str] = {}
        for server_name in sorted(actual):
            actual_keys = sorted(actual[server_name])
            supported_keys = sorted(supported.get(server_name, ()))
            if not supported_keys:
                fail(f"{self._managed_secrets_source_path()} mcp_servers.{server_name} is not supported by config/vendor/mcp.toml")
            if server_name in required and actual_keys != [required[server_name]]:
                fail(
                    f"{self._managed_secrets_source_path()} mcp_servers.{server_name} must declare "
                    f"{required[server_name]}"
                )
            if not set(actual_keys).issubset(set(supported_keys)):
                fail(
                    f"{self._managed_secrets_source_path()} mcp_servers.{server_name} must only declare "
                    f"supported env vars from config/vendor/mcp.toml: {', '.join(supported_keys)}"
                )
            for key in actual_keys:
                existing_server = seen_keys.get(key)
                if existing_server is not None:
                    fail(
                        f"{self._managed_secrets_source_path()} reuses env key {key} "
                        f"across mcp_servers.{existing_server} and mcp_servers.{server_name}"
                    )
                seen_keys[key] = server_name

    def _validate_home_mcp_managed_secret_config(self) -> None:
        required = self._expected_managed_secret_mcp_map()
        home_payload = self._resolved_user_apps_payload()
        actual = self._supported_managed_secret_mcp_env_map(home_payload, path_label="config/usr/apps.toml")

        for server_name in sorted(required):
            actual_keys = actual.get(server_name)
            if actual_keys != (required[server_name],):
                fail(
                    "config/usr/apps.toml mcp_servers."
                    f"{server_name} must declare bearer_token_env_var = {required[server_name]!r}"
                )

        config = self.secrets_config
        if config is None:
            fail("managed secrets config is not loaded")
        for server_name, key in config.configured_server_env_map().items():
            supported_keys = actual.get(server_name)
            if not supported_keys or key not in supported_keys:
                fail(
                    f"config/usr/apps.toml mcp_servers.{server_name} must expose managed env key {key} "
                    "through bearer_token_env_var or env_vars"
                )

    def _validate_login_auth_config(self) -> None:
        try:
            parse_login_auth_file(self._managed_auth_source_path())
        except CodexLoginAuthError as exc:
            fail(str(exc))

    def compile(self, output_dir: Path) -> CompiledArtifacts:
        target_output_dir = output_dir
        if self.dry_run:
            target_output_dir = Path(tempfile.mkdtemp(prefix="codex-compile-", dir=tempfile.gettempdir()))
        self._mkdir_path(target_output_dir)
        merged_config = compile_vendor_config(self.repo_layout, self.variables)
        config_out = target_output_dir / "config.toml"
        self._log(f"compiling merged runtime config into {config_out}")
        if self.dry_run:
            config_out.write_text(merged_config, encoding="utf-8")
        else:
            self._write_file(config_out, merged_config)
        return CompiledArtifacts(config_toml=config_out)

    def _log(self, message: str) -> None:
        print(f"[install] {message}")

    def _warn_once(self, message: str) -> None:
        if message in self._warnings_emitted:
            return
        self._warnings_emitted.add(message)
        print(f"[warn] {message}")

    def _share_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_SHARE_DIR", self.env["CODEX_SHARE_DIR"])

    def _docs_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"]) / "docs"

    def _human_docs_source_dir(self) -> Path:
        return self.repo_root / "docs"

    def _wrapper_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_WRAPPER_DIR", self.env["CODEX_WRAPPER_DIR"])

    def _schema_root_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"]) / "schema"

    def _schema_latest_snapshot_path(self) -> Path:
        return self._schema_root_dir() / "latest" / "config.schema.latest.json"

    def _helpers_dir(self) -> Path:
        return self._share_dir() / "helpers"

    def _wrapper_aliases_target(self) -> Path:
        return self._helpers_dir() / WRAPPER_ALIASES_FILENAME

    def _managed_secrets_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"]) / "lookup"

    def _managed_secrets_path(self) -> Path:
        return self._managed_secrets_dir() / SECRETS_FILENAME

    def _managed_secrets_source_path(self) -> Path:
        return self.repo_root / SECRETS_FILENAME

    def _managed_auth_path(self) -> Path:
        return self._managed_secrets_dir() / AUTH_FILENAME

    def _managed_auth_source_path(self) -> Path:
        return self.repo_root / AUTH_FILENAME

    def _managed_secret_env_helper_source_path(self) -> Path:
        return self.repo_root / "src" / "python" / "lib" / "keyring_env.py"

    def _managed_secret_env_helper_target(self) -> Path:
        return self._helpers_dir() / "codex-secret-tool-env.py"

    def _managed_secret_runtime_lib_dir(self) -> Path:
        return self._share_dir() / "lib"

    def _managed_secret_runtime_lib_sources(self) -> list[tuple[Path, Path]]:
        source_root = self.repo_root / "src" / "python" / "lib"
        target_root = self._managed_secret_runtime_lib_dir()
        return [
            (source_root / "__init__.py", target_root / "__init__.py"),
            (source_root / "managed_secrets.py", target_root / "managed_secrets.py"),
            (source_root / "runtime.py", target_root / "runtime.py"),
        ]

    def _codex_login_wrapper_source_path(self) -> Path:
        return self.repo_root / "src" / "python" / "lib" / "codex_login.py"

    def _codex_login_wrapper_target(self) -> Path:
        return self._wrapper_dir() / CODEX_LOGIN_WRAPPER_NAME

    def _codex_mcp_token_wrapper_source_path(self) -> Path:
        return self.repo_root / "src" / "python" / "lib" / "codex_mcp_token.py"

    def _codex_mcp_token_wrapper_target(self) -> Path:
        return self._wrapper_dir() / CODEX_MCP_TOKEN_WRAPPER_NAME

    def _mcp_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_MCP_DIR", self.env["CODEX_MCP_DIR"])

    def _mcp_ssh_key_path(self) -> Path:
        return self._mcp_dir() / "ssh" / "mcp_servers_ed25519"

    def _mcp_known_hosts_path(self) -> Path:
        return self._mcp_dir() / "ssh" / "known_hosts"

    def _configured_install_packages(self) -> list[str]:
        raw = self.env.get("CODEX_INSTALL_DEBIAN_PACKAGES", "").strip()
        if not raw:
            fail("missing required .env key: CODEX_INSTALL_DEBIAN_PACKAGES")

        packages: list[str] = []
        seen: set[str] = set()
        for package in raw.split():
            if not DEBIAN_PACKAGE_PATTERN.fullmatch(package):
                fail(f"invalid Debian package name in CODEX_INSTALL_DEBIAN_PACKAGES: {package}")
            if package in seen:
                continue
            seen.add(package)
            packages.append(package)

        if not packages:
            fail("CODEX_INSTALL_DEBIAN_PACKAGES must define at least one package")
        return packages

    def _codex_binary_path(self) -> Path:
        return self._share_dir() / "bin" / "codex"

    def _home_config_path(self) -> Path:
        return ensure_safe_absolute_path("CODEX_HOME", self.runtime_vars["CODEX_HOME"]) / "config.toml"

    def _path_profile_target(self) -> Path:
        system_dir = ensure_safe_absolute_path("CODEX_SYSTEM_DIR", self.env["CODEX_SYSTEM_DIR"])
        return system_dir.parent / "profile.d" / ENV_PROFILE_FILENAME

    def _codex_user_dir(self) -> Path:
        return ensure_safe_absolute_path("CODEX_USER_DIR", self.env["CODEX_USER_DIR"])

    def _default_sqlite_home(self) -> Path:
        return ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"]) / "sqlite"

    def _runtime_instructions_dir(self) -> Path:
        return self._codex_user_dir() / "instructions"

    def _runtime_home_dir(self) -> Path:
        runtime_layout = getattr(self, "runtime_layout", None)
        if runtime_layout is not None:
            return runtime_layout.home_dir
        return ensure_safe_absolute_path("CODEX_HOME", self.runtime_vars["CODEX_HOME"])

    def _runtime_plugins_dir(self) -> Path:
        if self.runtime_layout is not None:
            return self.runtime_layout.plugin_cache_dir
        return self._runtime_home_dir() / "plugins" / "cache"

    def _runtime_plugin_marketplace_dir(self) -> Path:
        if self.runtime_layout is not None:
            return self.runtime_layout.plugin_marketplace_dir
        return self._runtime_home_dir() / ".agents" / "plugins"

    def _runtime_agent_skills_path(self) -> Path:
        if self.runtime_layout is not None:
            return self.runtime_layout.agent_skills_path
        return self._runtime_home_dir() / ".agents" / "skills"

    def _runtime_plugin_marketplace_path(self) -> Path:
        if self.runtime_layout is not None:
            return self.runtime_layout.plugin_marketplace_path
        return self._runtime_plugin_marketplace_dir() / "marketplace.json"

    def _runtime_hooks_dir(self) -> Path:
        runtime_layout = getattr(self, "runtime_layout", None)
        if runtime_layout is not None:
            return runtime_layout.hooks_dir
        return self._runtime_home_dir() / ".hooks"

    def _runtime_hooks_config_path(self) -> Path:
        runtime_layout = getattr(self, "runtime_layout", None)
        if runtime_layout is not None:
            return runtime_layout.hooks_config_path
        return self._runtime_home_dir() / "hooks.json"

    def _runtime_hooks_scripts_dir(self) -> Path:
        return self._runtime_hooks_dir() / "scripts"

    def _runtime_hidden_hooks_dir(self) -> Path:
        return self._runtime_hooks_dir()

    def _runtime_hooks_lib_dir(self) -> Path:
        return self._runtime_hidden_hooks_dir() / "modules"

    def _runtime_hooks_schema_dir(self) -> Path:
        return self._runtime_hidden_hooks_dir() / "schema" / "generated"

    def _instructions_source_dir(self) -> Path:
        return self.repo_layout.instructions_dir

    def _profiles_source_dir(self) -> Path:
        return self.repo_layout.profiles_config_dir

    def _runtime_profiles_dir(self) -> Path:
        return self._runtime_home_dir()

    def _default_instruction_manifest_path(self) -> Path:
        repo_layout = getattr(self, "repo_layout", None)
        if repo_layout is not None:
            return repo_layout.instructions_default_metadata_path
        repo_root = Path(getattr(self, "repo_root", Path.cwd()))
        return repo_root / "resources" / "instructions" / "default" / "metadata.json"

    def _agents_instruction_manifest_path(self) -> Path:
        repo_layout = getattr(self, "repo_layout", None)
        if repo_layout is not None:
            return repo_layout.instructions_agents_metadata_path
        repo_root = Path(getattr(self, "repo_root", Path.cwd()))
        return repo_root / "resources" / "instructions" / "agents" / "metadata.json"

    def _profiles_instruction_manifest_path(self) -> Path:
        repo_layout = getattr(self, "repo_layout", None)
        if repo_layout is not None:
            return repo_layout.instructions_profiles_metadata_path
        repo_root = Path(getattr(self, "repo_root", Path.cwd()))
        return repo_root / "resources" / "instructions" / "profiles" / "metadata.json"

    def _instruction_manifest_entries(
        self,
        manifest_path: Path,
        *,
        config_file: str | None = None,
    ) -> list[dict[str, Any]]:
        if not manifest_path.is_file():
            return []
        manifest = parse_json_file(manifest_path)
        version = manifest.get("version")
        if version != 1:
            fail(f"{manifest_path} must declare version = 1")
        groups = manifest.get("groups")
        if not isinstance(groups, list):
            fail(f"{manifest_path} must declare a groups array")

        source_root = self._instructions_source_dir()
        seen_keys: set[tuple[str | None, str]] = set()
        entries: list[dict[str, Any]] = []
        for group in groups:
            if not isinstance(group, dict):
                fail(f"{manifest_path} group entry must be an object")
            group_name = str(group.get("name", "")).strip()
            if not INSTRUCTIONS_GROUP_PATTERN.fullmatch(group_name):
                fail(f"{manifest_path} group name is invalid: {group_name}")
            group_enabled = group.get("enabled", True)
            if not isinstance(group_enabled, bool):
                fail(f"{manifest_path} group.enabled must be boolean for {group_name}")
            group_entries = group.get("entries", [])
            if not isinstance(group_entries, list):
                fail(f"{manifest_path} group.entries must be a list for {group_name}")

            for entry in group_entries:
                if not isinstance(entry, dict):
                    fail(f"{manifest_path} group.entries items must be objects for {group_name}")

                entry_name = str(entry.get("name", "")).strip()
                if not entry_name:
                    fail(f"{manifest_path} entry missing name in group {group_name}")

                key_value = entry.get("config_key")
                config_key: str | None
                if key_value in (None, ""):
                    config_key = None
                else:
                    config_key = str(key_value).strip()
                    if not INSTRUCTIONS_ENTRY_KEY_PATTERN.fullmatch(config_key):
                        fail(f"{manifest_path} entry key is invalid: {config_key}")

                file_name = str(entry.get("file", "")).strip()
                if not file_name:
                    fail(f"{manifest_path} entry for {entry_name} must define file")
                if not INSTRUCTIONS_ENTRY_FILENAME_PATTERN.fullmatch(file_name):
                    fail(f"{manifest_path} entry file is invalid for {entry_name}: {file_name}")
                if "/" in file_name or "\\" in file_name:
                    fail(f"{manifest_path} entry file must be a basename for {entry_name}: {file_name}")
                if Path(file_name).suffix not in INSTRUCTIONS_ALLOWED_SUFFIXES:
                    allowed = ", ".join(sorted(INSTRUCTIONS_ALLOWED_SUFFIXES))
                    fail(f"{manifest_path} entry file must end with one of ({allowed}) for {entry_name}: {file_name}")

                entry_config_file = str(entry.get("config_file", "")).strip() or None
                if entry_config_file is not None and not INSTRUCTIONS_ENTRY_FILENAME_PATTERN.fullmatch(entry_config_file):
                    fail(f"{manifest_path} entry config_file is invalid for {entry_name}: {entry_config_file}")
                if config_key is not None:
                    dedupe_key = (entry_config_file, config_key)
                    if dedupe_key in seen_keys:
                        fail(
                            f"{manifest_path} duplicate key mapping"
                            f"{f' for {entry_config_file}' if entry_config_file else ''}: {config_key}"
                        )
                    seen_keys.add(dedupe_key)
                if config_file is not None and entry_config_file is not None and entry_config_file != config_file:
                    continue

                source_group = str(entry.get("source_group", group_name)).strip() or group_name
                source_path = source_root / source_group / file_name
                if not source_path.is_file():
                    fail(f"instructions source file not found for {entry_name}: {source_path}")

                entry_enabled = entry.get("enabled", group_enabled)
                if not isinstance(entry_enabled, bool):
                    fail(f"{manifest_path} entry.enabled must be boolean for {entry_name}")

                value_mode = str(entry.get("value_mode", "path")).strip() or "path"
                if value_mode not in {"inline_text", "path"}:
                    fail(f"{manifest_path} entry value_mode is invalid for {entry_name}: {value_mode}")

                resolved_targets: dict[str, str | None] = {}
                for field_name in ("default_enable_path", "default_disable_path"):
                    raw_target = entry.get(field_name)
                    if raw_target in (None, ""):
                        resolved_targets[field_name] = None
                        continue
                    if not isinstance(raw_target, str):
                        fail(f"{manifest_path} {entry_name}.{field_name} must be a string when provided")
                    resolved_targets[field_name] = resolve_placeholders(
                        raw_target.strip(),
                        self.variables,
                        f"{manifest_path} entry {entry_name}.{field_name}",
                    )
                source_text: str | None = None
                if value_mode == "inline_text":
                    source_text = source_path.read_text(encoding="utf-8").rstrip("\n")
                    if not source_text:
                        fail(f"{manifest_path} inline_text entry source must not be empty for {entry_name}")

                entries.append(
                    {
                        "config_key": config_key,
                        "enabled": entry_enabled,
                        "source_path": source_path,
                        "value_mode": value_mode,
                        "source_text": source_text,
                        "default_enable_path": resolved_targets["default_enable_path"],
                        "default_disable_path": resolved_targets["default_disable_path"],
                    }
                )
        return entries

    def _hooks_source_dir(self) -> Path:
        return self.repo_layout.hooks_scripts_dir

    def _hooks_lib_source_dir(self) -> Path:
        return self.repo_layout.hooks_scripts_dir / "lib"

    def _hooks_config_source_path(self) -> Path:
        return self.repo_layout.hooks_manifest_path

    def _hooks_schema_source_dir(self) -> Path:
        return self.repo_layout.hooks_dir / "schema" / "generated"

    def _hooks_runtime_config_source_path(self) -> Path:
        return self.repo_layout.hooks_scripts_dir / "lib" / "Codex" / "Hook" / "RuntimeConfig.pm"

    def _render_hooks_config_payload(self) -> dict[str, Any]:
        source_path = self._hooks_config_source_path()
        payload = parse_json_file(source_path)
        hooks = validate_hooks_config(
            source_path,
            self._hooks_source_dir(),
            hooks_payload=payload.get("hooks"),
        )
        payload["hooks"] = hooks
        rendered = resolve_object_placeholders(
            copy.deepcopy(payload),
            self.variables,
            str(source_path),
        )
        return rendered

    def _materialize_hooks_config(self) -> None:
        rendered = json.dumps(self._render_hooks_config_payload(), indent=2) + "\n"
        self._materialize_rendered_text(
            self._runtime_hooks_config_path(),
            rendered,
            dry_run_message="materialize runtime hooks config into",
        )

    def _render_user_fragment(self, path: Path) -> str:
        return _replace_known_placeholders_outside_toml_multiline_strings(
            path.read_text(encoding="utf-8"),
            self.variables,
        )

    def _plugins_source_dir(self) -> Path:
        return self.repo_layout.plugins_skills_dir

    def _instructions_manifest_path(self) -> Path:
        return self._default_instruction_manifest_path()

    def _backup_source_paths(self) -> list[tuple[str, Path]]:
        sources: list[tuple[str, Path]] = []
        for env_key, label in BACKUP_SOURCE_KEY_TO_LABEL:
            source = ensure_safe_absolute_path(env_key, self.runtime_vars[env_key])
            if source.exists() and not source.is_dir():
                fail(f"backup source must be a directory: {source}")
            sources.append((label, source))
        return sources

    def _backup_account_key(self, sources: list[tuple[str, Path]]) -> str:
        home_dir = ensure_safe_absolute_path("CODEX_HOME", self.runtime_vars["CODEX_HOME"])
        auth_path = home_dir / "auth.json"
        if not auth_path.is_file():
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        try:
            payload = json.loads(auth_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._log(f"falling back to unknown backup bucket because CODEX_HOME/auth.json is unreadable: {exc}")
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        if not isinstance(payload, dict):
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        account_ids: set[str] = set()
        pending: list[Any] = [payload]
        while pending:
            current = pending.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key == "account_id" and isinstance(value, str):
                        account_ids.add(value.strip())
                        continue
                    pending.append(value)
            elif isinstance(current, list):
                pending.extend(current)
        if not account_ids:
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        if len(account_ids) > 1:
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        account_id = next(iter(account_ids))
        account_key = account_id.strip()[:8]
        if not BACKUP_ACCOUNT_KEY_PATTERN.fullmatch(account_key):
            return BACKUP_UNKNOWN_ACCOUNT_KEY
        return account_key

    def _backup_run_root(self, backup_root: Path, *, account_key: str, flow: str) -> Path:
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        base_name = f"{timestamp}-{flow}-{account_key}"
        candidate = backup_root / base_name
        suffix = 1
        while candidate.exists():
            suffix += 1
            candidate = backup_root / f"{base_name}-{suffix}"
        return candidate

    def _user_home_dir(self) -> Path:
        if not self.user_home.is_absolute():
            fail(f"user home must be an absolute path: {self.user_home}")
        return self.user_home

    def _env_script_path(self) -> Path:
        script = self.repo_root / "src" / "python" / "lib" / "codex_env.sh"
        if not script.is_file():
            fail(f"missing CODEX environment helper script: {script}")
        return script

    def _run_with_sudo(self, args: list[str]) -> None:
        cmd = ["sudo", *args]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError as exc:
            fail(f"sudo is required for privileged operation but is unavailable: {exc}")
        except subprocess.CalledProcessError as exc:
            fail(f"sudo command failed ({' '.join(args)}), exit code {exc.returncode}")

    def _run_command(self, args: list[str]) -> None:
        try:
            subprocess.run(args, check=True)
        except FileNotFoundError as exc:
            fail(f"required command is unavailable: {exc}")
        except subprocess.CalledProcessError as exc:
            fail(f"command failed ({' '.join(args)}), exit code {exc.returncode}")

    def _debian_package_installed(self, package: str) -> bool:
        try:
            proc = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", package],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
        except FileNotFoundError as exc:
            fail(f"dpkg-query is required for dependency checks but is unavailable: {exc}")
        except subprocess.TimeoutExpired:
            fail(f"dpkg-query timed out while checking package {package}")
        return proc.returncode == 0 and proc.stdout.strip() == "install ok installed"

    def _ensure_install_dependencies(self) -> None:
        packages = self._configured_install_packages()
        missing = [package for package in packages if not self._debian_package_installed(package)]
        if not missing:
            return

        if self.dry_run or self._stage_mode():
            print("[dry-run] apt-get install --no-install-recommends " + " ".join(missing))
            return

        env = dict(os.environ)
        env["DEBIAN_FRONTEND"] = "noninteractive"
        commands = (
            ["sudo", "apt-get", "update"],
            ["sudo", "apt-get", "install", "-y", "--no-install-recommends", *missing],
        )
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, env=env, timeout=900)
            except FileNotFoundError as exc:
                fail(f"dependency install command is unavailable: {exc}")
            except subprocess.TimeoutExpired:
                fail(f"dependency install command timed out: {' '.join(cmd)}")
            except subprocess.CalledProcessError as exc:
                fail(f"dependency install command failed ({' '.join(cmd[1:])}), exit code {exc.returncode}")

    def _needs_sudo_write(self, path: Path) -> bool:
        return needs_sudo_write(path)

    def _mkdir_path(self, path: Path) -> None:
        if self.dry_run:
            print(f"[dry-run] mkdir -p {path}")
            return
        if self._needs_sudo_write(path):
            self._run_with_sudo(["mkdir", "-p", str(path)])
        else:
            path.mkdir(parents=True, exist_ok=True)

    def _install_file_with_sudo(self, src: Path, dst: Path, mode: int) -> None:
        self._run_with_sudo(["mkdir", "-p", str(dst.parent)])
        self._run_with_sudo(["install", "-m", f"{mode:04o}", str(src), str(dst)])

    def _write_file(self, path: Path, content: str, mode: int = 0o644) -> None:
        if self.dry_run:
            print(f"[dry-run] write {path}")
            return
        if path.is_file():
            try:
                current = path.read_text(encoding="utf-8")
                current_mode = stat.S_IMODE(path.stat().st_mode)
            except OSError:
                current = ""
                current_mode = -1
            if current == content and current_mode == mode:
                return
        if self._needs_sudo_write(path.parent):
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                prefix="codex-install-",
            ) as handle:
                handle.write(content)
                temp_path = Path(handle.name)
            try:
                self._install_file_with_sudo(temp_path, path, mode)
            finally:
                temp_path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(path, mode)

    def _write_text_preserving_mode(self, path: Path, content: str, *, default_mode: int = 0o644) -> None:
        mode = default_mode
        try:
            if path.is_file():
                mode = stat.S_IMODE(path.stat().st_mode) or default_mode
        except OSError:
            mode = default_mode
        self._write_file(path, content, mode=mode)

    def _copy_file(self, src: Path, dst: Path, mode: int = 0o644) -> None:
        if self.dry_run:
            print(f"[dry-run] copy {src} -> {dst}")
            return
        try:
            src_stat = src.stat()
        except OSError:
            src_stat = None
        if dst.is_file():
            try:
                dst_stat = dst.stat()
                dst_mode = stat.S_IMODE(dst_stat.st_mode)
                if dst_mode == mode:
                    if src_stat is not None:
                        src_mtime_ns = getattr(src_stat, "st_mtime_ns", int(src_stat.st_mtime * 1_000_000_000))
                        dst_mtime_ns = getattr(dst_stat, "st_mtime_ns", int(dst_stat.st_mtime * 1_000_000_000))
                        if dst_stat.st_size == src_stat.st_size and dst_mtime_ns == src_mtime_ns:
                            return
                    if src_stat is None or dst_stat.st_size == src_stat.st_size:
                        if filecmp.cmp(src, dst, shallow=False):
                            return
            except OSError:
                pass
        if self._needs_sudo_write(dst.parent):
            self._install_file_with_sudo(src, dst, mode)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            os.chmod(dst, mode)

    def _copy_tree(self, src: Path, dst: Path) -> None:
        if not src.is_dir():
            fail(f"copy source directory not found: {src}")
        if self.dry_run:
            print(f"[dry-run] sync tree {src} -> {dst}")
            return
        if self._needs_sudo_write(dst):
            self._run_with_sudo(["mkdir", "-p", str(dst)])
            self._run_with_sudo(["cp", "-a", f"{src}{os.sep}.", str(dst)])
        else:
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, dirs_exist_ok=True)

    def _sync_tree(self, src: Path, dst: Path, *, mirror_deletions: bool) -> None:
        self._sync_tree_filtered(
            src,
            dst,
            skip_root_toml=False,
            preserve_root_dirs=set(),
            preserve_root_files=set(),
            mirror_deletions=mirror_deletions,
        )

    def _render_schema_wrapper(
        self,
        command: str,
        launch_env: dict[str, str] | None = None,
    ) -> str:
        if command not in {"newest", "diff"}:
            fail(f"unsupported schema helper command: {command}")
        schema_root = self._schema_root_dir()
        release_package = self._share_dir() / "release" / "pkg" / self.env["CODEX_DOWNLOAD_PKG"]
        home_config_path = self._home_config_path()
        tool_path = self._helpers_dir() / SCHEMA_TOOL_SOURCE_FILENAME
        try:
            effective_launch_env = self.launch_env if launch_env is None else launch_env
            export_block = render_shell_export_block(effective_launch_env)
        except RuntimeRenderError as exc:
            fail(str(exc))
        if command == "newest":
            return (
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                f"{export_block}"
                "if (($# != 0)); then\n"
                "  echo \"usage: codex-schema-newest\" >&2\n"
                "  exit 2\n"
                "fi\n"
                f'exec /usr/bin/env python3 "{tool_path}" "newest" '
                f'--schema-root "{schema_root}" --release-package "{release_package}" '
                f'--host-config "{home_config_path}"\n'
            )

        return (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"{export_block}"
            "if (($# > 1)); then\n"
            "  echo \"usage: codex-schema-diff [--output]\" >&2\n"
            "  exit 2\n"
            "fi\n"
            "if (($# == 1)) && [[ \"$1\" != \"--output\" ]]; then\n"
            "  echo \"usage: codex-schema-diff [--output]\" >&2\n"
            "  exit 2\n"
            "fi\n"
            f'exec /usr/bin/env python3 "{tool_path}" "diff" '
            f'--schema-root "{schema_root}" --release-package "{release_package}" '
            f'--host-config "{home_config_path}" "$@"\n'
        )

    def _ensure_runtime_directories(self) -> None:
        path_values: set[str] = {self.env[key] for key in ENV_ROOT_KEYS}
        for key, value in self.runtime_vars.items():
            path_values.add(value)
        path_values.add(str(self._default_sqlite_home()))
        path_values.add(str(Path(self.env["CODEX_SYSTEM_DIR"]) / "skills"))
        path_values.add(str(Path(self.env["CODEX_SHARE_DIR"]) / "bin"))
        path_values.add(str(Path(self.env["CODEX_SHARE_DIR"]) / "helpers"))
        path_values.add(str(Path(self.env["CODEX_SHARE_DIR"]) / "release" / "pkg"))
        path_values.add(str(self._wrapper_dir()))
        path_values.add(str(self._managed_secrets_dir()))
        path_values.add(str(self._runtime_instructions_dir()))
        path_values.add(str(self._runtime_plugins_dir()))
        path_values.add(str(self._runtime_plugin_marketplace_dir()))

        for raw in sorted(path_values):
            path = Path(raw)
            self._mkdir_path(path)

    def _ensure_upgrade_directories(self) -> None:
        path_values = {
            Path(self.env["CODEX_SYSTEM_DIR"]),
            Path(self.env["CODEX_SYSTEM_DIR"]) / "skills",
            Path(self.env["CODEX_SHARE_DIR"]),
            Path(self.env["CODEX_SHARE_DIR"]) / "bin",
            Path(self.env["CODEX_SHARE_DIR"]) / "helpers",
            Path(self.env["CODEX_SHARE_DIR"]) / "release" / "pkg",
            self._wrapper_dir(),
            self._schema_root_dir(),
            Path(self.runtime_vars["CODEX_SKILLS"]),
            self._default_sqlite_home(),
            self._managed_secrets_dir(),
        }
        for path in sorted(path_values):
            self._mkdir_path(path)

    def _enabled_managed_secret_entries(self) -> list[tuple[str, str]]:
        config = self.secrets_config
        if config is None:
            fail("managed secrets config is not loaded")

        entries: list[tuple[str, str]] = []
        for server_name in sorted(config.mcp_servers):
            for key in sorted(config.mcp_servers[server_name]):
                if config.mcp_servers[server_name][key]:
                    entries.append((server_name, key))
        return entries

    def _prompt_managed_secret_value(self, *, server_name: str, key: str) -> str | None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            self._warn_once(
                f"managed secret {key} is enabled for mcp_servers.{server_name} but no interactive terminal is "
                "available; continuing without storing it"
            )
            return None

        prompt = f"Enter {key} for mcp_servers.{server_name} (or 's' to skip): "
        while True:
            try:
                value = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print(file=sys.stderr)
                return None
            normalized = value.strip()
            if normalized.lower() == "s":
                return None
            if not normalized:
                print(f"[warn] {key} cannot be empty; enter a value or 's' to skip")
                continue
            if "\n" in normalized or "\r" in normalized:
                fail(f"{key} must be single-line")
            return normalized

    def _ensure_enabled_managed_secrets(self) -> None:
        config = self.secrets_config
        if config is None:
            fail("managed secrets config is not loaded")
        entries = self._enabled_managed_secret_entries()
        if not entries:
            return
        if not secret_tool_available():
            fail("secret-tool is required when secrets.toml enables managed MCP credentials")

        for server_name, key in entries:
            try:
                if lookup_managed_secret(config, server_name).strip():
                    continue
            except ManagedSecretsError as exc:
                fail(str(exc))

            value = self._prompt_managed_secret_value(server_name=server_name, key=key)
            if value is None:
                self._warn_once(f"skipping optional managed secret {key} for mcp_servers.{server_name}")
                continue
            try:
                store_managed_secret(config, server_name, value, env_key=key)
            except ManagedSecretsError as exc:
                fail(str(exc))

    def _clear_all_managed_secrets(self) -> None:
        config = self.secrets_config
        if config is None:
            fail("managed secrets config is not loaded")
        server_names = config.all_server_names()
        if not server_names:
            return
        if not secret_tool_available():
            self._warn_once("secret-tool is unavailable; skipping managed MCP credential cleanup during uninstall")
            return
        for server_name in server_names:
            try:
                clear_managed_secret(config, server_name)
            except ManagedSecretsError as exc:
                self._warn_once(f"{exc}; continuing uninstall without removing that keyring entry")

    def _sync_managed_secrets_file(self) -> None:
        path = self._managed_secrets_path()
        source = self._managed_secrets_source_path()
        if not source.is_file():
            fail(f"missing managed secrets source file: {source}")
        self._mkdir_path(path.parent)
        if path.exists() and not path.is_file():
            fail(f"managed secrets file must be a regular file: {path}")
        self._copy_file(source, path, mode=0o644)

    def _sync_managed_auth_file(self) -> None:
        path = self._managed_auth_path()
        source = self._managed_auth_source_path()
        if not source.is_file():
            fail(f"missing login auth source file: {source}")
        self._mkdir_path(path.parent)
        if path.exists() and not path.is_file():
            fail(f"login auth file must be a regular file: {path}")
        self._copy_file(source, path, mode=0o644)

    def _secure_exec_directories(self) -> None:
        desired_mode = 0o755
        secure_paths = {
            Path(self.env["CODEX_SHARE_DIR"]) / "bin",
            Path(self.env["CODEX_SHARE_DIR"]) / "helpers",
            self._wrapper_dir(),
        }
        if self._stage_mode():
            for path in sorted(secure_paths):
                self._mkdir_path(path)
                if self.dry_run:
                    print(f"[dry-run] chmod {desired_mode:o} -- {path}")
                    continue
                try:
                    os.chmod(path, desired_mode)
                except PermissionError:
                    self._run_with_sudo(["chmod", f"{desired_mode:o}", str(path)])
            return

        for path in sorted(secure_paths):
            if self.dry_run:
                print(f"[dry-run] secure root-owned exec dir {path} mode {desired_mode:o}")
                continue

            needs_hardening = False
            try:
                st = path.stat()
            except (FileNotFoundError, PermissionError):
                needs_hardening = True
            else:
                mode = stat.S_IMODE(st.st_mode)
                needs_hardening = st.st_uid != 0 or st.st_gid != 0 or mode != desired_mode

            if not needs_hardening:
                continue

            self._run_with_sudo(["mkdir", "-p", str(path)])
            self._run_with_sudo(["chown", "root:root", str(path)])
            self._run_with_sudo(["chmod", f"{desired_mode:o}", str(path)])

    def _resolve_group_target_path(self, group: dict[str, Any]) -> Path:
        raw_path = str(group.get("runtime_path") or group.get("path") or "").strip()
        if not raw_path:
            fail(f"group missing runtime_path in resources/skills/metadata.json: {group}")
        rendered = resolve_placeholders(
            raw_path,
            self.variables,
            f"skills.group[{group.get('name', '?')}].runtime_path",
        )
        target = ensure_safe_absolute_path(f"group path {group.get('name', '?')}", rendered)
        if not any(is_within(target, root) for root in self.allowed_roots):
            fail(f"group path outside allowed roots: {target}")
        return target

    def _resolve_group_source_path(self, group: dict[str, Any]) -> Path:
        raw_source = str(group.get("source_path", "")).strip()
        if raw_source:
            source = (self.repo_layout.skills_dir / raw_source).resolve(strict=False)
        else:
            namespace = str(group.get("namespace", "")).strip()
            if not namespace:
                fail(f"group missing namespace in resources/skills/metadata.json: {group}")
            source = (self.repo_layout.skills_dir / namespace).resolve(strict=False)
        skills_root = self.repo_layout.skills_dir.resolve(strict=False)
        if not is_within(source, skills_root):
            fail(f"group source path is outside resources/skills: {source}")
        if not source.is_dir():
            fail(f"group source path not found: {source}")
        return source

    def _is_user_skill_target(self, target: Path) -> bool:
        return is_within(normalize_path(str(target)), normalize_path(self.runtime_vars["CODEX_SKILLS"]))

    def _is_system_skill_target(self, target: Path) -> bool:
        system_skills_root = normalize_path(self.env["CODEX_SYSTEM_DIR"]) / "skills"
        return is_within(normalize_path(str(target)), system_skills_root)

    def _skill_dependency_blocks_by_runtime_dir(self) -> dict[str, str]:
        mcp_servers = self.mcp_payload.get("mcp_servers", {})
        if not isinstance(mcp_servers, dict):
            fail("vendor MCP payload is missing mcp_servers")

        dependency_blocks: dict[str, str] = {}
        for runtime_dirname, role_name in runtime_skill_roles_by_dirname(self.skills_payload).items():
            role_tools = role_tools_from_skills(self.skills_payload, role_name)
            dependency_blocks[runtime_dirname] = render_dependency_block(role_tools, mcp_servers)
        return dependency_blocks

    def _rewrite_installed_skill_dependencies(
        self,
        target: Path,
        dependency_blocks: dict[str, str],
        *,
        skip_missing: bool = False,
    ) -> None:
        if not target.is_dir():
            if skip_missing or self.dry_run:
                print(f"[dry-run] skip dependency rewrite for missing target {target}")
                return
            fail(f"group target directory missing for dependency rewrite: {target}")

        for child in sorted(target.iterdir()):
            if not child.is_dir():
                continue
            openai_yaml = child / "agents" / "openai.yaml"
            if openai_yaml.is_file():
                dependency_block = dependency_blocks.get(child.name)
                if dependency_block is None:
                    fail(f"installed skill directory has no metadata role mapping: {child}")
                rewrite_openai_yaml_dependencies(
                    openai_yaml,
                    dependency_block,
                    self.dry_run,
                    write_file=lambda path, content: self._write_text_preserving_mode(path, content),
                )
                continue

            if any(grandchild.is_dir() for grandchild in child.iterdir()):
                self._rewrite_installed_skill_dependencies(child, dependency_blocks, skip_missing=skip_missing)

    def _sync_agent_skills_symlink(self) -> None:
        skills_root = Path(self.runtime_vars["CODEX_SKILLS"])
        link_path = self._runtime_agent_skills_path()

        self._mkdir_path(skills_root)
        self._mkdir_path(link_path.parent)

        if link_path.is_symlink():
            if link_path.resolve(strict=False) == skills_root.resolve(strict=False):
                return
            self._remove_path_force(link_path)
        elif link_path.exists():
            self._remove_path_force(link_path)

        if self.dry_run:
            print(f"[dry-run] ln -s {skills_root} {link_path}")
            return

        if self._needs_sudo_write(link_path.parent):
            self._run_with_sudo(["ln", "-sfn", str(skills_root), str(link_path)])
            return

        link_path.symlink_to(skills_root, target_is_directory=True)

    def _sync_skill_groups(self, *, user_only: bool = False, system_only: bool = False) -> None:
        if user_only and system_only:
            fail("skill group sync cannot be both user_only and system_only")
        groups = iter_skill_groups(self.skills_payload)
        dependency_blocks = self._skill_dependency_blocks_by_runtime_dir()
        for group in groups:
            if not bool(group.get("enabled", True)):
                continue
            target = self._resolve_group_target_path(group)
            if user_only and not self._is_user_skill_target(target):
                continue
            if system_only and not self._is_system_skill_target(target):
                continue
            source = self._resolve_group_source_path(group)
            self._sync_tree(source, target, mirror_deletions=True)
            self._rewrite_installed_skill_dependencies(target, dependency_blocks)

    def _rewrite_skill_group_dependencies_only(
        self,
        *,
        skip_missing: bool = False,
        user_only: bool = False,
        system_only: bool = False,
    ) -> None:
        if user_only and system_only:
            fail("dependency rewrite cannot be both user_only and system_only")
        groups = iter_skill_groups(self.skills_payload)
        dependency_blocks = self._skill_dependency_blocks_by_runtime_dir()
        for group in groups:
            if not bool(group.get("enabled", True)):
                continue
            target = self._resolve_group_target_path(group)
            if user_only and not self._is_user_skill_target(target):
                continue
            if system_only and not self._is_system_skill_target(target):
                continue
            self._rewrite_installed_skill_dependencies(target, dependency_blocks, skip_missing=skip_missing)

    def _sync_instruction_assets(self) -> None:
        self._sync_tree_filtered(
            self._instructions_source_dir(),
            self._runtime_instructions_dir(),
            skip_root_toml=True,
            mirror_deletions=True,
        )

    def _materialize_profile_config_paths(self, source_dir: Path | None = None) -> None:
        runtime_profiles_dir = self._runtime_profiles_dir()
        resolved_source_dir = source_dir or self._profiles_source_dir()
        if not resolved_source_dir.is_dir():
            return

        for source_path in sorted(path for path in resolved_source_dir.glob("*.toml") if path.is_file()):
            target_path = runtime_profiles_dir / source_path.name
            raw = source_path.read_text(encoding="utf-8")
            rendered = self._render_home_toml(
                raw,
                target_path,
                apply_instruction_overrides=True,
                instruction_manifest_path=self._profiles_instruction_manifest_path(),
                instruction_config_file=source_path.name,
            )
            mode = stat.S_IMODE(source_path.stat().st_mode) or 0o644
            self._materialize_rendered_text(
                target_path,
                rendered,
                mode=mode,
                dry_run_message="render profile config into",
            )

    def _sync_runtime_docs(self) -> None:
        docs_src = self._human_docs_source_dir()
        docs_dst = self._docs_dir()
        self._sync_tree_filtered(
            docs_src,
            docs_dst,
            skip_root_toml=False,
            mirror_deletions=True,
        )

    def _resolve_runtime_config_path(self, raw_path: str, *, label: str) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            target = ensure_safe_absolute_path(label, raw_path)
        else:
            base_dir = ensure_safe_absolute_path("CODEX_HOME", self.runtime_vars["CODEX_HOME"])
            target = (base_dir / candidate).resolve(strict=False)
        if not any(is_within(target, root) for root in self.allowed_roots):
            fail(f"{label} resolves outside allowed roots: {target}")
        return target

    def _materialize_instruction_default_assets(self) -> None:
        for entry in self._instruction_manifest_entries(self._default_instruction_manifest_path()):
            raw_target = entry.get("default_disable_path")
            if not raw_target:
                continue
            target = self._resolve_runtime_config_path(
                raw_target,
                label=f"instruction default asset for {entry.get('config_key') or entry['source_path'].name}",
            )
            if target.exists() and target.is_dir():
                self._remove_path_force(target)
            source_path = entry["source_path"]
            mode = stat.S_IMODE(source_path.stat().st_mode)
            self._copy_file(source_path, target, mode=mode)

    def _sync_hooks_assets(self) -> None:
        self._sync_tree_filtered(
            self._hooks_source_dir(),
            self._runtime_hooks_scripts_dir(),
            skip_root_toml=False,
            mirror_deletions=True,
        )
        self._remove_path_force(self._runtime_hooks_scripts_dir() / "lib")
        self._sync_tree_filtered(
            self._hooks_lib_source_dir(),
            self._runtime_hooks_lib_dir(),
            skip_root_toml=False,
            mirror_deletions=True,
        )
        self._sync_tree_filtered(
            self._hooks_schema_source_dir(),
            self._runtime_hooks_schema_dir(),
            skip_root_toml=False,
            mirror_deletions=True,
        )
        self._materialize_hooks_config()

    def _sync_tree_filtered(
        self,
        src: Path,
        dst: Path,
        *,
        skip_root_toml: bool,
        preserve_root_dirs: set[str] | None = None,
        preserve_root_files: set[str] | None = None,
        mirror_deletions: bool = False,
    ) -> None:
        if not src.is_dir():
            fail(f"copy source directory not found: {src}")
        preserve_dirs = preserve_root_dirs or set()
        preserve_files = preserve_root_files or set()
        if dst.exists() and not dst.is_dir():
            fail(f"copy destination must be a directory: {dst}")
        self._mkdir_path(dst)

        if mirror_deletions:
            self._prune_filtered_tree(
                src,
                dst,
                skip_root_toml=skip_root_toml,
                preserve_root_dirs=preserve_dirs,
                preserve_root_files=preserve_files,
            )

        for root, dirs, files in os.walk(src, topdown=True, followlinks=False):
            root_path = Path(root)
            rel_root = root_path.relative_to(src)
            rel_root_str = "" if rel_root == Path(".") else str(rel_root)
            target_root = dst if rel_root_str == "" else (dst / rel_root_str)
            if target_root.exists() and not target_root.is_dir():
                self._remove_path_force(target_root)
            self._mkdir_path(target_root)

            ordered_dirs = sorted(dirs)
            dirs[:] = [
                dirname
                for dirname in ordered_dirs
                if not (
                    rel_root_str == ""
                    and dirname in preserve_dirs
                )
            ]

            for filename in sorted(files):
                if rel_root_str == "":
                    if filename in preserve_files:
                        continue
                    if skip_root_toml and filename.endswith(".toml"):
                        continue
                rel_file = Path(filename) if rel_root_str == "" else Path(rel_root_str) / filename
                source_file = root_path / filename
                if not source_file.is_file():
                    continue
                target_file = dst / rel_file
                if target_file.exists() and target_file.is_dir():
                    self._remove_path_force(target_file)
                mode = stat.S_IMODE(source_file.stat().st_mode)
                if mode == 0:
                    mode = 0o644
                self._copy_file(source_file, target_file, mode=mode)

    def _is_filtered_preserve_path(
        self,
        rel_path: Path,
        *,
        skip_root_toml: bool,
        preserve_root_dirs: set[str],
        preserve_root_files: set[str],
    ) -> bool:
        parts = rel_path.parts
        if not parts:
            return False
        root_name = parts[0]
        if root_name in preserve_root_dirs:
            return True
        if len(parts) == 1 and root_name in preserve_root_files:
            return True
        return bool(skip_root_toml and len(parts) == 1 and rel_path.suffix == ".toml")

    def _prune_filtered_tree(
        self,
        src: Path,
        dst: Path,
        *,
        skip_root_toml: bool,
        preserve_root_dirs: set[str],
        preserve_root_files: set[str],
    ) -> None:
        if not dst.exists():
            return

        pending = [dst]
        while pending:
            current_dst = pending.pop()
            for child in sorted(current_dst.iterdir(), key=lambda item: item.name):
                rel_child = child.relative_to(dst)
                if self._is_filtered_preserve_path(
                    rel_child,
                    skip_root_toml=skip_root_toml,
                    preserve_root_dirs=preserve_root_dirs,
                    preserve_root_files=preserve_root_files,
                ):
                    continue
                source_child = src / rel_child
                if not source_child.exists():
                    self._remove_path_force(child)
                    continue
                if child.is_dir():
                    if not source_child.is_dir():
                        self._remove_path_force(child)
                        continue
                    pending.append(child)
                    continue
                if source_child.is_dir():
                    self._remove_path_force(child)

    def _merge_missing_tree(self, src: Path, dst: Path) -> None:
        if not src.is_dir():
            fail(f"merge source directory not found: {src}")
        if dst.exists():
            if not dst.is_dir():
                fail(f"merge destination must be a directory: {dst}")
        else:
            self._mkdir_path(dst)

        for root, dirs, files in os.walk(src, topdown=True, followlinks=False):
            root_path = Path(root)
            rel_root = root_path.relative_to(src)
            target_root = dst if rel_root == Path(".") else (dst / rel_root)
            if target_root.exists():
                if not target_root.is_dir():
                    fail(f"merge destination must be a directory: {target_root}")
            else:
                self._mkdir_path(target_root)

            keep_dirs: list[str] = []
            for dirname in sorted(dirs):
                source_dir = root_path / dirname
                target_dir = target_root / dirname
                if target_dir.exists():
                    if not target_dir.is_dir():
                        fail(f"merge destination must be a directory: {target_dir}")
                    keep_dirs.append(dirname)
                    continue
                self._copy_tree(source_dir, target_dir)
            dirs[:] = keep_dirs

            for filename in sorted(files):
                source_file = root_path / filename
                if not source_file.is_file():
                    continue
                target_file = target_root / filename
                if target_file.exists():
                    if not target_file.is_file():
                        fail(f"merge destination must be a file: {target_file}")
                    continue
                mode = stat.S_IMODE(source_file.stat().st_mode)
                if mode == 0:
                    mode = 0o644
                self._copy_file(source_file, target_file, mode=mode)

    def _seed_missing_home_runtime_state_from_repo(self, repo_home: Path, runtime_home: Path) -> None:
        memories_src = repo_home / "memories"
        memories_dst = runtime_home / "memories"
        if memories_dst.exists():
            if not memories_dst.is_dir():
                fail(f"runtime preserve target must be a directory: {memories_dst}")
            if memories_src.exists():
                if not memories_src.is_dir():
                    fail(f"repo preserve source must be a directory: {memories_src}")
                self._merge_missing_tree(memories_src, memories_dst)
            self._strip_memories_git_metadata(memories_dst)
            return
        if memories_src.exists():
            if not memories_src.is_dir():
                fail(f"repo preserve source must be a directory: {memories_src}")
            self._copy_tree(memories_src, memories_dst)
            self._strip_memories_git_metadata(memories_dst)
            return
        self._mkdir_path(memories_dst)

    def _strip_memories_git_metadata(self, memories_root: Path) -> None:
        git_dir = memories_root / ".git"
        if git_dir.exists() or git_dir.is_symlink():
            self._remove_path_force(git_dir)

    def _sync_schema_helpers(self, launch_env: dict[str, str] | None = None) -> None:
        source_tool = self.repo_root / "src" / "misc" / SCHEMA_TOOL_SOURCE_FILENAME
        if not source_tool.is_file():
            fail(f"missing schema helper source script: {source_tool}")

        helpers_dir = self._helpers_dir()
        self._mkdir_path(helpers_dir)
        self._copy_file(source_tool, helpers_dir / SCHEMA_TOOL_SOURCE_FILENAME, mode=0o755)

        for name, command in SCHEMA_HELPER_COMMANDS.items():
            wrapper_content = self._render_schema_wrapper(command, launch_env=launch_env)
            self._write_file(helpers_dir / name, wrapper_content, mode=0o755)

    def _sync_managed_secret_env_helper(self) -> None:
        self._copy_file(
            self._managed_secret_env_helper_source_path(),
            self._managed_secret_env_helper_target(),
            mode=0o755,
        )
        self._mkdir_path(self._managed_secret_runtime_lib_dir())
        for source, target in self._managed_secret_runtime_lib_sources():
            self._copy_file(source, target, mode=0o644)

    def _sync_codex_login_wrapper(self) -> None:
        self._copy_file(
            self._codex_login_wrapper_source_path(),
            self._codex_login_wrapper_target(),
            mode=0o755,
        )

    def _sync_codex_mcp_token_wrapper(self) -> None:
        self._copy_file(
            self._codex_mcp_token_wrapper_source_path(),
            self._codex_mcp_token_wrapper_target(),
            mode=0o755,
        )

    def _verify_schema_helpers(self) -> None:
        helpers_dir = self._helpers_dir()
        tool_path = helpers_dir / SCHEMA_TOOL_SOURCE_FILENAME
        if not tool_path.is_file():
            fail(f"missing installed schema helper tool: {tool_path}")
        if not os.access(tool_path, os.X_OK):
            fail(f"schema helper tool is not executable: {tool_path}")

        for name in SCHEMA_HELPER_NAMES:
            helper_path = helpers_dir / name
            if not helper_path.is_file():
                fail(f"missing installed schema helper wrapper: {helper_path}")
            if not os.access(helper_path, os.X_OK):
                fail(f"schema helper wrapper is not executable: {helper_path}")

    @staticmethod
    def _relative_file_manifest(root: Path) -> list[str]:
        if not root.is_dir():
            fail(f"missing directory: {root}")
        return sorted(
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file()
        )

    def _verify_runtime_hook_assets(self) -> None:
        runtime_scripts_dir = self._runtime_hooks_scripts_dir()
        runtime_driver = runtime_scripts_dir / "hook_driver.pl"
        if not runtime_driver.is_file():
            fail(f"missing runtime hook driver: {runtime_driver}")

        runtime_lib_dir = self._runtime_hooks_lib_dir()
        runtime_schema_dir = self._runtime_hooks_schema_dir()
        runtime_hooks_config_path = self._runtime_hooks_config_path()
        if not runtime_hooks_config_path.is_file():
            fail(f"missing runtime hooks config: {runtime_hooks_config_path}")

        source_script_files = sorted(
            path.name for path in self._hooks_source_dir().glob("*.pl") if path.is_file()
        )
        runtime_script_files = sorted(
            path.name for path in runtime_scripts_dir.glob("*.pl") if path.is_file()
        )
        if source_script_files != runtime_script_files:
            missing = sorted(set(source_script_files) - set(runtime_script_files))
            unexpected = sorted(set(runtime_script_files) - set(source_script_files))
            details: list[str] = []
            if missing:
                details.append(f"missing files: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected files: {', '.join(unexpected)}")
            fail(f"runtime hook scripts drift detected at {runtime_scripts_dir} ({'; '.join(details)})")

        checks = (
            ("runtime hook Perl libs", self._hooks_lib_source_dir(), runtime_lib_dir),
            ("runtime hook schemas", self._hooks_schema_source_dir(), runtime_schema_dir),
        )
        for label, source_root, runtime_root in checks:
            source_files = self._relative_file_manifest(source_root)
            runtime_files = self._relative_file_manifest(runtime_root)
            if source_files != runtime_files:
                missing = sorted(set(source_files) - set(runtime_files))
                unexpected = sorted(set(runtime_files) - set(source_files))
                details: list[str] = []
                if missing:
                    details.append(f"missing files: {', '.join(missing)}")
                if unexpected:
                    details.append(f"unexpected files: {', '.join(unexpected)}")
                fail(f"{label} drift detected at {runtime_root} ({'; '.join(details)})")

        for schema_path in sorted(runtime_schema_dir.glob("*.json")):
            try:
                payload = json.loads(schema_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                fail(f"runtime hook schema is not valid JSON: {schema_path}: {exc}")
            if not isinstance(payload, dict):
                fail(f"runtime hook schema must be a JSON object: {schema_path}")

        expected_hooks_payload = self._render_hooks_config_payload()
        actual_hooks_payload = parse_json_file(runtime_hooks_config_path)
        if actual_hooks_payload != expected_hooks_payload:
            fail(f"runtime hooks config drift detected at {runtime_hooks_config_path}")

    def _verify_lookup_assets(self) -> None:
        secrets_path = self._managed_secrets_path()
        auth_path = self._managed_auth_path()
        if not secrets_path.is_file():
            fail(f"missing installed managed secrets file: {secrets_path}")
        if not auth_path.is_file():
            fail(f"missing installed login auth file: {auth_path}")
        try:
            parse_managed_secrets_file(secrets_path)
            parse_login_auth_file(auth_path)
        except (ManagedSecretsError, CodexLoginAuthError) as exc:
            fail(str(exc))

    def _verify_release_schema_snapshot(self) -> None:
        latest_path = self._schema_latest_snapshot_path()
        if not latest_path.is_file():
            fail(f"missing latest release schema snapshot: {latest_path}")
        try:
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"latest release schema snapshot is not valid JSON: {latest_path}: {exc}")
        if not isinstance(payload, dict):
            fail(f"latest release schema snapshot must be a JSON object: {latest_path}")

    def _install_shell_path_profile(self) -> None:
        target = self._path_profile_target()
        try:
            content = render_shell_path_profile(
                self._share_dir(),
                self._wrapper_dir(),
                self._stage_environment_exports() if self._stage_mode() else self._shell_profile_exports(),
                guard_user=self._current_username(),
            )
        except RuntimeRenderError as exc:
            fail(str(exc))
        self._write_file(target, content, mode=0o644)

    def _current_username(self) -> str:
        username = getpass.getuser().strip()
        if not username:
            fail("unable to determine current username for environment guard")
        if any(ch in username for ch in ("\x00", "\n", "\r", '"')):
            fail("current username contains unsupported characters")
        return username

    def _install_user_shell_hooks(self) -> None:
        args = [
            "bash",
            str(self._env_script_path()),
            "hook",
            "--user-home",
            str(self._user_home_dir()),
            "--profile-path",
            str(self._path_profile_target()),
        ]
        if self.dry_run:
            args.append("--dry-run")
        self._run_command(args)

    def _completion_targets(self) -> dict[str, Path]:
        home = self._user_home_dir()
        return {shell: home / relative for shell, relative in SHELL_COMPLETION_TARGETS.items()}

    def _render_shell_completion(self, shell: str) -> str:
        if shell not in SHELL_COMPLETION_TARGETS:
            fail(f"unsupported completion shell: {shell}")
        binary_path = self._codex_binary_path()
        if not binary_path.is_file():
            fail(f"missing codex binary for completion generation: {binary_path}")
        if not os.access(binary_path, os.X_OK):
            fail(f"codex binary is not executable for completion generation: {binary_path}")
        try:
            proc = subprocess.run(
                [str(binary_path), "completion", shell],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        except FileNotFoundError as exc:
            fail(f"required command is unavailable: {exc}")
        except subprocess.TimeoutExpired as exc:
            fail(f"completion generation timed out for {shell}: {exc}")
        except subprocess.CalledProcessError as exc:
            fail(f"completion generation failed for {shell}, exit code {exc.returncode}")

        rendered = proc.stdout
        if not rendered.strip():
            fail(f"completion output is empty for {shell}")
        if "\x00" in rendered:
            fail(f"completion output contains unsupported characters for {shell}")
        if not rendered.endswith("\n"):
            rendered += "\n"
        return rendered

    def _install_user_shell_completions(self) -> None:
        for shell, target in sorted(self._completion_targets().items()):
            if self.dry_run:
                print(f"[dry-run] mkdir -p {target.parent}")
                print(f"[dry-run] write {target}")
                continue
            content = self._render_shell_completion(shell)
            self._mkdir_path(target.parent)
            self._write_file(target, content, mode=0o644)

    def _verify_shell_path_profile(self) -> None:
        target = self._path_profile_target()
        if not target.is_file():
            fail(f"missing shell PATH profile: {target}")
        text = target.read_text(encoding="utf-8")
        wrappers = str(self._wrapper_dir())
        helpers = str(self._share_dir() / "helpers")
        bin_dir = str(self._share_dir() / "bin")
        legacy_shims = str(self._share_dir() / "shims")
        if wrappers not in text:
            fail(f"shell PATH profile missing wrapper directory: {target}")
        if helpers not in text:
            fail(f"shell PATH profile missing helpers directory: {target}")
        if bin_dir in text:
            fail(f"shell PATH profile must not add share/bin to PATH: {target}")
        if legacy_shims in text:
            fail(f"shell PATH profile must not add legacy share/shims to PATH: {target}")
        guard_marker = f'codex_target_user="{self._current_username()}"'
        if guard_marker not in text:
            fail(f"shell PATH profile missing current-user guard: {target}")
        for key, value in self._shell_profile_exports().items():
            marker = f'export {key}="{value}"'
            if marker not in text:
                fail(f"shell PATH profile missing environment export for {key}: {target}")

    def _verify_user_shell_hooks(self) -> None:
        args = [
            "bash",
            str(self._env_script_path()),
            "hook",
            "--verify",
            "--user-home",
            str(self._user_home_dir()),
            "--profile-path",
            str(self._path_profile_target()),
        ]
        self._run_command(args)

    def _verify_user_shell_completions(self) -> None:
        for shell, target in sorted(self._completion_targets().items()):
            if not target.is_file():
                fail(f"missing {shell} completion file: {target}")
            rendered = target.read_text(encoding="utf-8")
            if not rendered.strip():
                fail(f"{shell} completion file is empty: {target}")

    @staticmethod
    def _legacy_secure_wrapper_name(binary_name: str) -> str:
        rendered = binary_name.strip()
        if not rendered:
            fail("wrapper binary name cannot be empty")
        return f"{rendered}-s"

    def _sync_wrapper_aliases(self, binary_names: list[str]) -> None:
        try:
            content = render_wrapper_aliases(binary_names)
        except RuntimeRenderError as exc:
            fail(str(exc))
        self._write_file(self._wrapper_aliases_target(), content, mode=0o644)

    def _remove_legacy_secure_release_shims(self, binary_names: list[str]) -> None:
        wrapper_dir = self._wrapper_dir()
        for name in sorted(set(binary_names)):
            legacy_path = wrapper_dir / self._legacy_secure_wrapper_name(name)
            if not legacy_path.exists():
                continue
            if not self._is_managed_wrapper_file(legacy_path):
                continue
            self._remove_path_force(legacy_path)

    def _sync_release_shims(
        self,
        binary_names: list[str],
        launch_env: dict[str, str] | None = None,
    ) -> None:
        if self.dry_run and not binary_names:
            print("[dry-run] write wrappers for all release binaries discovered at install time")
            return
        if not binary_names:
            fail("release install did not produce any binaries for wrapper generation")

        share_dir = self._share_dir()
        wrapper_dir = self._wrapper_dir()
        effective_launch_env = self.launch_env if launch_env is None else launch_env
        managed_secrets_path = self._managed_secrets_path()
        managed_secret_helper_path = self._managed_secret_env_helper_target()
        home_config_path = self._home_config_path()
        for name in sorted(set(binary_names)):
            binary_path = share_dir / "bin" / name
            shim_path = wrapper_dir / name
            try:
                shim_content = render_codex_shim(
                    binary_path,
                    launch_env=effective_launch_env,
                    share_dir=share_dir,
                    wrapper_dir=wrapper_dir,
                    managed_secrets_path=managed_secrets_path,
                    managed_secret_helper_path=managed_secret_helper_path,
                    host_config_path=home_config_path,
                )
            except RuntimeRenderError as exc:
                fail(str(exc))
            self._write_file(shim_path, shim_content, mode=0o755)
        self._remove_legacy_secure_release_shims(binary_names)

    def _install_runtime_binary_wrappers(self, binary_names: list[str]) -> None:
        self._log("installing managed secret helper")
        self._sync_managed_secret_env_helper()
        self._log("installing codex login wrapper")
        self._sync_codex_login_wrapper()
        self._log("installing codex MCP token wrapper")
        self._sync_codex_mcp_token_wrapper()
        self._sync_release_shims(binary_names)
        self._sync_wrapper_aliases(binary_names)
        self._log("installing shell completion files")
        self._install_user_shell_completions()
        self._log("installing schema helper wrappers")
        self._sync_schema_helpers()

    def _existing_release_binary_names(self) -> list[str]:
        bin_dir = self._share_dir() / "bin"
        if not bin_dir.is_dir():
            return []
        return sorted(path.name for path in bin_dir.iterdir() if path.is_file())

    def _refresh_runtime_launch_wrappers(self, launch_env: dict[str, str]) -> None:
        self._sync_managed_secret_env_helper()
        self._sync_codex_login_wrapper()
        self._sync_codex_mcp_token_wrapper()
        binary_names = self._existing_release_binary_names()
        if binary_names:
            self._sync_release_shims(binary_names, launch_env=launch_env)
            self._sync_wrapper_aliases(binary_names)

        helpers_dir = self._helpers_dir()
        if not helpers_dir.is_dir():
            return

        schema_targets_present = (helpers_dir / SCHEMA_TOOL_SOURCE_FILENAME).is_file() or any(
            (helpers_dir / name).is_file() for name in SCHEMA_HELPER_NAMES
        )
        if schema_targets_present:
            self._sync_schema_helpers(launch_env=launch_env)

    def apply_vars_init(self) -> None:
        self.setup_environment()
        self._log("refreshing launch environment in runtime wrappers/helpers")
        self._refresh_runtime_launch_wrappers(self.launch_env)

    def apply_vars_reset(self) -> None:
        self._log("removing launch environment from runtime wrappers/helpers")
        self._refresh_runtime_launch_wrappers({})
        self.reset_environment()

    def _verify_release_shims(self) -> None:
        share_dir = self._share_dir()
        bin_dir = share_dir / "bin"
        shims_dir = self._wrapper_dir()
        if not bin_dir.is_dir():
            fail(f"missing release bin directory: {bin_dir}")
        if not shims_dir.is_dir():
            fail(f"missing release shims directory: {shims_dir}")

        binaries = sorted(path for path in bin_dir.iterdir() if path.is_file())
        if not binaries:
            fail(f"release bin directory has no binaries: {bin_dir}")

        for binary in binaries:
            if not os.access(binary, os.X_OK):
                fail(f"release binary is not executable: {binary}")
            shim_path = shims_dir / binary.name
            if not shim_path.is_file():
                fail(f"missing shim for release binary {binary.name}: {shim_path}")
            if not os.access(shim_path, os.X_OK):
                fail(f"shim is not executable for release binary {binary.name}: {shim_path}")
            legacy_secure_shim = shims_dir / self._legacy_secure_wrapper_name(binary.name)
            if legacy_secure_shim.exists():
                fail(f"legacy secure shim must not exist for release binary {binary.name}: {legacy_secure_shim}")
        login_wrapper = self._codex_login_wrapper_target()
        if not login_wrapper.is_file():
            fail(f"missing managed codex login wrapper: {login_wrapper}")
        if not os.access(login_wrapper, os.X_OK):
            fail(f"managed codex login wrapper is not executable: {login_wrapper}")
        mcp_token_wrapper = self._codex_mcp_token_wrapper_target()
        if not mcp_token_wrapper.is_file():
            fail(f"missing managed codex MCP token wrapper: {mcp_token_wrapper}")
        if not os.access(mcp_token_wrapper, os.X_OK):
            fail(f"managed codex MCP token wrapper is not executable: {mcp_token_wrapper}")

    def _is_managed_wrapper_file(self, path: Path) -> bool:
        if path.is_symlink() or not path.is_file():
            return False
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:4096]
        except OSError:
            return False
        return "# managed by codex installer" in text

    def _managed_wrapper_targets_for_uninstall(self) -> list[Path]:
        wrapper_dir = self._wrapper_dir()
        targets: set[Path] = set()
        bin_dir = self._share_dir() / "bin"

        if bin_dir.is_dir():
            for binary in sorted(bin_dir.iterdir(), key=lambda item: item.name):
                if binary.is_file() and not binary.is_symlink():
                    targets.add(wrapper_dir / binary.name)

        if wrapper_dir.is_dir():
            for candidate in sorted(wrapper_dir.iterdir(), key=lambda item: item.name):
                if self._is_managed_wrapper_file(candidate):
                    targets.add(candidate)

        return sorted(targets, key=lambda item: str(item))

    def _copy_backup_source(
        self,
        source: Path,
        target: Path,
        *,
        exclude_root_children: frozenset[str] = frozenset(),
    ) -> None:
        def ignore(dir_path: str, names: list[str]) -> list[str]:
            if normalize_path(dir_path) != source:
                return []
            return sorted(name for name in names if name in exclude_root_children)

        if self._needs_sudo_write(target.parent):
            script = (
                "import json, shutil, sys\n"
                "from pathlib import Path\n"
                "src = Path(sys.argv[1])\n"
                "dst = Path(sys.argv[2])\n"
                "excluded = set(json.loads(sys.argv[3]))\n"
                "def ignore(dir_path, names):\n"
                "    if Path(dir_path).resolve(strict=False) != src:\n"
                "        return []\n"
                "    return sorted(name for name in names if name in excluded)\n"
                "if not src.exists():\n"
                "    dst.mkdir(parents=True, exist_ok=True)\n"
                "elif not src.is_dir():\n"
                "    raise SystemExit(f'backup source must be a directory: {src}')\n"
                "else:\n"
                "    dst.parent.mkdir(parents=True, exist_ok=True)\n"
                "    shutil.copytree(src, dst, symlinks=True, ignore=ignore)\n"
            )
            self._run_with_sudo(
                ["python3", "-c", script, str(source), str(target), json.dumps(sorted(exclude_root_children))]
            )
            return

        if not source.exists():
            target.mkdir(parents=True, exist_ok=True)
            return

        if not os.access(source, os.R_OK | os.X_OK):
            fail(f"backup source is not readable: {source}")

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=True, ignore=ignore)

    def _backup_to_run_root(
        self,
        *,
        backup_root: Path,
        run_root: Path,
        source: Path,
        label: str,
        flow: str,
    ) -> None:
        if is_within(source, backup_root) or is_within(backup_root, source):
            fail(f"backup root must not overlap source {source}: backup={backup_root}")
        target = run_root / label
        exclude_root_children = HOME_BACKUP_EXCLUDE_ROOT_CHILDREN if label == "home" else frozenset()

        if self.dry_run:
            print(f"[dry-run] backup[{flow}] {source} -> {target}")
            return

        if target.exists():
            self._remove_path_force(target)
        self._copy_backup_source(source, target, exclude_root_children=exclude_root_children)

    def _backup_install_state(self, *, flow: str) -> None:
        backup_root = ensure_safe_absolute_path("CODEX_BACKUP_DIR", self.env["CODEX_BACKUP_DIR"])
        if flow not in {"install", "runtime", "runtime-home", "runtime-skills", "runtime-instructions", "uninstall"}:
            fail(f"unsupported backup flow: {flow}")
        sources = self._backup_source_paths()
        account_key = self._backup_account_key(sources)

        if self.dry_run:
            print(f"[dry-run] mkdir -p {backup_root}")
        else:
            self._mkdir_path(backup_root)

        run_root = self._backup_run_root(backup_root, account_key=account_key, flow=flow)
        if self.dry_run:
            print(f"[dry-run] mkdir -p {run_root}")
        else:
            self._mkdir_path(run_root)

        for label, source in sources:
            self._backup_to_run_root(
                backup_root=backup_root,
                run_root=run_root,
                source=source,
                label=label,
                flow=flow,
            )

    def _is_same_or_within(self, path: Path, root: Path) -> bool:
        return path == root or is_within(path, root)

    def _is_preserved_path(self, path: Path, preserve_roots: list[Path]) -> bool:
        return any(self._is_same_or_within(path, root) for root in preserve_roots)

    def _contains_preserved_descendant(self, path: Path, preserve_roots: list[Path]) -> bool:
        return any(self._is_same_or_within(root, path) for root in preserve_roots)

    def _remove_path_force(self, path: Path) -> None:
        if self.dry_run:
            print(f"[dry-run] rm -rf {path}")
            return
        if needs_sudo_remove(path):
            self._run_with_sudo(["rm", "-rf", "--", str(path)])
        else:
            self._run_command(["rm", "-rf", "--", str(path)])

    def _nuke_path_preserving(self, path: Path, preserve_roots: list[Path]) -> None:
        if self._is_preserved_path(path, preserve_roots):
            return
        if not path.exists():
            return
        if not self._contains_preserved_descendant(path, preserve_roots):
            self._remove_path_force(path)
            return
        if not path.is_dir():
            self._remove_path_force(path)
            return

        for child in sorted(path.iterdir()):
            self._nuke_path_preserving(child, preserve_roots)

    def _sync_global_environment(self) -> None:
        self._log("installing current-user environment exports and hooks")
        self._install_shell_path_profile()
        self._install_user_shell_hooks()

    def _shell_profile_exports(self) -> dict[str, str]:
        exports = dict(self.global_vars)
        exports.update(self.launch_env)
        return exports

    def _stage_environment_exports(self) -> dict[str, str]:
        return self._shell_profile_exports()

    def _install_stage_environment_exports(self) -> None:
        activation_path = self._stage_activation_path()
        try:
            content = render_shell_path_profile(
                self._share_dir(),
                self._wrapper_dir(),
                self._stage_environment_exports(),
            )
        except RuntimeRenderError as exc:
            fail(str(exc))
        self._write_file(activation_path, content, mode=0o755)
        print(f'[info] source "{activation_path}" to test the staged dry-run wrappers')

    def _prepare_runtime_install_state(self, artifacts: CompiledArtifacts, *, flow: str) -> None:
        self._prepare_runtime_refresh_base(flow=flow)
        self.apply_home_bundle()
        self.apply_admin(artifacts)
        self.setup_environment()

    def _prepare_runtime_refresh_base(self, *, flow: str) -> None:
        self._log(f"creating {flow} backup")
        self._backup_install_state(flow=flow)
        self._log("ensuring runtime directories")
        self._ensure_runtime_directories()
        self._log("syncing managed secrets file")
        self._sync_managed_secrets_file()
        self._log("syncing login auth file")
        self._sync_managed_auth_file()
        if self._stage_mode():
            self._log("skipping managed secret-tool mutation for staged dry-run install")
        else:
            self._log("checking managed secret-tool entries")
            self._ensure_enabled_managed_secrets()
        self._log("hardening executable directories")
        self._secure_exec_directories()

    def _purge_codex_environment(self) -> None:
        env_script = self._env_script_path()
        args = [
            "bash",
            str(env_script),
            "unhook",
            "--user-home",
            str(self._user_home_dir()),
            "--profile-path",
            str(self._path_profile_target()),
        ]
        if self.dry_run:
            args.append("--dry-run")
        self._run_command(args)

    def reset_environment(self) -> None:
        if self._stage_mode():
            return
        self._log("removing current-user CODEX shell hooks and profile exports")
        self._purge_codex_environment()

    def uninstall(self) -> None:
        required_env = (
            "CODEX_ROOT_DIR",
            "CODEX_SYSTEM_DIR",
            "CODEX_USER_DIR",
            "CODEX_SHARE_DIR",
            "CODEX_WRAPPER_DIR",
            "CODEX_MCP_DIR",
            "CODEX_BACKUP_DIR",
        )
        required_runtime = (
            "CODEX_HOME",
            "CODEX_AGENTS",
            "CODEX_SKILLS",
            "CODEX_LOG_DIR",
            "CODEX_SQLITE_HOME",
        )

        for key in required_env:
            value = self.env.get(key, "").strip()
            if not value:
                fail(f"missing required .env key for nuke: {key}")
        for key in required_runtime:
            value = self.runtime_vars.get(key, "").strip()
            if not value:
                fail(f"missing required runtime path derived from .env for nuke: {key}")

        backup_root = ensure_safe_absolute_path("CODEX_BACKUP_DIR", self.env["CODEX_BACKUP_DIR"])
        mcp_root = ensure_safe_absolute_path("CODEX_MCP_DIR", self.env["CODEX_MCP_DIR"])
        sqlite_home = ensure_safe_absolute_path("CODEX_SQLITE_HOME", self.runtime_vars["CODEX_SQLITE_HOME"])
        auth_lookup = self._managed_auth_path()
        preserve_roots = sorted({backup_root, mcp_root, sqlite_home, auth_lookup}, key=lambda item: str(item))

        self._log("creating nuke backup")
        self._backup_install_state(flow="uninstall")

        root_dir = ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"])
        system_dir = ensure_safe_absolute_path("CODEX_SYSTEM_DIR", self.env["CODEX_SYSTEM_DIR"])
        target_paths = {root_dir, system_dir}

        candidate_paths = {
            ensure_safe_absolute_path("CODEX_ROOT_DIR", self.env["CODEX_ROOT_DIR"]),
            ensure_safe_absolute_path("CODEX_SYSTEM_DIR", self.env["CODEX_SYSTEM_DIR"]),
            ensure_safe_absolute_path("CODEX_USER_DIR", self.env["CODEX_USER_DIR"]),
            ensure_safe_absolute_path("CODEX_SHARE_DIR", self.env["CODEX_SHARE_DIR"]),
            ensure_safe_absolute_path("CODEX_MCP_DIR", self.env["CODEX_MCP_DIR"]),
            ensure_safe_absolute_path("CODEX_BACKUP_DIR", self.env["CODEX_BACKUP_DIR"]),
            ensure_safe_absolute_path("CODEX_HOME", self.runtime_vars["CODEX_HOME"]),
            ensure_safe_absolute_path("CODEX_AGENTS", self.runtime_vars["CODEX_AGENTS"]),
            ensure_safe_absolute_path("CODEX_SKILLS", self.runtime_vars["CODEX_SKILLS"]),
            ensure_safe_absolute_path("CODEX_LOG_DIR", self.runtime_vars["CODEX_LOG_DIR"]),
            ensure_safe_absolute_path("CODEX_SQLITE_HOME", self.runtime_vars["CODEX_SQLITE_HOME"]),
        }
        candidate_paths.add(self._mcp_ssh_key_path())
        candidate_paths.add(self._mcp_known_hosts_path())

        for candidate in sorted(candidate_paths, key=lambda item: str(item)):
            if self._is_preserved_path(candidate, preserve_roots):
                continue
            if self._is_same_or_within(candidate, root_dir):
                continue
            if self._is_same_or_within(candidate, system_dir):
                continue
            target_paths.add(candidate)

        target_paths.update(self._managed_wrapper_targets_for_uninstall())
        target_paths.add(self._path_profile_target())

        if self._stage_mode():
            self._log("skipping managed secret-tool cleanup for staged dry-run uninstall")
        else:
            self._log("clearing managed secret-tool entries (best-effort)")
            self._clear_all_managed_secrets()

        self._log("removing runtime paths (preserving backup/mcp/sqlite/codex-login auth)")
        for target in sorted(target_paths, key=lambda item: (len(item.parts), str(item))):
            self._nuke_path_preserving(target, preserve_roots)

        self.reset_environment()

    def _instruction_file_overrides(
        self,
        manifest_path: Path,
        *,
        config_file: str | None = None,
    ) -> dict[str, str]:
        overrides: dict[str, str] = {}
        for entry in self._instruction_manifest_entries(manifest_path, config_file=config_file):
            key = entry["config_key"]
            if key is None:
                continue
            if entry.get("value_mode") == "inline_text":
                source_text = entry.get("source_text")
                if source_text:
                    overrides[key] = source_text
                continue
            target_field = "default_enable_path" if entry["enabled"] else "default_disable_path"
            target_value = entry.get(target_field)
            if not target_value:
                continue
            overrides[key] = target_value
        return overrides

    def _local_plugin_bundle_dirs(self, source_root: Path) -> list[str]:
        return local_plugin_bundle_dirs(source_root)

    def _plugin_manifest_marketplace_name(self) -> str:
        inventory_path = getattr(self, "plugins_json_path", None)
        if inventory_path is None:
            repo_layout = getattr(self, "repo_layout", None)
            inventory_path = repo_layout.plugins_inventory_path if repo_layout is not None else None
        if inventory_path is None:
            return ""

        effective_payload = getattr(self, "effective_plugins_metadata_payload", {})
        if effective_payload:
            return plugin_manifest_marketplace_name(effective_payload, inventory_path)

        raw_payload = getattr(self, "plugins_metadata_payload", {})
        if not raw_payload:
            return ""
        return plugin_manifest_marketplace_name(raw_payload, inventory_path)

    def _plugin_skill_source_path(self, skill_source: str) -> Path:
        return plugin_skill_source_path(self.repo_root, self.plugins_json_path, skill_source)

    def _plugin_manifest_tools(self, bundle: dict[str, Any], bundle_name: str) -> tuple[dict[str, dict[str, Any]], list[Any]]:
        raise NotImplementedError("plugin manifest tools parsing moved to src/install/plugins.py")

    def _plugin_manifest_bundles(self, *, enabled_only: bool) -> list[PluginBundleSpec]:
        return plugin_manifest_bundles(
            repo_root=self.repo_root,
            plugins_payload=self.plugins_payload,
            plugins_path=self.plugins_path,
            plugins_metadata_payload=self.effective_plugins_metadata_payload,
            plugins_metadata_path=self.plugins_json_path,
            shared_mcp_servers=self.mcp_payload.get("mcp_servers", {}),
            enabled_only=enabled_only,
        )

    def _validate_plugin_bundle_inventory(self, source_root: Path) -> list[PluginBundleSpec]:
        return validate_plugin_bundle_inventory(self, source_root)

    def _sync_runtime_plugin_bundle(self, source_root: Path, target_root: Path, bundle: PluginBundleSpec) -> None:
        sync_runtime_plugin_bundle(self, source_root, target_root, bundle)

    def _sync_local_plugins(self) -> None:
        sync_local_plugins(self)

    @staticmethod
    def _parse_toml_table_path(line: str) -> list[str] | None:
        match = re.match(r"^\s*\[([^\]]+)\]\s*$", line)
        if not match:
            return None
        raw = match.group(1).strip()
        if not raw:
            return []
        parts = [part.strip().strip("\"'") for part in raw.split(".")]
        return [part for part in parts if part]

    def _replace_toml_assignment(self, text: str, key: str, value: str) -> tuple[str, bool]:
        lines = text.splitlines()
        key_path = [part for part in key.split(".") if part]
        table_path = key_path[:-1]
        assignment_key = key_path[-1]
        single_line_pattern = re.compile(
            rf"^(\s*{re.escape(assignment_key)}\s*=\s*)(\"[^\"]*\"|'[^']*')(\s*(?:#.*)?)$"
        )
        multiline_start_pattern = re.compile(
            rf"^(\s*{re.escape(assignment_key)}\s*=\s*)\"\"\"(.*)$"
        )
        current_table: list[str] = []
        for idx, line in enumerate(lines):
            parsed_table = self._parse_toml_table_path(line)
            if parsed_table is not None:
                current_table = parsed_table
                continue
            if current_table != table_path:
                continue
            match = single_line_pattern.match(line)
            if match:
                lines[idx] = f"{match.group(1)}{json.dumps(value)}{match.group(3)}"
                rendered = "\n".join(lines)
                if text.endswith("\n"):
                    rendered += "\n"
                return rendered, True
            multiline_start = multiline_start_pattern.match(line)
            if not multiline_start:
                continue
            if '"""' in value:
                fail(f"TOML multiline override for {key} contains triple quotes")
            prefix = multiline_start.group(1)
            initial_tail = multiline_start.group(2)
            end_idx: int | None = None
            closing_suffix = ""
            close_pos = initial_tail.find('"""')
            if close_pos >= 0:
                end_idx = idx
                closing_suffix = initial_tail[close_pos + 3 :]
            else:
                for candidate_idx in range(idx + 1, len(lines)):
                    close_pos = lines[candidate_idx].find('"""')
                    if close_pos < 0:
                        continue
                    end_idx = candidate_idx
                    closing_suffix = lines[candidate_idx][close_pos + 3 :]
                    break
            if end_idx is None:
                fail(f"unterminated TOML multiline string for {key}")
            replacement = [f'{prefix}"""']
            replacement.extend(value.splitlines())
            replacement.append(f'"""{closing_suffix}')
            lines[idx : end_idx + 1] = replacement
            rendered = "\n".join(lines)
            if text.endswith("\n"):
                rendered += "\n"
            return rendered, True
        return text, False

    def _apply_instruction_file_overrides(
        self,
        text: str,
        *,
        manifest_path: Path | None = None,
        config_file: str | None = None,
    ) -> str:
        rendered = text
        overrides = self._instruction_file_overrides(
            manifest_path or self._default_instruction_manifest_path(),
            config_file=config_file,
        )
        missing_keys: list[str] = []
        for key in sorted(overrides.keys()):
            # Config fragments are user-owned. If a key is commented out or removed,
            # leave it absent instead of treating that as an installer error.
            rendered, replaced = self._replace_toml_assignment(rendered, key, overrides[key])
            if not replaced:
                missing_keys.append(key)
        if missing_keys:
            self._warn_once(
                "instruction metadata references config keys left unset in the rendered user config: "
                + ", ".join(f"`{key}`" for key in missing_keys)
                + "; continuing without those overrides"
            )
        return rendered

    def _render_home_toml(
        self,
        raw: str,
        config_path: Path,
        *,
        apply_instruction_overrides: bool,
        instruction_manifest_path: Path | None = None,
        instruction_config_file: str | None = None,
    ) -> str:
        rendered = _replace_known_placeholders_outside_toml_multiline_strings(raw, self.variables)
        if apply_instruction_overrides:
            rendered = self._apply_instruction_file_overrides(
                rendered,
                manifest_path=instruction_manifest_path or self._default_instruction_manifest_path(),
                config_file=instruction_config_file,
            )
        unresolved = _first_unresolved_codex_placeholder_outside_toml_multiline_strings(rendered)
        if unresolved is not None:
            fail(f"unresolved CODEX_* placeholder remains in {config_path}: {unresolved}")
        try:
            tomllib.loads(rendered)
        except tomllib.TOMLDecodeError as exc:
            fail(f"invalid rendered home TOML ({config_path}): {exc}")
        return rendered

    def _render_user_config_toml(self, raw: str, config_path: Path) -> str:
        del raw, config_path
        rendered = ""
        for path in (
            self.repo_layout.user_config_path,
            self.repo_layout.user_pref_path,
            self.repo_layout.user_features_path,
            self.repo_layout.user_memory_path,
        ):
            rendered = self._append_compiled_fragment(rendered, self._render_user_fragment(path))
        rendered = self._append_compiled_fragment(rendered, self._render_home_apps_fragment())
        rendered = self._append_compiled_fragment(
            rendered,
            self._render_user_fragment(self.repo_layout.user_policy_path),
        )
        if rendered and not rendered.endswith("\n"):
            rendered += "\n"
        return self._apply_instruction_file_overrides(
            rendered,
            manifest_path=self._default_instruction_manifest_path(),
        )

    @staticmethod
    def _append_compiled_fragment(document: str, fragment: str) -> str:
        if not document:
            return fragment
        document = document.rstrip("\n")
        fragment = fragment.lstrip("\n")
        return document + "\n\n" + fragment

    @classmethod
    def _render_toml_table(cls, path: list[str], table: dict[str, Any]) -> str:
        scalar_items: list[tuple[str, Any]] = []
        child_items: list[tuple[str, dict[str, Any]]] = []
        for key, value in table.items():
            if isinstance(value, dict):
                child_items.append((key, value))
            else:
                scalar_items.append((key, value))

        sections: list[str] = []
        if path and (scalar_items or len(path) > 1):
            lines = ["[" + ".".join(toml_key(part) for part in path) + "]"]
            for key, value in scalar_items:
                lines.append(f"{toml_key(key)} = {toml_value(value)}")
            sections.append("\n".join(lines))

        for key, value in child_items:
            child = cls._render_toml_table([*path, key], value)
            if child:
                sections.append(child)
        return "\n\n".join(sections)

    @classmethod
    def _render_toml_document(cls, payload: dict[str, Any]) -> str:
        scalar_lines: list[str] = []
        sections: list[str] = []
        for key, value in payload.items():
            if isinstance(value, dict):
                child = cls._render_toml_table([key], value)
                if child:
                    sections.append(child)
                continue
            scalar_lines.append(f"{toml_key(key)} = {toml_value(value)}")
        if scalar_lines:
            sections.insert(0, "\n".join(scalar_lines))
        rendered = "\n\n".join(section for section in sections if section)
        if rendered and not rendered.endswith("\n"):
            rendered += "\n"
        return rendered

    def _resolved_user_apps_payload(self) -> dict[str, Any]:
        payload = resolve_object_placeholders(
            copy.deepcopy(self.plugins_payload),
            self.variables,
            "config/usr/apps.toml",
        )
        return self._ensure_runtime_local_marketplace(payload)

    def _ensure_runtime_local_marketplace(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            fail("config/usr/apps.toml must render to an object")

        marketplaces = payload.get("marketplaces", {})
        if marketplaces in (None, {}):
            marketplaces = {}
        if not isinstance(marketplaces, dict):
            fail("config/usr/apps.toml marketplaces must be an object")

        marketplace_name = self._plugin_manifest_marketplace_name()
        entry = marketplaces.get(marketplace_name, {})
        if entry in (None, {}):
            entry = {}
        if not isinstance(entry, dict):
            fail(f"config/usr/apps.toml marketplaces.{marketplace_name} must be an object")

        runtime_home = getattr(self, "runtime_vars", {}).get("CODEX_HOME") or getattr(self, "variables", {}).get("CODEX_HOME")
        if not isinstance(runtime_home, str) or not runtime_home:
            fail("CODEX_HOME must be available before rendering marketplaces")

        entry["source_type"] = "local"
        entry["source"] = runtime_home
        marketplaces[marketplace_name] = entry
        payload["marketplaces"] = marketplaces
        return payload

    def _render_home_apps_fragment(self) -> str:
        apps_payload = self._resolved_user_apps_payload()
        home_mcp_servers = apps_payload.get("mcp_servers", {})
        if home_mcp_servers in (None, {}):
            home_mcp_servers = {}
        if not isinstance(home_mcp_servers, dict):
            fail("config/usr/apps.toml mcp_servers must be an object")

        for server_name, override in home_mcp_servers.items():
            if not isinstance(server_name, str):
                fail(f"config/usr/apps.toml mcp_servers contains invalid server name: {server_name}")
            if not isinstance(override, dict):
                fail(f"config/usr/apps.toml mcp_servers.{server_name} must be an object")
            has_url = isinstance(override.get("url"), str) and override["url"].strip()
            has_command = isinstance(override.get("command"), str) and override["command"].strip()
            if not has_url and not has_command:
                self._warn_once(
                    "config/usr/apps.toml mcp_servers."
                    f"{server_name} does not define command or url; leaving that entry unchanged"
                )
        return self._render_toml_document(apps_payload)

    def _rendered_text_is_current(self, path: Path, rendered: str, *, mode: int) -> bool:
        if path.exists() and not path.is_file():
            fail(f"render target must be a regular file: {path}")
        if not path.is_file():
            return False
        try:
            current = path.read_text(encoding="utf-8")
            current_mode = stat.S_IMODE(path.stat().st_mode)
        except OSError:
            return False
        return current == rendered and current_mode == mode

    def _materialize_rendered_text(
        self,
        path: Path,
        rendered: str,
        *,
        mode: int = 0o644,
        dry_run_message: str,
    ) -> None:
        if self._rendered_text_is_current(path, rendered, mode=mode):
            return
        if self.dry_run:
            print(f"[dry-run] {dry_run_message} {path}")
            return
        self._write_file(path, rendered, mode=mode)

    def _materialize_home_config_paths(self, source_path: Path | None = None) -> None:
        del source_path
        config_path = Path(self.runtime_vars["CODEX_HOME"]) / "config.toml"
        rendered = self._render_user_config_toml("", config_path)
        self._materialize_rendered_text(
            config_path,
            rendered,
            dry_run_message="render compiled home config into",
        )

    def _materialize_agent_config_paths(self, source_dir: Path | None = None) -> None:
        runtime_agents_dir = Path(self.runtime_vars["CODEX_AGENTS"])
        resolved_source_dir = source_dir or runtime_agents_dir
        if not resolved_source_dir.is_dir():
            if source_dir is not None:
                fail(f"missing agent TOML source directory: {resolved_source_dir}")
            if not self.dry_run:
                fail(f"missing runtime agent TOML directory after sync: {runtime_agents_dir}")
            resolved_source_dir = self.repo_layout.agents_config_dir
            if not resolved_source_dir.is_dir():
                fail(f"missing agent TOML source directory: {resolved_source_dir}")

        source_paths = sorted(path for path in resolved_source_dir.glob("*.toml") if path.is_file())
        if not source_paths and source_dir is not None:
            fail(f"missing agent TOML source files: {resolved_source_dir}")

        for source_path in source_paths:
            target_path = runtime_agents_dir / source_path.name
            raw = source_path.read_text(encoding="utf-8")
            rendered = self._render_home_toml(
                raw,
                target_path,
                apply_instruction_overrides=True,
                instruction_manifest_path=self._agents_instruction_manifest_path(),
                instruction_config_file=source_path.name,
            )
            self._materialize_rendered_text(
                target_path,
                rendered,
                dry_run_message="render placeholders in",
            )

    def _render_runtime_toml_source(self, source_path: Path, label: str) -> str:
        raw = source_path.read_text(encoding="utf-8")
        rendered = replace_known_placeholders_in_text(raw, self.variables)
        if "$CODEX_" in rendered or "${CODEX_" in rendered:
            fail(f"unresolved CODEX_* placeholder remains in rendered {label}")
        try:
            tomllib.loads(rendered)
        except tomllib.TOMLDecodeError as exc:
            fail(f"invalid rendered {label}: {exc}")
        return rendered

    def _render_requirements_toml(self) -> str:
        raw = self.requirements_path.read_text(encoding="utf-8")
        return replace_known_placeholders_in_text(raw, self.variables)

    def _derive_package_version(self, package_name: str) -> str:
        normalized = package_name
        for suffix in (".tar.gz", ".tgz", ".tar.xz", ".zip"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        matches = VERSION_PATTERN.findall(normalized)
        if not matches:
            fail(f"unable to derive release version from package name: {package_name}")
        return matches[-1]

    def _download_file(self, url: str, destination: Path) -> None:
        if self.dry_run:
            print(f"[dry-run] download {url} -> {destination}")
            return

        headers = {"User-Agent": "codex-install/2.0"}

        with tempfile.NamedTemporaryFile(prefix="codex-download-", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)

        try:
            last_error = ""
            for attempt in range(1, 4):
                req = urllib.request.Request(url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=90) as response:
                        with temp_path.open("wb") as download_handle:
                            shutil.copyfileobj(response, download_handle)
                    self._copy_file(temp_path, destination)
                    return
                except Exception as exc:  # pragma: no cover - network/runtime dependent
                    last_error = str(exc)
                    if attempt < 3:
                        time.sleep(1)
            fail(f"failed to download {url}: {last_error}")
        finally:
            temp_path.unlink(missing_ok=True)

    def _install_release_schema_snapshot(self, extract_root: Path) -> None:
        if not extract_root.is_dir():
            fail(f"release extract root is not a directory for schema install: {extract_root}")

        candidates: list[Path] = []
        for candidate in sorted(extract_root.rglob(RELEASE_SCHEMA_FILENAME)):
            if not candidate.is_file():
                continue
            if candidate.parent.name != "share":
                continue
            candidates.append(candidate)

        if not candidates:
            fail("release package does not include share/config.schema.json")
        if len(candidates) > 1:
            rendered = ", ".join(str(path.relative_to(extract_root)) for path in candidates)
            fail(f"release package contains multiple share/config.schema.json files: {rendered}")

        source = candidates[0]
        latest_path = self._schema_latest_snapshot_path()
        self._copy_file(source, latest_path, mode=0o644)

    def _release_package_path(self) -> Path:
        return Path(self.env["CODEX_SHARE_DIR"]) / "release" / "pkg" / self.env["CODEX_DOWNLOAD_PKG"]

    def _release_package_url(self) -> str:
        package_name = self.env["CODEX_DOWNLOAD_PKG"]
        release_version = self._derive_package_version(package_name)
        return f"{self.env['CODEX_DOWNLOAD_URL'].rstrip('/')}/{release_version}/{package_name}"

    def _prepare_release_package(self) -> Path:
        expected_sha = self.env["CODEX_DOWNLOAD_SHA"].lower()
        full_url = self._release_package_url()
        archive_path = self._release_package_path()

        if archive_path.is_file():
            current_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            if current_sha != expected_sha:
                if self.dry_run:
                    print(f"[dry-run] remove invalid cached package {archive_path}")
                else:
                    if self._needs_sudo_write(archive_path.parent):
                        self._run_with_sudo(["rm", "-f", str(archive_path)])
                    else:
                        archive_path.unlink(missing_ok=True)

        if not archive_path.is_file():
            self._download_file(full_url, archive_path)

        if not self.dry_run:
            actual_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                fail(f"release package checksum mismatch: {archive_path}")
        return archive_path

    def _install_release_binary(self) -> list[str]:
        archive_path = self._prepare_release_package()
        release_bin_dir = Path(self.env["CODEX_SHARE_DIR"]) / "bin"

        if self.dry_run:
            print(f"[dry-run] install all release binaries from {archive_path} -> {release_bin_dir}")
            print(
                "[dry-run] install latest release schema snapshot "
                f"from {archive_path} -> {self._schema_latest_snapshot_path()}"
            )
            return []

        with tempfile.TemporaryDirectory(prefix="codex-release-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            try:
                with tarfile.open(archive_path, "r:gz") as tf:
                    safe_extractall(tf, tmp_root)
            except (tarfile.TarError, ArchiveSafetyError) as exc:
                fail(f"unable to extract release package {archive_path}: {exc}")

            try:
                discovered = discover_release_binaries(tmp_root)
            except (RuntimeError, ReleaseAssetError) as exc:
                fail(str(exc))
            self._install_release_schema_snapshot(tmp_root)
            installed: list[str] = []
            for binary in discovered:
                target = release_bin_dir / binary.name
                self._copy_file(binary, target, mode=0o755)
                installed.append(binary.name)

            if not installed:
                fail("release package did not produce installed binaries")
            self._log("installed release binaries: " + ", ".join(installed))
            return installed

    def _install_source_build_binary(self, output_dir: Path) -> list[str]:
        release_bin_dir = Path(self.env["CODEX_SHARE_DIR"]) / "bin"
        resolved_output_dir = output_dir.resolve(strict=False)
        if not resolved_output_dir.is_dir():
            fail(f"source build output directory is not a directory: {resolved_output_dir}")

        try:
            discovered = discover_release_binaries(resolved_output_dir)
        except (RuntimeError, ReleaseAssetError) as exc:
            fail(str(exc))

        schema_source = resolved_output_dir / "share" / RELEASE_SCHEMA_FILENAME
        if not schema_source.is_file():
            fail(f"source build output is missing share/{RELEASE_SCHEMA_FILENAME}: {resolved_output_dir}")

        if self.dry_run:
            print(f"[dry-run] install source-built binaries from {resolved_output_dir} -> {release_bin_dir}")
            print(
                "[dry-run] install patched schema snapshot "
                f"from {schema_source} -> {self._schema_latest_snapshot_path()}"
            )
            return [binary.name for binary in discovered]

        self._copy_file(schema_source, self._schema_latest_snapshot_path(), mode=0o644)
        installed: list[str] = []
        for binary in discovered:
            target = release_bin_dir / binary.name
            self._copy_file(binary, target, mode=0o755)
            installed.append(binary.name)

        if not installed:
            fail("source build output did not produce installed binaries")
        self._log("installed source-built binaries: " + ", ".join(installed))
        return installed

    def build_install(self, artifacts: CompiledArtifacts) -> None:
        self._ensure_install_dependencies()
        try:
            source_build_env = dict(self.env)
            source_build_env.update(load_source_build_environment(self.repo_root))
            if self._stage_mode():
                source_build_env.update(self._stage_source_build_overrides())
            source_build_settings = load_source_build_settings(source_build_env)
        except SourceBuildError as exc:
            fail(str(exc))

        if self.dry_run:
            source_ref = source_build_settings.base_ref or "HEAD"
            print(
                "[dry-run] build codex from source "
                f"({source_build_settings.repo_url} @ {source_ref}) into {source_build_settings.output_dir}"
            )
            print(
                "[dry-run] install source-built binaries "
                f"from {source_build_settings.output_dir} into {Path(self.env['CODEX_SHARE_DIR']) / 'bin'}"
            )
            return

        self._log("building source artifacts")
        try:
            build_result = build_from_settings(source_build_settings)
        except SourceBuildError as exc:
            fail(str(exc))

        self._prepare_runtime_install_state(artifacts, flow="install")
        self._log("installing source-built binaries and patched schema snapshot")
        installed_binaries = self._install_source_build_binary(build_result.output_dir)
        self._install_runtime_binary_wrappers(installed_binaries)

    def apply(self, artifacts: CompiledArtifacts) -> None:
        self._ensure_install_dependencies()
        self._prepare_runtime_install_state(artifacts, flow="install")
        self._log("installing release binaries")
        installed_binaries = self._install_release_binary()
        self._install_runtime_binary_wrappers(installed_binaries)

    def apply_runtime(self, artifacts: CompiledArtifacts) -> None:
        self._prepare_runtime_install_state(artifacts, flow="runtime")
        self._log("refreshing runtime wrappers/helpers for installed binaries")
        self._refresh_runtime_launch_wrappers(self.launch_env)
        self._log("installing shell completion files")
        self._install_user_shell_completions()

    def apply_runtime_home(self, artifacts: CompiledArtifacts) -> None:
        self._prepare_runtime_refresh_base(flow="runtime-home")
        self.apply_home()
        self.apply_admin(artifacts)
        self.setup_environment()
        self._log("refreshing runtime wrappers/helpers for installed binaries")
        self._refresh_runtime_launch_wrappers(self.launch_env)

    def apply_runtime_skills(self, artifacts: CompiledArtifacts) -> None:
        self._prepare_runtime_refresh_base(flow="runtime-skills")
        self.apply_apps()
        self.apply_skills()
        self._log("rendering CODEX_HOME/config.toml from config fragments")
        self._materialize_home_config_paths()
        self._log("rendering CODEX_AGENTS/*.toml with runtime paths")
        self._materialize_agent_config_paths(source_dir=self.repo_layout.agents_config_dir)
        self.apply_admin(artifacts)

    def apply_runtime_instructions(self) -> None:
        self._prepare_runtime_refresh_base(flow="runtime-instructions")
        self._log("syncing instruction assets")
        self._sync_instruction_assets()
        self._log("materializing default instruction assets")
        self._materialize_instruction_default_assets()
        self._log("rendering CODEX_HOME/config.toml from config fragments")
        self._materialize_home_config_paths()
        self._log("rendering CODEX_HOME/*.config.toml profile layers with runtime paths")
        self._materialize_profile_config_paths(source_dir=self.repo_layout.profiles_config_dir)

    def apply_home(self) -> None:
        home_src = self.repo_layout.home_user_dir
        profiles_src = self.repo_layout.profiles_config_dir
        agents_src = self.repo_layout.agents_config_dir
        home_dst = Path(self.runtime_vars["CODEX_HOME"])
        agents_dst = Path(self.runtime_vars["CODEX_AGENTS"])
        self._log("ensuring preserved CODEX_HOME roots exist without runtime->repo sync")
        self._seed_missing_home_runtime_state_from_repo(home_src, home_dst)
        self._log("syncing resources/home/user assets to CODEX_HOME (filtered)")
        self._sync_tree_filtered(
            home_src,
            home_dst,
            skip_root_toml=True,
            preserve_root_dirs=set(HOME_FILTER_PRESERVE_DIRS),
            preserve_root_files=set(HOME_FILTER_PRESERVE_FILES),
            mirror_deletions=True,
        )
        self._log("syncing runtime docs to CODEX_ROOT_DIR/docs")
        self._sync_runtime_docs()
        self._log("syncing config/agents role TOMLs to CODEX_AGENTS (filtered)")
        self._sync_tree_filtered(
            agents_src,
            agents_dst,
            skip_root_toml=False,
            preserve_root_dirs=set(),
            preserve_root_files=set(),
            mirror_deletions=True,
        )
        self._log("syncing instruction assets")
        self._sync_instruction_assets()
        self._log("materializing default instruction assets")
        self._materialize_instruction_default_assets()
        self._log("syncing Codex hook assets")
        self._sync_hooks_assets()
        self._log("rendering CODEX_HOME/config.toml from config fragments")
        self._materialize_home_config_paths()
        self._log("rendering CODEX_HOME/*.config.toml profile layers with runtime paths")
        self._materialize_profile_config_paths(source_dir=profiles_src)
        self._log("rendering CODEX_AGENTS/*.toml with runtime paths")
        self._materialize_agent_config_paths(source_dir=agents_src)
        self._log("linking CODEX_HOME/.agents/skills to CODEX_SKILLS")
        self._sync_agent_skills_symlink()

    def apply_home_bundle(self) -> None:
        self.apply_home()
        self.apply_apps()
        self.apply_skills()

    def _write_system_config_files(self, artifacts: CompiledArtifacts) -> None:
        system_dir = Path(self.env["CODEX_SYSTEM_DIR"])
        system_config_path = system_dir / "config.toml"
        rendered_system_config = artifacts.config_toml.read_text(encoding="utf-8")
        self._materialize_rendered_text(
            system_config_path,
            rendered_system_config,
            dry_run_message="materialize system config into",
        )
        self._materialize_rendered_text(
            system_dir / "requirements.toml",
            self._render_requirements_toml(),
            dry_run_message="materialize system requirements into",
        )
        self._remove_path_force(system_dir / "mcp.toml")
        self._remove_path_force(system_dir / "skills.toml")

    def apply_admin(self, artifacts: CompiledArtifacts) -> None:
        system_dir = Path(self.env["CODEX_SYSTEM_DIR"])
        self._log("ensuring system admin target directories")
        self._mkdir_path(system_dir)

        self._log("writing system configuration files")
        self._write_system_config_files(artifacts)
        self._log("syncing system/admin skill groups")
        self._sync_skill_groups(system_only=True)

    def apply_skills(self) -> None:
        self._log("ensuring user skills directory")
        self._mkdir_path(Path(self.runtime_vars["CODEX_SKILLS"]))
        self._log("syncing user skill groups")
        self._sync_skill_groups(user_only=True)
        self._log("linking CODEX_HOME/.agents/skills to CODEX_SKILLS")
        self._sync_agent_skills_symlink()

    def apply_apps(self) -> None:
        self._log("validating comprehensive plugin inventory")
        self._log("syncing runtime plugin bundles and marketplace")
        self._sync_local_plugins()

    def setup_environment(self) -> None:
        if self._stage_mode():
            self._log("writing staged dry-run activation exports")
            self._install_stage_environment_exports()
            return
        self._log("writing current-user environment files")
        self._sync_global_environment()

    def verify(self, output_dir: Path | None = None) -> None:
        self._render_requirements_toml()

        with tempfile.TemporaryDirectory(prefix="codex-verify-") as td:
            compiled_root = Path(td)
            if output_dir is not None:
                artifacts = self.compile(output_dir)
            else:
                artifacts = self.compile(compiled_root / "compiled")
            runtime_payload = parse_toml_file(artifacts.config_toml)
            mcp_servers = runtime_payload.get("mcp_servers")
            if not isinstance(mcp_servers, dict):
                fail("compiled config missing [mcp_servers] section")

            source_servers = self.mcp_payload.get("mcp_servers", {})
            if not set(source_servers.keys()).issubset(set(mcp_servers.keys())):
                fail("compiled config is missing shared mcp servers from config/vendor/mcp.toml")

            home_rendered = self._render_user_config_toml(
                "",
                Path(self.runtime_vars["CODEX_HOME"]) / "config.toml",
            )
            home_payload = tomllib.loads(home_rendered)
            home_mcp_servers = home_payload.get("mcp_servers")
            if home_mcp_servers not in (None, {}):
                if not isinstance(home_mcp_servers, dict):
                    fail("compiled home config mcp_servers must be an object when present")
                for server_name, server in home_mcp_servers.items():
                    if not isinstance(server, dict):
                        fail(f"compiled home config mcp_servers.{server_name} must be an object")
                    if not (
                        isinstance(server.get("url"), str) and server["url"].strip()
                    ) and not (
                        isinstance(server.get("command"), str) and server["command"].strip()
                    ):
                        fail(
                            "compiled home config mcp_servers."
                            f"{server_name} must include a full MCP transport definition"
                        )
            plugins = home_payload.get("plugins")
            if not isinstance(plugins, dict) or not plugins:
                fail("compiled home config missing [plugins] section")
            self._verify_rendered_plugin_runtime(compiled_root / "plugin-runtime", home_payload)

            verify_stage_root = compiled_root / "verify-stage"
            stage_installer = Installer(
                self.repo_root,
                dry_run=False,
                stage_root=verify_stage_root,
            )
            stage_installer.load()
            stage_installer.validate()
            stage_artifacts = stage_installer.compile(compiled_root / "verify-stage-compiled")
            stage_installer.apply(stage_artifacts)
            stage_installer._verify_lookup_assets()
            stage_installer._verify_runtime_hook_assets()
            stage_installer._verify_release_shims()
            stage_installer._verify_schema_helpers()
            stage_installer.apply_vars_init()
            stage_installer.apply_vars_reset()
            stage_installer.uninstall()

    def _enabled_plugin_ids_from_home_payload(self, home_payload: dict[str, Any]) -> set[str]:
        plugins = home_payload.get("plugins")
        if not isinstance(plugins, dict) or not plugins:
            fail("compiled home config missing [plugins] section")

        enabled_ids: set[str] = set()
        for plugin_id, payload in plugins.items():
            enabled: bool | None = None
            if isinstance(payload, bool):
                enabled = payload
            elif isinstance(payload, dict):
                enabled_value = payload.get("enabled")
                if not isinstance(enabled_value, bool):
                    fail(f"compiled home config plugin entry must declare boolean enabled for {plugin_id}")
                enabled = enabled_value
            else:
                fail(f"compiled home config plugin entry is invalid for {plugin_id}")
            if enabled:
                enabled_ids.add(plugin_id)
        return enabled_ids

    def _verify_rendered_plugin_runtime(self, output_root: Path, home_payload: dict[str, Any]) -> None:
        active_entries = self._plugin_manifest_bundles(enabled_only=True)
        if not active_entries:
            fail("resources/plugins/manifest.json did not render any enabled plugin bundles")

        enabled_plugin_ids = self._enabled_plugin_ids_from_home_payload(home_payload)
        rendered_plugin_ids = {entry.plugin_id for entry in active_entries}
        if enabled_plugin_ids != rendered_plugin_ids:
            missing_rendered = sorted(enabled_plugin_ids - rendered_plugin_ids)
            missing_config = sorted(rendered_plugin_ids - enabled_plugin_ids)
            details: list[str] = []
            if missing_rendered:
                details.append(f"missing rendered bundles: {', '.join(missing_rendered)}")
            if missing_config:
                details.append(f"missing config enablement: {', '.join(missing_config)}")
            fail(f"plugin config/manifest drift detected: {'; '.join(details)}")

        marketplace_name = self._plugin_manifest_marketplace_name()
        marketplaces = home_payload.get("marketplaces")
        if not isinstance(marketplaces, dict):
            fail("compiled home config missing [marketplaces] section")
        marketplace_entry = marketplaces.get(marketplace_name)
        if not isinstance(marketplace_entry, dict):
            fail(f"compiled home config missing [marketplaces.{marketplace_name}] section")
        if marketplace_entry.get("source_type") != "local":
            fail(f"compiled home config marketplaces.{marketplace_name}.source_type must be local")
        if marketplace_entry.get("source") != self.runtime_vars["CODEX_HOME"]:
            fail(
                f"compiled home config marketplaces.{marketplace_name}.source must equal "
                f"{self.runtime_vars['CODEX_HOME']}"
            )

        runtime_plugins_root = output_root / "plugins" / "cache" / marketplace_name
        marketplace_path = output_root / ".agents" / "plugins" / "marketplace.json"
        self._mkdir_path(runtime_plugins_root)
        self._mkdir_path(marketplace_path.parent)

        for bundle in active_entries:
            sync_runtime_plugin_bundle(
                self,
                self.repo_layout.plugins_skills_dir,
                runtime_plugins_root / bundle.name / "local",
                bundle,
            )

        self._write_file(
            marketplace_path,
            render_runtime_plugin_marketplace(marketplace_name, active_entries),
        )

        marketplace_payload = parse_json_file(marketplace_path)
        if marketplace_payload.get("name") != marketplace_name:
            fail(f"{marketplace_path} marketplace name does not match manifest marketplace_name")
        marketplace_plugins = marketplace_payload.get("plugins")
        if not isinstance(marketplace_plugins, list):
            fail(f"{marketplace_path} plugins must be a list")
        if len(marketplace_plugins) != len(active_entries):
            fail(f"{marketplace_path} plugin count does not match enabled bundle count")

        expected_marketplace_names = {entry.name for entry in active_entries}
        actual_marketplace_names: set[str] = set()
        for plugin_entry in marketplace_plugins:
            if not isinstance(plugin_entry, dict):
                fail(f"{marketplace_path} plugin entries must be objects")
            plugin_name = str(plugin_entry.get("name", "")).strip()
            if plugin_name not in expected_marketplace_names:
                fail(f"{marketplace_path} contains unknown plugin entry: {plugin_name}")
            source = plugin_entry.get("source")
            if not isinstance(source, dict):
                fail(f"{marketplace_path} plugin source must be an object for {plugin_name}")
            if source.get("source") != "local":
                fail(f"{marketplace_path} plugin source must be local for {plugin_name}")
            expected_path = runtime_marketplace_source_path(marketplace_name, plugin_name)
            if source.get("path") != expected_path:
                fail(f"{marketplace_path} plugin source path is invalid for {plugin_name}")
            actual_marketplace_names.add(plugin_name)
        if actual_marketplace_names != expected_marketplace_names:
            fail(f"{marketplace_path} marketplace entries do not match enabled bundles")

        for bundle in active_entries:
            plugin_root = runtime_plugins_root / bundle.name / "local"
            manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
            manifest_payload = parse_json_file(manifest_path)
            if manifest_payload.get("name") != bundle.name:
                fail(f"{manifest_path} plugin name does not match bundle name")
            if manifest_payload.get("skills") != "./skills":
                fail(f"{manifest_path} skills path must be ./skills")
            interface = manifest_payload.get("interface")
            if not isinstance(interface, dict):
                fail(f"{manifest_path} interface must be an object")
            if interface.get("displayName") != bundle.display_name:
                fail(f"{manifest_path} displayName does not match plugin manifest inventory for {bundle.name}")
            if interface.get("shortDescription") != bundle.short_description:
                fail(f"{manifest_path} shortDescription does not match plugin manifest inventory for {bundle.name}")
            if interface.get("defaultPrompt") != bundle.default_prompt:
                fail(f"{manifest_path} defaultPrompt does not match plugin manifest inventory for {bundle.name}")

            skills_root = plugin_root / "skills"
            if not skills_root.is_dir():
                fail(f"rendered plugin skills root is missing: {skills_root}")
            for skill_source in bundle.skills:
                skill_name = plugin_skill_source_path(self.repo_root, self.plugins_json_path, skill_source).name
                skill_yaml = skills_root / skill_name / "agents" / "openai.yaml"
                if not skill_yaml.is_file():
                    fail(f"rendered plugin skill metadata is missing: {skill_yaml}")
                validate_openai_yaml_mcp_dependencies(skill_yaml)

            mcp_path = plugin_root / ".mcp.json"
            if bundle.mcp_servers:
                mcp_payload = parse_json_file(mcp_path)
                mcp_servers = mcp_payload.get("mcpServers")
                if not isinstance(mcp_servers, dict):
                    fail(f"{mcp_path} mcpServers must be an object")
                if set(mcp_servers.keys()) != set(bundle.mcp_servers.keys()):
                    fail(f"{mcp_path} server names do not match rendered plugin inventory for {bundle.name}")
            elif mcp_path.exists():
                fail(f"{mcp_path} should not exist for plugin without MCP servers: {bundle.name}")

            app_path = plugin_root / ".app.json"
            if bundle.apps:
                app_payload = parse_json_file(app_path)
                apps = app_payload.get("apps")
                if not isinstance(apps, dict):
                    fail(f"{app_path} apps must be an object")
                if set(apps.keys()) != {app.name for app in bundle.apps}:
                    fail(f"{app_path} app ids do not match rendered plugin inventory for {bundle.name}")
            elif app_path.exists():
                fail(f"{app_path} should not exist for plugin without apps: {bundle.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex installer")
    parser.add_argument(
        "command",
        choices=(
            "preflight",
            "verify",
            "build-src",
            "build-install",
            "install",
            "runtime",
            "runtime-home",
            "runtime-skills",
            "runtime-instructions",
            "vars-init",
            "vars-reset",
            "nuke",
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "For install/build-install, perform an isolated staged install under /data/dryrun/codex "
            "(or $CODEX_DRY_RUN_STAGE_ROOT if set); "
            "for other commands, print actions without mutating files"
        ),
    )
    parser.add_argument(
        "--compiled-dir",
        default="src/misc/compiled",
        help="Directory for compiled artifacts (default: src/misc/compiled)",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    ensure_non_root_user()
    stage_dry_run = args.dry_run and args.command in {"install", "build-install"}

    if args.command == "build-src":
        repo_root = Path(__file__).resolve().parents[2]
        try:
            source_build_settings = load_source_build_settings(load_source_build_environment(repo_root))
        except SourceBuildError as exc:
            fail(str(exc))
        if args.dry_run:
            print(f"[dry-run] source repo url={source_build_settings.repo_url}")
            print(f"[dry-run] source ref={source_build_settings.base_ref or 'HEAD'}")
            print(f"[dry-run] source checkout={source_build_settings.checkout_dir}")
            print(f"[dry-run] build root={source_build_settings.build_root}")
            print(f"[dry-run] cache root={source_build_settings.cache_root}")
            print(f"[dry-run] published output={source_build_settings.output_dir}")
            return 0
        try:
            result = build_from_settings(source_build_settings)
        except SourceBuildError as exc:
            fail(str(exc))
        print(f"[ok] build-src complete ({result.output_dir})")
        return 0

    repo_root = Path(__file__).resolve().parents[2]
    installer = Installer(
        repo_root=repo_root,
        dry_run=args.dry_run and not stage_dry_run,
        stage_root=resolve_dry_run_stage_root() if stage_dry_run else None,
    )

    installer.load()

    if args.command == "nuke":
        # Nuke must not depend on config rendering or other install-time checks.
        installer.uninstall()
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] nuke complete")
        print('[info] current shell variables remain until session refresh (e.g., run: exec "$SHELL" -l)')
        return 0

    if args.command == "vars-reset":
        installer.apply_vars_reset()
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] vars-reset complete")
        print('[info] current shell variables remain until session refresh (e.g., run: exec "$SHELL" -l)')
        return 0

    if args.command == "vars-init":
        installer.validate()
        installer.apply_vars_init()
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] vars-init complete")
        return 0

    if args.command == "build-install":
        installer.validate()
        compiled_dir = (
            installer._resolved_stage_root() / "compiled"
            if stage_dry_run
            else (repo_root / args.compiled_dir).resolve(strict=False)
        )
        artifacts = installer.compile(compiled_dir)
        installer.build_install(artifacts)
        if stage_dry_run:
            print(f"[ok] staged dry-run build-install complete ({installer._resolved_stage_root()})")
            return 0
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] build-install complete")
        return 0

    if args.command == "runtime":
        installer.validate()
        compiled_dir = (repo_root / args.compiled_dir).resolve(strict=False)
        artifacts = installer.compile(compiled_dir)
        installer.apply_runtime(artifacts)
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] runtime complete")
        return 0

    installer.validate()

    if args.command == "preflight":
        print("[ok] preflight passed")
        return 0

    if args.command == "verify":
        compiled_dir = (repo_root / args.compiled_dir).resolve(strict=False)
        installer.verify(compiled_dir)
        print("[ok] verification passed")
        return 0

    compiled_dir = (
        installer._resolved_stage_root() / "compiled"
        if stage_dry_run
        else (repo_root / args.compiled_dir).resolve(strict=False)
    )
    artifacts = installer.compile(compiled_dir)

    if args.command == "runtime-home":
        installer.apply_runtime_home(artifacts)
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] runtime-home complete")
        return 0

    if args.command == "runtime-skills":
        installer.apply_runtime_skills(artifacts)
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] runtime-skills complete")
        return 0

    if args.command == "runtime-instructions":
        installer.apply_runtime_instructions()
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] runtime-instructions complete")
        return 0

    if args.command == "install":
        installer.apply(artifacts)
        if stage_dry_run:
            print(f"[ok] staged dry-run install complete ({installer._resolved_stage_root()})")
            return 0
        if args.dry_run:
            print("[ok] dry-run complete")
            return 0
        print("[ok] install complete")
        return 0

    fail(f"unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except InstallError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
