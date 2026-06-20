# Memory router
Purpose: provide a stable source-managed entrypoint for repo-aware memory usage without treating runtime dumps as pack source.

## Use this file when
- the task is repo-aware and prior decisions may matter
- the task is ambiguous and you need the shortest path to relevant prior context
- you are validating whether memory artifacts belong in the repo-managed carry-forward set

## Routing order
1. Read this file.
2. If present and relevant, read `raw_memories.md`.
3. If present and relevant, read the phase rollups referenced by the runtime memory workflow.
4. Stop once the needed task family or repository context is clear.

## Repo-managed versus runtime-only
- Repo-managed carry-forward:
  - `memories/**`
  - `history.jsonl`
  - `session_index.jsonl`
  - `version.json`
  - `.personality_migration`
- Runtime-only, never synced back here:
  - `../sessions/`
  - `../shell_snapshots/`
  - `../.credentials.json`

## Notes
- This file is source-managed so `$CODEX_HOME/memories/MEMORY.md` always exists after install.
- Generated rollups next to this file are runtime-managed data, not overview documentation.
- If the memory tree is absent or sparse, continue with direct repo discovery instead of inventing context.
