#!/usr/bin/env perl
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/lib";

use Codex::Hook::Script qw(exec_driver);

exec_driver(
    script_dir => $Bin,
    event_arg  => 'pre-tool-use',
);
