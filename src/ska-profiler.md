#SKA Profiling Framework


This script is part of the SKA Profiler and will profile FLOPS and Watts from
Intel-based CPU's for applications run. It uses Intel Hardware counters and the
RAPL/powercapping framework.

## Prerequisites 

* Kernel version 3.15 or greater
* perf version 3.15 or greater
* Kernel configured with RAPL/powercapping framework
* modprobe msr

## Test

To Run:

perf list

Look for energy-pkg, energy-cores and energy-ram for power capturing.

## Running
export PATH=${PATH}:<path_to>/<perf_flop_per_watt.sh>

To Run:

./perf_flop_per_watt.sh <output_dir> "<my application>"

To Run with Docker:

If running with Docker you will need to setup the following first:

echo 0 > /proc/sys/kernel/perf_event_paranoid
