#!/usr/bin/env bash
# Pins the x86 laptop to a stable clock for benchmarking: performance governor,
# turbo off. Run with sudo before `scripts/run_paper.sh`; `--restore` undoes it.
# Also: keep the laptop on AC power, close other programs (ideally run from a
# text console), and let it cool down before starting.
set -euo pipefail
[ "$(uname -m)" = x86_64 ] || { echo "x86 only"; exit 1; }
[ "$(id -u)" -eq 0 ] || { echo "run with sudo"; exit 1; }

gov=performance; turbo_off=1
if [ "${1:-}" = "--restore" ]; then gov=powersave; turbo_off=0; fi

for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo "$gov" > "$g"; done
if [ -w /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
  echo "$turbo_off" > /sys/devices/system/cpu/intel_pstate/no_turbo
elif [ -w /sys/devices/system/cpu/cpufreq/boost ]; then
  echo $((1 - turbo_off)) > /sys/devices/system/cpu/cpufreq/boost
else
  echo "WARNING: no turbo control found (intel_pstate/no_turbo or cpufreq/boost)"
fi
echo "governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "no_turbo: $(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo n/a)"
