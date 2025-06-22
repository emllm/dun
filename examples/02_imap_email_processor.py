"""
Example 2: IMAP Email Processor
Demonstrates how to process emails from an IMAP server.
"""
import os
from dotenv import load_dotenv
from dun.processor_engine import ProcessorEngine
from dun.llm_analyzer import LLMAnalyzer

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    llm = LLMAnalyzer(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "mistral:7b")
    )
    processor = ProcessorEngine(llm)
    
    # Process emails from IMAP
    print("Processing emails from IMAP...")
    result = processor.process_natural_request(
        "Pobierz 5 najnowszych wiadomości z INBOX i wyświetl ich tematy"
    )
    
    print("\n=== Processing Result ===")
    print(result)

if __name__ == "__main__":
    main()
