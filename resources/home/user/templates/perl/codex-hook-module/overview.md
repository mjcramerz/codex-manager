# Codex hook module template
Purpose: scaffold a small Perl hook/runtime module with a matching CLI wrapper for local validation.

## Inputs
- Module name
- Hook/runtime purpose
- Expected input/output shape

## Outputs
- `lib/Codex/Hook/Example.pm`
- `bin/example-hook.pl`

## Next steps
1. Rename the module/package.
2. Add repo-local tests or validation commands.
3. Wire the module into the hook/runtime entrypoint that will call it.
