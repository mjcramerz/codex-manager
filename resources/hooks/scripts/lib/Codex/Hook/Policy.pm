package Codex::Hook::Policy;

use strict;
use warnings;

use Exporter qw(import);

our @EXPORT_OK = qw(
  compact_system_message
  destructive_command_reason
  permission_request_message
  pre_tool_policy_lines
  subagent_stop_system_message
);

sub destructive_command_reason {
    my (%args) = @_;
    my $tool_name = $args{tool_name} // '';
    my $tool_input = $args{tool_input};
    return undef if $tool_name !~ /(?:\Aexec_command\z|\Aapply_patch\z|\b(?:shell|bash|write)\b)/i;
    return undef if ref($tool_input);
    return undef if !defined $tool_input || !length $tool_input;

    return 'PreToolUse rejected a destructive `git reset --hard` path. Use a non-destructive alternative unless the user explicitly requested that exact operation.'
      if $tool_input =~ /\bgit\s+reset\s+--hard\b/i;
    return 'PreToolUse rejected a destructive `git checkout --` path. Preserve user changes unless they explicitly asked to discard them.'
      if $tool_input =~ /\bgit\s+checkout\s+--\b/i;
    return 'PreToolUse rejected an unsafe root-targeted remove path.'
      if $tool_input =~ /\brm\s+-rf\s+--?\s*\/(?:\s|\z)/i;
    return undef;
}

sub pre_tool_policy_lines {
    my (%args) = @_;
    my $repo_has_patch_release = $args{repo_has_patch_release};
    my $tool_name = $args{tool_name} // 'tool';

    my @lines = ("Pre-tool guardrails for `$tool_name`:");
    push @lines, '- Prefer deterministic commands, bounded I/O, and the smallest reviewable mutation.';
    push @lines, '- Avoid destructive git history rewrites or broad filesystem deletes unless the user explicitly requested them.'
      if $tool_name =~ /(?:\Aexec_command\z|\Aapply_patch\z|\b(?:exec|shell|bash|write)\b)/i;
    push @lines, '- Patch-release repo detected; keep local patch operations check-only with `git apply --check` until the patch contract is satisfied.'
      if $repo_has_patch_release;
    return @lines;
}

sub permission_request_message {
    my (%args) = @_;
    my $tool_name = $args{tool_name} // 'tool';
    return join(
        "\n",
        "Permission request for `$tool_name`:",
        '- Keep the scope minimal and name the exact files, paths, or network boundary being requested.',
        '- The justification should connect directly to the current task and avoid broad future-looking access asks.',
    );
}

sub compact_system_message {
    my ($phase) = @_;
    return join(
        "\n",
        "$phase compact guidance:",
        '- Preserve repo identity, current branch, changed files, pending validation work, and explicit user constraints.',
        '- Preserve hook-derived context around source builds, release patches, memory cues, and subagent ownership boundaries.',
    );
}

sub subagent_stop_system_message {
    return join(
        "\n",
        'Subagent stop guidance:',
        '- Summarize owned files, checks run, unresolved risks, and whether follow-up validation is still required.',
        '- If validation could not complete, state the exact blocker before the parent turn ends.',
    );
}

1;
