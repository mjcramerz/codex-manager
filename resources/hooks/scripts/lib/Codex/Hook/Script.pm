package Codex::Hook::Script;

use strict;
use warnings;

use Cwd qw(abs_path);
use Exporter qw(import);
use File::Spec;

our @EXPORT_OK = qw(exec_driver seed_runtime_schema_env);

sub seed_runtime_schema_env {
    my (%args) = @_;
    return if defined $ENV{CODEX_HOOK_SCHEMA_DIR} && length $ENV{CODEX_HOOK_SCHEMA_DIR};

    my $script_dir = $args{script_dir};
    return if !defined $script_dir || !length $script_dir;

    my @candidates = (
        File::Spec->catdir($script_dir, 'schema', 'generated'),
        File::Spec->catdir($script_dir, '..', 'schema', 'generated'),
        File::Spec->catdir($script_dir, '..', '..', '.hooks', 'schema', 'generated'),
        File::Spec->catdir($script_dir, '..', '..', '.codex', 'hooks', 'schema', 'generated'),
    );

    for my $candidate (@candidates) {
        my $resolved = abs_path($candidate);
        next if !defined $resolved || !-d $resolved;
        $ENV{CODEX_HOOK_SCHEMA_DIR} = $resolved;
        last;
    }
}

sub exec_driver {
    my (%args) = @_;
    my $script_dir = $args{script_dir};
    my $event_arg = $args{event_arg};
    my $profile_name = $args{profile_name};
    die "script_dir is required\n" if !defined $script_dir || !length $script_dir;
    die "event_arg is required\n" if !defined $event_arg || !length $event_arg;

    seed_runtime_schema_env(script_dir => $script_dir);
    if (defined $profile_name && length $profile_name) {
        $ENV{CODEX_HOOK_TOOL_PROFILE} = $profile_name;
    } else {
        delete $ENV{CODEX_HOOK_TOOL_PROFILE};
    }
    my $driver_path = File::Spec->catfile($script_dir, 'hook_driver.pl');
    exec { $^X } $^X, $driver_path, $event_arg;
    die "failed to exec hook driver $driver_path: $!\n";
}

1;
