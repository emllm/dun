"""Lint Python code using flake8 and mypy."""
import subprocess
import sys
from pathlib import Path

def run_flake8() -> bool:
    """Run flake8 linter."""
    print("🔍 Running flake8...")
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    cmd = ["flake8", str(src_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        print("❌ flake8 found issues", file=sys.stderr)
        return False
    
    print("✅ flake8 passed")
    return True

def run_mypy() -> bool:
    """Run mypy type checker."""
    print("\n🔍 Running mypy...")
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    cmd = ["mypy", str(src_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        print("❌ mypy found issues", file=sys.stderr)
        return False
    
    print("✅ mypy passed")
    return True

def main():
    """Run all linters."""
    flake8_passed = run_flake8()
    mypy_passed = run_mypy()
    
    if not all([flake8_passed, mypy_passed]):
        print("\n❌ Linting failed", file=sys.stderr)
        sys.exit(1)
    
    print("\n✨ All linting passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
