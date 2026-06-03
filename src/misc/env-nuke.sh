CURRENT_USER_HOME="$HOME"

sudo CURRENT_USER_HOME="$CURRENT_USER_HOME" bash <<'ROOT'
set -euo pipefail
IFS=$'\n\t'
export LC_ALL=C TZ=UTC

scrub_file() {
  local path=$1
  [[ -f "$path" ]] || return 0
  local tmp
  tmp="$(mktemp)"
  awk '
    $0 == "# >>> codex-shell-hook >>>" { in_block = 1; next }
    in_block == 1 && $0 == "# <<< codex-shell-hook <<<" { in_block = 0; next }
    in_block == 1 { next }
    /CODEX_[A-Z0-9_]+/ { next }
    /50-codex/ { next }
    { print }
  ' "$path" > "$tmp"
  cat "$tmp" > "$path"
  rm -f "$tmp"
}

for path in \
  /etc/environment /etc/profile /etc/bash.bashrc /etc/bashrc \
  /root/.profile /root/.bashrc /root/.bash_profile /root/.bash_login /root/.zshrc \
  /etc/skel/.profile /etc/skel/.bashrc /etc/skel/.bash_profile /etc/skel/.bash_login /etc/skel/.zshrc \
  "$CURRENT_USER_HOME/.profile" "$CURRENT_USER_HOME/.bashrc" "$CURRENT_USER_HOME/.bash_profile" "$CURRENT_USER_HOME/.bash_login" "$CURRENT_USER_HOME/.zshrc"
do
  scrub_file "$path"
done

while IFS= read -r -d '' path; do
  scrub_file "$path"
done < <(
  find \
    /etc/profile.d /etc/environment.d /etc/default \
    /etc/systemd/user.conf.d /etc/systemd/system.conf.d \
    /usr/lib/environment.d /usr/lib/systemd/user.conf.d /usr/lib/systemd/system.conf.d \
    /run/environment.d /run/systemd/user.conf.d /run/systemd/system.conf.d \
    /usr/local/etc/profile.d /usr/local/etc/environment.d \
    -maxdepth 1 -type f -print0 2>/dev/null
)

rm -f \
  /etc/systemd/user.conf.d/50-codex.conf \
  /etc/profile.d/50-codex-path.sh \
  /etc/profile.d/50-codex-user-env.sh

mapfile -t keys < <(systemctl show-environment 2>/dev/null | awk -F= '/^CODEX_[A-Z0-9_]+=/{print $1}' | sort -u)
if ((${#keys[@]})); then
  systemctl unset-environment "${keys[@]}" || true
fi
systemctl daemon-reexec || true
ROOT

mapfile -t user_keys < <(systemctl --user show-environment 2>/dev/null | awk -F= '/^CODEX_[A-Z0-9_]+=/{print $1}' | sort -u)
if ((${#user_keys[@]})); then
  systemctl --user unset-environment "${user_keys[@]}" || true
fi
systemctl --user daemon-reexec || true

sudo -Hiu root bash <<'ROOTUSER'
set -euo pipefail
IFS=$'\n\t'
mapfile -t keys < <(systemctl --user show-environment 2>/dev/null | awk -F= '/^CODEX_[A-Z0-9_]+=/{print $1}' | sort -u)
if ((${#keys[@]})); then
  systemctl --user unset-environment "${keys[@]}" || true
fi
systemctl --user daemon-reexec || true
ROOTUSER

while IFS='=' read -r name _; do
  case "$name" in
    CODEX_*) unset "$name" ;;
  esac
done < <(env)

echo 'Done. Open a new shell (or run: exec "$SHELL" -l) to drop inherited CODEX_* values from the current session.'
