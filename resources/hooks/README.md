# Hooks Runtime

Perl scripts and Perl modules under `resources/hooks/scripts/` are the hook
behavior source of truth in this repository.

The install-facing split is:

1. `config/usr/apps.toml` defines the inline Codex `[hooks]` matcher groups that
   are merged into `$CODEX_HOME/config.toml`.
2. `resources/hooks/scripts/*.pl` provides the installed command entrypoints for
   those matcher groups.
3. `resources/hooks/scripts/lib/Codex/Hook/*.pm` contains the shared hook
   behavior, repo profiles, tool classification, and output shaping.
4. `resources/hooks/schema/generated/` vendors the current hook input/output
   schemas that the Perl runtime validates against.

The `home` / `install` / `upgrade` flow materializes the hook runtime by:

1. Syncing runtime hook assets from `resources/hooks/scripts/` into
   `$CODEX_HOME/hooks/`
2. Syncing vendored hook schemas from `resources/hooks/schema/generated/` into
   `$CODEX_HOME/.hooks/schema/generated/`
3. Merging the inline `[hooks]` table from `config/usr/apps.toml` into
   `$CODEX_HOME/config.toml`

No `hooks.json` bridge is generated or installed. Do not reintroduce a second
same-layer hook source. OpenAI Codex merges matching hook sources, and if both
inline `[hooks]` and `hooks.json` exist in one layer, both sets run.

## Behavioral sources

- `lib/Codex/Hook/RuntimeConfig.pm`
  Shared repo-profile metadata, environment probes, focus areas, prompt rules,
  and stop rules.
- `lib/Codex/Hook/ToolProfile.pm`
  Tool-family classification for shell, edit, and MCP flows.
- `lib/Codex/Hook/Driver.pm`
  Event dispatcher and generic runtime behavior.
- `lib/Codex/Hook/Policy.pm`
  Pre-tool, approval, compaction, and destructive-action guardrails.
- `lib/Codex/Hook/MultiAgent.pm`
  Shared multi-agent prompt detection plus role-family guidance for subagent
  lifecycle hooks.
- `lib/Codex/Hook/SubagentStop.pm`
  Subagent stop handoff guidance.

## Inline hook wiring

`config/usr/apps.toml` carries the full runtime `[hooks]` table. The current
tool-scoped matcher groups are intentionally split so they can have different
commands, timeouts, and status messages:

- `PreToolUse`
  - shell matcher: `^(Bash|exec_command|shell)$`
  - edit matcher: `^(apply_patch|Edit|Write)$`
  - MCP matcher: `^mcp__`
- `PermissionRequest`
  - shell matcher: `^(Bash|exec_command|shell)$`
  - edit matcher: `^(apply_patch|Edit|Write)$`
  - MCP matcher: `^mcp__`
- `PostToolUse`
  - shell matcher: `^(Bash|exec_command|shell)$`
  - edit matcher: `^(apply_patch|Edit|Write)$`
  - MCP matcher: `^mcp__`
- `SubagentStart`
  - coordination matcher: `^(default|manager)$`
  - delivery matcher: `^(worker|coder)$`
  - integrator matcher: `^integrator$`
  - research matcher: `^(explorer|hunter)$`
  - validation matcher: `^(reviewer|tester)$`
  - generic fallback matcher: `^(?!(?:default|manager|worker|coder|integrator|explorer|hunter|reviewer|tester)$).+`
- `SubagentStop`
  - coordination matcher: `^(default|manager)$`
  - delivery matcher: `^(worker|coder)$`
  - integrator matcher: `^integrator$`
  - research matcher: `^(explorer|hunter)$`
  - validation matcher: `^(reviewer|tester)$`
  - generic fallback matcher: `^(?!(?:default|manager|worker|coder|integrator|explorer|hunter|reviewer|tester)$).+`

Because Codex runs multiple matching command hooks for the same event
concurrently, keep matcher groups mutually exclusive.

`SessionStart` uses a source matcher and currently covers:

- `startup`
- `resume`
- `clear`
- `compact`

`UserPromptSubmit` and `Stop` do not use matchers in current Codex behavior and
must self-filter inside the command logic when event-specific gating is needed.
The multi-agent prompt guidance in this repo therefore self-filters for
delegation keywords such as `spawn_agent`, `send_input`, `resume_agent`,
`wait_agent`, `close_agent`, `delegate`, and orchestration terms inside the
Perl runtime instead of relying on TOML matchers.

## Event output expectations

Event output payloads are not all equivalent:

- `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and
  `SubagentStart` can return `hookSpecificOutput.additionalContext`.
- `PermissionRequest`, `PreCompact`, `PostCompact`, and the informational part
  of `SubagentStop` should use `systemMessage`.
- `Stop` and the blocking portion of `SubagentStop` should use top-level
  `decision`, `reason`, and `stopReason`.

The runtime wrappers seed `CODEX_HOOK_SCHEMA_DIR` automatically from either:

- a repo-local `resources/hooks/schema/generated/` tree during development, or
- the installed `$CODEX_HOME/.hooks/schema/generated/` tree at runtime

Hook work in this repo should stay schema-first: emit only fields allowed by
the event output schema, and prefer transcript-driven context over generic
boilerplate.
