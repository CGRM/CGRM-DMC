#!/usr/bin/env perl
# 检测并修正已发布的`Level1资料`头文件信息
use strict;
use warnings;
use 5.010;

$ENV{SAC_DISPLAY_COPYRIGHT}=0;
# my $path_data="/data/Level1/CENC";
my $path_data="/data/scripts/testdata";
my $path_info="/data/scripts/info/station.revision.txt";
open (A,'<',$path_info) or die "Could not open file '$path_info' $!\n";

my @info=<A>;
my @events=<$path_data/*>;
my $l_info=$#info;
my $l_events=$#events;
my @net;
my @sta;
my @lat;
my @lon;
my @ele;
my @tb;
my @te;
my $ind1;
my $ind2;
my $nan='NAN';

# 从`station.revision.txt`中提取信息
foreach (0..$l_info){
	chomp($info[$_]);
	($net[$_],$sta[$_],$lat[$_],$lon[$_],$ele[$_],$tb[$_],$te[$_])=split(/\s+/,$info[$_]);
}

# 对地震事件目录的遍历
foreach (0..$l_events){
	# 读取一个事件下的所有SAC数据
	my @data=<$events[$_]/*.SAC>;
	my $l_data=$#data;

	# 对SAC数据的遍历
	open (SAC,"| sac") or die "Error opening sac\n";
	foreach $ind1 (0..$l_data){
		my (undef,undef,undef,undef,$t,$name)=split("/",$data[$ind1]);
		my $t_re=substr($t,0,8);
		my ($year,$kday,$hour,$min,$sec,undef,$sac_net,$sac_sta,undef,undef,undef,undef)=split(/\./,$name);
	
		# 对`station.revision.txt`中信息的遍历
		foreach $ind2 (0..$l_info){
			if ( $lat[$ind2] eq $nan || $lon[$ind2] eq $nan || $ele[$ind2] eq $nan ){
				next;
			}
			
			if ( $sac_net eq $net[$ind2] && $sac_sta eq $sta[$ind2] && $t_re >= $tb[$ind2] && $t_re < $te[$ind2] ){
				print SAC "wild echo off\n";
				print SAC "r $data[$ind1]\n";
				print SAC "ch STLA $lat[$ind2]\n";
				print SAC "ch STLO $lon[$ind2]\n";
				print SAC "ch STEL $ele[$ind2]\n";
				print SAC "wh\n";
			}
		}
		say "$data[$ind1] $ind1/$l_data";
	}
	print SAC "q\n";
	close(SAC);
	say "****** $_/$l_events ******";
}
close (A);
