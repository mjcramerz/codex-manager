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
  mcp_group => tool_group_name('mcp__openaiDeveloperDocs__search_openai_docs'),
  mcp_label => tool_group_label('mcp__openaiDeveloperDocs__search_openai_docs'),
});
'''
        proc = run_perl(code)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["shell_group"], "shell")
        self.assertEqual(payload["shell_label"], "shell command")
        self.assertEqual(payload["mcp_group"], "mcp")
        self.assertEqual(payload["mcp_label"], "MCP tool call")

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
