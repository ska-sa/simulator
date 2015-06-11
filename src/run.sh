#!/bin/bash -ve

if [ -z "$1" ]; then
    DATA=/
else
    DATA=$1
fi

if [ -z "$USER" ]; then
  export USER=root
fi

echo "The config file is"
echo ${config}

pyxis CFG=/input/${config} OUTFILE=/${DATA}/output/results OUTDIR=${DATA}/output azishe

