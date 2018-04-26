#!/usr/bin/env perl
use strict;
use warnings;
use 5.010;

my $file="CENC.info";
open (A,'>>',$file) or die "Could not open file '$file' $!";
my @events=</data/Level1/CENC/201*>;
my $tp1;
my $tp2;

foreach $tp1 (@events){
	my @data=<$tp1/*.SAC>;
	foreach $tp2 (@data){
		print A "$tp2\n";
	}
}
close (A);
