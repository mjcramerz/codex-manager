# Codex Pack Index

Start here (order):
- `$CODEX_HOME/AGENTS.md` for global rules
- `$CODEX_HOME/memories/MEMORY.md` for memory context (`default/global` when unsure)
- `$CODEX_HOME/INDEX.md` (this router) for entrypoints
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md` for execution framing
- `$CODEX_HOME/index/pack/skills.md` for relevant skill playbooks
- follow `$CODEX_HOME/UNIX.md` before execution

## Fast onboarding catalogs
- Runtime docs hub: `$CODEX_HOME/docs/OVERVIEW.md`
- Runtime prompts hub: `$CODEX_HOME/prompts/OVERVIEW.md`
- Runtime snippets hub: `$CODEX_HOME/snippets/OVERVIEW.md`
- Runtime templates hub: `$CODEX_HOME/templates/OVERVIEW.md`
- Runtime skill roots: `$CODEX_SKILLS` and the managed admin skill root
- Plugin runtime guide: `$CODEX_HOME/docs/plugins.md`
- Multi-agent role guide: `$CODEX_HOME/MULTI_AGENT.md`

Use this router to jump to hubs, core entrypoints, domains, and style guides.
This file is generated from `$CODEX_HOME/index/manifest.yml`.

## Routing order (stop once you have the right entrypoint)
- `$CODEX_HOME/index/OVERVIEW.md` → routing guardrails and when to branch
- `$CODEX_HOME/index/core/overview.md` → core workflows (plan/testing/security/etc.)
- `$CODEX_HOME/index/domains/overview.md` → domain routers (system/infra/observability/etc.)
- `$CODEX_HOME/index/pack/overview.md` → pack hubs (docs/plans/prompts/templates/snippets/skills)
- `$CODEX_HOME/index/style/overview.md` → style guides

## Quick decision (pick one)
- Pack maintenance → `$CODEX_HOME/index/pack/overview.md`.
- Domain/tooling-specific → `$CODEX_HOME/index/domains/overview.md`.
- Workflow-level or unclear → `$CODEX_HOME/index/core/overview.md`.
- Language/shell conventions only → `$CODEX_HOME/index/style/overview.md`.

## When to route
- Core: use for cross-cutting workflow guidance.
- Domains: use for platform/tooling specifics.
- Pack hubs: use for pack maintenance and catalogs.
- Style: use for language- or shell-specific conventions.
- Avoid deep docs unless the entrypoint requires it.

## Multi-agent clarity
- When multiple agents share a task, require each agent to follow AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> one entrypoint.
- Use `$CODEX_HOME/index/core/agent-orchestration.md` for delegation, ownership, and reconciliation guidance, and `$CODEX_HOME/MULTI_AGENT.md` to choose the right role mix.

## Pack Hubs
- `$CODEX_HOME/index/pack/config.md` — stable link to the pack’s configuration and runtime settings.
- `$CODEX_HOME/index/pack/docs.md` — stable index to the pack’s documentation.
- `$CODEX_HOME/index/pack/plans.md` — stable index to pack plan templates.
- `$CODEX_HOME/index/pack/prompts.md` — stable index to prompt-maintenance workflow guidance and assets.
- `$CODEX_HOME/index/pack/workflows.md` — stable index to the pack’s workflow playbooks.
- `$CODEX_HOME/index/pack/templates.md` — stable index to the pack’s templates.
- `$CODEX_HOME/index/pack/snippets.md` — stable index to hardened snippets and patterns.
- `$CODEX_HOME/index/pack/skills.md` — stable index to skills and deep playbooks.
- `$CODEX_HOME/index/pack/style.md` — stable link to language and scripting style entrypoints.
- `$CODEX_HOME/index/pack/rules.md` — stable link to execpolicy rule files and structure.
- `$CODEX_HOME/index/pack/plugins.md` — stable link to runtime plugin bundle guidance.

## Core Entrypoints
- `$CODEX_HOME/index/core/agent-orchestration.md` — stable link to multi-agent orchestration workflow guidance.
- `$CODEX_HOME/index/core/ci-cd.md` — stable link to CI/CD guidance and templates.
- `$CODEX_HOME/index/core/codex-repo.md` — stable link to Codex repository implementation workflow guidance.
- `$CODEX_HOME/index/core/execpolicy.md` — stable link to execpolicy rules and guardrails.
- `$CODEX_HOME/index/core/perf.md` — stable link to performance guidance.
- `$CODEX_HOME/index/core/plan.md` — stable link to the pack’s planning workflow.
- `$CODEX_HOME/index/core/repo-ops.md` — stable link to repo automation guidance.
- `$CODEX_HOME/index/core/review-hardening.md` — stable link to the security review checklist.
- `$CODEX_HOME/index/core/security.md` — stable link to the security overview and checklists.
- `$CODEX_HOME/index/core/supply-chain.md` — stable link to supply-chain guidance and audit controls.
- `$CODEX_HOME/index/core/testing.md` — stable link to the testing workflow and strategy guidance.

## Domains
- `$CODEX_HOME/index/domains/desktop/overview.md` — desktop entrypoints
- `$CODEX_HOME/index/domains/infra/overview.md` — infra entrypoints
- `$CODEX_HOME/index/domains/lang/overview.md` — lang entrypoints
- `$CODEX_HOME/index/domains/observability/overview.md` — observability entrypoints
- `$CODEX_HOME/index/domains/system/overview.md` — system entrypoints
- `$CODEX_HOME/index/domains/vscode/overview.md` — vscode entrypoints
- `$CODEX_HOME/index/domains/web/overview.md` — web entrypoints

## Style
- `$CODEX_HOME/index/style/style-guides.md` — stable link to the pack’s style guide index.
- `$CODEX_HOME/index/style/bash.md` — stable link to the canonical Bash style guide.
- `$CODEX_HOME/index/style/go.md` — stable link to the canonical Go style guide.
- `$CODEX_HOME/index/style/python.md` — stable link to the canonical Python style guide.
- `$CODEX_HOME/index/style/rust.md` — stable link to the canonical Rust style guide.
- `$CODEX_HOME/index/style/sh.md` — stable link to the canonical POSIX sh style guide.
- `$CODEX_HOME/index/style/typescript.md` — stable link to the canonical TypeScript style guide.
