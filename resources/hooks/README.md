# Hooks Manifest

`resources/hooks/manifest.json` is the only source of truth for the hook pack.

The `home` / `install` / `upgrade` flow materializes the hook runtime by:

1. Syncs runtime hook assets from `resources/hooks/scripts/` into `$CODEX_HOME/hooks/`
2. Generates `$CODEX_HOME/hooks/scripts/hook_driver.py` and `$CODEX_HOME/hooks.json` from `resources/hooks/manifest.json`

Nothing generated belongs in this repository. If you need to change hook behavior,
edit `resources/hooks/manifest.json` or the runtime driver under
`resources/hooks/scripts/hook_driver.py`, then run `make home`. `make install`
and `make upgrade` also materialize the same generated hook runtime.

`resources/hooks/manifest.json` supports real `#` comments. Use those for
template markers or local notes instead of fake `_comment` keys.

The baseline hook behavior does not depend on repo-specific manifest entries.
The generated driver performs generic detection for:

- git repo root and current branch
- mirror refs (`github/*`, `gitlab/*`, including `origin/...`)
- `patches/release/`
- root instruction files such as `AGENTS.md`
- local hook-source layout (`resources/hooks/manifest.json`)
- local Codex hook source layout (`codex-rs/hooks/schema/generated`)

The manifest is for runtime settings plus optional overlays.

## Shared multi-agent section

The optional top-level `multi_agent` section is shared across repos. It is used
for prompt-time guidance when the user asks about delegation, agents, or
multi-agent coordination.

Fields:

- `trigger_patterns`
  Regexes checked against the user prompt.
- `shared_lines`
  Shared generic guidance rendered before the role list.
- `roles`
  The full shared role catalog.

Each `roles[]` entry contains:

- `name`
- `description`
- `use_when`

Role names must match the configured shared agent names from `config/usr/apps.toml`
and `config/agents/*.toml`.

## Repository blocks

Each repo block contains:

- `id`
- `display_name`
- `match`
  - `repo_names`
  - `all_of_paths`
  - `any_of_paths`

Additional keys such as `environment`, `focus_areas`, `session_start`,
`user_prompt_submit`, and `stop` are optional overlays. If they are omitted, the
generic detection layer still generates usable hooks.

`focus_areas` are repo-relative changed-file buckets. They do not trigger hook
execution by themselves. They are used to turn changed paths into higher-level
focus labels such as `installer`, `runtime`, `engine`, or `core`, which then
show up in session/resume context via `{changed_areas_csv}`.

## Stop rules

If you add manifest stop overlays, supported fields are:

- `id`
- `changed_path_globs`
- `branch_matches_any`
- `when_has_mirror_refs`
- `require_all_patterns`
- `require_any_patterns`
- `forbid_any_patterns`
- `message`

`id` is a stable rule label for humans and tooling. It is currently validated for
shape and uniqueness intent, but it does not drive runtime matching behavior by
itself. Runtime behavior comes from `changed_path_globs`, `branch_matches_any`,
`when_has_mirror_refs`, `require_*`, `forbid_any_patterns`, and `message`.

`message` supports these placeholders:

- `{changed_areas_csv}`
- `{changed_files_preview}`
- `{current_branch}`
- `{repo_id}`
- `{repo_name}`
- `{repo_root}`
- `{runtime_hooks_dir}`
- `{runtime_hooks_driver_path}`

If you add manifest prompt overlays, prompt rules are regex-driven:

- `patterns`
- `lines`

If a rule matches, its `lines` are rendered into hook-specific additional context.
