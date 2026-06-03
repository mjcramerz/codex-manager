# Go style guide
Canonical Go guidance for this pack. Follow repo-specific conventions first.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/style/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline
- Use `gofmt` and `goimports` in CI.
- Keep packages small and cohesive.
- Prefer explicit errors over panic; wrap with context.

## Security
- Validate inputs at boundaries; enforce size limits.
- Set timeouts on all network calls.

## Testing
- Prefer table-driven tests.
- Keep tests deterministic and fast.

## References
- `overview.md`
- Snippets: `$CODEX_HOME/snippets/go/`
- Template: `$CODEX_HOME/templates/go/cli-app/`
- `$CODEX_HOME/index/pack/style.md`
- `$CODEX_HOME/index/style/go.md`
