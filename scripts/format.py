"""Format Python code using black and isort."""
import subprocess
import sys
from pathlib import Path

def main():
    """Run code formatters."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("🔄 Running isort...")
    isort_cmd = [
        "isort",
        "--profile", "black",
        "--line-length", "88",
        str(src_dir)
    ]
    
    if subprocess.run(isort_cmd).returncode != 0:
        print("❌ isort failed", file=sys.stderr)
        sys.exit(1)
    
    print("\n🔄 Running black...")
    black_cmd = [
        "black",
        "--line-length", "88",
        "--target-version", "py311",
        str(src_dir)
    ]
    
    if subprocess.run(black_cmd).returncode != 0:
        print("❌ black failed", file=sys.stderr)
        sys.exit(1)
    
    print("\n✅ Formatting complete!")
    sys.exit(0)

if __name__ == "__main__":
    main()
