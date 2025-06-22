"""
Example 1: Basic Email Analysis
Analyzes an email message using the LLM analyzer.
"""
from dun.llm_analyzer import LLMAnalyzer

def main():
    # Initialize the LLM analyzer
    llm = LLMAnalyzer(
        base_url="http://localhost:11434",
        model="mistral:7b"
    )
    
    # Example email content
    email_content = """
    From: john.doe@example.com
    To: jane.smith@example.com
    Subject: Meeting Tomorrow
    
    Hi Jane,
    
    I hope this email finds you well. I'd like to schedule a meeting for tomorrow at 2 PM 
    to discuss the project timeline. Please let me know if this works for you.
    
    Best regards,
    John
    """
    
    # Analyze the email
    analysis = llm.analyze(
        f"Analyze this email and extract key information:\n\n{email_content}"
    )
    
    print("\n=== Email Analysis Result ===")
    print(analysis)

if __name__ == "__main__":
    main()
