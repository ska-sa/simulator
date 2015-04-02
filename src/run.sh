#!/bin/bash -ve

if [ -z "$1" ]; then
    DATA=/
else
    DATA=$1
fi

export PATH=/code/depends/PyMORESANE/bin:$PATH
export PATH=/code/depends/simms/bin:$PATH
export PYTHONPATH=/code/depends/simms:$PYTHONPATH

if [ -z "$USER" ]; then
  export USER=root
fi

echo "where are we now"
pwd

pyxis CFG=${DATA}/input/parameters.json OUTFILE=/${DATA}/output/results OUTDIR=${DATA}/output azishe

