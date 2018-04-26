#!/usr/bin/env perl
# 检测并修正已发布的`Level1资料`头文件信息
use strict;
use warnings;
use 5.010;
@ARGV==1 or die "Usage: perl $0 sac\n";
$ENV{SAC_DISPLAY_COPYRIGHT}=0;
my $data=$ARGV[0];
my $path_data="/data/Level1/CENC";
# my $path_data="/data/scripts/testdata";
my $path_info="/data/scripts/info/station.revision.txt";
open (A,'<',$path_info) or die "Could not open file '$path_info' $!\n";

my @info=<A>;
my $l_info=$#info;
my @net;
my @sta;
my @lat;
my @lon;
my @ele;
my @tb;
my @te;
my $ind2;
my $nan='NAN';

# 从`station.revision.txt`中提取信息
foreach (0..$l_info){
	chomp($info[$_]);
	($net[$_],$sta[$_],$lat[$_],$lon[$_],$ele[$_],$tb[$_],$te[$_])=split(/\s+/,$info[$_]);
}

# 对SAC数据的遍历
open (SAC,"| sac") or die "Error opening sac\n";
my (undef,undef,undef,undef,$t,$name)=split("/",$data);
my $t_re=substr($t,0,8);
my ($year,$kday,$hour,$min,$sec,undef,$sac_net,$sac_sta,undef,undef,undef,undef)=split(/\./,$name);

# 对`station.revision.txt`中信息的遍历
foreach $ind2 (0..$l_info){
	if ( $lat[$ind2] eq $nan || $lon[$ind2] eq $nan || $ele[$ind2] eq $nan ){
		next;
	}
	
	if ( $sac_net eq $net[$ind2] && $sac_sta eq $sta[$ind2] && $t_re >= $tb[$ind2] && $t_re < $te[$ind2] ){
		print SAC "wild echo off\n";
		print SAC "rh $data\n";
		print SAC "ch STLA $lat[$ind2]\n";
		print SAC "ch STLO $lon[$ind2]\n";
		print SAC "ch STEL $ele[$ind2]\n";
		print SAC "wh\n";
	}
}
print SAC "q\n";
close(SAC);
close (A);
