# Prompt writing
Purpose: write concise, testable prompts that produce deterministic engineering outputs.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Include (high-signal)
- exact behavior to implement
- acceptance criteria (observable, verifiable)
- constraints (no network, target OS, perf budget)
- examples (inputs/outputs) when behavior is subtle
- tests to add or run
- threat model notes when handling untrusted input

## Avoid
- long preambles
- restating generic best practices
- ambiguous scope (“make it better” without a target)

## Tips
- Reference files or modules to anchor the agent.
- Use absolute paths for critical files and commands.
- Prefer one clear objective over multi-part requests in a single prompt.
- Call out non-negotiables first (security, data safety, rollout constraints).

See also:
- `workflows/planning.md`
