"""
Example 3: Email Organizer
Organizes emails into folders based on their content and date.
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
    
    # Organize emails
    print("Organizing emails into folders...")
    result = processor.process_natural_request(
        "Posortuj wiadomości w folderze INBOX do podfolderów wg roku i miesiąca"
    )
    
    print("\n=== Organization Result ===")
    print(result)

if __name__ == "__main__":
    main()
