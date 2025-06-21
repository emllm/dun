"""Runy - Dynamiczny Procesor Danych."""

def main():
    """Run the main application."""
    from .processor_engine import ProcessorEngine
    from .llm_analyzer import LLMAnalyzer
    
    print("Runy - Dynamiczny Procesor Danych")
    print("Wpisz 'exit' aby zakończyć")
    
    llm_analyzer = LLMAnalyzer()
    engine = ProcessorEngine(llm_analyzer)
    
    while True:
        try:
            request = input("\nWprowadź żądanie: ")
            if request.lower() in ('exit', 'quit'):
                break
                
            result = engine.process_natural_request(request)
            print("\nWynik:", result)
            
        except KeyboardInterrupt:
            print("\nZakończono działanie.")
            break
        except Exception as e:
            print(f"\nBłąd: {e}")

if __name__ == "__main__":
    main()
