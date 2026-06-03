# Agent orchestration workflow

Start with `$CODEX_HOME/plans/workflows/workflow-agent-orchestration.md` before executing this workflow.
Purpose: coordinate multi-agent execution with explicit ownership, deterministic handoffs, and bounded risk.
This is the canonical codex-agent playbook for `spawn_agent`/`send_input`/`wait`/`close_agent` workflows.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
- Start from the linked workflow plan template above, then tailor scope, constraints, and validation commands before editing.
- Keep the plan updated as execution progresses, including risk and rollback notes for any sensitive change.
- Use `$CODEX_HOME/MULTI_AGENT.md` to choose the role mix before assigning tracks.

## Role selection
- `manager` owns decomposition, gating, and final reconciliation.
- `explorer` and `hunter` gather local and external evidence before implementation depends on it.
- `worker` and `coder` own bounded implementation tracks.
- `reviewer` and `tester` close the loop with review and validation evidence.

## Workflow
1) **Triage**: split the request into independent tracks with clear acceptance criteria.
2) **Assign**: choose roles from `$CODEX_HOME/MULTI_AGENT.md`, then define ownership by file scope and expected deliverables for each agent.
3) **Run**: launch agents with explicit entrypoints, constraints, and stop conditions.
4) **Reconcile**: merge findings, resolve conflicts, and run final verification as coordinator.

## Ownership contract
- Each agent owns a disjoint file set whenever possible.
- Every handoff must include: objective, scope, constraints, commands run, and remaining risks.
- Coordinators consolidate test evidence and final risk notes before completion.

## Coordination protocol
- Reiterate routing order for each child agent: `$CODEX_HOME/AGENTS.md` -> `$CODEX_HOME/memories/MEMORY.md` -> `$CODEX_HOME/INDEX.md` -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> single entrypoint.
- Use `spawn_agent` for independent tracks only; keep dependent edits in one owner.
- Use `send_input` to refine scope mid-flight, `wait` for completion, and `close_agent` after collecting outputs.

## Security checkpoints
- Assign least-privilege credentials per agent track; never reuse release tokens across tracks.
- Sanitize handoff artifacts (logs, diffs, repro data) before sharing beyond the owning track.
- Require coordinator approval for any sandbox escape, network write, or destructive git operation.

## Testing checkpoints
- Split validation ownership up front (which track runs unit, integration, and security checks).
- Require each agent to report exact commands, exit codes, and scoped evidence for touched files.
- Run one coordinator reconciliation pass (targeted checks plus final smoke) after merging outputs.

## Deployment checkpoints
- Sequence merges by dependency order so deployment jobs never run on partial multi-agent state.
- Gate promotion on a unified risk log with unresolved items and explicit owner sign-off.
- Keep a rollback branch or patch set ready before promoting reconciled multi-agent changes.

## Multi-agent handoff
- Sender includes objective, owned files, stop condition, and required entrypoint in one handoff note.
- Receiver replies with first command and validation plan before making edits.
- Coordinator records handoff status, blockers, and next owner in the execution log.
See also:
- `$CODEX_HOME/MULTI_AGENT.md`
- `overview.md`
- `planning.md`
- `repo-ops.md`
- `code-review.md`
- `$CODEX_HOME/index/core/plan.md`
- `$CODEX_HOME/index/core/repo-ops.md`
- `$CODEX_HOME/index/core/testing.md`
- Use skill `workflow-plans`.
