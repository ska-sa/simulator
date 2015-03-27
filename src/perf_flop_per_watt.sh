#!/bin/bash
export LC_ALL=C
#Part of the profiling framework for the SKA Telescope project. Flops/Watt
#profiling script.

#Copyright (C) 2014 Rahim Lakhoo (a.k.a. Raz) <rahim.lakhoo@oerc.ox.ac.uk> and Chen Wu <chen.wu@uwa.edu.au>

#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along
#with this program; if not, write to the Free Software Foundation, Inc.,
#51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

#If you would like to contact us please do using the above email addresses.

#Uncomment this if manual CPU frequency and core calulations are needed.
#echo "Please enter the freqency of your CPU (GHz), i.e. 3.33"
#read cpu_freq
#echo "Please enter the number of CPU cores, i.e. 8"
#read cpu_cores
#echo ""

#setup file-based logging
log_dir=$1

cpu_freq=`lscpu|awk '/CPU MHz/ {print $3}'`
cpu_cores=`lscpu|awk '/Core\(s\) per socket/ {print $4}'`

perf stat -o $log_dir/watt_output.dat -a -e power/energy-pkg/,power/energy-cores/,power/energy-ram/ perf stat -o $log_dir/flop_output.dat -e ref-cycles,instructions,r53003c,r530110,r531010,r532010,r534010,r538010,r530111,r530211 $2

#redirect profiler output to file.
exec 1>> $log_dir/flop_watt_output.dat
exec 2>&1

#set log files
flop_out=$log_dir/flop_output.dat
watt_out=$log_dir/watt_output.dat

#calculate flops and watts
echo ""
echo "SKA Profiling Framework"
echo "======================="
echo ""

echo "FLOP per Watt"
echo "============="
echo ""
echo "Using Intel formulas and hardware counters"
echo ""

echo "System Information"
echo "=================="
echo "Detected CPU Freq $cpu_freq MHz"
echo "Detected CPU Core Count $cpu_cores"
echo ""

echo "Elapsed time calculation"
echo "========================"
unhalted_cycles=$(cat ${flop_out}| awk '/r53003c/ {print $1}'|sed 's/,//g')
cpu=$cpu_freq
elapsed_time=`echo "$unhalted_cycles / $cpu / $cpu_cores"|bc -l`
echo "UNHALTED_CPU_CYCLES Elapsed time (secs) $elapsed_time"
ref_cycles=$(cat ${flop_out} | awk '/ref-cycles/ {print $1}'|sed 's/,//g')
ref_elapsed_time=`echo "$ref_cycles / $cpu / $cpu_cores"|bc -l`
#echo "REF_CPU_CYCLES Elapsed time (secs) $ref_elapsed_time"
echo ""

echo "FLOP Calculation for x87 non-scalar"
echo "==================================="
flop_x87=`cat $log_dir/flop_output.dat | awk '/r530110/ {print $1}'|sed 's/,//g'`
mflops=`echo "$flop_x87 / (1*10^6) / $elapsed_time"|bc -l`
echo "UNHALTED_CORE_CYCLES Total is $mflops MFLOPS"
ref_mflops=`echo "$flop_x87 / (1*10^6) / $ref_elapsed_time"|bc -l`
#echo "Total based on REF_CORE_CYCLES $ref_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SSE packed double"
echo "======================================"
flop_packed_double=`cat $log_dir/flop_output.dat | awk '/r531010/ {print $1}'|sed 's/,//g'`
sse_d_mflops=`echo "($flop_packed_double *2) / (1*10^6) / $elapsed_time"|bc -l`
ref_sse_d_mflops=`echo "($flop_packed_double *2) / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $sse_d_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_sse_d_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SSE packed single"
echo "======================================"
flop_packed_single=`cat $log_dir/flop_output.dat | awk '/r534010/ {print $1}'|sed 's/,//g'`
sse_s_mflops=`echo "($flop_packed_single * 4) / (1*10^6) / $elapsed_time"|bc -l`
ref_sse_s_mflops=`echo "$flop_packed_single / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $sse_s_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_sse_s_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SSE scalar double"
echo "======================================"
flop_scalar_double=`cat $log_dir/flop_output.dat | awk '/r538010/ {print $1}'|sed 's/,//g'`
avx_d_mflops=`echo "($flop_scalar_double *2) / (1*10^6) / $elapsed_time"|bc -l`
ref_avx_d_mflops=`echo "($flop_scalar_double *2) / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $avx_d_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_avx_d_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SSE scalar single"
echo "======================================"
flop_scalar_single=`cat $log_dir/flop_output.dat | awk '/r532010/ {print $1}'|sed 's/,//g'`
avx_s_mflops=`echo "($flop_scalar_single * 4) / (1*10^6) / $elapsed_time"|bc -l`
ref_avx_s_mflops=`echo "$flop_scalar_single / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $avx_s_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_avx_s_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SIMD single"
echo "================================"
flop_simd_single=`cat $log_dir/flop_output.dat | awk '/r530111/ {print $1}'|sed 's/,//g'`
simd_s_mflops=`echo "($flop_simd_single * 8) / (1*10^6) / $elapsed_time"|bc -l`
ref_simd_s_mflops=`echo "$flop_simd_single / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $simd_s_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_avx_s_mflops MFLOPS"
echo ""

echo "FLOP Calculation for SIMD double"
echo "================================"
flop_simd_double=`cat $log_dir/flop_output.dat | awk '/r530211/ {print $1}'|sed 's/,//g'`
simd_d_mflops=`echo "($flop_simd_double * 4) / (1*10^6) / $elapsed_time"|bc -l`
ref_simd_d_mflops=`echo "$flop_simd_double / (1*10^6) / $ref_elapsed_time"|bc -l`
echo "UNHALTED_CPU_CYCLES Total is $simd_d_mflops MFLOPS"
#echo "REF_CPU_CYCLES Total is $ref_avx_s_mflops MFLOPS"
echo ""

echo "Total FLOP Calculation"
echo "======================="
total_mflops=`echo "$mflops + $sse_d_mflops + $sse_s_mflops + $avx_d_mflops + $avx_s_mflops + $simd_s_mflops + $simd_d_mflops"|bc -l`
echo "Total MFLOPS based on UNHALTED_CPU_CYCLES $total_mflops"
ref_total_mflops=`echo "$ref_mflops + $ref_sse_d_mflops + $ref_sse_s_mflops + $ref_avx_d_mflops + $ref_avx_s_mflops + $ref_simd_s_mflops + $ref_simd_d_mflops"|bc -l`
#echo "Total MFLOPS based on REF_CPU_CYCLES $ref_total_mflops"
echo ""

echo "Power Calculation (Watts)"
echo "========================="
power_pkg=`cat $log_dir/watt_output.dat | awk '/Joules power\/energy-pkg\// {print $1}'`
power_cores=`cat $log_dir/watt_output.dat | awk '/Joules power\/energy-cores\// {print $1}'`
power_ram=`cat $log_dir/watt_output.dat | awk '/Joules power\/energy-ram\// {print $1}'`
p_time=`cat $log_dir/watt_output.dat | awk '/seconds time elapsed/ {print $1}'`
total_power_pkg_watt=`echo "$power_pkg / $p_time"|bc -l`
total_power_cores_watt=`echo "$power_cores / $p_time"|bc -l`
total_power_ram_watt=`echo "$power_ram / $p_time"|bc -l`
echo "Power usage CPU(s) packages $total_power_pkg_watt Watts"
echo "Power usage CPU cores packages $total_power_cores_watt Watts"
echo "Power usage RAM $total_power_ram_watt Watts"
echo ""
total_cpu_ram_power=`echo "$total_power_pkg_watt + $total_power_ram_watt"|bc -l`
echo "Total Power usage (CPUs + RAM) $total_cpu_ram_power Watts"
echo ""

echo "Total execution time (perf)"
echo "==========================="
perf_time=`cat $log_dir/flop_output.dat | awk '/seconds time elapsed/ {print $1}'`
echo "Total execution time $perf_time secs"
echo ""

echo "MFLOPS per Watt Calculation"
echo "=========================="
flop_per_watt=`echo "$mflops / ($total_power_pkg_watt + $total_power_ram_watt)"|bc -l`
#echo "UNHALTED_CPU_CYCLES MFLOPS per Watt x87 only $flop_per_watt"
#echo ""
ref_flop_per_watt=`echo "$ref_mflops / ($total_power_pkg_watt + $total_power_ram_watt)"|bc -l`
##echo "REF_CPU_CYCLES MFLOPS per Watt x87 only $ref_flop_per_watt"
#echo ""
total_flop_per_watt=`echo "$total_mflops / ($total_power_pkg_watt + $total_power_ram_watt)"|bc -l`
echo "UNHALTED_CPU_CYCLES MFLOPS per Watt (CPU PKG + RAM) $total_flop_per_watt"
pkg_flop_per_watt=`echo "$total_mflops / ($total_power_pkg_watt)"|bc -l`
echo "UNHALTED_CPU_CYCLES MFLOPS per Watt (CPU PKG) $pkg_flop_per_watt"
cores_flop_per_watt=`echo "$total_mflops / ($total_power_cores_watt)"|bc -l`
echo "UNHALTED_CPU_CYCLES MFLOPS per Watt (CPU CORES) $cores_flop_per_watt"
ref_total_flop_per_watt=`echo "$ref_total_mflops / ($total_power_pkg_watt + $total_power_ram_watt)"|bc -l`
echo ""
#echo "REF_CPU_CYCLES MFLOPS per Watt (CPU PKG + RAM) $ref_total_flop_per_watt"
ref_pkg_flop_per_watt=`echo "$ref_total_mflops / ($total_power_pkg_watt)"|bc -l`
#echo "REF_CPU_CYCLES MFLOPS per Watt (CPU PKG) $ref_pkg_flop_per_watt"
ref_cores_flop_per_watt=`echo "$ref_total_mflops / ($total_power_cores_watt)"|bc -l`
#echo "REF_CPU_CYCLES MFLOPS per Watt (CPU CORES) $ref_cores_flop_per_watt"

echo "Cost Calculation (kWh)"
echo "======================"
echo "Based on 0.3 Euro per kWh"
kwh_cost=0.3
kwh_time=1
total_power_kwh=`echo "($total_cpu_ram_power * $kwh_time) / 1000"|bc -l`
echo "UNHALTED_CPU_CYCLES power usage (CPU PKG + RAM) $total_power_kwh kWh"
cost_per_kwh=`echo "$total_power_kwh * $kwh_cost"|bc -l`
echo "UNHALTED_CPU_CYCLES power usage (CPU PKG + RAM) $cost_per_kwh Euros for 1 hour"
echo ""
#cat $log_dir/flop_output.dat
#cat $log_dir/watt_output.dat

#echo "FLOP counters"
#echo "============="
#echo ""
#echo "r53003c = UNHALTED_CORE_CYCLES - Cycles when thread is not halted"
#echo "r530110 = FP_COMP_OPS_EXE:X87 - Computational floating-point operations executed"
#echo "r531010 = FP_COMP_OPS_EXE:SSE_FP_PACKED_DOUBLE"
#echo "r532010 - FP_COMP_OPS_EXE:SSE_FP_SCALAR_SINGLE"
#echo "r534010 - FP_COMP_OPS_EXE:SSE_PACKED_SINGLE"
#echo "r538010 - FP_COMP_OPS_EXE:SSE_SCALAR_DOUBLE"
#echo ""
#echo "MFLOPS Formula = FP_COMP_OPS_EXE.FP / 1x10^6 / Elapsed Time"
#echo "Elapsed time = UNHALTED_CORE_CYCLES / Processor-Frequency / Number-of-Cores"
#echo ""
#echo "Example: 3.33GHz CPU, 12 cores, 15.206 secs runtime"
#echo "Elapsed Time = 607,652,000,000.00 / 3.33 x 10^9 / 12 = 15.206 secs"
#echo "MFLOP = 18,470,000,000.00 / 1x10^6/ 15.206 secs = 1,214.652 MFLOPS"
#echo ""
#echo "Calulations for FLOPS from [https://software.intel.com/en-us/articles/estimating-flops-using-event-based-sampling-ebs/]"
