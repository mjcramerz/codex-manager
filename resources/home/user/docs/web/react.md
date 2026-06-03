# React
Guidance for React component architecture and UX hygiene.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/web/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Prefer function components and hooks.
- Keep state local; lift only when necessary.
- Memoize expensive computations in hot paths.
- Keep component contracts typed (`props`, callbacks, domain models) and avoid implicit `any`.
- Separate presentational and data-fetching concerns to keep tests fast.

## Performance
- Split bundles by route or feature.
- Avoid large dependency trees and repeated re-renders.

## Validation checklist
- Type safety: `pnpm -r typecheck` (or `tsc --noEmit`) on affected packages.
- Quality gates: `pnpm -r lint`, targeted unit/component tests, and production build.
- Accessibility: keyboard flow, focus order, semantic landmarks, and color contrast checks.
- Security: no secrets in client code, sanitize untrusted HTML, and enforce safe URL handling.

See also:
- `overview.md`
- `nextjs.md`
- `$CODEX_HOME/templates/web/react-vite-app/`
- Use skill web-react.
- `$CODEX_HOME/index/domains/web/frameworks.md`
- `$CODEX_HOME/index/domains/web/react.md`
