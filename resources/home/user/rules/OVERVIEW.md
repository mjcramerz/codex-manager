# Execpolicy rules (OVERVIEW) (`$CODEX_HOME/rules/*.rules`)
These rules control command execution outside the sandbox.

Design intent of this pack:
- Keep broad day-to-day automation available without constant approval prompts.
- Keep explicit hard-deny coverage for destructive, privilege-escalating, and outage-causing commands.
- Keep rule ordering deterministic so behavior is reviewable and reproducible.

## Multi-agent handoffs
- Share this entrypoint plus the AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> entrypoint order with any agent you `spawn_agent`.
- Log the handoff (entrypoint + stop condition) and keep status visible via `send_input`/`wait`/`close_agent` so reviewers can trace who handled each rule set.

## Rule evaluation
- Codex picks the strictest decision when multiple rules match.
- Keep broad allow rules in lower-numbered files and strict denies in `90-forbidden.rules`.
- When adding new tooling, add/adjust allows in the closest domain file and add a deny if the command has obvious destructive modes.

## Rule format (schema)
Rules are function calls using `prefix_rule`, which matches command-token prefixes.

```
prefix_rule(
  pattern = ["git","status"],
  decision = "allow",
  match = [
    ["git","status","--porcelain=v1"],
  ],
  not_match = [
    ["git","status","--ignored"],
  ],
)
```

Fields:
- `pattern`: command tokens matched as a prefix.
- `decision`: `allow` or `forbidden`.
- `match`: examples that must match.
- `not_match` (optional): examples that must not match.

## Rule files
- `$CODEX_HOME/rules/00-core.rules` - broad baseline shell and inspection tooling.
- `$CODEX_HOME/rules/10-vcs.rules` - git and VCS workflows.
- `$CODEX_HOME/rules/12-scripting.rules` - language runtime and script execution tooling.
- `$CODEX_HOME/rules/20-network.rules` - network, cloud, and remote-access tooling.
- `$CODEX_HOME/rules/25-packages.rules` - package manager and toolchain installers.
- `$CODEX_HOME/rules/30-system.rules` - host, filesystem, service, and process operations.
- `$CODEX_HOME/rules/35-crypto.rules` - key, certificate, and signing tools.
- `$CODEX_HOME/rules/40-infra.rules` - containers, orchestration, and infra tooling.
- `$CODEX_HOME/rules/90-forbidden.rules` - explicit hard-deny rules (privilege escalation, destructive ops, outage commands).

## Editing checklist
- Keep command coverage broad enough for routine maintenance.
- Add explicit forbids for high-risk subcommands and destructive command forms.
- Add `match`/`not_match` examples so intent is self-tested.
- Re-run `make preflight`, `make verify`, and any targeted `python3 -m py_compile` or `python3 -m unittest` checks after edits.
