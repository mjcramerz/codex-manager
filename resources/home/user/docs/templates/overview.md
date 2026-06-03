# Templates overview
Guidance for choosing and applying templates in this pack.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/templates/daily-note.md` — Daily Note
- `$CODEX_HOME/docs/templates/note.md` — Note Template
- `$CODEX_HOME/docs/templates/using-templates.md` — Using templates
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Inputs
- Scope to scaffold (app, CI, infra, observability, system, or desktop).
- Runtime/toolchain version policy (pin versions/digests; avoid `latest`).
- Delivery model (standard CI vs GitLab -> GitHub release delivery).

## Outputs
- A selected template path from `$CODEX_HOME/templates/`.
- A deterministic apply checklist from `using-templates.md`.
- Template-specific Inputs/Outputs/Next steps from the chosen `overview.md`.

## Quick map
- Template catalog: `$CODEX_HOME/templates/OVERVIEW.md`
- Usage guide: `using-templates.md`
- Template contract (Inputs/Outputs/Next steps): `$CODEX_HOME/templates/OVERVIEW.md`
- Build workflow: `../workflows/build-an-app.md`
- Template plan: `$CODEX_HOME/plans/templates-library.md`

## Categories
- Common repo hygiene: `$CODEX_HOME/templates/common/`
- CI: `$CODEX_HOME/templates/ci/` (includes GitHub/GitLab release scaffolds for protected release-tag delivery)
- Infrastructure: `$CODEX_HOME/templates/infra/`
- Observability: `$CODEX_HOME/templates/observability/`
- Prompts: `$CODEX_HOME/templates/prompts/`
- Containers: `$CODEX_HOME/templates/containers/`
- systemd: `$CODEX_HOME/templates/systemd/`
- Filesystems: `$CODEX_HOME/templates/filesystems/`
- System hardening: `$CODEX_HOME/templates/system/`
- Virtualization: `$CODEX_HOME/templates/virtualization/`
- Languages: `$CODEX_HOME/templates/python/`, `$CODEX_HOME/templates/rust/`, `$CODEX_HOME/templates/go/`, `$CODEX_HOME/templates/typescript/`
- Web: `$CODEX_HOME/templates/web/`
- Desktop: `$CODEX_HOME/templates/desktop/`

## Next steps
1) Choose a template path from `$CODEX_HOME/templates/OVERVIEW.md`.
2) Apply it with the deterministic flow in `using-templates.md`.
3) Run the template's local verification commands before commit.

See also: `$CODEX_HOME/index/pack/templates.md`
