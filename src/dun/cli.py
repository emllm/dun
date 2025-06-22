"""Command-line interface for Dun."""
import argparse
import sys
from typing import Optional, List

from .processor_engine import ProcessorEngine
from .llm_analyzer import LLMAnalyzer


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Dun - Dynamiczny Procesor Danych',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Main command
    cmd_parser = subparsers.add_parser('run', help='Run a command')
    cmd_parser.add_argument('command_text', nargs='?', help='Command to execute')
    cmd_parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    
    # Email commands
    email_parser = subparsers.add_parser('email', help='Email operations')
    email_subparsers = email_parser.add_subparsers(dest='email_command')
    
    # Email list command
    list_parser = email_subparsers.add_parser('list', help='List emails')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number of emails to list')
    list_parser.add_argument('--folder', default='INBOX', help='IMAP folder to list emails from')
    
    # Email get command
    get_parser = email_subparsers.add_parser('get', help='Get email content')
    get_parser.add_argument('message_id', help='ID of the email to retrieve')
    get_parser.add_argument('--folder', default='INBOX', help='IMAP folder containing the email')
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Run the CLI application."""
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    if not parsed_args.command and not args:
        # No arguments provided, run in interactive mode
        return interactive_mode()
    
    try:
        if parsed_args.command == 'run':
            if parsed_args.interactive or not parsed_args.command_text:
                return interactive_mode()
            return execute_command(parsed_args.command_text)
        elif parsed_args.command == 'email':
            return handle_email_command(parsed_args)
        elif parsed_args.command == 'version':
            print("Dun - Dynamiczny Procesor Danych")
            print("Wersja: 0.1.0")
            return 0
        else:
            print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def execute_command(command: str) -> int:
    """Execute a single command."""
    try:
        llm_analyzer = LLMAnalyzer()
        engine = ProcessorEngine(llm_analyzer)
        result = engine.process_natural_request(command)
        print(result)
        return 0
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return 1


def interactive_mode() -> int:
    """Run in interactive mode."""
    print("Dun - Dynamiczny Procesor Danych")
    print("Wpisz 'exit' lub 'quit' aby zakończyć")
    print("Wpisz 'help' aby wyświetlić pomoc")
    
    llm_analyzer = LLMAnalyzer()
    engine = ProcessorEngine(llm_analyzer)
    
    while True:
        try:
            command = input("\ndun> ").strip()
            if not command:
                continue
                
            if command.lower() in ('exit', 'quit'):
                break
                
            if command.lower() == 'help':
                print_help()
                continue
                
            result = engine.process_natural_request(command)
            print(f"\n{result}")
            
        except KeyboardInterrupt:
            print("\nUżyj 'exit' lub 'quit' aby wyjść")
        except Exception as e:
            print(f"Błąd: {e}")
    
    return 0


def handle_email_command(args: argparse.Namespace) -> int:
    """Handle email subcommands."""
    if args.email_command == 'list':
        print(f"Listing up to {args.limit} emails from {args.folder}")
        # TODO: Implement actual email listing
        return 0
    elif args.email_command == 'get':
        print(f"Getting email {args.message_id} from {args.folder}")
        # TODO: Implement actual email retrieval
        return 0
    else:
        print(f"Unknown email command: {args.email_command}", file=sys.stderr)
        return 1


def print_help() -> None:
    """Print help information."""
    help_text = """
Dostępne komendy:
  help                - Wyświetl tę pomoc
  exit/quit          - Zakończ program
  email list         - Wyświetl listę emaili
  email get <id>     - Pokaż zawartość emaila o podanym ID
  <dowolne polecenie> - Wykonaj polecenie w języku naturalnym

Przykłady:
  dun "pokaż 10 najnowszych emaili"
  dun email list --limit 5
  dun email get 123
"""
    print(help_text)


if __name__ == "__main__":
    sys.exit(main())
