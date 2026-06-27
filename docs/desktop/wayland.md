# Wayland / Labwc stack
Guidance for a lean Wayland desktop with Labwc.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/desktop/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Core components
- **labwc**: window manager
- **waybar**: status bar
- **kanshi**: output/profile manager
- **swaylock**: screen locker
- **wofi**: app launcher
- **wlr-randr**: output configuration
- **cage**: kiosk wrapper (optional)
- **greetd + regreet**: display manager / greeter

## Baseline practices
- Keep configs in `~/.config/` and version them.
- Prefer Wayland flags for browsers/apps (`--ozone-platform=wayland`).
- Use minimal autostart entries; avoid shell scripts where possible.

## Config locations (typical)
- Labwc: `~/.config/labwc/`
- Waybar: `~/.config/waybar/`
- Kanshi: `~/.config/kanshi/config`
- Swaylock: `~/.config/swaylock/config`
- Wofi: `~/.config/wofi/config`
- Greetd: `/etc/greetd/config.toml`

## Safety notes
- Ensure the greeter runs with minimal privileges.
- Avoid storing secrets in desktop configs.
- Test new configs with a fallback TTY login available.

See also:
- `overview.md`
- `desktop-entries.md`
- `$CODEX_HOME/templates/desktop/wayland-skeleton/`
- `$CODEX_HOME/snippets/desktop/`
- `../workflows/desktop-wayland.md`
- Use skill desktop-wayland.
- `$CODEX_HOME/index/domains/desktop/stack.md`
- `$CODEX_HOME/index/domains/desktop/wayland.md`
