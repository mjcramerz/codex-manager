# Go
Guidance for Go module structure and operational defaults.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/lang/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Use modules (`go.mod`) and keep dependencies minimal.
- Prefer `cmd/<app>` for binaries and `internal/` for private packages.
- Add context/timeouts to network calls.

## Testing
- Keep unit tests fast and deterministic.
- Use `go test ./...` in CI with `-race` where feasible.

See also:
- `overview.md`
- `../style/go.md`
- `$CODEX_HOME/templates/go/cli-app/`
- `$CODEX_HOME/snippets/go/main.go`
- Use skill lang-go.
- `$CODEX_HOME/index/domains/lang/languages.md`
- `$CODEX_HOME/index/domains/lang/go.md`
