# Core routing (overview)
Use this when the task is **workflow-level** and not tied to a specific domain.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/index/core/agent-orchestration.md` — Agent orchestration workflow (entrypoint)
- `$CODEX_HOME/index/core/ci-cd.md` — CI/CD workflow (entrypoint)
- `$CODEX_HOME/index/core/codex-repo.md` — Codex repository workflow (entrypoint)
- `$CODEX_HOME/index/core/execpolicy.md` — Execpolicy workflow (entrypoint)
- `$CODEX_HOME/index/core/perf.md` — Performance playbook (entrypoint)
- `$CODEX_HOME/index/core/plan.md` — Planning workflow (entrypoint)
- `$CODEX_HOME/index/core/repo-ops.md` — Repo operations workflow (entrypoint)
- `$CODEX_HOME/index/core/review-hardening.md` — Review hardening checklist (entrypoint)
- `$CODEX_HOME/index/core/security.md` — Security overview (entrypoint)
- `$CODEX_HOME/index/core/supply-chain.md` — Supply-chain controls (entrypoint)
- `$CODEX_HOME/index/core/testing.md` — Testing workflow (entrypoint)
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/index/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


Before routing, ensure this context order is loaded:
1) `$CODEX_HOME/AGENTS.md`
2) `$CODEX_HOME/memories/MEMORY.md`
3) `$CODEX_HOME/INDEX.md`
4) `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
5) `$CODEX_HOME/index/pack/skills.md`
6) follow `$CODEX_HOME/UNIX.md` before execution


## When to route here
- You need a **plan** or structured workflow guidance.
- You’re doing **testing**, **security**, **CI/CD**, **performance**, or **repo ops** work.
- You need **supply-chain** or **execpolicy** guidance.
- You need **multi-agent orchestration** guidance for parallel task execution.

## Pick one entrypoint (then stop)
- Agent orchestration: `$CODEX_HOME/index/core/agent-orchestration.md`
- Codex repository alignment: `$CODEX_HOME/index/core/codex-repo.md`
- Planning: `$CODEX_HOME/index/core/plan.md`
- Testing: `$CODEX_HOME/index/core/testing.md`
- Security: `$CODEX_HOME/index/core/security.md`
- Review hardening: `$CODEX_HOME/index/core/review-hardening.md`
- CI/CD: `$CODEX_HOME/index/core/ci-cd.md`
- Performance: `$CODEX_HOME/index/core/perf.md`
- Repo ops: `$CODEX_HOME/index/core/repo-ops.md`
- Supply-chain: `$CODEX_HOME/index/core/supply-chain.md`
- Execpolicy: `$CODEX_HOME/index/core/execpolicy.md`

## When NOT to use core
- If the task is **domain/tooling-specific**, go to `$CODEX_HOME/index/domains/overview.md`.
- If you’re **maintaining the pack itself**, go to `$CODEX_HOME/index/pack/overview.md`.
- If you only need **language or shell conventions**, go to `$CODEX_HOME/index/style/overview.md`.
