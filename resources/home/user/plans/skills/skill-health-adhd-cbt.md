# Plan

Use this plan when applying or updating the `health-adhd-cbt` skill.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/skills/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- Use skill health-adhd-cbt.
- health-adhd-cbt skill asset `assets/templates/`
- health-adhd-cbt skill asset `assets/styles/pdf.css`
- health-adhd-cbt skill asset `assets/data/pack-config.json`

## Scope
- In: generating ADHD/CBT printable templates, PDF packs, or updating the health-adhd-cbt skill assets/scripts.
- Out: unrelated mental health guidance or medical advice.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Use skill health-adhd-cbt and linked references.
[ ] Confirm whether the user means CBT or CBD when ambiguous.
[ ] Select templates and data sources (JSON or inline).
[ ] Render HTML/PDF using `render_template.py` or `build_pack.py`.
[ ] Review layout/spacing and adjust CSS if needed.

## Testing and validation
- Run a sample render to HTML to confirm placeholders fill as expected.
- If available, generate a PDF with wkhtmltopdf/weasyprint/pandoc.

## Security checkpoints
- Confirm trust boundaries, credentials, and least-privilege assumptions before execution.
- Validate input bounds, timeout/retry limits, and failure behavior for risky operations.
- Record any approved exception, owner, and expiry before proceeding.

## Testing checkpoints
- Define fast-path and deep validation commands before making changes.
- Capture expected outcomes and acceptance criteria for each validation step.
- Re-run impacted checks after major changes and before final handoff.

## Deployment checkpoints
- Document rollout order, blast-radius controls, and rollback conditions.
- Confirm migration/backfill or feature-flag sequencing when applicable.
- Record post-deploy verification owners and evidence.

## Multi-agent handoff
- Coordinator hands off scope, constraints, and stop condition with the target entrypoint.
- Executor reports touched files, commands run, evidence, blockers, and next action.
- Receiving agent acknowledges handoff completeness before continuing execution.

## Risks and edge cases
- Missing PDF engine (fallback to HTML).
- Oversized data/JSON causing output truncation.
- Misinterpretation of "CBD" vs "CBT".

## Examples
- Example objective: "Generate a 5-day ADHD daily pack with a weekly plan page."
- Example validation: `python3 health-adhd-cbt skill script `scripts/build_pack.py` --config health-adhd-cbt skill asset `assets/data/pack-config.json` --out /tmp/adhd-pack.html`

## Open questions
- None.
