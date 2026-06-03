# VS Code overview
Guidance for consistent editor configuration across teams and machines.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/vscode/devcontainer.md` — VS Code devcontainers
- `$CODEX_HOME/docs/vscode/settings.md` — VS Code settings
- `$CODEX_HOME/docs/vscode/theming.md` — VS Code theming
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Scope
- Settings and keybindings (`settings.json`, `keybindings.json`)
- Shared defaults and machine-specific overrides
- Devcontainers and remote development
- Theming and UX consistency
- Extensions and marketplace hygiene

## Recommended posture
- Keep settings minimal and intentional; avoid per-user drift.
- Prefer documented settings layers for machine- or role-specific customization.
- Treat devcontainers as code: pin images, review changes, keep secrets out.
- Enforce workspace trust defaults; avoid executing untrusted code.

## Quick map
- Settings: `settings.md`
- Devcontainers: `devcontainer.md`
- Theming: `theming.md`
- Extensions workflow: `../workflows/vscode-extensions.md`

See also:
- `$CODEX_HOME/index/domains/vscode/guidance.md`
- `$CODEX_HOME/index/domains/vscode/vscode-extension.md`
