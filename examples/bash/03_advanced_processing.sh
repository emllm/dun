#!/bin/bash
# Advanced processing with dun tool

# Set strict mode for better error handling
set -euo pipefail

# Configuration
CONFIG_FILE="${1:-.env}"
LOG_FILE="/tmp/dun_processing_$(date +%Y%m%d_%H%M%S).log"
PROCESSED_DIR="/tmp/processed_emails"

# Initialize logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Load configuration
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log "Error: Config file $CONFIG_FILE not found"
        log "Please copy .env.example to $CONFIG_FILE and update with your settings"
        exit 1
    fi
    
    # Load environment variables
    export $(grep -v '^#' "$CONFIG_FILE" | xargs)
    
    # Verify required variables
    for var in IMAP_SERVER IMAP_EMAIL IMAP_PASSWORD; do
        if [ -z "${!var:-}" ]; then
            log "Error: $var is not set in $CONFIG_FILE"
            exit 1
        fi
    done
}

# Process emails with retry logic
process_emails() {
    local max_retries=3
    local retry_count=0
    local success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        log "Processing emails (Attempt $((retry_count + 1)) of $max_retries)"
        
        if python3 -m dun.cli process \
            --folder "$1" \
            --query "$2" \
            --limit 5 \
            --output-dir "$PROCESSED_DIR" 2>> "$LOG_FILE"; then
            success=true
            log "Successfully processed emails"
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                log "Retrying in 5 seconds..."
                sleep 5
            fi
        fi
    done
    
    if [ "$success" = false ]; then
        log "Failed to process emails after $max_retries attempts"
        return 1
    fi
}

# Main execution
main() {
    log "Starting email processing"
    log "Log file: $LOG_FILE"
    
    # Load configuration
    load_config
    
    # Create output directory
    mkdir -p "$PROCESSED_DIR"
    
    # Process different email types
    declare -A email_types=(
        ["unread"]="UNSEEN"
        ["important"]="KEYWORD important"
        ["recent"]="SINCE $(date -d "-7 days" +%d-%b-%Y)"
    )
    
    for type in "${!email_types[@]}"; do
        log "Processing $type emails..."
        process_emails "INBOX" "${email_types[$type]}" || continue
        
        # Additional processing for specific types
        case $type in
            "important")
                log "Running additional processing for important emails..."
                python3 -m dun.cli analyze --folder "INBOX" --query "KEYWORD important" --limit 2
                ;;
            "unread")
                log "Marking processed unread emails as read..."
                python3 -m dun.cli mark-read --folder "INBOX" --query "UNSEEN" --limit 5
                ;;
        esac
    done
    
    # Generate summary report
    log "Generating summary report..."
    python3 -m dun.cli stats --output "$PROCESSED_DIR/summary_$(date +%Y%m%d).txt"
    
    log "Processing completed successfully"
    log "Processed files are in: $PROCESSED_DIR"
}

# Run main function
main "$@"
