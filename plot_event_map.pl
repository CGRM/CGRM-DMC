#!/usr/bin/env perl
#
# Plot events distribution based on event catalog
#
use strict;
use warnings;

@ARGV >= 1 or die "Usage: perl $0 events.csv ...\n";

my $PS = "event_map.ps";
my $J = "N120/25c";
my $R = "g";
my $Bx = "a60g60";
my $By = "a30g30";
my $B = "WSen+t'Events Distribution'";

my $scale = 0.1;
system "gmt set MAP_GRID_PEN_PRIMARY 0p,gray,-";
system "gmt set MAP_TITLE_OFFSET -5p FONT_TITLE 20p";
system "gmt set FORMAT_GEO_MAP ddd:mm:ssF";
system "gmt pscoast -J$J -R$R -Da -Glightgray -A10000 -Bx$Bx -By$By -B$B -K > $PS";
for my $catalog (@ARGV) {
    open(IN, "< $catalog") or die "Error in openning $catalog\n";
    my @events = <IN>;
    chomp(@events);
    close(IN);

    open(PSXY, "| gmt psxy -J$J -R$R -Sc -K -O -Glightred\@30 >> $PS");
    for my $event (@events) {
        my @items = split " ", $event;
        printf PSXY "%f %f %f\n", $items[2], $items[1], (int($items[4])-4)*$scale;
    }
    close(PSXY);
}

open(LEGEND, "| gmt pslegend -J$J -R$R -DjBR+w3.2c+o-6.5c/-0.5c -F -K -O >> $PS");
printf LEGEND "S 0.2c c %f lightred\@30 - 0.5c Mw: >8.0\n", (8-4)*$scale;
printf LEGEND "S 0.2c c %f lightred\@30 - 0.5c Mw: 6.0-7.0\n", (7-4)*$scale;
printf LEGEND "S 0.2c c %f lightred\@30 - 0.5c Mw: 6.0-7.0\n", (6-4)*$scale;
printf LEGEND "S 0.2c c %f lightred\@30 - 0.5c Mw: 5.0-6.0\n", (5-4)*$scale;
close(LEGEND);

system "gmt psxy -J$J -R$R -T -O >> $PS";
system "gmt psconvert -P -Tg $PS";
unlink glob "gmt.*";
