#!/bin/bash

WD=`pwd`

# ============== LOAD MODULES ================
source /usr/bin/gmx

# ============== GROMACS EXACUTABLES ================
EXE1="gmx grompp"
EXE2="gmx mdrun"

# ================ INPUT FILES FOR GROMACS ==================
TOP="../02-REPLICATE/05-PE_final_residues_noH_replicate.top"
MDP="./nvt_473K_5ns.mdp"
GRO="../03-MINIMIZATION/confout.part0001_center.gro"

# ============================ GPU RTX3090 =============================
${EXE1} -f $MDP -p $TOP -c $GRO -o new_topo.tpr -maxwarn 10 >& out_grompp.dat
#export OMP_NUM_THREADS=28
${EXE2} -s new_topo.tpr -noappend -v >& out_md.dat
