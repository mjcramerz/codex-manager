#!/usr/bin/env perl
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/lib";

$ENV{CODEX_HOOK_SUBAGENT_PROFILE} = 'analysis';

use Codex::Hook::Script qw(exec_driver);

exec_driver(
    script_dir => $Bin,
    event_arg  => 'subagent-stop',
);
