package Codex::Hook::RuntimeConfig;

use strict;
use warnings;

use Exporter qw(import);

our @EXPORT_OK = qw(runtime_config);

sub _role {
    my ($name, $description, $use_when) = @_;
    return {
        name        => $name,
        description => $description,
        use_when    => $use_when,
    };
}

sub runtime_config {
    return {
        version     => 1,
        multi_agent => {
            trigger_patterns => [
                '\bagent\b',
                '\bagents\b',
                '\bsubagent\b',
                '\bsub-agent\b',
                '\bspawn_agent\b',
                '\bspawn_agents_on_csv\b',
                '\bsend_input\b',
                '\bresume_agent\b',
                '\bwait_agent\b',
                '\bclose_agent\b',
                '\bdelegate\b',
                '\bdelegation\b',
                '\bmulti-agent\b',
                '\bmulti_agents\b',
                '\bparallel agents?\b',
                '\bfanout\b',
                '\borchestrat\b',
                '\bhandoff\b',
            ],
            shared_lines => [
                'Multi-agent roles are shared across repos and come from the shared configured role catalog.',
                'Prefer the smallest role that fits the task, keep ownership boundaries explicit, and hand off commands, files, evidence, and residual risks.',
            ],
            prompt_submit_lines => [
                'Only use `spawn_agent` when the user explicitly asks for sub-agents, delegation, or parallel agent work.',
                'Keep the next critical-path step local, then delegate only bounded sidecar work with explicit file ownership, commands, and acceptance criteria.',
                'Prefer `send_input` or `resume_agent` when follow-up depends on an existing child context, use `wait_agent` only when the critical path is blocked, and use `close_agent` only after you reconcile the child handoff.',
            ],
            roles => [
                _role(
                    'default',
                    'Baseline generalist agent for most coding, configuration, and integration tasks with live web-search access.',
                    'Use for small or mixed tasks that do not need a specialized handoff role.',
                ),
                _role(
                    'manager',
                    'Project manager that owns planning, gating, artifact checks, and multi-agent handoffs.',
                    'Use to decompose work, define acceptance criteria, assign owned slices, and gate handoffs between other agents.',
                ),
                _role(
                    'worker',
                    'Scoped delivery agent for bounded tasks with explicit file ownership and tight handoffs.',
                    'Use for fast, narrow execution on a clearly owned slice with low ambiguity.',
                ),
                _role(
                    'coder',
                    'Implementation-heavy coding agent for complex root-cause fixes and cross-cutting changes.',
                    'Use for substantial implementation work, root-cause fixes, and changes that cut across modules.',
                ),
                _role(
                    'integrator',
                    'Read-first integration agent that checks mirror sync and release patch readiness without applying patches.',
                    'Use for mirror-awareness, release-patch validation, and repository-safety checks where mutation should stay minimal or read-only.',
                ),
                _role(
                    'hunter',
                    'Search-forward research agent for current docs, APIs, runtime behavior, and external evidence.',
                    'Use when the answer depends on live external references, current docs, or source-backed research.',
                ),
                _role(
                    'explorer',
                    'Read-heavy explorer for repository mapping, dependency tracing, and codebase discovery.',
                    'Use for deep read-only repo exploration, dependency tracing, and handoff-ready architecture mapping.',
                ),
                _role(
                    'reviewer',
                    'Review agent for syntax, hardening, functionality, regressions, and best-practice checks.',
                    'Use for review passes that need severity-ranked findings, correctness checks, and regression analysis.',
                ),
                _role(
                    'tester',
                    'Verification agent that reproduces issues, runs targeted tests, and validates completed work.',
                    'Use for focused verification, reproduction, failure-path checks, and evidence-backed validation.',
                ),
            ],
            subagent_profiles => [
                {
                    id         => 'coordination',
                    role_names => ['default', 'manager'],
                    start_lines => [
                        'Own decomposition, acceptance criteria, and sequencing before you ask any child agent to do work.',
                        'Delegate discovery to `explorer` or `hunter`, implementation to `worker` or `coder`, and sign-off to `reviewer` or `tester`.',
                    ],
                    stop_lines => [
                        'Do not accept the handoff until it lists owned files, exact commands, evidence, and residual blockers.',
                        'Reconcile each child result against the parent plan before you re-delegate or end the turn.',
                    ],
                },
                {
                    id         => 'delivery',
                    role_names => ['worker', 'coder'],
                    start_lines => [
                        'Stay inside the assigned file boundary and return exact edits, commands, or blockers instead of broad redesign guidance.',
                        'Do not spawn another child unless the remaining task is clearly orthogonal and the parent explicitly needs that split.',
                    ],
                    stop_lines => [
                        'Report the owned files, commands run, and any unverified assumptions in the handoff.',
                        'If validation was skipped, say exactly what blocked it and whether the parent must rerun it.',
                    ],
                },
                {
                    id         => 'integrator',
                    role_names => ['integrator'],
                    start_lines => [
                        'Keep the scope read-first and repository-safe unless the parent explicitly broadened the task beyond integration checks.',
                        'Focus on merge points, config layering, release or mirror contracts, and drift between child slices.',
                    ],
                    stop_lines => [
                        'Call out conflicts between child outputs, config layers, or promotion contracts before the parent integrates anything.',
                        'Flag unresolved compatibility or sequencing risks explicitly.',
                    ],
                },
                {
                    id         => 'research',
                    role_names => ['explorer', 'hunter'],
                    start_lines => [
                        'Gather source-backed repository or documentation evidence and avoid speculative implementation advice.',
                        'Return precise references, affected surfaces, and confidence notes instead of patches unless the parent explicitly asked for edits.',
                    ],
                    stop_lines => [
                        'Separate confirmed facts from hypotheses and list any gaps that still need local validation.',
                        'If sources conflict, say that clearly instead of blending them.',
                    ],
                },
                {
                    id         => 'validation',
                    role_names => ['reviewer', 'tester'],
                    start_lines => [
                        'Reproduce or verify the claimed behavior with the narrowest deterministic checks that prove or falsify the concern.',
                        'Return raw outcomes, exact commands, and failing boundaries instead of redesign suggestions.',
                    ],
                    stop_lines => [
                        'State pass, fail, or untested per check, plus the exact blocker whenever a check could not run.',
                        'Surface regression risk and missing coverage explicitly before the parent closes the task.',
                    ],
                },
            ],
        },
        repos => [
            {
                id           => 'codex-manager',
                display_name => 'codex-manager',
                match        => {
                    repo_names   => ['codex-manager', 'c0d3x'],
                    all_of_paths => [
                        'src/install/codex_install.py',
                        'config/usr/apps.toml',
                        'Makefile',
                    ],
                    any_of_paths => ['Makefile'],
                },
                environment => {
                    required_commands => ['bash', 'make'],
                    optional_commands => ['shellcheck', 'yamllint', 'uv', 'wrangler', 'node', 'npx'],
                    optional_probes   => [
                        {
                            label   => 'docker ps',
                            command => ['docker', 'ps'],
                        },
                    ],
                },
                focus_areas => [
                    {
                        label      => 'installer',
                        path_globs => ['src/install/**', 'Makefile'],
                    },
                    {
                        label      => 'runtime',
                        path_globs => ['resources/**', 'tests/**'],
                    },
                    {
                        label      => 'agents',
                        path_globs => ['config/agents/**', 'config/usr/apps.toml'],
                    },
                ],
                session_start => {
                    startup_context => [
                        'Repo role: Codex installer and runtime-configuration source tree.',
                        'Primary edit surfaces: `src/install/**`, `config/usr/apps.toml`, `config/agents/*.toml`, runtime configuration under `config/usr/*`, `config/vendor/*`, and source/supporting assets under `resources/**`.',
                        'Primary local checks for installer and runtime-generation work are `python3 -m compileall -q src tests` and `python3 -m unittest discover -s tests`.',
                    ],
                    resume_context => [
                        'Resume focus stays on `src/install/**`, `config/usr/**`, `config/vendor/**`, `config/agents/**`, `resources/**`, and `tests/**`.',
                    ],
                },
                user_prompt_submit => {
                    rules => [
                        {
                            patterns => [
                                '\binstall\b',
                                '\binstaller\b',
                                '\bruntime\b',
                                '\bconfig\b',
                                '\bconfig\.toml\b',
                                '\bapps\.toml\b',
                            ],
                            lines => [
                                'For `codex-manager`, source changes for installer and runtime configuration usually touch `src/install/**`, `config/usr/apps.toml`, `config/usr/*`, `config/vendor/*`, and `config/agents/*.toml`.',
                            ],
                        },
                        {
                            patterns => [
                                '\btest\b',
                                '\btests\b',
                                '\bverify\b',
                                '\bverification\b',
                                '\bvalidate\b',
                                '\bvalidation\b',
                                '\bcheck\b',
                            ],
                            lines => [
                                'For `codex-manager` validation, run `python3 -m compileall -q src tests` and `python3 -m unittest discover -s tests`.',
                            ],
                        },
                    ],
                },
                stop => {
                    rules => [
                        {
                            id                 => 'runtime_generation_validation',
                            changed_path_globs => ['resources/**', 'src/install/**', 'tests/**', 'Makefile'],
                            require_all_patterns => ['\bpython3? -m compileall\b'],
                            message            => 'Runtime-generation changes ({changed_files_preview}) need `python3 -m compileall -q src tests`.',
                        },
                        {
                            id                 => 'runtime_generation_unit_tests',
                            changed_path_globs => ['resources/**', 'tests/**'],
                            require_any_patterns => [
                                '\bpython3? -m unittest discover -s tests\b',
                                '\bpython3? -m unittest\b',
                                'pytest[^\n]*tests/',
                            ],
                            message            => 'Runtime-generation changes ({changed_files_preview}) need targeted regression coverage from the local test suite.',
                        },
                    ],
                },
            },
            {
                id           => 'codex',
                display_name => 'codex',
                match        => {
                    repo_names   => ['codex'],
                    all_of_paths => ['codex-rs/core/src/codex.rs', 'codex-rs/Cargo.toml'],
                    any_of_paths => ['codex-rs/tui/src', 'codex-rs/tui_app_server/**'],
                },
                environment => {
                    required_commands => ['cargo', 'just'],
                    optional_commands => ['cargo-insta'],
                    optional_probes   => [
                        {
                            label   => 'cargo test -p codex-core --target x86_64-unknown-linux-gnu --no-run',
                            command => [
                                'cargo',
                                'test',
                                '-p',
                                'codex-core',
                                '--target',
                                'x86_64-unknown-linux-gnu',
                                '--no-run',
                            ],
                        },
                    ],
                },
                focus_areas => [
                    {
                        label      => 'core',
                        path_globs => ['codex-rs/core/**'],
                    },
                    {
                        label      => 'tui',
                        path_globs => ['codex-rs/tui/**', 'codex-rs/tui_app_server/**'],
                    },
                    {
                        label      => 'workspace',
                        path_globs => ['codex-rs/**'],
                    },
                ],
                session_start => {
                    startup_context => [
                        'Repo role: upstream Codex source tree and runtime-contract implementation.',
                        'High-touch areas for this repo include `codex-rs/core/**`, `codex-rs/tui/**`, `codex-rs/tui_app_server/**`, and other Rust crates under `codex-rs/**`.',
                        'For local Rust work, run `cd codex-rs && just fmt`, then use the smallest deterministic crate-scoped command with `--target x86_64-unknown-linux-gnu`.',
                    ],
                    resume_context => [
                        'Resume focus stays on the touched crates under `codex-rs/**` and the smallest deterministic crate-scoped command with `--target x86_64-unknown-linux-gnu`.',
                    ],
                },
                user_prompt_submit => {
                    rules => [
                        {
                            patterns => ['\breview\b', '\baudit\b'],
                            lines    => [
                                'For `codex` reviews, prioritize correctness, regressions, contract drift, and missing tests in the touched crates.',
                            ],
                        },
                        {
                            patterns => ['\bcore\b', '\bengine\b', '\bruntime\b', '\bprotocol\b'],
                            lines    => [
                                'For `codex` engine work, focus first on `codex-rs/core/**`, related protocol crates, and the smallest deterministic crate-scoped validation command with `--target x86_64-unknown-linux-gnu`.',
                            ],
                        },
                        {
                            patterns => ['\btui\b', '\bui\b', '\brender\b', '\bsnapshot\b'],
                            lines    => [
                                'For `codex` UI work, watch `codex-rs/tui/**`, `codex-rs/tui_app_server/**`, and snapshot coverage.',
                            ],
                        },
                        {
                            patterns => [
                                '\btest\b',
                                '\btests\b',
                                '\bverify\b',
                                '\bverification\b',
                                '\bvalidate\b',
                                '\bvalidation\b',
                                '\bcheck\b',
                            ],
                            lines => [
                                'For `codex` changes, run `cd codex-rs && just fmt`, then targeted crate commands such as `cargo check -p codex-core --target x86_64-unknown-linux-gnu`, `cargo test -p codex-core --target x86_64-unknown-linux-gnu`, or `cargo test -p codex-tui --target x86_64-unknown-linux-gnu`.',
                            ],
                        },
                    ],
                },
                stop => {
                    rules => [
                        {
                            id                 => 'rust_format',
                            changed_path_globs => ['codex-rs/**/*.rs', 'codex-rs/Cargo.toml', 'codex-rs/Cargo.lock'],
                            require_any_patterns => ['\bjust fmt\b', '\bcargo fmt\b'],
                            message            => 'Rust changes ({changed_files_preview}) need `cd codex-rs && just fmt` or `cargo fmt`.',
                        },
                        {
                            id                 => 'core_crate_validation',
                            changed_path_globs => ['codex-rs/core/**'],
                            require_any_patterns => [
                                '\bcargo test -p codex-core --target x86_64-unknown-linux-gnu\b',
                                '\bcargo check -p codex-core --target x86_64-unknown-linux-gnu\b',
                            ],
                            message            => 'Core runtime changes ({changed_files_preview}) need `cargo test -p codex-core --target x86_64-unknown-linux-gnu` or `cargo check -p codex-core --target x86_64-unknown-linux-gnu`.',
                        },
                        {
                            id                 => 'tui_crate_validation',
                            changed_path_globs => ['codex-rs/tui/**', 'codex-rs/tui_app_server/**'],
                            require_any_patterns => [
                                '\bcargo test -p codex-tui --target x86_64-unknown-linux-gnu\b',
                                '\bcargo check -p codex-tui --target x86_64-unknown-linux-gnu\b',
                            ],
                            message            => 'UI changes ({changed_files_preview}) need `cargo test -p codex-tui --target x86_64-unknown-linux-gnu` or `cargo check -p codex-tui --target x86_64-unknown-linux-gnu`.',
                        },
                        {
                            id                 => 'workspace_validation',
                            changed_path_globs => ['codex-rs/**'],
                            require_any_patterns => [
                                '\bcargo check --target x86_64-unknown-linux-gnu\b',
                                '\bcargo test --target x86_64-unknown-linux-gnu\b',
                                '\bcargo test -p codex-core --target x86_64-unknown-linux-gnu\b',
                                '\bcargo test -p codex-tui --target x86_64-unknown-linux-gnu\b',
                            ],
                            message            => 'Workspace Rust changes ({changed_files_preview}) need a deterministic target-scoped cargo validation command with `--target x86_64-unknown-linux-gnu`.',
                        },
                    ],
                },
            },
        ],
    };
}

1;
