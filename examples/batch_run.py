"""
Non-interactive batch processor for Dun commands.
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import dun
sys.path.insert(0, str(Path(__file__).parent.parent))

def process_commands(input_file, output_dir):
    """Process commands from input file and save results to output directory."""
    from dun.processor_engine import ProcessorEngine
    from dun.llm_analyzer import LLMAnalyzer
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    llm_analyzer = LLMAnalyzer()
    engine = ProcessorEngine(llm_analyzer)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] Processing: {cmd}")
        output_file = output_dir / f"command_{i:03d}.log"
        
        try:
            result = engine.process_natural_request(cmd)
            output = f"Command: {cmd}\n\nResult:\n{result if result is not None else 'No output'}"
            status = "SUCCESS"
        except Exception as e:
            output = f"Command: {cmd}\n\nError: {str(e)}"
            status = "ERROR"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{output}\n\nStatus: {status}")
        
        print(f"  -> {status}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_file> <output_dir>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    process_commands(input_file, output_dir)
