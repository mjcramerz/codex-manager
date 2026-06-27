# Thorium Browser
Guidance for building and configuring Thorium.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/desktop/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Follow upstream build instructions; pin toolchains and dependencies.
- Build in a clean environment (VM or container) to ensure reproducibility.
- Verify build outputs and record hashes.

## Build workflow (high‑level)
1) Clone the repository and submodules.
2) Install pinned toolchain dependencies.
3) Configure build flags (release, target, symbols).
4) Build and package.
5) Create a `.desktop` entry and verify runtime flags.

## Safety notes
- Avoid running build steps as root.
- Keep build artifacts isolated from browser user-data directories.

See also:
- `browsers.md`
- `../workflows/browsers.md`
- Use skill desktop-thorium.
- `$CODEX_HOME/index/domains/desktop/thorium.md`
