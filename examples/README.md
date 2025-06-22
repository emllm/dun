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

### Prerequisites

Before running examples, make sure you have:
1. Ollama server running (default: http://localhost:11434)
2. IMAP access credentials configured in `.env`

### Individual Examples

1. **Basic Email Analysis**
   ```bash
   python 01_email_analysis.py
   ```

2. **IMAP Email Processor**
   ```bash
   python 02_imap_email_processor.py
   ```

3. **Email Organizer**
   ```bash
   python 03_email_organizer.py
   ```

4. **Email Summarizer**
   ```bash
   python 04_email_summarizer.py
   ```

5. **Command Line IMAP Client**
   ```bash
   # Using .env for configuration
   python 05_command_line_imap.py
   
   # Or override settings via command line
   python 05_command_line_imap.py \
     --imap-server imap.example.com \
     --email your@email.com \
     --password yourpassword \
     --folder INBOX \
     --limit 5
   ```

### Using Docker Compose

1. From the project root directory, copy the example configuration:
   ```bash
   cp examples/docker-compose.example.yml docker-compose.yml
   ```

2. Edit the `docker-compose.yml` file and update the following environment variables:
   ```yaml
   environment:
     - IMAP_SERVER=your_imap_server
     - IMAP_EMAIL=your_email@example.com
     - IMAP_PASSWORD=your_app_password
   ```

3. Start the services (this will download the Ollama image and build the Dun container):
   ```bash
   docker-compose up -d
   ```

4. View logs to monitor the progress:
   ```bash
   docker-compose logs -f
   ```

5. To stop the services:
   ```bash
   docker-compose down
   ```

Note: The first run may take a few minutes as it needs to download the Ollama container and the Mistral 7B model.

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
