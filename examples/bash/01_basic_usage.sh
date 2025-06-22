#!/bin/bash
# Basic usage examples of the dun tool

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Example 1: Analyze a single email from a file
echo "=== Example 1: Analyzing email from file ==="
cat > /tmp/example_email.txt << 'EOM'
From: john.doe@example.com
To: jane.smith@example.com
Subject: Test Email
Date: Sun, 22 Jun 2025 12:00:00 +0200

Hello Jane,

This is a test email for demonstration purposes.

Best regards,
John
EOM

python3 -m dun.cli analyze --file /tmp/example_email.txt

# Example 2: Process IMAP inbox (requires IMAP settings in .env)
echo -e "\n=== Example 2: Processing IMAP inbox (first 2 emails) ==="
python3 -m dun.cli process --imap-folder INBOX --limit 2

# Example 3: Search for emails with specific criteria
echo -e "\n=== Example 3: Searching emails from today ==="
python3 -m dun.cli search --query "SINCE $(date +%d-%b-%Y)" --limit 1

# Cleanup
rm -f /tmp/example_email.txt
