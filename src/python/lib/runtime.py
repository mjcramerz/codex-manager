from __future__ import annotations

import re
from pathlib import Path


class RuntimeRenderError(RuntimeError):
    """Raised when runtime path rendering receives unsafe input."""


def _sanitize_env_path(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if any(ch in cleaned for ch in ("\x00", "\n", "\r")):
        raise RuntimeRenderError(f"{label} contains control characters")
    return cleaned


def _validate_shell_path(label: str, value: Path) -> str:
    rendered = str(value)
    if not rendered:
        raise RuntimeRenderError(f"{label} cannot be empty")
    if any(ch in rendered for ch in ("\x00", "\n", "\r", '"')):
        raise RuntimeRenderError(f"{label} contains unsupported characters")
    return rendered


EXPORT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
SHELL_ALIAS_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
WRAPPER_ALIASES_FILENAME = "codex-wrapper-aliases.sh"
WRAPPER_SECRET_ENV_FLAG = "CODEX_INJECT_SECRETS"


def _validate_shell_export_value(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise RuntimeRenderError(f"{label} cannot be empty")
    if any(ch in cleaned for ch in ("\x00", "\n", "\r", '"')):
        raise RuntimeRenderError(f"{label} contains unsupported characters")
    return cleaned


def _validate_tmpfs_size(label: str, value: str) -> str:
    cleaned = value.strip()
    if not TMPFS_SIZE_PATTERN.fullmatch(cleaned):
        raise RuntimeRenderError(f"{label} must be a percentage like 36%")
    return cleaned


def _render_shell_exports(global_vars: dict[str, str] | None) -> list[str]:
    exports: list[str] = []
    for key in sorted((global_vars or {}).keys()):
        if not EXPORT_KEY_PATTERN.fullmatch(key):
            raise RuntimeRenderError(f"invalid shell export key: {key}")
        value = _validate_shell_export_value(f"shell export value for {key}", global_vars[key])
        exports.append(f'export {key}="{value}"')
    return exports


def render_shell_export_block(*variable_sets: dict[str, str] | None) -> str:
    combined_exports: dict[str, str] = {}
    for variable_set in variable_sets:
        if variable_set:
            combined_exports.update(variable_set)
    exports = _render_shell_exports(combined_exports)
    if not exports:
        return ""
    return "\n".join(exports) + "\n"


def derive_runtime_globals_from_env(env: dict[str, str]) -> dict[str, str]:
    user_dir = _sanitize_env_path("CODEX_USER_DIR", env.get("CODEX_USER_DIR", ""))
    root_dir = _sanitize_env_path("CODEX_ROOT_DIR", env.get("CODEX_ROOT_DIR", ""))

    def join_path(base: str, *parts: str) -> str:
        if not base:
            return ""
        return str(Path(base).joinpath(*parts))

    return {
        "CODEX_HOME": join_path(user_dir, "home"),
        "CODEX_AGENTS": join_path(user_dir, "agents"),
        "CODEX_SKILLS": join_path(user_dir, "skills"),
        "CODEX_LOG_DIR": join_path(root_dir, "log"),
    }


def render_shell_path_profile(
    share_dir: Path,
    wrapper_dir: Path,
    global_vars: dict[str, str] | None = None,
    guard_user: str | None = None,
) -> str:
    wrappers_dir = _validate_shell_path("wrapper path", wrapper_dir)
    helpers_dir = _validate_shell_path("share helpers path", share_dir / "helpers")
    aliases_path = _validate_shell_path("wrapper aliases path", share_dir / "helpers" / WRAPPER_ALIASES_FILENAME)
    export_block = render_shell_export_block(global_vars)

    guard_block = ""
    if guard_user:
        guarded_user = _validate_shell_export_value("guard user", guard_user)
        guard_block = (
            f'codex_target_user="{guarded_user}"\n'
            'codex_current_user="${LOGNAME:-${USER:-}}"\n'
            'if [ -z "${codex_current_user}" ] && command -v id >/dev/null 2>&1; then\n'
            '  codex_current_user="$(id -un 2>/dev/null || true)"\n'
            "fi\n"
            'if [ "${codex_current_user}" != "${codex_target_user}" ]; then\n'
            "  return 0 2>/dev/null || exit 0\n"
            "fi\n"
        )

    return (
        "#!/bin/sh\n"
        "# managed by codex installer\n"
        f"{guard_block}"
        f"{export_block}"
        f'for codex_path in "{wrappers_dir}" "{helpers_dir}"; do\n'
        '  if [ -d "${codex_path}" ]; then\n'
        '    case ":${PATH:-}:" in\n'
        '      *:"${codex_path}":*) ;;\n'
        '      *) PATH="${codex_path}:${PATH:-}" ;;\n'
        "    esac\n"
        "  fi\n"
        "done\n"
        "export PATH\n"
        f'if [ -r "{aliases_path}" ]; then\n'
        f'  . "{aliases_path}"\n'
        "fi\n"
    )


def render_wrapper_aliases(binary_names: list[str], *, secret_env_flag: str = WRAPPER_SECRET_ENV_FLAG) -> str:
    if not EXPORT_KEY_PATTERN.fullmatch(secret_env_flag):
        raise RuntimeRenderError(f"invalid secret env flag: {secret_env_flag}")

    lines = [
        "# managed by codex installer",
        'case "${-:-}" in',
        "  *i*) ;;",
        "  *) return 0 2>/dev/null || exit 0 ;;",
        "esac",
    ]
    for name in sorted(set(binary_names)):
        if not SHELL_ALIAS_NAME_PATTERN.fullmatch(name):
            raise RuntimeRenderError(f"invalid wrapper alias name: {name}")
        alias_name = f"{name}-s"
        lines.append(f"unalias {alias_name} 2>/dev/null || true")
        lines.append(f"alias {alias_name}='{secret_env_flag}=1 command {name}'")
    return "\n".join(lines) + "\n"


def render_codex_shim(
    binary_path: Path,
    launch_env: dict[str, str] | None = None,
    share_dir: Path | None = None,
    wrapper_dir: Path | None = None,
    managed_secrets_path: Path | None = None,
    managed_secret_helper_path: Path | None = None,
    host_config_path: Path | None = None,
) -> str:
    binary = _validate_shell_path("shim binary path", binary_path)
    export_block = render_shell_export_block(launch_env)
    path_block = ""
    if share_dir is not None:
        if wrapper_dir is None:
            raise RuntimeRenderError("wrapper path is required when share dir is configured")
        wrappers_dir = _validate_shell_path("wrapper path", wrapper_dir)
        helpers_dir = _validate_shell_path("share helpers path", share_dir / "helpers")
        path_block = (
            f'for codex_path in "{wrappers_dir}" "{helpers_dir}"; do\n'
            '  if [ -d "${codex_path}" ]; then\n'
            '    case ":${PATH:-}:" in\n'
            '      *:"${codex_path}":*) ;;\n'
            '      *) PATH="${codex_path}:${PATH:-}" ;;\n'
            "    esac\n"
            "  fi\n"
            "done\n"
            "export PATH\n"
        )

    keyring_block = ""
    if managed_secrets_path is not None:
        rendered_managed_secrets_path = _validate_shell_path(
            "managed secrets path",
            managed_secrets_path,
        )
        if managed_secret_helper_path is None:
            raise RuntimeRenderError("managed secret helper path is required when managed secrets are configured")
        if host_config_path is None:
            raise RuntimeRenderError("host config path is required when managed secrets are configured")
        rendered_managed_secret_helper_path = _validate_shell_path(
            "managed secret helper path",
            managed_secret_helper_path,
        )
        rendered_host_config_path = _validate_shell_path(
            "host config path",
            host_config_path,
        )
        keyring_block = (
            f'if [ -n "${{{WRAPPER_SECRET_ENV_FLAG}:-}}" ]; then\n'
            f'  if [ ! -x "{rendered_managed_secret_helper_path}" ]; then\n'
            f'    echo "missing codex managed secret helper: {rendered_managed_secret_helper_path}" >&2\n'
            "    exit 1\n"
            "  fi\n"
            f'  exec /usr/bin/env python3 "{rendered_managed_secret_helper_path}" exec '
            f'--secrets-file "{rendered_managed_secrets_path}" --host-config "{rendered_host_config_path}" '
            f'--binary "{binary}" -- "$@"\n'
            "fi\n"
        )

    return (
        "#!/bin/sh\n"
        "# managed by codex installer\n"
        f"{export_block}"
        f"{path_block}"
        f"{keyring_block}"
        f'exec "{binary}" "$@"\n'
    )
