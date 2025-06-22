# Bash Script Examples for Dun

This directory contains bash scripts that demonstrate various ways to use the Dun email processing tool from the command line.

## Prerequisites

1. Bash 4.0 or higher
2. Python 3.10+ with Dun installed
3. `.env` file with proper IMAP configuration
4. Ollama server running (for LLM features)

## Scripts Overview

### 1. Basic Usage
`01_basic_usage.sh`
- Demonstrates simple operations:
  - Analyzing an email from a file
  - Processing IMAP inbox
  - Searching emails with criteria

### 2. IMAP Operations
`02_imap_operations.sh`
- Shows various IMAP operations:
  - Listing IMAP folders
  - Counting emails in folders
  - Categorizing unread emails
  - Exporting emails to JSON
  - Processing attachments

### 3. Advanced Processing
`03_advanced_processing.sh`
- Implements advanced features:
  - Error handling with retries
  - Logging to file
  - Processing different email types
  - Generating summary reports

## How to Run

1. Make the scripts executable:
   ```bash
   chmod +x *.sh
   ```

2. Run a script:
   ```bash
   ./01_basic_usage.sh
   ```

3. For the advanced script, you can specify a custom config file:
   ```bash
   ./03_advanced_processing.sh /path/to/your/config.env
   ```

## Environment Variables

Create a `.env` file in the examples directory with these variables:

```ini
# IMAP Configuration
IMAP_SERVER=your_imap_server
IMAP_PORT=993
IMAP_EMAIL=your_email@example.com
IMAP_PASSWORD=your_app_password
IMAP_FOLDER=INBOX

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

## Logging

- Scripts output to both console and log files
- Log files are stored in `/tmp/dun_processing_*.log`
- Processed emails are saved in `/tmp/processed_emails` by default

## Error Handling

- Scripts include basic error handling
- The advanced script implements retry logic for failed operations
- Check the log file for detailed error messages

## Security Notes

- Never commit your `.env` file to version control
- Use app passwords instead of your main email password
- Review script contents before running with elevated privileges
