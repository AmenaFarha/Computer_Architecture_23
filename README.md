# Computer_Architecture_23
Title: Parallel execution of Smart Contract in Blockchain 

## Overview
This project involves a multi-faceted implementation, combining MPI-based parallel processing and a Python-based smart contract system. The primary components include:

1. **test_input module:**
   -  Generates transactions as an input for the system
     
2. **Transaction depenedency graph module:**
   -  organizes independent transactions into blocks from an imported batch from test_input module. 
   - after generating each block of independent transactions it pass through the block to the 2PQC_protocol module, which is MPI-based.
     
3. **MPI-based 2pqc_protocol Module:**
   - A module utilizing the Message Passing Interface (MPI) for parallel processing.
   - Each node of MPI-based program will have multiple threads.
   - when this module will be called from Transaction depenedency graph module it will 
     utilize multiple processors and multiple threads within each processors to 
     enhance parallelism.

2. **Python Smart Contract:**
   - A simple banking system's smart contract written in Python.
   - Includes conditions on deploying and interacting with the smart contract.

## Setup and Installation
This project relies on Python and MPI4Py for efficient parallel processing
\\
pip install mpi4py

### Running Transaction dependency graph Module which will executes all other module parallelly

python Transaction dependency graph.py

### For HPC Enviroment based on AUHPC
1. **Creating Enviroment for mpi4py:**
Conda environments:
https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
Installing mpi4py in a conda environment:
https://anaconda.org/anaconda/mpi4py

3. **Slurm file configuration:**
   #!/bin/bash
#SBATCH --job-name=my_project
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=10
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=output.txt

# Load the required modules
module load anaconda3

# Activate your Python environment
source activate myenv  # Replace with the actual name of your conda environment

# Run your main Python script
python Transaction dependency graph.py

