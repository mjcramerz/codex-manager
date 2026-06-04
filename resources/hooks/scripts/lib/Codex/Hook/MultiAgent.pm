package Codex::Hook::MultiAgent;

use strict;
use warnings;

use Exporter qw(import);

our @EXPORT_OK = qw(
  multi_agent_prompt_context
  subagent_role_context
);

sub _trim {
    my ($value) = @_;
    return '' if !defined $value || ref($value);
    $value =~ s/^\s+|\s+$//g;
    return $value;
}

sub _lines {
    my ($value) = @_;
    return () if ref($value) ne 'ARRAY';
    my @lines;
    for my $line (@{$value}) {
        next if !defined $line || !length _trim($line);
        push @lines, _trim($line);
    }
    return @lines;
}

sub _role_catalog {
    my ($manifest) = @_;
    return () if ref($manifest) ne 'HASH';
    my $block = $manifest->{multi_agent};
    return () if ref($block) ne 'HASH';
    return grep { ref($_) eq 'HASH' } @{ $block->{roles} || [] };
}

sub _role_line {
    my ($roles, $agent_type) = @_;
    for my $role (@{$roles || []}) {
        my $name = _trim($role->{name});
        next if !length($name) || $name ne $agent_type;
        my $description = _trim($role->{description});
        my $use_when = _trim($role->{use_when});
        my $line = "`$name`: $description";
        $line .= " Use when: $use_when" if length $use_when;
        return $line;
    }
    return undef;
}

sub _profile_catalog {
    my ($manifest) = @_;
    return () if ref($manifest) ne 'HASH';
    my $block = $manifest->{multi_agent};
    return () if ref($block) ne 'HASH';
    return grep { ref($_) eq 'HASH' } @{ $block->{subagent_profiles} || [] };
}

sub _profile_by_id {
    my ($profiles, $profile_id) = @_;
    return undef if !length $profile_id;
    for my $profile (@{$profiles || []}) {
        my $id = _trim($profile->{id});
        return $profile if length($id) && $id eq $profile_id;
    }
    return undef;
}

sub _profile_by_agent_type {
    my ($profiles, $agent_type) = @_;
    for my $profile (@{$profiles || []}) {
        my $role_names = $profile->{role_names};
        next if ref($role_names) ne 'ARRAY';
        for my $name (@{$role_names}) {
            return $profile if _trim($name) eq $agent_type;
        }
    }
    return undef;
}

sub _match_patterns {
    my ($text, $patterns) = @_;
    return 0 if !defined $text || !length _trim($text) || ref($patterns) ne 'ARRAY';
    for my $pattern (@{$patterns}) {
        next if !defined $pattern || !length $pattern;
        return 1 if $text =~ /$pattern/i;
    }
    return 0;
}

sub multi_agent_prompt_context {
    my (%args) = @_;
    my $manifest = $args{manifest};
    my $prompt = _trim($args{prompt});
    return undef if !length $prompt;

    my $block = ref($manifest) eq 'HASH' ? $manifest->{multi_agent} : undef;
    return undef if ref($block) ne 'HASH';
    return undef if !_match_patterns($prompt, $block->{trigger_patterns});

    my @sections;
    my @shared_lines = _lines($block->{shared_lines});
    my @prompt_lines = _lines($block->{prompt_submit_lines});
    if (@shared_lines || @prompt_lines) {
        my @lines = ('Multi-agent orchestration guidance:');
        push @lines, map { "- $_" } @shared_lines;
        push @lines, map { "- $_" } @prompt_lines;
        push @sections, join("\n", @lines);
    }

    my @role_lines;
    for my $role (_role_catalog($manifest)) {
        my $name = _trim($role->{name});
        next if !length $name;
        my $description = _trim($role->{description});
        my $use_when = _trim($role->{use_when});
        my $line = "`$name`: $description";
        $line .= " Use when: $use_when" if length $use_when;
        push @role_lines, $line;
    }
    if (@role_lines) {
        push @sections, join("\n", 'Available role hints:', map { "- $_" } @role_lines);
    }

    return @sections ? join("\n\n", @sections) : undef;
}

sub subagent_role_context {
    my (%args) = @_;
    my $manifest = $args{manifest};
    my $agent_type = _trim($args{agent_type}) || 'subagent';
    my $phase = _trim($args{phase}) || 'start';
    my $profile_id = _trim($args{profile_id});

    my @profiles = _profile_catalog($manifest);
    my $profile = _profile_by_id(\@profiles, $profile_id);
    $profile = _profile_by_agent_type(\@profiles, $agent_type) if !defined $profile;

    my @lines;
    if (defined $profile) {
        my $id = _trim($profile->{id});
        push @lines, "Role profile: `$id`." if length $id;
        my $phase_key = $phase eq 'stop' ? 'stop_lines' : 'start_lines';
        push @lines, map { "- $_" } _lines($profile->{$phase_key});
    }

    my @roles = _role_catalog($manifest);
    my $role_line = _role_line(\@roles, $agent_type);
    push @lines, "- Role contract: $role_line" if defined $role_line && length $role_line;

    return @lines ? join("\n", @lines) : undef;
}

1;
