# Perl style guide
Canonical Perl guidance for this pack. Follow repo-specific conventions first.

## Baseline
- Enable `use strict;` and `use warnings;`.
- Prefer lexical filehandles, three-arg `open`, and explicit UTF-8 handling when reading text.
- Keep parsing, normalization, and rendering logic in small pure functions where possible.
- Use `Path::Tiny`, `File::Spec`, or `File::Basename` patterns instead of hand-rolled path string hacks.

## Input safety
- Treat hook payloads, env vars, files, and subprocess output as untrusted.
- Validate key presence, scalar shapes, ranges, and path boundaries before mutating anything.
- Avoid passing untrusted input through a shell; prefer list-form `system` or direct module APIs.

## Data formats
- Prefer explicit JSON/TOML/YAML parsing libraries instead of regex-only transforms.
- Reparse generated output before finishing the turn.
- Keep STDERR human-readable and STDOUT machine-readable for CLI helpers.

## Validation
- `perl -c path/to/file.pm`
- `prove -lr t` when the repo ships Perl tests

## Related
- `$CODEX_HOME/docs/lang/perl.md`
- `$CODEX_HOME/templates/perl/codex-hook-module/`
- `$CODEX_HOME/index/style/perl.md`
