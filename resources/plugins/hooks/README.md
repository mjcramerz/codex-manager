# Plugin hook assets

Plugin-specific hook files live under `resources/plugins/hooks/<plugin-name>/`.

- The plugin manifest keeps the runtime-relative path in `plugins.<name>.hooks`, for example `./hooks.json`.
- The installer resolves that path against `resources/plugins/hooks/<plugin-name>/` and copies the file into the runtime plugin bundle at the same relative location.
- Home/runtime hook wiring now lives in `resources/hooks/hooks.json` and installs into `$CODEX_HOME/hooks.json`; plugin hook files are optional bundle-local additions, not a replacement for the home hook contract.
- The current plugin hook bundles inject lightweight plugin-specific prompt context by calling the installed global helper at `$CODEX_HOME/.hooks/scripts/plugin_prompt_submit.pl`.
