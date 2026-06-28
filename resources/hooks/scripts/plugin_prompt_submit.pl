#!/usr/bin/env perl
use strict;
use warnings;

use FindBin qw($Bin);
use Cwd qw(abs_path);
use File::Spec;

BEGIN {
    my @candidates = (
        File::Spec->catdir($Bin, "..", "modules"),
        File::Spec->catdir($Bin, "lib"),
    );
    for my $candidate (@candidates) {
        my $resolved = abs_path($candidate);
        next if !defined $resolved || !-d $resolved;
        unshift @INC, $resolved;
        last;
    }
}

use JSON::PP qw(decode_json);

use Codex::Hook::Model qw(normalize_input);
use Codex::Hook::Output qw(emit_context);
use Codex::Hook::PluginHint qw(plugin_prompt_context);
use Codex::Hook::Schema qw(validate_event_input);

local $Codex::Hook::Output::CURRENT_EVENT_ARG = 'user-prompt-submit';

my $bundle = $ENV{CODEX_HOOK_PLUGIN_BUNDLE} // '';
exit 0 if !length $bundle;

local $/;
my $raw = <STDIN>;
exit 0 if !defined $raw || $raw !~ /\S/;
my $payload = decode_json($raw);
die "plugin prompt hook input must decode to an object\n" if ref($payload) ne 'HASH';

$payload = normalize_input('user-prompt-submit', $payload);
validate_event_input('user-prompt-submit', $payload, cwd => $payload->{cwd});

my $context = plugin_prompt_context(
    bundle => $bundle,
    prompt => $payload->{prompt},
);
exit 0 if !defined $context || !length $context;

emit_context('UserPromptSubmit', $context, undef);
exit 0;
