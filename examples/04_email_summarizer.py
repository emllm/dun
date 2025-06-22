"""
Example 4: Email Summarizer
Creates summaries of email conversations.
"""
import os
from dotenv import load_dotenv
from dun.llm_analyzer import LLMAnalyzer

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize LLM analyzer
    llm = LLMAnalyzer(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "mistral:7b")
    )
    
    # Example email thread
    email_thread = """
    From: alice@example.com
    To: team@example.com
    Subject: Project Update
    
    Hi team,
    Just checking in on the project status. How are we doing with the Q2 goals?
    
    ---
    
    From: bob@example.com
    To: alice@example.com, team@example.com
    Subject: Re: Project Update
    
    Hi Alice,
    We're about 70% done with the Q2 goals. The frontend is complete, 
    and we're working on the backend integration.
    
    ---
    
    From: charlie@example.com
    To: alice@example.com, team@example.com
    Subject: Re: Project Update
    
    I've finished the database optimizations. Performance has improved by 40%.
    """
    
    # Generate summary
    print("Generating email thread summary...")
    summary = llm.analyze(
        f"Please summarize this email thread and extract action items:\n\n{email_thread}"
    )
    
    print("\n=== Email Thread Summary ===")
    print(summary)

if __name__ == "__main__":
    main()
