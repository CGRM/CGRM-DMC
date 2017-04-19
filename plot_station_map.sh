#!/bin/bash
R=70/138/13/56
J=M105/35/6.5i
PS=station-maps.ps

gmt set MAP_GRID_PEN_PRIMARY 0.25p,gray,2_2:1
gmt set FORMAT_GEO_MAP ddd:mm:ssF MAP_FRAME_WIDTH 3p
gmt set FONT_ANNOT_PRIMARY 7p
gmt set FONT_LABEL 8p,35 MAP_LABEL_OFFSET 4p
gmt set FONT_TITLE 16p

# 绘制中国地图
gmt pscoast -J$J -R$R -G244/243/239 -S167/194/223 -B10f5g10 -B+t'Stations Distribution' -Lg85/17.5+c17.5+w800k+f+u+l'比例尺' -K > $PS
gmt psxy CN-border-La.dat -J$J -R$R -W0.3p,gray50 -O -K >> $PS
gmt psxy station.info -J$J -R$R -St0.1c -Gred -i2,1 -K -O >> $PS

# 绘制南海区域
R=105/123/3/24
J=M1.1i
gmt psbasemap -J$J -R$R -B0 -X5.4i --MAP_FRAME_TYPE=plain --MAP_FRAME_PEN=1p -K -O >> $PS
gmt pscoast -J$J -R$R -N1/0.1p -W1/0.25p -G244/243/239 -S167/194/223 -K -O >> $PS
gmt psxy CN-border-La.dat -J$J -R$R -W0.25p -O -K >> $PS
echo "南海诸岛" | gmt pstext -J$J -R$R -F+f10p,35+cBC -D0c/0.1c -N -Gwhite -O >> $PS

gmt psconvert -A -P -Tg $PS

rm gmt.conf gmt.history
