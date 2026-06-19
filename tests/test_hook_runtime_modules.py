import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_LIB = REPO_ROOT / "resources" / "hooks" / "scripts" / "lib"
INSTALL_SRC = REPO_ROOT / "src" / "install"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))

from hook_runtime_catalog import load_hook_catalog  # noqa: E402


def run_perl(code: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["perl", f"-I{HOOK_LIB}", "-MJSON::PP", "-e", code, *args],
        text=True,
        capture_output=True,
        check=True,
        env=merged_env,
    )


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "checkout", "-qb", "mcr/main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=path, check=True)


class HookRuntimeModulesTests(unittest.TestCase):
    def test_perl_catalog_matches_manifest_metadata(self) -> None:
        code = r'''
use Codex::Hook::Catalog qw(hook_catalog);
print JSON::PP::encode_json(hook_catalog());
'''
        proc = run_perl(code)
        perl_catalog = json.loads(proc.stdout)
        manifest_catalog = load_hook_catalog()
        expected_catalog = {
            "version": manifest_catalog["version"],
            "tool_profiles": manifest_catalog["tool_profiles"],
            "roles": manifest_catalog["roles"],
            "subagent_profiles": manifest_catalog["subagent_profiles"],
        }
        self.assertEqual(perl_catalog, expected_catalog)

    def test_tool_profile_uses_shared_catalog_for_matchers_and_labels(self) -> None:
        code = r'''
use Codex::Hook::ToolProfile qw(tool_group_label tool_group_name);
print JSON::PP::encode_json({
  shell_group => tool_group_name('exec_command'),
  shell_label => tool_group_label('exec_command'),
  openai_group => tool_group_name('mcp__openaiDeveloperDocs__search_openai_docs'),
  openai_label => tool_group_label('mcp__openaiDeveloperDocs__search_openai_docs'),
  time_group => tool_group_name('mcp__time__get_current_time'),
  time_label => tool_group_label('mcp__time__get_current_time'),
  git_group => tool_group_name('mcp__git__git_status'),
  git_label => tool_group_label('mcp__git__git_status'),
  memory_group => tool_group_name('mcp__memory__read_graph'),
  memory_label => tool_group_label('mcp__memory__read_graph'),
  markdown_group => tool_group_name('mcp__markdown__convert'),
  markdown_label => tool_group_label('mcp__markdown__convert'),
  playwright_group => tool_group_name('mcp__playwright__browser_navigate'),
  playwright_label => tool_group_label('mcp__playwright__browser_navigate'),
  chrome_group => tool_group_name('mcp__chrome_devtools__navigate_page'),
  chrome_label => tool_group_label('mcp__chrome_devtools__navigate_page'),
  postgres_group => tool_group_name('mcp__postgres__query'),
  postgres_label => tool_group_label('mcp__postgres__query'),
  sqlite_group => tool_group_name('mcp__sqlite__read_query'),
  sqlite_label => tool_group_label('mcp__sqlite__read_query'),
  semgrep_group => tool_group_name('mcp__semgrep__scan'),
  semgrep_label => tool_group_label('mcp__semgrep__scan'),
  generic_mcp_group => tool_group_name('mcp__github_router__git_status'),
  generic_mcp_label => tool_group_label('mcp__github_router__git_status'),
  generic_group => tool_group_name('write_stdin'),
  generic_label => tool_group_label('write_stdin'),
});
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["shell_group"], "shell")
        self.assertEqual(payload["shell_label"], "shell command")
        self.assertEqual(payload["openai_group"], "mcp_openai_developer_docs")
        self.assertEqual(payload["openai_label"], "OpenAI developer docs MCP call")
        self.assertEqual(payload["time_group"], "mcp_time")
        self.assertEqual(payload["time_label"], "time MCP call")
        self.assertEqual(payload["git_group"], "mcp_git")
        self.assertEqual(payload["git_label"], "git MCP call")
        self.assertEqual(payload["memory_group"], "mcp_memory")
        self.assertEqual(payload["memory_label"], "memory MCP call")
        self.assertEqual(payload["markdown_group"], "mcp_markdown")
        self.assertEqual(payload["markdown_label"], "markdown MCP call")
        self.assertEqual(payload["playwright_group"], "mcp_playwright")
        self.assertEqual(payload["playwright_label"], "Playwright MCP call")
        self.assertEqual(payload["chrome_group"], "mcp_chrome_devtools")
        self.assertEqual(payload["chrome_label"], "Chrome DevTools MCP call")
        self.assertEqual(payload["postgres_group"], "mcp_postgres")
        self.assertEqual(payload["postgres_label"], "Postgres MCP call")
        self.assertEqual(payload["sqlite_group"], "mcp_sqlite")
        self.assertEqual(payload["sqlite_label"], "SQLite MCP call")
        self.assertEqual(payload["semgrep_group"], "mcp_semgrep")
        self.assertEqual(payload["semgrep_label"], "Semgrep MCP call")
        self.assertEqual(payload["generic_mcp_group"], "mcp")
        self.assertEqual(payload["generic_mcp_label"], "MCP tool call")
        self.assertEqual(payload["generic_group"], "generic")
        self.assertEqual(payload["generic_label"], "tool call")

    def test_script_dispatch_resolves_wrapper_name_to_event_and_profile(self) -> None:
        code = r'''
use Codex::Hook::Script qw(resolve_wrapper_dispatch);
print JSON::PP::encode_json({
  subagent => resolve_wrapper_dispatch(wrapper_name => 'subagent_stop_validation.pl'),
  mcp => resolve_wrapper_dispatch(wrapper_name => 'pre_tool_use_mcp_cloudflare_api.pl'),
  singleton => resolve_wrapper_dispatch(wrapper_name => 'stop.pl'),
});
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["subagent"]["event_arg"], "subagent-stop")
        self.assertEqual(payload["subagent"]["subagent_profile"], "validation")
        self.assertEqual(payload["mcp"]["event_arg"], "pre-tool-use")
        self.assertEqual(payload["mcp"]["profile_name"], "mcp_cloudflare_api")
        self.assertEqual(payload["singleton"]["event_arg"], "stop")

    def test_driver_glob_matching_keeps_single_star_within_one_path_segment(self) -> None:
        code = r'''
use Codex::Hook::Driver ();
print JSON::PP::encode_json({
  single => Codex::Hook::Driver::_matches_any_glob('resources/hooks/file.pl', ['resources/*']) ? JSON::PP::true() : JSON::PP::false(),
  double => Codex::Hook::Driver::_matches_any_glob('resources/hooks/file.pl', ['resources/**']) ? JSON::PP::true() : JSON::PP::false(),
});
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["single"])
        self.assertTrue(payload["double"])

    def test_runner_captures_stdout_stderr_and_exit_code(self) -> None:
        code = r'''
use Codex::Hook::Runner qw(run_command);
my $result = run_command(
  command => ['perl', '-e', 'print qq(stdout); print STDERR qq(stderr); exit 3'],
  timeout => 5,
);
print JSON::PP::encode_json($result);
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["rc"], 3)
        self.assertEqual(payload["stdout"], "stdout")
        self.assertEqual(payload["stderr"], "stderr")

    def test_runner_times_out_without_hanging_on_stderr_output(self) -> None:
        code = r'''
use Codex::Hook::Runner qw(run_command);
my $result = run_command(
  command => ['perl', '-e', 'print STDERR q(x) x 131072; select undef, undef, undef, 2;'],
  timeout => 1,
);
print JSON::PP::encode_json($result);
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["rc"], 124)
        self.assertEqual(payload["stderr"], "command timed out")

    def test_repo_reuses_cached_git_calls_within_one_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir()
            init_git_repo(repo)
            (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "github/mcr/main"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text("base\nchange\n", encoding="utf-8")
            (repo / "new.txt").write_text("new\n", encoding="utf-8")

            real_git = shutil.which("git")
            self.assertIsNotNone(real_git)
            wrapper_dir = Path(tmpdir) / "bin"
            wrapper_dir.mkdir()
            log_path = Path(tmpdir) / "git.log"
            (wrapper_dir / "git").write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' \"$*\" >> \"{log_path}\"\n"
                f"exec \"{real_git}\" \"$@\"\n",
                encoding="utf-8",
            )
            (wrapper_dir / "git").chmod(0o755)

            code = r'''
use Codex::Hook::Repo qw(
  git_root
  current_branch
  list_changed_files
  summarize_worktree
  list_mirror_refs
  preferred_mirror_main_branch
);
my $cwd = $ARGV[0];
my $root = git_root($cwd);
my $branch = current_branch($root);
my @changed_one = list_changed_files($root);
my $summary = summarize_worktree($root);
my @changed_two = list_changed_files($root);
my @refs_one = list_mirror_refs($root);
my $preferred = preferred_mirror_main_branch($root);
my @refs_two = list_mirror_refs($root);
print JSON::PP::encode_json({
  root => $root,
  branch => $branch,
  changed_one => \@changed_one,
  changed_two => \@changed_two,
  summary => $summary,
  refs_one => \@refs_one,
  refs_two => \@refs_two,
  preferred => $preferred,
});
'''
            proc = run_perl(
                code,
                str(repo),
                env={"PATH": f"{wrapper_dir}:{os.environ['PATH']}"},
            )
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["branch"], "mcr/main")
            self.assertEqual(payload["preferred"], "github/mcr/main")
            self.assertEqual(sorted(payload["changed_one"]), sorted(payload["changed_two"]))
            self.assertIn("tracked.txt", payload["changed_one"])
            self.assertIn("new.txt", payload["changed_one"])
            self.assertEqual(payload["summary"]["unstaged"], 1)
            self.assertEqual(payload["summary"]["untracked"], 1)

            logged = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(logged), 3, logged)

    def test_output_rejects_empty_block_reason(self) -> None:
        proc = subprocess.run(
            [
                "perl",
                f"-I{HOOK_LIB}",
                "-MCodex::Hook::Output=emit_block",
                "-e",
                'eval { emit_block(q{}) }; if ($@) { print $@; exit 0 } exit 1;',
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("block reason must not be empty", proc.stdout)


if __name__ == "__main__":
    unittest.main()
