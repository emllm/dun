"""Dun - Data Understanding and Navigation CLI entrypoint."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from dun import __version__
from dun.config_generator import TaskConfigGenerator
from dun.llm_analyzer import LLMAnalyzer
from dun.processor_engine import ProcessorEngine
from dun.routing import library_router, task_router
from dun.task_validator import TaskValidator


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


def _run_route(query_parts: List[str]) -> int:
    """Classify a natural-language prompt offline using BM25-lite lexical routing."""
    query = " ".join(query_parts).strip()
    task_ranked = task_router().rank(query)
    lib_ranked = library_router().rank(query)
    payload = {
        "query": query,
        "task_type": task_ranked[0][0] if task_ranked else "generic_processing",
        "libraries": [lib for lib, _score in lib_ranked],
        "scores": {
            "task_types": {rid: round(score, 4) for rid, score in task_ranked},
            "libraries": {lib: round(score, 4) for lib, score in lib_ranked},
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _run_config(query_parts: List[str], output_file: Optional[str]) -> int:
    """Generate a deterministic dun.io/v1 YAML task configuration offline."""
    query = " ".join(query_parts).strip()
    generator = TaskConfigGenerator()
    config = generator.generate_config_from_nlp(query)
    if output_file:
        saved_path = generator.save_config_to_file(config, output_file)
        print(saved_path)
    else:
        print(yaml.dump(config, default_flow_style=False, allow_unicode=True, indent=2))
    return 0


def _run_validate(config_file: str) -> int:
    """Validate a YAML task configuration file."""
    path = Path(config_file)
    if not path.exists():
        print(json.dumps({"valid": False, "errors": [f"File not found: {config_file}"]}))
        return 1
    validator = TaskValidator()
    config = validator.load_config(str(path))
    result = validator.validate(config)
    print(result.model_dump_json(indent=2))
    return 0 if result.valid else 1


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

    route_parser = subparsers.add_parser("route", help="Route a natural-language task offline")
    route_parser.add_argument("query", nargs="+", help="Natural-language request text")

    config_parser = subparsers.add_parser("config", help="Generate dun.io/v1 YAML task config")
    config_parser.add_argument("query", nargs="+", help="Natural-language request text")
    config_parser.add_argument("--output", "-o", help="Optional YAML output file path")

    validate_parser = subparsers.add_parser("validate", help="Validate a YAML task configuration")
    validate_parser.add_argument("config_file", help="Path to YAML configuration file")

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

    if parsed.subcommand == "route":
        sys.exit(_run_route(parsed.query))

    if parsed.subcommand == "config":
        sys.exit(_run_config(parsed.query, parsed.output))

    if parsed.subcommand == "validate":
        sys.exit(_run_validate(parsed.config_file))

    if parsed.subcommand == "run":
        if parsed.command_text and not parsed.interactive:
            sys.exit(_run_natural_command(parsed.command_text))

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
