# UNIX.md - Unix shell execution guide

Use this file for shell-sensitive work after `$CODEX_HOME/AGENTS.md` confirms the active runtime.

## Required Order
- `$CODEX_HOME/AGENTS.md`
- `$CODEX_HOME/memories/MEMORY.md`
- `$CODEX_HOME/INDEX.md`
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/skills.md`
- `$CODEX_HOME/UNIX.md`

## Shared
- Confirm the active shell first, then use the matching shell and the matching skill: `shell-bash`, `shell-zsh`, or `shell-sh`.
- Default to deterministic environment for reproducible commands:
  - `LC_ALL=C`
  - `TZ=UTC`
  - `PYTHONHASHSEED=0`
  - `PYTHONDONTWRITEBYTECODE=1`
- Prefer machine-readable flags where possible:
  - `--json`
  - `--porcelain`
  - `--null`
  - `--color=never`
  - `--no-pager`
- Prefer read-only discovery first, then the smallest deterministic edit.
- Avoid interactive flows, fuzzy output parsing, and destructive commands unless explicitly requested.
- Use `apply_patch` for focused text edits; use deterministic scripts only when broad repetition makes them safer.

## Shared Command Catalog

### Search
- Text search:
  - `LC_ALL=C TZ=UTC rg -n --sort path --color=never 'pattern'`
- Fixed-string search:
  - `LC_ALL=C TZ=UTC rg -n --fixed-strings --sort path --color=never -- 'literal'`
- File listing:
  - `LC_ALL=C TZ=UTC rg --files --sort path`
- Shell/script listing:
  - `LC_ALL=C TZ=UTC find . -type f \\( -name '*.sh' -o -name '*.bash' -o -name '*.zsh' \\) | sort`
- Directory search with filters:
  - `LC_ALL=C TZ=UTC find path -type f -name '*.toml' | sort`

### File Reads
- Head/slice:
  - `LC_ALL=C TZ=UTC sed -n '1,200p' path/to/file`
- Numbered slice:
  - `LC_ALL=C TZ=UTC nl -ba path/to/file | sed -n '40,120p'`
- Tail:
  - `LC_ALL=C TZ=UTC tail -n 100 path/to/file`
- Structured preview:
  - `python3 - <<'PY' ... PY`

### Git
- Worktree state:
  - `LC_ALL=C TZ=UTC git -c color.ui=never status -sb`
- Tracked diff summary:
  - `LC_ALL=C TZ=UTC git -c color.ui=never diff --stat`
- Unstaged diff:
  - `LC_ALL=C TZ=UTC git -c color.ui=never diff`
- Staged diff:
  - `LC_ALL=C TZ=UTC git -c color.ui=never diff --cached`
- File history:
  - `LC_ALL=C TZ=UTC git -c color.ui=never log --oneline -- path/to/file`
- Blame:
  - `LC_ALL=C TZ=UTC git -c color.ui=never blame -L 40,80 path/to/file`
- Branches:
  - `LC_ALL=C TZ=UTC git -c color.ui=never branch --all`
- Show commit:
  - `LC_ALL=C TZ=UTC git -c color.ui=never show --stat <rev>`

### JSON / TOML / YAML
- JSON pretty-print:
  - `python3 -m json.tool file.json`
- TOML parse:
  - `python3 - <<'PY'\nimport tomllib, pathlib\nprint(tomllib.loads(pathlib.Path('file.toml').read_text()))\nPY`
- YAML parse:
  - `python3 - <<'PY'\nimport yaml, pathlib\nprint(yaml.safe_load(pathlib.Path('file.yaml').read_text()))\nPY`
- Deterministic rewrite:
  - use a short `python3` script with explicit key ordering instead of brittle `sed`

### Python
- Syntax check:
  - `LC_ALL=C TZ=UTC python3 -m py_compile path/to/file.py`
- Tree compile:
  - `LC_ALL=C TZ=UTC python3 -m compileall -q src`
- Unit tests:
  - `LC_ALL=C TZ=UTC python3 -m unittest discover -s tests`
- Module run:
  - `LC_ALL=C TZ=UTC PYTHONPATH=src/python python3 -m package.module`

### Shell Validation
- Bash:
  - `LC_ALL=C TZ=UTC bash -n path/to/script.sh`
- Zsh:
  - `LC_ALL=C TZ=UTC zsh -n path/to/script.zsh`
- POSIX sh:
  - `LC_ALL=C TZ=UTC dash -n path/to/script.sh`
  - `LC_ALL=C TZ=UTC sh -n path/to/script.sh`
- Shared shell assets:
  - validate in every runtime the asset claims to support

### Build / Task Runners
- Make dry inspection:
  - `LC_ALL=C TZ=UTC make -n target`
- Make execution:
  - `LC_ALL=C TZ=UTC make target`
- NPM script list:
  - `node -e "console.log(require('./package.json').scripts)"`
- Cargo metadata:
  - `cargo metadata --format-version 1 --no-deps`
- Just recipes:
  - `just --list`

### Processes / Environment
- Current process tree:
  - `ps -ef | sed -n '1,40p'`
- Port listeners:
  - `ss -ltnp`
- Environment subset:
  - `env | sort | rg '^(PATH|HOME|SHELL|USER|TMPDIR)='`
- Command resolution:
  - `command -v bash`
  - `command -v zsh`
  - `command -v sh`
  - `command -v python3`

### Network
- Prefer explicit timeouts and fail-fast flags:
  - `curl --fail --location --max-time 20 --silent --show-error URL`
- Headers only:
  - `curl --fail --location --max-time 20 --silent --show-error --head URL`
- Do not download-and-execute.
- Prefer checksums and pinned URLs when downloads are necessary.

### Networking Diagnostics
- Routes:
  - `ip route`
- Interfaces:
  - `ip addr`
- DNS resolution:
  - `getent hosts example.com`
  - `dig +short example.com`
- Listener inventory:
  - `ss -ltnp`
  - `ss -lunp`
- Active connections:
  - `ss -tnp`
- HTTP probe:
  - `curl --fail --location --max-time 10 --silent --show-error -I https://example.com`
- TLS probe:
  - `openssl s_client -connect example.com:443 -servername example.com </dev/null`

### Archive / File Ops
- Directory tree:
  - `find path -maxdepth 3 | sort`
- Copy preserving mode and timestamps:
  - `cp -a src dst`
- Move/rename:
  - `mv -- src dst`
- Remove file:
  - `rm -- path/to/file`
- Remove tree:
  - `rm -rf -- path/to/dir`
- Create directory:
  - `mkdir -p path/to/dir`
- Symlink target:
  - `readlink -f path`
- Checksum:
  - `sha256sum file`
- Tar list:
  - `tar -tf archive.tar`
- Tar extract to explicit directory:
  - `mkdir -p out && tar -xf archive.tar -C out`
- Zip list:
  - `unzip -l archive.zip`
- Zip extract to explicit directory:
  - `unzip archive.zip -d out`

### Permissions / Ownership
- Mode bits:
  - `stat -c '%a %U %G %n' path`
- Long listing:
  - `ls -ld path`
- Change mode:
  - `chmod 0644 file`
  - `chmod 0755 script.sh`
- Recursive mode change:
  - `chmod -R u=rwX,go=rX dir`
- Change owner:
  - `chown user:group path`
- Recursive owner change:
  - `chown -R user:group dir`
- Check ACLs when relevant:
  - `getfacl path`

### Diff / Patch Workflows
- Unified diff for a file:
  - `diff -u old new`
- Git diff for a file:
  - `git -c color.ui=never diff -- path/to/file`
- Word diff:
  - `git -c color.ui=never diff --word-diff -- path/to/file`
- Check patch applies:
  - `git apply --check patch.diff`
- Apply patch:
  - `git apply patch.diff`
- Reverse patch:
  - `git apply -R patch.diff`
- Prefer `apply_patch` for focused repo edits instead of ad-hoc shell patching.

### Service / systemd
- Unit status:
  - `systemctl status name.service --no-pager`
- Show failed units:
  - `systemctl --failed --no-pager`
- Journal tail:
  - `journalctl -u name.service -n 100 --no-pager`
- Follow journal:
  - `journalctl -u name.service -f`
- Show unit file:
  - `systemctl cat name.service`
- Verify unit:
  - `systemd-analyze verify path/to/unit.service`
- Reload systemd:
  - `systemctl daemon-reload`

### Containers
- Docker ps:
  - `docker ps --format '{{.Names}}\\t{{.Status}}'`
- Podman ps:
  - `podman ps --format '{{.Names}}\\t{{.Status}}'`
- Compose config render:
  - `docker compose config`
  - `podman compose config`
- Image list:
  - `docker images`
- Container logs:
  - `docker logs --tail 100 name`
- Inspect:
  - `docker inspect name`
- Exec:
  - `docker exec -it name sh`
- Prefer explicit compose files, project names, and pinned images.

### JSON / YAML / TOML Mutation Recipes
- JSON key update:
  - `python3 - <<'PY'\nimport json, pathlib\np = pathlib.Path('file.json')\ndata = json.loads(p.read_text())\ndata['key'] = 'value'\np.write_text(json.dumps(data, indent=2) + '\\n')\nPY`
- TOML key update:
  - `python3 - <<'PY'\nimport tomllib, pathlib\ntry:\n    import tomli_w\nexcept ImportError:\n    raise SystemExit('tomli_w required for TOML rewrite')\np = pathlib.Path('file.toml')\ndata = tomllib.loads(p.read_text())\ndata['section']['key'] = 'value'\np.write_text(tomli_w.dumps(data))\nPY`
- YAML key update:
  - `python3 - <<'PY'\nimport yaml, pathlib\np = pathlib.Path('file.yaml')\ndata = yaml.safe_load(p.read_text())\ndata['key'] = 'value'\np.write_text(yaml.safe_dump(data, sort_keys=False))\nPY`
- Prefer explicit scripts over brittle `sed -i` for structured formats.
- Keep rewrites stable: preserve ordering when possible, append final newline, and reparse after mutation.

## Shared Structure
- Discovery:
  - confirm runtime
  - inspect state
  - identify smallest target
- Change:
  - patch the smallest surface
  - avoid format churn
  - keep commands deterministic
- Validate:
  - run the narrowest syntax or parse check first
  - then targeted tests/build checks
  - then broader checks only if justified
- Report:
  - assumptions
  - commands run
  - outcome
  - remaining risk

## Bash
- Invoke explicitly with `bash` for Bash-sensitive commands and Bash assets.
- Prefer non-login `bash -c` for deterministic subprocesses; use login semantics only when startup files are truly required.
- Use Bash-only features intentionally:
  - arrays
  - `[[ ... ]]`
  - `mapfile`
  - `set -Eeuo pipefail`
- Prefer array-based subprocess execution:
  - `cmd=(git status --short)`
  - `"${cmd[@]}"`
- Good Bash validation pattern:
  - `LC_ALL=C TZ=UTC bash -n path/to/script.sh`
  - `shellcheck path/to/script.sh`

## Zsh
- Invoke explicitly with `zsh` for zsh-sensitive commands and zsh assets.
- Prefer non-login `zsh -c` for deterministic subprocesses; use login semantics only when startup files are required.
- Keep zsh assumptions explicit:
  - glob qualifiers
  - `setopt` / `unsetopt`
  - associative arrays
  - completion hooks
  - wrapper semantics
- Use `emulate -L zsh` inside reusable functions when localizing options matters.
- Validate zsh behavior directly:
  - `LC_ALL=C TZ=UTC zsh -n path/to/file.zsh`
- Do not assume Bash semantics for arrays, word splitting, or option names.

## POSIX sh
- Invoke explicitly with `sh` or `dash` for portable `/bin/sh` assets.
- Prefer `shell-sh` when portability matters more than shell convenience.
- Stay inside POSIX syntax:
  - no arrays
  - no `[[ ... ]]`
  - no brace expansion
  - no process substitution
  - no shell-specific flags unless guarded
- Prefer:
  - `set -eu`
  - `IFS= read -r line`
  - `printf`
  - `command -v`
- Validate with:
  - `LC_ALL=C TZ=UTC dash -n path/to/script.sh`
  - `LC_ALL=C TZ=UTC sh -n path/to/script.sh`

## Safety
- Never dump secrets or full environment blobs into logs.
- Refuse to operate on empty paths, `/`, or ambiguous globs in mutating commands.
- Use `--` before untrusted positional arguments where supported.
- Prefer fixed-string search over regex search when the intent is literal matching.
- Prefer temp-file plus atomic rename over in-place mutation when script safety matters.
- If the active shell changes mid-task, rerun the detection command from `$CODEX_HOME/AGENTS.md` and switch to the matching section above.
