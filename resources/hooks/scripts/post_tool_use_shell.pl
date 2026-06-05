#!/usr/bin/env perl
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/lib";

use Codex::Hook::Script qw(dispatch_named_wrapper);

dispatch_named_wrapper(
    script_dir    => $Bin,
    wrapper_name  => $0,
);
