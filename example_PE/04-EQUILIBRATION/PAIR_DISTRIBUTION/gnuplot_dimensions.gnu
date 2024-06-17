reset
set term wxt 1 enhanced dashed size 1200,1200 font "Arial,10"
set multiplot layout 2,2
set xlabel "t (ps)"
set ylabel "<Rg^2> (angstroms)"
set grid
set style fill transparent solid 0.5 noborder

set title "Radius of gyration"
p "./Rg.dat" u 2:3 w l notitle lc "black" lw 2.0 dt 1,\
  1025.01 lc "black" lw 3 dt 2 notitle,\
  1025.01 with filledcurves y1=1025.01 lt 1 lc "grey" notitle, 1025.01 with filledcurves y1=1025.01 lt 1 lc "grey" notitle

set xlabel "t (ps)"
set ylabel "<Ree^2> (angstroms)"
set grid
set style fill transparent solid 0.5 noborder

set title "End-to-End distance"
p "./Ree.dat" u 2:3 w l notitle lc "blue" lw 2.0 dt 1,\
  -999999.99 lc "blue" lw 3 dt 2 notitle,\
  0.0 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle, -1999999.98 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle

set xlabel "t (ps)"
set ylabel "<Ree^2>/<Rg^2>"
set grid
set style fill transparent solid 0.5 noborder

set title "<R_{ee}^2>/<R_g^2>"
p "./Ree2Rg2.dat" u 2:3 w l notitle lc "red" lw 2.0 dt 1,\
  -999999.99 lc "red" lw 3 dt 2 notitle,\
  0.0 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle, -1999999.98 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle

set xlabel "t (ps)"
set ylabel "Cn"
set grid
set style fill transparent solid 0.5 noborder

set title "Characteristic ratio"
p "./Cn.dat" u 2:3 w l notitle lc "orange" lw 2.0 dt 1,\
  -999999.99 lc "orange" lw 3 dt 2 notitle,\
  0.0 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle, -1999999.98 with filledcurves y1=-999999.99 lt 1 lc "grey" notitle


unset multiplot