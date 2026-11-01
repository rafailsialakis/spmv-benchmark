#!/usr/bin/env bash
# Benchmark campaign for the paper: records the platform, refuses to run an
# x86 campaign with turbo enabled (override with ALLOW_TURBO=1), then runs every
# matrix with SPMV_REPS repetitions (default 5) in a shuffled order.
set -euo pipefail
cd "$(dirname "$0")/.."

make all
scripts/platform_info.sh

if [ "$(uname -m)" = x86_64 ] && [ "${ALLOW_TURBO:-0}" != 1 ]; then
  nt=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo unknown)
  if [ "$nt" != 1 ]; then
    echo "Turbo is not disabled (no_turbo=$nt). Run: sudo scripts/x86_stable_freq.sh"
    exit 1
  fi
fi

export SPMV_REPS="${SPMV_REPS:-5}"
echo "Running with SPMV_REPS=$SPMV_REPS"
make run-all 2>&1 | tee -a "results/run_$(uname -m)_$(date +%Y%m%d_%H%M%S).log"
