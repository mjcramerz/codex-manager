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
TMPFS_SIZE_PATTERN = re.compile(r"^[0-9]+%$")
TMPFS_HELPER_FILENAME = "codex-ensure-tmpfs"
TMPFS_DEFAULT_SIZE = "36%"


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


def render_shell_exec_block(label: str, script_path: Path | None) -> str:
    if script_path is None:
        return ""
    rendered = _validate_shell_path(label, script_path)
    return (
        f'if [ ! -x "{rendered}" ]; then\n'
        f'  echo "missing {label}: {rendered}" >&2\n'
        "  exit 1\n"
        "fi\n"
        f'"{rendered}"\n'
        "codex_helper_status=$?\n"
        'if [ "${codex_helper_status}" -ne 0 ]; then\n'
        '  exit "${codex_helper_status}"\n'
        "fi\n"
        "unset codex_helper_status\n"
    )


def render_codex_tmpfs_helper(
    size: str = TMPFS_DEFAULT_SIZE,
    launch_env: dict[str, str] | None = None,
    *,
    mount_enabled: bool = True,
) -> str:
    tmpfs_size = _validate_tmpfs_size("tmpfs size", size)
    mount_opts = _validate_shell_export_value(
        "tmpfs mount options",
        f"size={tmpfs_size},mode=1777,nodev,nosuid",
    )
    export_block = render_shell_export_block(launch_env)

    if not mount_enabled:
        return (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "IFS=$'\\n\\t'\n"
            "\n"
            f"{export_block}"
            'codex_tmpdir=""\n'
            "\n"
            "log_error() {\n"
            "  printf 'ERROR: %s\\n' \"$*\" >&2\n"
            "}\n"
            "\n"
            "resolve_tmpdir() {\n"
            "  local candidate=\"${TMPDIR:-}\"\n"
            "  if [[ -z \"${candidate}\" ]]; then\n"
            "    candidate=\"${CODEX_TMPDIR:-}\"\n"
            "  fi\n"
            "  if [[ -z \"${candidate}\" ]]; then\n"
            "    log_error \"TMPDIR or CODEX_TMPDIR must be set before starting codex\"\n"
            "    return 1\n"
            "  fi\n"
            "  if [[ \"${candidate}\" != /* ]]; then\n"
            "    log_error \"tmpdir target must be an absolute path: ${candidate}\"\n"
            "    return 1\n"
            "  fi\n"
            "  if [[ \"${candidate}\" == \"/\" ]]; then\n"
            "    log_error \"tmpdir target cannot be /\"\n"
            "    return 1\n"
            "  fi\n"
            "  if [[ \"${candidate}\" =~ [[:space:]] ]]; then\n"
            "    log_error \"tmpdir target cannot contain whitespace: ${candidate}\"\n"
            "    return 1\n"
            "  fi\n"
            "  codex_tmpdir=\"${candidate}\"\n"
            "}\n"
            "\n"
            "main() {\n"
            "  if (($# != 0)); then\n"
            "    echo \"usage: codex-ensure-tmpfs\" >&2\n"
            "    return 2\n"
            "  fi\n"
            "  resolve_tmpdir\n"
            "  mkdir -p -- \"${codex_tmpdir}\"\n"
            "}\n"
            "\n"
            "main \"$@\"\n"
        )

    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "IFS=$'\\n\\t'\n"
        "\n"
        f"{export_block}"
        'codex_tmpdir=""\n'
        f'codex_mount_opts="{mount_opts}"\n'
        "\n"
        "log_error() {\n"
        "  printf 'ERROR: %s\\n' \"$*\" >&2\n"
        "}\n"
        "\n"
        "resolve_tmpdir() {\n"
        "  local candidate=\"${TMPDIR:-}\"\n"
        "  if [[ -z \"${candidate}\" ]]; then\n"
        "    candidate=\"${CODEX_TMPDIR:-}\"\n"
        "  fi\n"
        "  if [[ -z \"${candidate}\" ]]; then\n"
        "    log_error \"TMPDIR or CODEX_TMPDIR must be set before starting codex\"\n"
        "    return 1\n"
        "  fi\n"
        "  if [[ \"${candidate}\" != /* ]]; then\n"
        "    log_error \"tmpfs target must be an absolute path: ${candidate}\"\n"
        "    return 1\n"
        "  fi\n"
        "  if [[ \"${candidate}\" == \"/\" ]]; then\n"
        "    log_error \"tmpfs target cannot be /\"\n"
        "    return 1\n"
        "  fi\n"
        "  if [[ \"${candidate}\" =~ [[:space:]] ]]; then\n"
        "    log_error \"tmpfs target cannot contain whitespace: ${candidate}\"\n"
        "    return 1\n"
        "  fi\n"
        "  codex_tmpdir=\"${candidate}\"\n"
        "}\n"
        "\n"
        "current_mount_state() {\n"
        "  local fstype=\"\"\n"
        "  if command -v findmnt >/dev/null 2>&1; then\n"
        "    fstype=\"$(findmnt -M \"${codex_tmpdir}\" -n -o FSTYPE 2>/dev/null || true)\"\n"
        "    if [[ -n \"${fstype}\" ]]; then\n"
        "      printf '%s\\n' \"${fstype}\"\n"
        "      return 0\n"
        "    fi\n"
        "  fi\n"
        "  if command -v mountpoint >/dev/null 2>&1 && mountpoint -q -- \"${codex_tmpdir}\"; then\n"
        "    printf '%s\\n' \"mounted\"\n"
        "  fi\n"
        "}\n"
        "\n"
        "run_with_optional_sudo() {\n"
        "  local -a cmd=(\"$@\")\n"
        "  if \"${cmd[@]}\" 2>/dev/null; then\n"
        "    return 0\n"
        "  fi\n"
        "  if ! command -v sudo >/dev/null 2>&1; then\n"
        "    return 1\n"
        "  fi\n"
        "  local -a sudo_cmd=(sudo)\n"
        "  if [[ ! -t 0 ]]; then\n"
        "    sudo_cmd+=(-n)\n"
        "  fi\n"
        "  sudo_cmd+=(\"${cmd[@]}\")\n"
        "  \"${sudo_cmd[@]}\"\n"
        "}\n"
        "\n"
        "ensure_tmpdir() {\n"
        "  if run_with_optional_sudo mkdir -p -- \"${codex_tmpdir}\"; then\n"
        "    return 0\n"
        "  fi\n"
        "  log_error \"failed to create CODEX_TMPDIR: ${codex_tmpdir}\"\n"
        "  return 1\n"
        "}\n"
        "\n"
        "mount_tmpfs() {\n"
        "  if run_with_optional_sudo mount -t tmpfs -o \"${codex_mount_opts}\" tmpfs \"${codex_tmpdir}\"; then\n"
        "    return 0\n"
        "  fi\n"
        "  case \"$(current_mount_state)\" in\n"
        "    tmpfs|mounted)\n"
        "      return 0\n"
        "      ;;\n"
        "  esac\n"
        "  log_error \"failed to mount CODEX_TMPDIR as tmpfs: ${codex_tmpdir}\"\n"
        "  return 1\n"
        "}\n"
        "\n"
        "main() {\n"
        "  local mount_state=\"\"\n"
        "  if (($# != 0)); then\n"
        "    echo \"usage: codex-ensure-tmpfs\" >&2\n"
        "    return 2\n"
        "  fi\n"
        "  resolve_tmpdir\n"
        "  ensure_tmpdir\n"
        "  mount_state=\"$(current_mount_state)\"\n"
        "  case \"${mount_state}\" in\n"
        "    tmpfs|mounted)\n"
        "      return 0\n"
        "      ;;\n"
        "    \"\")\n"
        "      ;;\n"
        "    *)\n"
        "      log_error \"CODEX_TMPDIR is already mounted with unsupported filesystem ${mount_state}: ${codex_tmpdir}\"\n"
        "      return 1\n"
        "      ;;\n"
        "  esac\n"
        "  mount_tmpfs\n"
        "  mount_state=\"$(current_mount_state)\"\n"
        "  case \"${mount_state}\" in\n"
        "    tmpfs|mounted)\n"
        "      return 0\n"
        "      ;;\n"
        "  esac\n"
        "  log_error \"failed to verify CODEX_TMPDIR mount state: ${codex_tmpdir}\"\n"
        "  return 1\n"
        "}\n"
        "\n"
        "main \"$@\"\n"
    )


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
        "CODEX_TMPDIR": join_path(root_dir, "tmp"),
    }


def render_shell_path_profile(
    share_dir: Path,
    wrapper_dir: Path,
    global_vars: dict[str, str] | None = None,
    guard_user: str | None = None,
) -> str:
    wrappers_dir = _validate_shell_path("wrapper path", wrapper_dir)
    helpers_dir = _validate_shell_path("share helpers path", share_dir / "helpers")
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
    )


def render_codex_shim(
    binary_path: Path,
    launch_env: dict[str, str] | None = None,
    share_dir: Path | None = None,
    wrapper_dir: Path | None = None,
    managed_secrets_path: Path | None = None,
    managed_secret_helper_path: Path | None = None,
) -> str:
    binary = _validate_shell_path("shim binary path", binary_path)
    export_block = render_shell_export_block(launch_env)
    tmpfs_block = ""
    if share_dir is not None:
        tmpfs_block = render_shell_exec_block(
            "codex tmpfs helper",
            share_dir / "helpers" / TMPFS_HELPER_FILENAME,
        )

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
        rendered_managed_secret_helper_path = _validate_shell_path(
            "managed secret helper path",
            managed_secret_helper_path,
        )
        keyring_block = (
            f'if [ ! -x "{rendered_managed_secret_helper_path}" ]; then\n'
            f'  echo "missing codex managed secret helper: {rendered_managed_secret_helper_path}" >&2\n'
            "  exit 1\n"
            "fi\n"
            f'exec /usr/bin/env python3 "{rendered_managed_secret_helper_path}" exec '
            f'--secrets-file "{rendered_managed_secrets_path}" '
            f'--binary "{binary}" -- "$@"\n'
        )

    return (
        "#!/bin/sh\n"
        "# managed by codex installer\n"
        f"{export_block}"
        f"{tmpfs_block}"
        f"{path_block}"
        f"{keyring_block}"
        f'exec "{binary}" "$@"\n'
    )
