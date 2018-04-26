#!/usr/bin/env perl
use strict;
use warnings;
use 5.010;

my $file="/data/scripts/info/CENC.info";
# my $file="/data/scripts/testdata/path.info";
open (A,'<',$file) or die "Could not open '$file' $!";
my @info=<A>;
my $tp1;

foreach $tp1 (@info){
	chomp($tp1);
	system "perl check_header2.pl $tp1";
	say "$tp1";
}
