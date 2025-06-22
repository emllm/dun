#!/bin/bash

# Check if run.txt exists
if [ ! -f "run.txt" ]; then
    echo "Error: run.txt not found in the current directory"
    exit 1
fi

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DUN_DIR="$(dirname "$SCRIPT_DIR")"

# Create output directory for logs
LOG_DIR="${SCRIPT_DIR}/dun_runs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# Counter for commands
COUNT=1
TOTAL=$(grep -v '^\s*$' "${SCRIPT_DIR}/run.txt" | wc -l)  # Count non-empty lines

# Create a temporary Python script that will process all commands
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOL'
import sys
from dun.processor_engine import ProcessorEngine
from dun.llm_analyzer import LLMAnalyzer

def main():
    llm_analyzer = LLMAnalyzer()
    engine = ProcessorEngine(llm_analyzer)
    
    # Read commands from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        try:
            print(f"Processing: {line}")
            result = engine.process_natural_request(line)
            print(f"Result: {result if result is not None else 'No output'}")
            print("---")
        except Exception as e:
            print(f"Error processing command '{line}': {str(e)}", file=sys.stderr)
            print("---")

if __name__ == "__main__":
    main()
EOL

# Process all commands in a single Python process
(cd "$DUN_DIR" && \
 cat "${SCRIPT_DIR}/run.txt" | \
 grep -v '^\s*$' | \
 grep -v '^\s*#' | \
 while IFS= read -r line; do
    echo "[$COUNT/$TOTAL] $line"
    echo "$line" | poetry run python "$TEMP_SCRIPT" 2>&1 | tee "$LOG_DIR/command_${COUNT}.log"
    ((COUNT++))
    sleep 0.5
done)

# Clean up
rm -f "$TEMP_SCRIPT"

echo "All commands executed. Logs saved in $LOG_DIR/"
