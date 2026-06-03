# Agent orchestration workflow (entrypoint)
Purpose: stable link to multi-agent orchestration workflow guidance.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/index/core/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


Canonical content: `$CODEX_HOME/docs/workflows/agent-orchestration.md`

Use when:
- a task is large enough to benefit from multiple parallel agents
- you need explicit ownership boundaries and deterministic handoffs
- reviewers need a clean accountability trail for files, tests, and risks
- you want codex-agent style delegation with `spawn_agent`/`send_input`/`wait`/`close_agent`
- you need the role-selection matrix in `$CODEX_HOME/MULTI_AGENT.md`

<!-- BEGIN:related -->
Related:
- `$CODEX_HOME/MULTI_AGENT.md`
- `$CODEX_HOME/docs/workflows/planning.md`
- `$CODEX_HOME/docs/workflows/repo-ops.md`
- `$CODEX_HOME/docs/workflows/code-review.md`
- `$CODEX_HOME/index/pack/workflows.md`
- Use skill `workflow-plans`.
- Use skill `repo-ops`.
<!-- END:related -->
