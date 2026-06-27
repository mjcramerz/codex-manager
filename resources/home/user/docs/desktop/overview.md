# Desktop stack overview
Purpose: route minimal Wayland desktop, desktop-entry, and hardened-browser work to the correct guide for the Codex coding agent.
You must read only the smallest section that resolves the current task, follow the first matching route, and stop broad browsing once the next concrete file or command is clear.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Scope
- Wayland/labwc session setup
- greetd/regreet/cage launch surfaces
- desktop-entry integration
- hardened browser guidance

## Quick map
- Wayland stack: `wayland.md`
- Desktop entries: `desktop-entries.md`
- Browser stack: `browsers.md`

## You must enforce these guardrails
- You must keep configs minimal and versioned.
- You must prefer Wayland-native flags and apps.
- You must keep privilege boundaries explicit around polkit, launchers, and browser profile handling.
