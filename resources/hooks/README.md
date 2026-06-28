# Hooks Runtime

`resources/hooks/hooks.json` is the checked-in home hook manifest source for this
repository.

## Source layout

1. `resources/hooks/hooks.json`
   - Defines the full runtime hook event table that installs to
     `$CODEX_HOME/hooks.json`.
   - Uses `${CODEX_HOME}` placeholders in command strings; the installer
     materializes them to absolute runtime paths during install and verify.
2. `resources/hooks/scripts/*.pl`
   - Provides the installed command entrypoints referenced by `hooks.json`.
   - Installs to `$CODEX_HOME/.hooks/scripts/`.
3. `resources/hooks/scripts/lib/Codex/Hook/*.pm`
   - Contains the shared hook behavior, repo profiles, tool classification, and
     output shaping used by the Perl runtime.
   - Installs to `$CODEX_HOME/.hooks/modules/Codex/Hook/`.
4. `resources/hooks/schema/generated/`
   - Vendors the current hook input/output schemas that the Perl runtime
     validates against.
5. `resources/hooks/scripts/lib/Codex/Hook/HookManifest.toml`
   - Holds generation and validation metadata for tool profiles, subagent
     profiles, and shared role definitions used by the repo-side validators and
     Perl catalog.

## Install flow

The installer materializes the hook runtime by:

1. Syncing `resources/hooks/scripts/*.pl` into `$CODEX_HOME/.hooks/scripts/`
2. Syncing `resources/hooks/scripts/lib/` into `$CODEX_HOME/.hooks/modules/`
3. Syncing `resources/hooks/schema/generated/` into
   `$CODEX_HOME/.hooks/schema/generated/`
4. Rendering `resources/hooks/hooks.json` into `$CODEX_HOME/hooks.json`

`$CODEX_HOME/config.toml` no longer carries inline `[hooks]` entries for the
home runtime.

## Validation rules

- Keep `resources/hooks/hooks.json` aligned with the checked-in hook scripts and
  the generated layout derived from `HookManifest.toml`.
- Keep matcher groups mutually exclusive because Codex can run matching command
  hooks concurrently.
- `UserPromptSubmit` and `Stop` still self-filter inside the Perl command logic
  when event-specific gating is required.
- Hook work should stay schema-first: emit only fields allowed by the event
  output schema, and prefer transcript-driven context over generic boilerplate.

## Behavioral sources

- `lib/Codex/Hook/RuntimeConfig.pm`
  - Shared repo-profile metadata, environment probes, focus areas, prompt
    rules, and stop rules.
- `lib/Codex/Hook/ToolProfile.pm`
  - Tool-family classification for shell, edit, MCP, and generic tool fallback
    flows.
- `lib/Codex/Hook/Driver.pm`
  - Event dispatcher and generic runtime behavior.
- `lib/Codex/Hook/Policy.pm`
  - Pre-tool, approval, compaction, and destructive-action guardrails.
- `lib/Codex/Hook/MultiAgent.pm`
  - Shared multi-agent prompt detection plus role-family guidance for subagent
    lifecycle hooks.
- `lib/Codex/Hook/SubagentStop.pm`
  - Subagent stop handoff guidance.

Managed MCP auth remains outside the hook payload contract:

- URL MCP servers may declare `bearer_token_env_var`.
- Stdio / `command` MCP servers must use wrapper `env_vars` instead.
