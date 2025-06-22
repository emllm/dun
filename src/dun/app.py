"""Main application module for Dun."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from dun.core.contexts import get_context
from dun.services.diagnostics import print_diagnostic_report
from dun.services.filesystem import FileSystemService
from dun.services.ollama import OllamaService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("dun")
console = Console()

class DunApplication:
    """Main application class for Dun."""
    
    def __init__(self):
        self.running = False
        self.context = get_context()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        if self.running:
            logger.info("Shutdown signal received, stopping application...")
            self.running = False
        else:
            logger.warning("Force shutdown requested!")
            sys.exit(1)
    
    async def initialize_services(self):
        """Initialize all application services."""
        logger.info("Initializing services...")
        
        # Register core services
        self.context.register_service(FileSystemService())
        self.context.register_service(OllamaService())
        
        # Initialize all services
        await self.context.initialize_services()
        
        logger.info("All services initialized")
    
    async def run_diagnostics(self) -> bool:
        """Run system diagnostics and report any issues."""
        console.rule("System Diagnostics")
        results = await print_diagnostic_report()
        
        # Check for critical failures
        critical_failures = False
        for category, checks in results.items():
            for check in checks:
                if not check.status and check.name not in ["ollama_connected"]:
                    critical_failures = True
                    break
            if critical_failures:
                break
        
        if critical_failures:
            console.print("\n[red]Critical failures detected! Some features may not work correctly.[/red]")
            return False
        
        return True
    
    async def run(self):
        """Run the main application loop."""
        self.running = True
        
        try:
            # Initialize services
            await self.initialize_services()
            
            # Run diagnostics
            if not await self.run_diagnostics():
                console.print("\n[bold yellow]Warning:[/bold yellow] Some services are not available.")
            
            # Main application loop
            console.rule("Dun - Data Understanding and Navigation")
            console.print("Type 'exit' or 'quit' to exit\n")
            
            while self.running:
                try:
                    # Get user input
                    try:
                        user_input = input("dun> ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break
                    
                    # Process commands
                    if user_input.lower() in ('exit', 'quit'):
                        break
                    
                    # Process the input
                    await self.process_input(user_input)
                    
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
        
        finally:
            # Cleanup
            await self.shutdown()
    
    async def process_input(self, user_input: str):
        """Process user input."""
        # This is a placeholder - actual processing will be implemented
        # based on the specific requirements
        if user_input == "test":
            console.print("Test command received!")
        else:
            console.print(f"You entered: {user_input}")
    
    async def shutdown(self):
        """Shutdown the application gracefully."""
        if hasattr(self, 'context'):
            await self.context.shutdown()
        logger.info("Application shutdown complete")


async def main():
    """Main entry point for the application."""
    app = DunApplication()
    try:
        await app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1
    return 0


def run():
    """Run the application."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(run())
