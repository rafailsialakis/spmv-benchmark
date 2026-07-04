#!/usr/bin/env bash
set -euo pipefail

make run-all && make run-all-tlb && make run-all-cache && make plot
