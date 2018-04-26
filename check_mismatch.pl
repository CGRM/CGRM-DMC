#!/usr/bin/env perl
use strict;
use warnings;
use 5.010;

my $path_data="/data/Level1/CENC";
my $path_resp="/data/Level1/Response";
my @data=<$path_data/*>;
my @resp=<$path_resp/*>;
my $file_mismatch="/data/scripts/info/mismatch.txt";
open (A,'>>',$file_mismatch) or die "Could not open file '$file_mismatch' $!";
my $tp1;
my $tp2;
my $k=0;
my @data_just;

foreach $tp1 (@data){
	my (undef,undef,undef,undef,$data_ele)=split("/",$tp1);
	$data_just[$k]=$data_ele;
	$k=$k+1;
}

foreach $tp2 (@resp){
	my (undef,undef,undef,undef,$resp_just)=split("/",$tp2);
	if ( grep { $_ eq $resp_just } @data_just ){
		say "Exist!";
	}else{
		print A "$resp_just\n";
	}
}
close (A);
