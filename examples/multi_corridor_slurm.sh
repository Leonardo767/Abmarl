#!/bin/bash

#SBATCH --job-name=test-predator-prey
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=2:00:00
#SBATCH --partition=pvis
#SBATCH --exclusive
#SBATCH --no-kill
#SBATCH --output="slurm-%j.out"

source /usr/WS1/rusu1/abmarl_scale_test/v_abmarl/bin/activate
abmarl train multi_corridor_example.py
