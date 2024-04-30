reset
set term wxt 1 enhanced dashed size 1200,1200 font "Arial,10"
set multiplot layout 2,2
set xlabel "t (ps)"
set ylabel "C(n)"
set grid
set style fill transparent solid 0.5 noborder

set title "Cn vs t"
unset xrange
p "./Cn.dat" u 2:3 w l notitle lc "black" lw 2.0 dt 1

set xlabel "n"
set ylabel "C(n)"
set grid
set style fill transparent solid 0.5 noborder

set title "Cn vs t"
unset xrange
p "./cn_internal_distances.dat" u 1:3 w l notitle lc "blue" lw 2.0 dt 1

set xlabel "1/n"
set ylabel "C(n)"
set grid
set style fill transparent solid 0.5 noborder

set title "Asymptotic Cn vs 1/n"
linear(x) = a*x+b
set xrange[0.0001:0.10]
p "./cn_internal_distances.dat" u (1/$1):3 w p notitle lc "red" lw 2.0 dt 1


unset multiplot