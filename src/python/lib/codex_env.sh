#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

readonly MANAGED_BLOCK_START="# >>> codex-shell-hook >>>"
readonly MANAGED_BLOCK_END="# <<< codex-shell-hook <<<"

log_info() {
  printf '%s\n' "$*"
}

log_warn() {
  printf 'WARN: %s\n' "$*" >&2
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

contains_control_chars() {
  local value=${1:-}
  [[ "${value}" != *$'\n'* && "${value}" != *$'\r'* ]]
}

safe_tmp_base() {
  printf '%s\n' "/tmp"
}

mktemp_file() {
  local template=${1:?template is required}
  local tmp_base
  tmp_base="$(safe_tmp_base)"
  mktemp "${tmp_base}/${template}"
}

hook_usage() {
  cat <<'USAGE'
usage: codex_env.sh hook --user-home <absolute-path> --profile-path <absolute-path> [--verify] [--dry-run]

Install or verify managed shell hook blocks that source the codex profile script.
USAGE
}

unhook_usage() {
  cat <<'USAGE'
usage: codex_env.sh unhook --user-home <absolute-path> --profile-path <absolute-path> [--dry-run]

Remove managed shell hook blocks and the managed codex profile script for the current user.
USAGE
}

render_hook_block() {
  local path=${1:?shell file path is required}
  local profile_path=${2:?profile path is required}
  local base
  base="$(basename -- "${path}")"

  cat <<BLOCK
${MANAGED_BLOCK_START}
# managed by codex installer
if [ -r "${profile_path}" ]; then
  . "${profile_path}"
fi
BLOCK

  if [[ "${base}" == ".bashrc" ]]; then
    cat <<'BLOCK'
if [ -n "${BASH_VERSION:-}" ] && [ -r "${HOME}/.local/share/bash-completion/completions/codex" ]; then
  . "${HOME}/.local/share/bash-completion/completions/codex"
fi
BLOCK
  fi

  cat <<BLOCK
${MANAGED_BLOCK_END}
BLOCK
}

render_profile_source_block() {
  local profile_path=${1:?profile path is required}
  cat <<BLOCK
# managed by codex installer
if [ -r "${profile_path}" ]; then
  . "${profile_path}"
fi
BLOCK
}

strip_managed_block() {
  local path=${1:?path is required}
  awk -v start="${MANAGED_BLOCK_START}" -v end="${MANAGED_BLOCK_END}" '
    $0 == start { in_block = 1; next }
    in_block == 1 && $0 == end { in_block = 0; next }
    in_block == 0 { print }
  ' "${path}"
}

trim_trailing_blank_lines() {
  local src=${1:?source path is required}
  local dst=${2:?destination path is required}
  awk '
    { lines[NR] = $0 }
    END {
      last = NR
      while (last > 0 && lines[last] ~ /^[[:space:]]*$/) {
        last--
      }
      for (i = 1; i <= last; i++) {
        print lines[i]
      }
    }
  ' "${src}" > "${dst}"
}

strip_profile_source_block() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}
  local header="# managed by codex installer"
  local guard="if [ -r \"${profile_path}\" ]; then"
  local source="  . \"${profile_path}\""
  local done_line="fi"

  awk -v header="${header}" -v guard="${guard}" -v source="${source}" -v done_line="${done_line}" '
    function flush_pending() {
      if (state == 1) {
        print header
      } else if (state == 2) {
        print header
        print guard
      } else if (state == 3) {
        print header
        print guard
        print source
      }
      state = 0
    }

    state == 0 {
      if ($0 == header) {
        state = 1
        next
      }
      print
      next
    }

    state == 1 {
      if ($0 == guard) {
        state = 2
        next
      }
      flush_pending()
      print
      next
    }

    state == 2 {
      if ($0 == source) {
        state = 3
        next
      }
      flush_pending()
      print
      next
    }

    state == 3 {
      if ($0 == done_line) {
        state = 0
        next
      }
      flush_pending()
      print
      next
    }

    END {
      flush_pending()
    }
  ' "${path}"
}

ensure_target_file() {
  local path=${1:?path is required}
  local dry_run=${2:?dry-run flag is required}

  if [[ -e "${path}" && ! -f "${path}" ]]; then
    die "shell hook target must be a regular file: ${path}"
  fi
  if [[ -e "${path}" && "${dry_run}" != "1" && ! -w "${path}" ]]; then
    die "shell hook target is not writable: ${path}"
  fi
  if [[ -e "${path}" ]]; then
    return 0
  fi
  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] touch ${path}"
    return 0
  fi

  local parent
  parent="$(dirname -- "${path}")"
  mkdir -p -- "${parent}"
  [[ -w "${parent}" ]] || die "shell hook parent directory is not writable: ${parent}"
  : > "${path}"
}

is_posix_shell_target() {
  local path=${1:?path is required}
  case "$(basename -- "${path}")" in
    .bashrc|.bash_profile|.bash_login|.profile)
      return 0
      ;;
  esac
  return 1
}

repair_dangling_unexpected_fi() {
  local path=${1:?path is required}
  local dry_run=${2:?dry-run flag is required}
  local repairs=0
  local max_repairs=8

  is_posix_shell_target "${path}" || return 0
  [[ -f "${path}" ]] || return 0

  while (( repairs < max_repairs )); do
    local lint_output=""
    if lint_output="$(bash -n "${path}" 2>&1)"; then
      return 0
    fi
    if [[ "${lint_output}" != *"unexpected token"* || "${lint_output}" != *"fi"* ]]; then
      return 0
    fi

    local line
    line="$(printf '%s\n' "${lint_output}" | LC_ALL=C sed -n 's/^.*: line \([0-9][0-9]*\): syntax error near unexpected token .*$/\1/p' | head -n 1)"
    [[ -n "${line}" ]] || return 0

    local raw_line
    raw_line="$(LC_ALL=C sed -n "${line}p" "${path}")"
    [[ "${raw_line}" =~ ^[[:space:]]*fi[[:space:]]*$ ]] || return 0

    if [[ "${dry_run}" == "1" ]]; then
      log_info "[dry-run] remove dangling unexpected fi at ${path}:${line}"
      return 0
    fi

    local tmp
    tmp="$(mktemp_file "codex-shell-hook-fixfi.XXXXXX")"
    awk -v bad_line="${line}" 'NR != bad_line { print }' "${path}" > "${tmp}"
    cat -- "${tmp}" > "${path}"
    rm -f -- "${tmp}"
    repairs=$((repairs + 1))
  done

  die "failed to repair shell file after ${max_repairs} dangling-fi cleanup attempts: ${path}"
}

install_hook_file() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}
  local dry_run=${3:?dry-run flag is required}

  ensure_target_file "${path}" "${dry_run}"
  repair_dangling_unexpected_fi "${path}" "${dry_run}"

  local clean_tmp trimmed_tmp merged_tmp
  clean_tmp="$(mktemp_file "codex-shell-hook-clean.XXXXXX")"
  trimmed_tmp="$(mktemp_file "codex-shell-hook-trimmed.XXXXXX")"
  merged_tmp="$(mktemp_file "codex-shell-hook-merged.XXXXXX")"

  if [[ -f "${path}" ]]; then
    strip_managed_block "${path}" > "${clean_tmp}"
  else
    : > "${clean_tmp}"
  fi
  trim_trailing_blank_lines "${clean_tmp}" "${trimmed_tmp}"

  if [[ -s "${trimmed_tmp}" ]]; then
    cat -- "${trimmed_tmp}" > "${merged_tmp}"
    printf '\n\n' >> "${merged_tmp}"
  fi
  render_hook_block "${path}" "${profile_path}" >> "${merged_tmp}"
  printf '\n' >> "${merged_tmp}"

  if [[ -f "${path}" ]] && cmp -s -- "${path}" "${merged_tmp}"; then
    rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
    return 0
  fi

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] install codex shell hook in ${path}"
    rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
    return 0
  fi

  cat -- "${merged_tmp}" > "${path}"
  rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
}

install_profile_source_file() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}
  local dry_run=${3:?dry-run flag is required}

  ensure_target_file "${path}" "${dry_run}"
  repair_dangling_unexpected_fi "${path}" "${dry_run}"

  local clean_tmp trimmed_tmp merged_tmp
  clean_tmp="$(mktemp_file "codex-profile-clean.XXXXXX")"
  trimmed_tmp="$(mktemp_file "codex-profile-trimmed.XXXXXX")"
  merged_tmp="$(mktemp_file "codex-profile-merged.XXXXXX")"

  if [[ -f "${path}" ]]; then
    strip_profile_source_block "${path}" "${profile_path}" > "${clean_tmp}"
  else
    : > "${clean_tmp}"
  fi
  trim_trailing_blank_lines "${clean_tmp}" "${trimmed_tmp}"

  if [[ -s "${trimmed_tmp}" ]]; then
    cat -- "${trimmed_tmp}" > "${merged_tmp}"
    printf '\n' >> "${merged_tmp}"
  fi
  render_profile_source_block "${profile_path}" >> "${merged_tmp}"
  printf '\n' >> "${merged_tmp}"

  if [[ -f "${path}" ]] && cmp -s -- "${path}" "${merged_tmp}"; then
    rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
    return 0
  fi

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] install codex profile source block in ${path}"
    rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
    return 0
  fi

  cat -- "${merged_tmp}" > "${path}"
  rm -f -- "${clean_tmp}" "${trimmed_tmp}" "${merged_tmp}"
}

verify_hook_file() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}
  local optional=${3:?optional flag is required}
  local base
  base="$(basename -- "${path}")"

  if [[ ! -e "${path}" ]]; then
    if [[ "${optional}" == "1" ]]; then
      return 0
    fi
    die "missing shell rc file: ${path}"
  fi
  [[ -f "${path}" ]] || die "shell hook target must be a regular file: ${path}"

  local start_count
  start_count="$(grep -Fc -- "${MANAGED_BLOCK_START}" "${path}" || true)"
  if [[ "${start_count}" == "0" ]]; then
    die "missing managed shell hook block in ${path}"
  fi
  [[ "${start_count}" == "1" ]] || die "multiple managed shell hook blocks in ${path}"

  grep -Fq -- "${MANAGED_BLOCK_END}" "${path}" || die "missing managed shell hook end marker in ${path}"
  grep -Fq -- ". \"${profile_path}\"" "${path}" || die "missing codex profile source line in ${path}"
  if [[ "${base}" == ".bashrc" ]]; then
    grep -Fq -- '. "${HOME}/.local/share/bash-completion/completions/codex"' "${path}" \
      || die "missing codex bash completion source line in ${path}"
  fi
}

verify_profile_source_file() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}

  [[ -e "${path}" ]] || die "missing shell rc file: ${path}"
  [[ -f "${path}" ]] || die "shell hook target must be a regular file: ${path}"

  local header_count
  header_count="$(grep -Fxc -- "# managed by codex installer" "${path}" || true)"
  [[ "${header_count}" -ge 1 ]] || die "missing managed profile source block in ${path}"
  grep -Fq -- "if [ -r \"${profile_path}\" ]; then" "${path}" \
    || die "missing managed profile guard in ${path}"
  grep -Fq -- ". \"${profile_path}\"" "${path}" \
    || die "missing codex profile source line in ${path}"
}

remove_hook_file() {
  local path=${1:?path is required}
  local dry_run=${2:?dry-run flag is required}
  [[ -f "${path}" ]] || return 0

  local clean_tmp trimmed_tmp
  clean_tmp="$(mktemp_file "codex-shell-hook-clean.XXXXXX")"
  trimmed_tmp="$(mktemp_file "codex-shell-hook-trimmed.XXXXXX")"
  strip_managed_block "${path}" > "${clean_tmp}"
  trim_trailing_blank_lines "${clean_tmp}" "${trimmed_tmp}"

  if cmp -s -- "${path}" "${trimmed_tmp}"; then
    rm -f -- "${clean_tmp}" "${trimmed_tmp}"
    return 0
  fi

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] remove codex shell hook from ${path}"
    rm -f -- "${clean_tmp}" "${trimmed_tmp}"
    return 0
  fi

  cat -- "${trimmed_tmp}" > "${path}"
  rm -f -- "${clean_tmp}" "${trimmed_tmp}"
}

remove_profile_source_file() {
  local path=${1:?path is required}
  local profile_path=${2:?profile path is required}
  local dry_run=${3:?dry-run flag is required}
  [[ -f "${path}" ]] || return 0

  local clean_tmp trimmed_tmp
  clean_tmp="$(mktemp_file "codex-profile-clean.XXXXXX")"
  trimmed_tmp="$(mktemp_file "codex-profile-trimmed.XXXXXX")"
  strip_profile_source_block "${path}" "${profile_path}" > "${clean_tmp}"
  trim_trailing_blank_lines "${clean_tmp}" "${trimmed_tmp}"

  if cmp -s -- "${path}" "${trimmed_tmp}"; then
    rm -f -- "${clean_tmp}" "${trimmed_tmp}"
    return 0
  fi

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] remove codex profile source block from ${path}"
    rm -f -- "${clean_tmp}" "${trimmed_tmp}"
    return 0
  fi

  cat -- "${trimmed_tmp}" > "${path}"
  rm -f -- "${clean_tmp}" "${trimmed_tmp}"
}

remove_profile_file() {
  local path=${1:?path is required}
  local dry_run=${2:?dry-run flag is required}
  [[ -e "${path}" ]] || return 0
  [[ -f "${path}" ]] || die "managed codex profile must be a regular file: ${path}"

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] remove managed codex profile ${path}"
    return 0
  fi

  rm -f -- "${path}"
}

cmd_hook() {
  local dry_run=0
  local verify_mode=0
  local user_home=""
  local profile_path=""

  while (($# > 0)); do
    case "$1" in
      --dry-run)
        dry_run=1
        shift
        ;;
      --verify)
        verify_mode=1
        shift
        ;;
      --user-home)
        [[ $# -ge 2 ]] || die "--user-home requires a value"
        user_home="$2"
        shift 2
        ;;
      --profile-path)
        [[ $# -ge 2 ]] || die "--profile-path requires a value"
        profile_path="$2"
        shift 2
        ;;
      --help|-h)
        hook_usage
        exit 0
        ;;
      *)
        hook_usage >&2
        die "unknown argument: $1"
        ;;
    esac
  done

  [[ -n "${user_home}" ]] || die "--user-home is required"
  [[ "${user_home}" = /* ]] || die "--user-home must be an absolute path"
  contains_control_chars "${user_home}" || die "--user-home contains unsupported control characters"

  [[ -n "${profile_path}" ]] || die "--profile-path is required"
  [[ "${profile_path}" = /* ]] || die "--profile-path must be an absolute path"
  contains_control_chars "${profile_path}" || die "--profile-path contains unsupported control characters"
  [[ "${profile_path}" != *'"'* ]] || die "--profile-path contains unsupported characters"

  local -a required_targets=(
    "${user_home}/.bashrc"
    "${user_home}/.zshrc"
  )
  local -a optional_targets=(
    "${user_home}/.bash_profile"
    "${user_home}/.bash_login"
  )

  if [[ "${verify_mode}" == "1" ]]; then
    verify_profile_source_file "${user_home}/.profile" "${profile_path}"
    local path=""
    for path in "${required_targets[@]}"; do
      verify_hook_file "${path}" "${profile_path}" "0"
    done
    for path in "${optional_targets[@]}"; do
      verify_hook_file "${path}" "${profile_path}" "1"
    done
    log_info "[ok] codex shell hook verification complete"
    return 0
  fi

  install_profile_source_file "${user_home}/.profile" "${profile_path}" "${dry_run}"
  local path=""
  for path in "${required_targets[@]}"; do
    install_hook_file "${path}" "${profile_path}" "${dry_run}"
  done
  for path in "${optional_targets[@]}"; do
    if [[ -e "${path}" ]]; then
      install_hook_file "${path}" "${profile_path}" "${dry_run}"
    fi
  done

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] codex shell hook install audit complete"
  else
    log_info "[ok] codex shell hook install complete"
  fi
}

cmd_unhook() {
  local dry_run=0
  local user_home=""
  local profile_path=""

  while (($# > 0)); do
    case "$1" in
      --dry-run)
        dry_run=1
        shift
        ;;
      --user-home)
        [[ $# -ge 2 ]] || die "--user-home requires a value"
        user_home="$2"
        shift 2
        ;;
      --profile-path)
        [[ $# -ge 2 ]] || die "--profile-path requires a value"
        profile_path="$2"
        shift 2
        ;;
      --help|-h)
        unhook_usage
        exit 0
        ;;
      *)
        unhook_usage >&2
        die "unknown argument: $1"
        ;;
    esac
  done

  [[ -n "${user_home}" ]] || die "--user-home is required"
  [[ "${user_home}" = /* ]] || die "--user-home must be an absolute path"
  contains_control_chars "${user_home}" || die "--user-home contains unsupported control characters"

  [[ -n "${profile_path}" ]] || die "--profile-path is required"
  [[ "${profile_path}" = /* ]] || die "--profile-path must be an absolute path"
  contains_control_chars "${profile_path}" || die "--profile-path contains unsupported control characters"

  local -a hook_targets=(
    "${user_home}/.bashrc"
    "${user_home}/.zshrc"
    "${user_home}/.bash_profile"
    "${user_home}/.bash_login"
  )

  remove_profile_source_file "${user_home}/.profile" "${profile_path}" "${dry_run}"
  local path=""
  for path in "${hook_targets[@]}"; do
    remove_hook_file "${path}" "${dry_run}"
  done
  remove_profile_file "${profile_path}" "${dry_run}"

  if [[ "${dry_run}" == "1" ]]; then
    log_info "[dry-run] codex shell hook removal audit complete"
  else
    log_info "[ok] codex shell hook removal complete"
  fi
}

usage() {
  cat <<'USAGE'
usage: codex_env.sh <command> [options]

Commands:
  hook    Install or verify managed shell hook blocks.
  unhook  Remove managed shell hook blocks and profile exports.
USAGE
}

main() {
  [[ $# -gt 0 ]] || {
    usage >&2
    die "missing command"
  }

  local command="$1"
  shift || true

  case "${command}" in
    hook)
      cmd_hook "$@"
      ;;
    unhook)
      cmd_unhook "$@"
      ;;
    --help|-h)
      usage
      ;;
    *)
      usage >&2
      die "unknown command: ${command}"
      ;;
  esac
}

main "$@"
