package Codex::Hook::Subagent;

use strict;
use warnings;

use Exporter qw(import);

our @EXPORT_OK = qw(
  start_context
  stop_system_message
);

sub start_context {
    my (%args) = @_;
    my $agent_type = $args{agent_type} // 'subagent';
    my $role_context = $args{role_context};

    my @sections = ("Subagent start for `$agent_type`:");
    push @sections, $role_context if defined $role_context && length $role_context;
    push @sections, '- Hand off commands, touched files, evidence, and residual risks explicitly.';
    return join("\n", @sections);
}

sub stop_system_message {
    return join(
        "\n",
        'Subagent stop guidance:',
        '- Summarize owned files, checks run, unresolved risks, and whether follow-up validation is still required.',
        '- If validation could not complete, state the exact blocker before the parent turn ends.',
    );
}

1;
