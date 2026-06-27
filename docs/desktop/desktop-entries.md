# Desktop entries
Guidance for creating `.desktop` files for application launchers.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/desktop/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Use absolute paths in `Exec=`.
- Avoid `sh -c` unless required; prefer direct arguments.
- Keep `Name`, `Comment`, `Icon`, and `Categories` consistent.
- Set `Terminal=false` unless a terminal is required.

## Install locations
- Per‑user: `~/.local/share/applications/`
- System‑wide: `/usr/share/applications/`

## Safety notes
- Do not embed secrets in `Exec` arguments.
- Quote only where required (space‑containing args).

See also:
- `overview.md`
- `$CODEX_HOME/templates/desktop/desktop-entry/`
- `$CODEX_HOME/snippets/desktop/desktop-entry.desktop`
- `../workflows/desktop-entries.md`
- Use skill desktop-entries.
- `$CODEX_HOME/index/domains/desktop/desktop-entries.md`
