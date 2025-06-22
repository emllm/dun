#!/bin/bash

# Check if run.txt exists
if [ ! -f "run.txt" ]; then
    echo "Error: run.txt not found"
    exit 1
fi

# Create output directory for logs
LOG_DIR="dun_runs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# Counter for commands
COUNT=1
TOTAL=$(wc -l < run.txt)

# Read and execute each command
while IFS= read -r command; do
    # Skip empty lines
    [ -z "$command" ] && continue
    
    echo "[$COUNT/$TOTAL] Executing: $command"
    
    # Execute command and log output
    dun "$command" 2>&1 | tee "$LOG_DIR/command_${COUNT}.log"
    
    # Add separator
    echo -e "\n---\n"
    
    # Increment counter
    ((COUNT++))
    
    # Small delay between commands
    sleep 1
    
done < run.txt

echo "All commands executed. Logs saved in $LOG_DIR/"
