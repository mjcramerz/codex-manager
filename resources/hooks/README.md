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
- `lib/Codex/Hook/HookManifest.toml`
  Generation/validation metadata for the exact inline hook routing contract plus
  shared role/profile metadata. It is not read by the installed Perl runtime.
- `lib/Codex/Hook/ToolProfile.pm`
  Tool-family classification for shell, edit, MCP, and generic tool fallback
  flows.
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

`config/usr/apps.toml` carries the full runtime `[hooks]` table. Keep every hook
group explicit there. `lib/Codex/Hook/HookManifest.toml` is generation/validation-only
metadata for every hook family plus shared role/profile metadata; it must not
replace the explicit TOML hook routing contract.

The repo validator treats that manifest as the canonical expected inline
contract: matcher groups, script command, timeout, and status message must stay
aligned with the manifest and the checked-in Perl catalog.

- `SessionStart`
  - explicit in `config/usr/apps.toml`
- `UserPromptSubmit`
  - explicit in `config/usr/apps.toml`
- `PreToolUse`
  - explicit in `config/usr/apps.toml`
- `PermissionRequest`
  - explicit in `config/usr/apps.toml`
- `PostToolUse`
  - explicit in `config/usr/apps.toml`
- `PreCompact`
  - explicit in `config/usr/apps.toml`
- `PostCompact`
  - explicit in `config/usr/apps.toml`
- `SubagentStart`
  - explicit in `config/usr/apps.toml`
- `SubagentStop`
  - explicit in `config/usr/apps.toml`
- `Stop`
  - explicit in `config/usr/apps.toml`

Because Codex runs multiple matching command hooks for the same event
concurrently, keep matcher groups mutually exclusive.

Tool events keep explicit shell, edit, and MCP matcher groups plus an explicit
generic fallback group so uncategorized tool calls still pass through hook
guidance and validation.

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
