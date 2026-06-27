# Wayland desktop workflow

Start with `$CODEX_HOME/plans/workflows/workflow-desktop-wayland.md` before executing this workflow.
Purpose: configure a minimal Wayland desktop with Labwc and related tools.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
- Start from the linked workflow plan template above, then tailor scope, constraints, and validation commands before editing.
- Keep the plan updated as execution progresses, including risk and rollback notes for any sensitive change.

## Workflow
1) **Scope**: target apps, displays, login/greeter requirements.
2) **Install**: labwc + required components (waybar, kanshi, swaylock, wofi).
3) **Configure**: place configs under `~/.config/`.
4) **Login**: configure greetd/regreet (optional).
5) **Verify**: test session, locking, and output switching.

## Safety rules
- Keep a fallback TTY or alternate session.
- Avoid autostart scripts that run privileged commands.

## Security checkpoints
- Ensure session config and startup scripts are user-owned and not group/world writable.
- Review autostart entries for privileged commands or unsafe environment injection.
- Confirm lock-screen and idle behavior protect active sessions.

## Testing checkpoints
- Test login, lock/unlock, monitor hotplug, and session recovery from a TTY fallback.
- Verify portal, clipboard, and screenshot permissions for allowed applications.
- Validate required workflow apps across single and multi-monitor setups.

## Deployment checkpoints
- Roll out by host profile with backups of previous compositor configs.
- Keep a known-good config snapshot for quick restore after regressions.
- Schedule session restarts and communicate expected user impact.

## Multi-agent handoff
- Coordinator specifies compositor stack versions, display topology, and must-have apps.
- Executor shares config diffs plus login/lock/output test results.
- Receiver manages per-user overrides and unresolved hardware quirks.
See also:
- `overview.md`
- `../desktop/wayland.md`
- `$CODEX_HOME/templates/desktop/wayland-skeleton/`
- `$CODEX_HOME/snippets/desktop/`
- Use skill `desktop-wayland`.
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/domains/desktop/stack.md`
- `$CODEX_HOME/index/domains/desktop/wayland.md`
