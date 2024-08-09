#!/bin/bash
#SBATCH --partition=all
#SBATCH -w aoki04
#SBATCH --exclude=""
#SBATCH --cpus-per-task=1
#SBATCH --mem=2000M
#SBATCH --job-name=TEST

WD=`pwd`

source /optnfs/home/student/cgarcia/Programs/sandboxes/sandbox_common/bin/activate

topology_cmd -i 02-aPP_initial.pdb -p pruebaaaa -r 03-aPP_initial_HEADTAIL.dat -a 04-aPP_initial_RESIDUES.dat
