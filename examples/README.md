# Dun Examples

This directory contains example scripts demonstrating various features of the Dun email processing tool.

## Prerequisites

1. Python 3.10+
2. Ollama server running (for LLM processing)
3. IMAP access to an email account

## Setup

1. Copy `.env.example` to `.env` and update with your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your IMAP and Ollama settings
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

## Running Examples

### Individual Examples

1. **Basic Email Analysis**
   ```bash
   python examples/01_email_analysis.py
   ```

2. **IMAP Email Processor**
   ```bash
   python examples/02_imap_email_processor.py
   ```

3. **Email Organizer**
   ```bash
   python examples/03_email_organizer.py
   ```

4. **Email Summarizer**
   ```bash
   python examples/04_email_summarizer.py
   ```

5. **Command Line IMAP Client**
   ```bash
   # Using .env for configuration
   python examples/05_command_line_imap.py
   
   # Or override settings via command line
   python examples/05_command_line_imap.py \
     --imap-server imap.example.com \
     --email your@email.com \
     --password yourpassword \
     --folder INBOX \
     --limit 5
   ```

### Using Docker Compose

1. Copy and configure the Docker Compose file:
   ```bash
   cp examples/docker-compose.example.yml docker-compose.yml
   # Edit docker-compose.yml with your IMAP settings
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | URL of the Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model to use for LLM processing | `mistral:7b` |
| `IMAP_SERVER` | IMAP server address | - |
| `IMAP_PORT` | IMAP server port | `993` |
| `IMAP_EMAIL` | Email address for authentication | - |
| `IMAP_PASSWORD` | Email password or app password | - |
| `IMAP_FOLDER` | IMAP folder to process | `INBOX` |
| `PROCESSING_DIR` | Directory to store processed emails | `./processed_emails` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Security Notes

- Never commit your `.env` file to version control
- Use app passwords instead of your main email password
- Make sure the `processed_emails` directory has proper permissions
