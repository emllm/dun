"""Run tests using pytest."""
import subprocess
import sys

def main():
    """Run the test suite."""
    print("🚀 Running tests...")
    
    cmd = ["pytest", "--cov=dun", "--cov-report=term-missing", "-v"]
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("❌ Tests failed", file=sys.stderr)
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
