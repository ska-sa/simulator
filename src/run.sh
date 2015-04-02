#!/bin/bash -ve

if [ -z "$1" ]; then
    DATA=/
else
    DATA=$1
fi

if [ -z "$USER" ]; then
  export USER=root
fi

echo "where are we now"
pwd

pyxis CFG=${DATA}/input/parameters.json OUTFILE=/${DATA}/output/results OUTDIR=${DATA}/output azishe

