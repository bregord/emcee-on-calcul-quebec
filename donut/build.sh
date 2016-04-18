#!/bin/bash
#PBS -l nodes=1:ppn=4
#PBS -l walltime=00:10:00
#PBS -A ejf-610-aa
#PBS -V
#PBS -N JobTest
#PBS -q debug

#PBS -m bae
 
# Defining an email address. If you want to send emails to a specific
# email address, specify it with the following option

#PBS -M brendan.gordon@mail.mcgill.ca
 
cd ~/workspace/

#add instad of load
module load ifort_icc/15.0 
module load openmpi/1.8.3-intel
module load gcc/4.8.2
module load MKL/11.1.4
module load python/2.7.3-MKL
module load python/3.3.2
#virtualenv testPip 

source env2/bin/activate
#source env/bin/activate
#source ./testPip/bin/activate

#pip install --upgrade pip

#pip install emcee
#pip install numpy
#pip install mpi4py
#pip install scipy
#pip install corner


#mpiexec python ~/ToyAxdBlissMPNoPlot.py > output.txt

mpiexec  python ~/workspace/detectorModel.py > output.txt


#env
### You can use the following syntax for your application
#./your_app arg1 arg2 arg3 ... > output.txt
