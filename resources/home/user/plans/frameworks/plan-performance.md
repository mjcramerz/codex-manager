# Plan

Use this plan when optimizing performance or reducing resource usage.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Baseline metrics and target thresholds.
- Workloads or scenarios to optimize.

## Scope
- In: hot paths, critical workflows, and tests.
- Out: unrelated refactors or feature work.

## Dependencies and assumptions
- <benchmark environment parity and workload realism assumptions>
- <instrumentation/profiling access and data retention assumptions>

## Success metrics and exit criteria
- <target latency/throughput/resource improvements>
- <regression guard thresholds and acceptable trade-offs>
- <approval owner for release readiness>

## Files and entry points
- <hot path modules>
- <benchmarks or load tests>

## Action items
[ ] Capture baseline metrics and reproduce workloads.
[ ] Profile and identify bottlenecks.
[ ] Propose optimizations and trade-offs.
[ ] Implement minimal changes and re-measure.
[ ] Add or update performance regression guards.
[ ] Document results and tuning knobs.

## Testing and validation
- <benchmarks, load tests, perf counters>

## Rollout / monitoring
- <alerts for regressions, SLO impact>

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
- <correctness trade-offs, caching pitfalls>

## Examples

- Example objective: "Reduce <latency/CPU> for <path>."
- Example validation: "hyperfine "<command>""

## Open questions
- <missing metrics or tooling>
