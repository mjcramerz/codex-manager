# Codex Install And Runtime Workflow
Purpose: document the host-side commands for installing and maintaining the managed Codex environment.

## Install roots
- Runtime root: `/data/codex`
- Runtime home: `/data/codex/usr/home`
- Lookup files: `/data/codex/lookup/`
- Installed operator docs: `/data/codex/docs/`
- Wrappers: `/data/bin/`

## Main commands
1. `make install`
Installs Debian package dependencies from `.env`, refreshes runtime assets, downloads or installs Codex, rewrites managed config, wrappers, skills, instructions, and docs, and works as both fresh install and in-place upgrade.

2. `make runtime`
Refreshes managed runtime assets without reinstalling Debian package dependencies.

3. `make runtime-home`
Refreshes the runtime-home tree, agents, instructions, system config, and the installed docs copy.

4. `make runtime-skills`
Refreshes skills, plugins, marketplace content, and system skill bundles.

5. `make runtime-instructions`
Refreshes instruction assets and rewrites instruction-file paths into the rendered config.

6. `make vars-init`
Writes the managed shell/profile exports and wrapper launch environment.

7. `make vars-reset`
Removes the managed shell/profile exports and clears the wrapper launch environment from rendered outputs.

8. `make nuke`
Backs up managed state, preserves backup/MCP/sqlite roots, clears managed shell hooks and best-effort keyring entries, and removes managed runtime paths.

## Validation
- `make preflight`
- `python3 -m compileall src tests`
- `python3 -m unittest discover -s tests`
