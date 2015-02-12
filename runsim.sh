#!/bin/bash
export PATH=/code/PyMORESANE/bin:$PATH
if [ -z "$USER"]; then
  export USER=root
fi
pyxis CFG=/sims.cfg OUTFILE=/results/results OUTDIR=/results azishe
