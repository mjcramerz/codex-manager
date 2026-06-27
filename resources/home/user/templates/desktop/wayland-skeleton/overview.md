# Wayland desktop skeleton (overview)
Purpose: tell the Codex coding agent how to use `templates/desktop/wayland-skeleton/overview.md` as a runtime-pack surface and when to stop browsing.
Minimal configs for a Labwc‑based Wayland session.

## Outputs
- `labwc/rc.xml`
- `waybar/config.jsonc`
- `kanshi/config`
- `swaylock/config`
- `wofi/config`
- `greetd/config.toml`
- `regreet.css`

## Usage
1) Copy configs into `~/.config/` (or `/etc/` for greetd).
2) Adjust paths and commands for your system.
3) Test with a fallback TTY available.

## Inputs
- Destination repository path for this template.
- Exact runtime/toolchain versions and pinning policy.
- Repository-specific values for placeholders, secrets, and host paths.

## Next steps
1) Copy files into deterministic repository paths.
2) Replace placeholders and pin versions/images before first commit.
3) Run the narrowest relevant checks (lint/test/build or dry-run) before commit.

Related:
- `$CODEX_HOME/docs/desktop/wayland.md`
- `$CODEX_HOME/docs/workflows/desktop-wayland.md`
