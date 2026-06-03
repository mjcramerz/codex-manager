# /<command>

## Objective
State exactly what this command should achieve.

## Inputs
- `$ARGUMENTS`: required argument contract and accepted formats.
- Optional context constraints.

## Constraints
- Preserve existing behavior unless explicitly requested.
- Keep output deterministic and reviewable.
- Avoid unsafe or destructive operations without explicit confirmation.

## Workflow
1) Confirm the task scope and assumptions.
2) Inspect only the files needed for this command.
3) Apply minimal edits and keep references synchronized.
4) Run focused verification before full pack verification.

## Verification

## Output contract
- Provide changed file paths.
- Provide checks run and outcomes.
- Provide residual risks or next steps.
