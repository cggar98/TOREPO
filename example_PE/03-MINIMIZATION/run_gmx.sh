#!/bin/bash

WD=`pwd`

# ============== LOAD MODULES ================
#source /usr/bin/gmx

# ============== GROMACS EXACUTABLES ================
EXE1="gmx grompp"
EXE2="gmx mdrun"

# ================ INPUT FILES FOR GROMACS ==================
TOP="../02-REPLICATE/05-PE_final_residues_noH_replicate.top"
MDP="./minim.mdp"
GRO="../02-REPLICATE/05-PE_final_residues_noH_replicate.gro"

# ============================ GPU RTX3090 =============================
${EXE1} -f $MDP -p $TOP -c $GRO -o new_topol.tpr -maxwarn 10 >& out_grompp.dat
#export OMP_NUM_THREADS=28
#${EXE2} -s new_topol.tpr -noappend -v >& out_md.dat
${EXE2} -nt 8 -s new_topol.tpr -noappend -v >& out_md.dat
