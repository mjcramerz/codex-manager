# Plugins runtime overview

Use this guide when working with runtime plugin bundles inside an installed Codex home.

## What exists at runtime
- Plugin enablement lives in `$CODEX_HOME/config.toml` under `[plugins]`.
- Marketplace metadata lives in `$CODEX_HOME/.agents/plugins/marketplace.json`.
- Installed plugin bundles live under `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/local/`.
- Plugin bundle ids use `<plugin>@<marketplace>`.

## How to invoke plugins and skills
- Plugins do not appear in `/` slash-command lists.
- Plugin bundle mentions use the `$` mention picker and store `plugin://<plugin@marketplace>` bindings.
- Plugin-local skills, tools, and apps also use the `$` mention picker and `skill://...` or `app://...` bindings.
- Select the popup entry so Codex stores the hidden bound mention for that turn.
- Typing plain `$plugin-name`, `$skill-name`, or `$app-name` text without selecting the popup is not the same as inserting the bound mention.

## What a bundle contains
- `.codex-plugin/plugin.json` — plugin manifest and interface metadata.
- `skills/` — plugin-local skills exposed by the bundle.
- `.mcp.json` — plugin-scoped MCP server definitions when present.
- `.app.json` — plugin-scoped app definitions when present.

## Runtime checks
- Inspect enabled plugins with `rg -n "^\[plugins\]" "$CODEX_HOME/config.toml"` and `rg -n "enabled =" "$CODEX_HOME/config.toml"`.
- Inspect the marketplace with `python3 -m json.tool "$CODEX_HOME/.agents/plugins/marketplace.json"`.
- Inspect one installed bundle with `find "$CODEX_HOME/plugins/cache" -maxdepth 5 -type f | sort`.
- Verify skills/apps/MCP parity for each runtime bundle:
  ```bash
  python3 - <<'PY'
  import json
  import os
  from pathlib import Path

  root = Path(os.environ["CODEX_HOME"]) / "plugins" / "cache"
  for plugin in sorted(root.glob("*/*/local/.codex-plugin/plugin.json")):
      data = json.loads(plugin.read_text())
      has_skills = bool(data.get("skills"))
      has_mcp = str(data.get("mcpServers", "")).endswith(".mcp.json")
      has_apps = str(data.get("apps", "")).endswith(".app.json")
      print(f"{data.get('name')}: skills={has_skills} mcp={has_mcp} apps={has_apps}")
  PY
  ```

## Related runtime paths
- `$CODEX_HOME/config.toml`
- `$CODEX_HOME/.agents/plugins/marketplace.json`
- `$CODEX_HOME/plugins/cache/`
- `$CODEX_HOME/index/pack/plugins.md`
