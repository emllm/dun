#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DUN_DIR="$(dirname "$SCRIPT_DIR")"

# Create output directory for logs
LOG_DIR="${SCRIPT_DIR}/dun_runs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# Count total commands (excluding empty lines and comments)
TOTAL_COMMANDS=$(grep -v '^\s*$' "${SCRIPT_DIR}/run.txt" | grep -v '^\s*#' | wc -l)
echo "Found $TOTAL_COMMANDS commands to process in run.txt"

# Run the batch processor
cd "$DUN_DIR" && \
python -m examples.batch_run "${SCRIPT_DIR}/run.txt" "$LOG_DIR"

echo -e "\nAll commands executed. Logs saved in $LOG_DIR/"
