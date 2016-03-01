#!/bin/bash -ve

if [ -z "$1" ]; then
    DATA=/
else
    DATA=$1
fi

pyxis CFG=/input/parameters.json OUTFILE=/${DATA}/output/results OUTDIR=${DATA}/output azishe

