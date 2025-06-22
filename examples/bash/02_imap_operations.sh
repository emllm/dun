#!/bin/bash
# IMAP Operations with dun tool

# Load environment variables
source .env 2>/dev/null || {
    echo "Error: .env file not found. Please create it from .env.example"
    exit 1
}

# Check if required variables are set
for var in IMAP_SERVER IMAP_EMAIL IMAP_PASSWORD; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env"
        exit 1
    fi
done

# Function to display section headers
section() {
    echo -e "\n=== $1 ==="
    echo "$2"
    echo ""
}

# 1. List all IMAP folders
section "1. Listing IMAP folders" "Shows all available folders in your IMAP account"
python3 -m dun.cli list-folders

# 2. Count emails in different folders
section "2. Email counts" "Shows email count in different folders"
for folder in INBOX Sent Drafts; do
    count=$(python3 -m dun.cli count --folder "$folder" 2>/dev/null || echo "Error accessing $folder")
    echo "$folder: $count emails"
done

# 3. Process and categorize emails
section "3. Categorize unread emails" "Moves unread emails to appropriate folders based on content"
python3 -m dun.cli process --query "UNSEEN" --action categorize --limit 3

# 4. Export recent emails to JSON
section "4. Export recent emails to JSON" "Saves email metadata to a JSON file"
OUTPUT_FILE="/tmp/recent_emails_$(date +%Y%m%d_%H%M%S).json"
python3 -m dun.cli export --format json --limit 2 --output "$OUTPUT_FILE"
echo "Exported to: $OUTPUT_FILE"

# 5. Search for specific emails
section "5. Search for important emails" "Finds emails marked as important"
python3 -m dun.cli search --query "KEYWORD important" --limit 2

# 6. Process attachments
section "6. Process email attachments" "Downloads and processes attachments from recent emails"
ATTACH_DIR="/tmp/attachments_$(date +%s)"
mkdir -p "$ATTACH_DIR"
python3 -m dun.cli process-attachments --output-dir "$ATTACH_DIR" --limit 1
echo "Attachments saved to: $ATTACH_DIR"

echo -e "\n=== IMAP Operations Completed ==="
