"""Diagnostic tools for checking system environment and services."""
import asyncio
import importlib
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from dun.core.protocols import DiagnosticProtocol, DiagnosticResult
from dun.config.settings import get_settings

class EnvironmentDiagnostic:
    """Diagnostic checks for the runtime environment."""
    
    def __init__(self):
        self.name = "environment"
    
    async def run_checks(self) -> List[DiagnosticResult]:
        """Run environment diagnostic checks."""
        results: List[DiagnosticResult] = []
        
        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        results.append(DiagnosticResult(
            "python_version",
            True,
            f"Python {py_version} ({platform.python_implementation()})",
            {"version": py_version, "implementation": platform.python_implementation()}
        ))
        
        # Platform
        results.append(DiagnosticResult(
            "platform",
            True,
            f"{platform.system()} {platform.release()}",
            {"system": platform.system(), "release": platform.release()}
        ))
        
        # Required directories
        settings = get_settings()
        for dir_name in ["BASE_DIR", "DATA_DIR", "LOGS_DIR", "CACHE_DIR"]:
            path = getattr(settings, dir_name, None)
            if path and isinstance(path, Path):
                exists = path.exists()
                writable = os.access(str(path), os.W_OK) if exists else False
                results.append(DiagnosticResult(
                    f"dir_{dir_name.lower()}",
                    exists and writable,
                    f"{'✓' if exists and writable else '✗'} {dir_name}: {path}",
                    {"path": str(path), "exists": exists, "writable": writable}
                ))
        
        return results


class DependencyDiagnostic:
    """Diagnostic checks for Python dependencies."""
    
    def __init__(self):
        self.name = "dependencies"
        self.required_packages = [
            "pandas",
            "pydantic",
            "python-dotenv",
            "requests",
            "loguru",
        ]
    
    async def run_checks(self) -> List[DiagnosticResult]:
        """Check for required Python packages."""
        results: List[DiagnosticResult] = []
        
        for package in self.required_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, "__version__", "unknown")
                results.append(DiagnosticResult(
                    f"pkg_{package}",
                    True,
                    f"✓ {package} ({version})",
                    {"package": package, "version": version}
                ))
            except ImportError:
                results.append(DiagnosticResult(
                    f"pkg_{package}",
                    False,
                    f"✗ {package} (not installed)",
                    {"package": package, "installed": False}
                ))
        
        return results


class ExecutableDiagnostic:
    """Diagnostic checks for required executables."""
    
    def __init__(self):
        self.name = "executables"
        self.required_executables = ["git", "python3"]
    
    async def run_checks(self) -> List[DiagnosticResult]:
        """Check for required executables in PATH."""
        results: List[DiagnosticResult] = []
        
        for exe in self.required_executables:
            path = shutil.which(exe)
            results.append(DiagnosticResult(
                f"exe_{exe}",
                path is not None,
                f"{'✓' if path else '✗'} {exe} ({path if path else 'not found'})",
                {"executable": exe, "found": path is not None, "path": path}
            ))
        
        return results


class OllamaDiagnostic:
    """Diagnostic checks for Ollama service."""
    
    def __init__(self):
        self.name = "ollama"
        self.settings = get_settings()
    
    async def run_checks(self) -> List[DiagnosticResult]:
        """Check Ollama service availability."""
        results: List[DiagnosticResult] = []
        
        if not self.settings.OLLAMA_ENABLED:
            results.append(DiagnosticResult(
                "ollama_enabled",
                False,
                "Ollama integration is disabled in settings",
                {"enabled": False}
            ))
            return results
        
        # Check if we can import ollama
        try:
            import ollama
            results.append(DiagnosticResult(
                "ollama_installed",
                True,
                f"ollama Python package is installed (v{ollama.__version__})",
                {"version": getattr(ollama, "__version__", "unknown")}
            ))
            
            # Try to connect to Ollama server
            try:
                client = ollama.Client(host=self.settings.OLLAMA_BASE_URL)
                models = client.list()
                results.append(DiagnosticResult(
                    "ollama_connected",
                    True,
                    f"Connected to Ollama at {self.settings.OLLAMA_BASE_URL}",
                    {"models": len(models.get('models', []))}
                ))
            except Exception as e:
                results.append(DiagnosticResult(
                    "ollama_connected",
                    False,
                    f"Failed to connect to Ollama at {self.settings.OLLAMA_BASE_URL}: {str(e)}",
                    {"error": str(e)}
                ))
                
        except ImportError:
            results.append(DiagnosticResult(
                "ollama_installed",
                False,
                "ollama Python package is not installed",
                {"installed": False}
            ))
        
        return results


class DiagnosticRunner:
    """Run all diagnostic checks and report results."""
    
    def __init__(self):
        self.checks: List[DiagnosticProtocol] = [
            EnvironmentDiagnostic(),
            DependencyDiagnostic(),
            ExecutableDiagnostic(),
            OllamaDiagnostic(),
        ]
    
    async def run_all_checks(self) -> Dict[str, List[DiagnosticResult]]:
        """Run all diagnostic checks and return results."""
        results: Dict[str, List[DiagnosticResult]] = {}
        
        for check in self.checks:
            try:
                results[check.name] = await check.run_checks()
            except Exception as e:
                results[check.name] = [
                    DiagnosticResult(
                        "error",
                        False,
                        f"Error running {check.name} checks: {str(e)}",
                        {"error": str(e), "check": check.name}
                    )
                ]
        
        return results
    
    def print_report(self, results: Dict[str, List[DiagnosticResult]]) -> None:
        """Print a formatted diagnostic report."""
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        
        for category, checks in results.items():
            table = Table(title=f"{category.upper()} Checks", show_header=True, header_style="bold magenta")
            table.add_column("Status", width=10)
            table.add_column("Check")
            table.add_column("Details")
            
            for check in checks:
                status = "[green]PASS[/green]" if check.status else "[red]FAIL[/red]"
                table.add_row(status, check.name, check.message)
            
            console.print(table)
            console.print()


async def run_diagnostics() -> Dict[str, List[DiagnosticResult]]:
    """Run all diagnostics and return results."""
    runner = DiagnosticRunner()
    results = await runner.run_all_checks()
    return results


def print_diagnostic_report() -> None:
    """Run diagnostics and print a formatted report."""
    runner = DiagnosticRunner()
    results = asyncio.run(runner.run_all_checks())
    runner.print_report(results)
    return results
