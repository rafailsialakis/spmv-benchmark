#!/usr/bin/env bash
# Records the software/hardware configuration of the current machine next to
# its results (results/<platform>_results/platform.txt). The file contains no
# hostname or user name, but check it before sharing it in an anonymous artifact.
set -uo pipefail

case "$(uname -m)" in
  x86_64)  out=results/x86_results/platform.txt ;;
  aarch64) out=results/arm_results/platform.txt ;;
  *) echo "Unsupported platform $(uname -m)"; exit 1 ;;
esac
mkdir -p "$(dirname "$out")"

section() { printf '\n## %s\n' "$1"; }
{
  echo "# Platform info, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  section "kernel / OS";   uname -srm; grep PRETTY_NAME /etc/os-release 2>/dev/null
  section "compiler";      gcc --version | head -1
  section "lscpu";         lscpu
  section "memory";        free -g
  section "NUMA";          (command -v numactl >/dev/null && numactl -H) || echo "numactl not installed"
  section "page size";     getconf PAGESIZE
  section "transparent huge pages"
  for f in enabled defrag; do
    printf '%s: ' "$f"; cat /sys/kernel/mm/transparent_hugepage/$f 2>/dev/null || echo n/a
  done
  section "frequency scaling"
  printf 'governors: '; cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | sort | uniq -c | tr '\n' ' ' || true; echo
  printf 'intel_pstate no_turbo: '; cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo n/a
  printf 'cpufreq boost: ';         cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null || echo n/a
  printf 'cur freq (kHz): ';        cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ' ' || true; echo
  section "power supply (laptops)"
  cat /sys/class/power_supply/A*/online 2>/dev/null | sed 's/^/AC online: /' || echo n/a
  section "OpenMP environment"; env | grep '^OMP_' || echo "(none set; the Makefile exports OMP_PLACES/OMP_PROC_BIND)"
  section "libraries"
  (command -v dpkg >/dev/null && dpkg -l 2>/dev/null | awk '/scotch|cxsparse|papi|libgomp/ {print $2, $3}') ||
  (command -v rpm  >/dev/null && rpm -qa | grep -Ei 'scotch|suitesparse|papi|libgomp') || echo n/a
  section "cloud instance (AWS IMDSv2, empty elsewhere)"
  tok=$(curl -s -m 1 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null)
  if [ -n "$tok" ]; then
    curl -s -m 1 -H "X-aws-ec2-metadata-token: $tok" http://169.254.169.254/latest/meta-data/instance-type; echo
  else
    echo "not on EC2 (or IMDS unreachable)"
  fi
} > "$out" 2>&1
echo "Wrote $out"
