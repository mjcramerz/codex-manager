# Codex repository workflow

Start with `$CODEX_HOME/plans/workflows/workflow-codex-repo.md` before executing this workflow.
Purpose: keep the Codex source repo and this config pack aligned across tooling, CI/CD, release, and web-stack guidance.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
- Start from the linked workflow plan template above, then tailor scope, constraints, and validation commands before editing.
- Keep the plan updated as execution progresses, including risk and rollback notes for any sensitive change.

## Current upstream anchors
- Upstream reference commit (realtime transport behavior): `10a3adad8ee8d2cc5a22d0d85622d9ea84d2989f` (2026-02-23).
- Upstream schema source-of-truth: `https://raw.githubusercontent.com/openai/codex/refs/heads/main/codex-rs/core/config.schema.json`.
- Upstream bundled model catalog source: `https://raw.githubusercontent.com/openai/codex/main/codex-rs/core/models.json`.

## Source scope
- Primary implementation surface: `codex-rs/` (Rust workspace)
- TypeScript tooling packages: `shell-tool-mcp/`, `sdk/typescript/`, `codex-cli/`
- CI/release orchestration: `.github/workflows/*.yml`
- Adjacent delivery/workflow repos to cross-check for drift:

## Audit workflow
1) **Inventory** language/tooling and test/build entrypoints (`justfile`, Cargo, pnpm, Python scripts).
2) **Close gaps** by updating pack assets with concrete commands, risk notes, and verification steps.
3) **Regenerate** routing artifacts when entrypoints change.
4) **Verify** with the narrowest relevant runtime checks and document residual gaps.

## Config parity checklist (schema -> pack)
- Ensure `$CODEX_HOME/config.toml` covers Codex-home runtime keys used by operators:
  - `model_catalog_json`
  - `background_terminal_max_timeout`
  - `js_repl_node_module_dirs` / `js_repl_node_path` (with practical commented examples)
  - `approval_policy` fine-grained reject example (`RejectConfig`)
  - `mcp_oauth_credentials_store` mode example (`OAuthCredentialsStoreMode`)
- Ensure `/etc/codex/config.toml` keeps commented reference examples for:
  - `experimental_realtime_ws_backend_prompt`
  - `experimental_realtime_ws_base_url`
- Keep layer expectations explicit:
  - `config/vendor/*` compiles only into `/etc/codex/config.toml` and `/etc/codex/requirements.toml`
  - `config/usr/*` compiles only into `$CODEX_HOME/config.toml`
  - `$CODEX_HOME/config.toml` keeps structured inline profile maps under `[permissions]`
  - `/etc/codex/config.toml` keeps structured inline vendor maps under `[permissions]` without normalizing them into another shape
- Keep `$CODEX_HOME/.credentials.json` present as file-store bootstrap for OAuth credentials (`mcp_oauth_credentials_store = "file"` deployments).
- Keep `$CODEX_HOME/.models/model_catalog.json` in sync with upstream `codex-rs/core/models.json`.

## Web stack coverage
- Current Codex source has TypeScript tooling packages but no production React/Next.js/HTMX app tree.
- Keep web guidance ready-to-use for new product surfaces via:
  - `$CODEX_HOME/docs/workflows/web-frontend.md`
  - `$CODEX_HOME/docs/web/overview.md`
  - Use skill `web-react`.
  - Use skill `web-nextjs`.
  - Use skill `web-htmx`.

## CI/CD and release alignment checklist
- Build + tag-guard pipeline: `.github/workflows/build-codex-rs.yml`
- Release publish orchestration from build artifacts: `.github/workflows/release-codex-rs.yml`
- Post-publish release hook: `.github/workflows/publish-codex-rs.yml`
- GitLab delivery baseline and include wiring: `.gitlab-ci.yml` (shared includes via `${GL_CICD_SHARED_PROJ}`)
- Always reflect branch/tag policy and signing/publish behavior in pack docs.

## Contributor process alignment
- Source policy references: `<codex-source-repo>/docs/contributing.md`, `<codex-source-repo>/docs/CLA.md`
- Keep pack guidance explicit about issue-first intake, CLA expectations, and reproducible test evidence.
- This fork snapshot does not currently ship `.github/pull_request_template.md` or `.github/workflows/cla.yml`; treat those as optional overlays instead of required anchors.

## Security checkpoints
- Ensure pack guidance mirrors source trust boundaries (contributor policy, CI permissions, protected release refs).
- Verify referenced workflows do not require broader secrets/scopes than source pipelines allow.
- Track every source-pack security mismatch with owner, issue link, and due date.

## Testing checkpoints
- For each mapping update, run or cite source-equivalent Rust/pnpm/Python checks.
- Validate that every referenced source path/workflow file exists before publishing pack updates.
- Validate TOML syntax after config changes:
  - `python3 -c "import tomllib; tomllib.load(open('$CODEX_HOME/config.toml','rb')); tomllib.load(open('/etc/codex/config.toml','rb'))"`
- Validate catalog JSON syntax after model-catalog refresh:
  - `python3 -c "import json; json.load(open('$CODEX_HOME/.models/model_catalog.json','r',encoding='utf-8'))"`
- Re-run pack verification after edits to confirm indexes and links stay consistent.

## Deployment checkpoints
- Land pack alignment changes before related source release branch/tag cuts whenever possible.
- Coordinate CI/release doc updates so branch/tag policies stay synchronized across repos.
- Keep a rollback note to the previous pack commit if updated guidance causes operator confusion.

## Multi-agent handoff
- Source auditor hands file-to-file mapping (`source path -> pack doc`) with unresolved gaps.
- Pack doc owner records which gaps were fixed, deferred, or escalated.
- Release/docs maintainer confirms `verify.sh` evidence before syncing the updated pack.
See also:
- `overview.md`
- `ci-cd.md`
- `testing.md`
- `release.md`
- `repo-ops.md`
- `web-frontend.md`
- `$CODEX_HOME/index/core/codex-repo.md`
