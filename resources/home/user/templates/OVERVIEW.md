# Template catalog
Purpose: provide reusable project skeletons, repo hygiene assets, and operational scaffolds.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use this file when
- you need a larger scaffold than a snippet can provide
- you are choosing a starting layout for a new app, service, CI pipeline, or host workflow
- you are maintaining template families and their overview contracts

## Template contract
- Each template directory should include an `overview.md`.
- Each template overview should state Inputs, Outputs, and Next steps.
- Templates should be copyable with deterministic paths and explicit placeholder replacement guidance.
- Templates should point to the narrowest relevant docs, workflows, and plans rather than duplicating long explanations.

## Major template families
- Common repo hygiene
- Prompt-maintenance scaffolds
- Shell, CI, infra, containers, systemd, filesystems, virtualization
- Language and framework app skeletons
- Observability, system hardening, and desktop stacks

## Selection rules
- Use a template when multiple files must stay aligned.
- Use a snippet when one file or one compact pattern is enough.
- Use a workflow or plan when execution order and validation matter more than scaffold content.

## Copy and adaptation rules
1. Copy the template directory into the target repo.
2. Replace placeholders and sample values before first commit.
3. Run the exact validation commands listed by the template and the target repo.
4. Remove template-only explanatory content that should not ship downstream.

## Related
- `$CODEX_HOME/index/pack/templates.md`
- `$CODEX_HOME/docs/templates/overview.md`
- `$CODEX_HOME/docs/templates/using-templates.md`
- `$CODEX_HOME/plans/templates-library.md`
- `$CODEX_HOME/snippets/OVERVIEW.md`
