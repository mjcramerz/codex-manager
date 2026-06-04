package Codex::Hook::ToolProfile;

use strict;
use warnings;

use Exporter qw(import);

our @EXPORT_OK = qw(
  tool_group_label
  tool_group_name
);

sub _trim {
    my ($value) = @_;
    return '' if !defined $value || ref($value);
    $value =~ s/^\s+|\s+$//g;
    return $value;
}

sub tool_group_name {
    my ($tool_name) = @_;
    my $profile = _trim($ENV{CODEX_HOOK_TOOL_PROFILE});
    return $profile if $profile =~ /\A(?:shell|edit|mcp)\z/;

    my $name = _trim($tool_name);
    return 'shell' if $name =~ /\A(?:Bash|exec_command|shell)\z/i;
    return 'edit'  if $name =~ /\A(?:apply_patch|Edit|Write)\z/i;
    return 'mcp'   if $name =~ /\Amcp__/;
    return 'generic';
}

sub tool_group_label {
    my ($tool_name) = @_;
    my $group = tool_group_name($tool_name);
    return 'shell command' if $group eq 'shell';
    return 'edit operation' if $group eq 'edit';
    return 'MCP tool call' if $group eq 'mcp';
    return 'tool call';
}

1;
