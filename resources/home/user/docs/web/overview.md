# Web frameworks overview
Guidance for frontend framework selection and safe defaults.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/web/htmx.md` — HTMX
- `$CODEX_HOME/docs/web/nextjs.md` — Next.js
- `$CODEX_HOME/docs/web/nuxt.md` — Nuxt
- `$CODEX_HOME/docs/web/react.md` — React
- `$CODEX_HOME/docs/web/sveltekit.md` — Svelte / SvelteKit
- `$CODEX_HOME/docs/web/vue.md` — Vue
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Quick map
- React: `react.md`
- Next.js: `nextjs.md`
- Svelte/SvelteKit: `sveltekit.md`
- Vue: `vue.md`
- Nuxt: `nuxt.md`
- HTMX: `htmx.md`

## Baseline practices
- Prefer small bundles and code-splitting.
- Avoid unbounded client-side state and large dependencies.
- Keep accessibility in scope (keyboard, contrast, ARIA).

## Decision checklist
- Use **React** when you need flexible component composition with explicit client-state management.
- Use **Next.js** when you need mixed SSR/SSG/ISR with clear server/client module boundaries.
- Use **HTMX** when server-driven rendering and progressive enhancement are priorities.
- Keep TypeScript strict across all options and wire lint/test/build commands into CI before rollout.

## Codex source reality check
- Codex source currently uses TypeScript for tooling packages, not a production web app surface.
- Treat these docs as implementation-ready guidance for new UI surfaces and keep them path-backed once frontend code is introduced.

See also:
- `$CODEX_HOME/templates/web/`
- `../workflows/web-frontend.md`
- `$CODEX_HOME/index/domains/web/frameworks.md`
