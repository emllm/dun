#!/usr/bin/env python3
"""
Example 5: Command Line IMAP Client
Demonstrates how to use dun from command line with IMAP configuration.
"""
import os
import argparse
from dotenv import load_dotenv
from dun.processor_engine import ProcessorEngine
from dun.llm_analyzer import LLMAnalyzer

def parse_args():
    parser = argparse.ArgumentParser(description='Process emails using dun')
    parser.add_argument('--imap-server', help='IMAP server address')
    parser.add_argument('--imap-port', type=int, help='IMAP server port')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--password', help='Email password or app password')
    parser.add_argument('--folder', default='INBOX', help='IMAP folder to process')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of emails to process')
    return parser.parse_args()

def main():
    # Load environment from .env file if it exists
    load_dotenv()
    
    # Parse command line arguments
    args = parse_args()
    
    # Use command line args or fall back to environment variables
    config = {
        'imap_server': args.imap_server or os.getenv('IMAP_SERVER'),
        'imap_port': args.imap_port or int(os.getenv('IMAP_PORT', 993)),
        'email': args.email or os.getenv('IMAP_EMAIL'),
        'password': args.password or os.getenv('IMAP_PASSWORD'),
        'folder': args.folder or os.getenv('IMAP_FOLDER', 'INBOX'),
        'limit': args.limit
    }
    
    # Validate configuration
    if not all([config['imap_server'], config['email'], config['password']]):
        print("Error: Missing required IMAP configuration. Please provide --imap-server, --email, and --password")
        return
    
    print(f"Connecting to {config['email']} on {config['imap_server']}:{config['imap_port']}")
    
    try:
        # Initialize components
        llm = LLMAnalyzer(
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            model=os.getenv('OLLAMA_MODEL', 'mistral:7b')
        )
        processor = ProcessorEngine(llm)
        
        # Process emails
        result = processor.process_natural_request(
            f"Pobierz {config['limit']} najnowszych wiadomości z {config['folder']} "
            f"i wyświetl ich tematy i nadawców"
        )
        
        print("\n=== Processing Result ===")
        print(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure your IMAP settings are correct and the server is accessible.")
        print("You can configure them via command line arguments or .env file.")

if __name__ == "__main__":
    main()
