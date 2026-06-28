package Codex::Hook::Learning;

use strict;
use warnings;

use Exporter qw(import);

use Codex::Hook::Runner qw(read_file_tail);

our @EXPORT_OK = qw(
  prompt_keyword_context_lines
  tool_response_summary_lines
  transcript_summary_lines
);

sub _pattern_catalog {
    return (
        {
            label => 'permission or sandbox denials',
            regex => qr/\b(?:permission denied|requires approval|sandbox|not permitted)\b/i,
        },
        {
            label => 'test failures',
            regex => qr/\b(?:FAIL|FAILED|AssertionError|panic:|test failed|Traceback)\b/i,
        },
        {
            label => 'lint or static-analysis failures',
            regex => qr/\b(?:shellcheck|ruff|mypy|eslint|clippy|taplo|yamllint)\b.*\b(?:error|warning|failed)\b/i,
        },
        {
            label => 'timeout boundaries',
            regex => qr/\b(?:timed out|timeout|deadline exceeded)\b/i,
        },
        {
            label => 'missing commands or dependencies',
            regex => qr/\b(?:command not found|not installed|no such file or directory|missing required command)\b/i,
        },
        {
            label => 'auth or network boundaries',
            regex => qr/\b(?:401|403|forbidden|unauthorized|certificate|tls|ssl|dns|network access|connection refused|name or service not known)\b/i,
        },
        {
            label => 'config or syntax failures',
            regex => qr/\b(?:TOMLDecodeError|JSONDecodeError|invalid JSON|invalid TOML|syntax error|perl -c|py_compile|compileall)\b/i,
        },
    );
}

sub _match_counts {
    my ($text) = @_;
    return () if !defined $text || !length $text;

    my @hits;
    for my $entry (_pattern_catalog()) {
        my $count = 0;
        while ($text =~ /$entry->{regex}/g) {
            $count++;
        }
        next if !$count;
        push @hits, {
            count => $count,
            label => $entry->{label},
        };
    }

    return sort {
        $b->{count} <=> $a->{count}
          || $a->{label} cmp $b->{label}
    } @hits;
}

sub _warning_lines {
    my ($text) = @_;
    return () if !defined $text || !length $text;

    my @lines;
    my %seen;
    for my $line (split /\n/, $text) {
        my $trimmed = _sanitize_warning_line($line);
        next if !length $trimmed;
        next if $seen{$trimmed}++;
        push @lines, $trimmed;
    }
    return @lines;
}

sub _sanitize_warning_line {
    my ($line) = @_;
    return '' if !defined $line;

    my $trimmed = $line;
    $trimmed =~ s/^\s+|\s+$//g;
    return '' if !length $trimmed;
    return '' if $trimmed !~ /\b(?:warn|warning|error|failed|denied|timeout)\b/i;
    return '' if $trimmed =~ /\b(?:base_instructions|skills_instructions|plugins_instructions|session_meta)\b/i;
    return '' if $trimmed =~ /<skills_instructions>|<plugins_instructions>/i;
    return '' if $trimmed =~ /### (?:Available skills|Skill roots)/i;

    return $trimmed;
}

sub transcript_summary_lines {
    my (%args) = @_;
    my $path = $args{path};
    return () if !defined $path || !length $path;

    my %tail_args = (path => $path);
    $tail_args{max_bytes} = $args{max_bytes} if exists $args{max_bytes};
    my $text = read_file_tail(%tail_args);
    return () if !length $text;

    my @lines;
    my @counts = _match_counts($text);
    if (@counts) {
        push @lines, join(
            ', ',
            map { "$_->{label} x$_->{count}" } @counts
        );
    }
    push @lines, map { "Recent warning: $_" } _warning_lines($text);
    return @lines;
}

sub tool_response_summary_lines {
    my (%args) = @_;
    my $text = $args{text} // '';
    return () if !length $text;

    my @lines;
    my @counts = _match_counts($text);
    if (@counts) {
        push @lines, join(
            ', ',
            map { "$_->{label} x$_->{count}" } @counts
        );
    }
    if ($text =~ /\b(?:FAIL|FAILED|AssertionError|panic:|test failed)\b/i) {
        push @lines, 'Tool output contains test-failure signals; keep the next step scoped to the failing test boundary.';
    }
    if ($text =~ /\b(?:shellcheck|ruff|mypy|eslint|clippy|taplo|yamllint)\b/i) {
        push @lines, 'Tool output contains lint or static-analysis signals; tighten the next step to the reported file and line before widening scope.';
    }
    push @lines, map { "Observed: $_" } _warning_lines($text);
    return @lines;
}

sub prompt_keyword_context_lines {
    my (%args) = @_;
    my $prompt = $args{prompt} // '';
    return () if !length $prompt;

    my @lines;
    if ($prompt =~ /\b(?:build-src|build-install|build from source|build-codex\.sh|config\.schema\.json|release overlay)\b/i) {
        push @lines, 'Source-build requests in this repo should follow the upstream `scripts/release/build-codex.sh` contract, then validate the patched `config.schema.json` before changing local TOML knobs.';
    }
    if ($prompt =~ /\b(?:hook|hooks|perl|transcript|memory|compact|subagent)\b/i) {
        push @lines, 'Hook work should stay schema-first: emit only fields allowed by the event output schema, and prefer transcript-driven context over generic boilerplate.';
        push @lines, 'When describing the installed runtime, use `$CODEX_HOME/hooks.json`, `$CODEX_HOME/.hooks/scripts`, and `$CODEX_HOME/.hooks/modules` instead of repository source paths.';
        push @lines, 'Include the full hook context needed to resolve the task; do not omit relevant changed-file, validation, or next-step detail just for brevity.';
    }
    if ($prompt =~ /\b(?:plugin|plugins|marketplace|skills|roles)\b/i) {
        push @lines, 'Plugin and skill work in this repo should keep runtime marketplace metadata, plugin bundle manifests, and generated `agents/openai.yaml` dependencies in sync.';
    }
    return @lines;
}

1;
