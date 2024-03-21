reset
set term wxt 1 enhanced dashed size 1200,1200 font "Arial,10"
set multiplot layout 2,2
set xlabel "Ree (angstroms)"
set ylabel "P(Ree) (angstroms)^-1"
set grid
set style fill transparent solid 0.5 noborder

set title "End-to-End distance distribution"
gauss(x) = (4*pi*(x**2)*(3./(2.*pi*-999999.99))**(3./2.))*exp(-3.*x**2./(2.*-999999.99))
p "./Ree_distribution.dat" u 1:2 w p notitle lc "black" lw 2.0 dt 1, gauss(x) w l lw 4

set xlabel "Rg (angstroms)"
set ylabel "P(Rg) (angstroms)^-1"
set grid
set style fill transparent solid 0.5 noborder

set title "Radius of gyration distribution"
p "./Rg_distribution.dat" u 1:2 w p notitle lc "blue" lw 2.0 dt 1,\

set xlabel "Ree^2/Rg^2"
set ylabel "P(Ree^2/Rg^2) "
set grid
set style fill transparent solid 0.5 noborder

set title "<R_{ee}^2>/<R_g^2> distribution"
p "./Ree2Rg2_distribution.dat" u 1:2 w p notitle lc "red" lw 2.0 dt 1,\


unset multiplot