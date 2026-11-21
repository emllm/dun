"""Dun - Data Understanding and Navigation."""
import argparse
import sys
from typing import List, Optional

from dun import __version__
from dun.llm_analyzer import LLMAnalyzer
from dun.processor_engine import ProcessorEngine


def _run_natural_command(command_text: str) -> int:
    """Execute one natural-language request and print a structured summary."""
    analyzer = LLMAnalyzer()
    engine = ProcessorEngine(analyzer)
    result = engine.process_natural_request(command_text)
    if isinstance(result, dict):
        output_file = result.get("output_file")
        if output_file:
            print(f"Zapisano połączony zbiór danych: {output_file}")
        else:
            print(result)
    elif result is not None:
        print(result)
    return 0


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI flags and subcommands."""
    parser = argparse.ArgumentParser(
        prog="dun",
        description="Dun - Data Understanding and Navigation",
    )
    parser.add_argument(
        "--command",
        "-c",
        dest="command_flag",
        help="Execute a single natural-language command",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print package version and exit",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    run_parser = subparsers.add_parser("run", help="Run a command or interactive loop")
    run_parser.add_argument("command_text", nargs="?", help="Natural-language task")
    run_parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    subparsers.add_parser("version", help="Show version information")

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Run the Dun CLI entrypoint."""
    raw_args = sys.argv[1:] if args is None else list(args)
    parsed = parse_args(raw_args)

    if parsed.version or parsed.subcommand == "version":
        print(f"dun {__version__}")
        sys.exit(0)

    if parsed.command_flag:
        sys.exit(_run_natural_command(parsed.command_flag))

    if parsed.subcommand == "run":
        if parsed.command_text and not parsed.interactive:
            sys.exit(_run_natural_command(parsed.command_text))

    # Interactive / mocked-stdin single or multi-turn loop
    non_interactive_stdin = not sys.stdin.isatty()
    exit_code = 0
    while True:
        try:
            user_input = input("dun> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        exit_code = _run_natural_command(user_input)
        if non_interactive_stdin:
            break

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
