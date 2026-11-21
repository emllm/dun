"""Interactive natural-language task-to-library mapper for Dun."""
from __future__ import annotations

import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from dun.library_catalog import (
    LIBRARY_PRIORITIES,
    LibraryInterface,
    TaskMapping,
    build_library_database,
    build_task_mappings,
)
from dun.packages import dist_to_module, is_module_available
from dun.routing import library_router


class InteractiveMapper:
    """Map natural-language tasks to Python libraries and collect parameters."""

    def __init__(self) -> None:
        self.library_database: Dict[str, LibraryInterface] = build_library_database()
        self.task_mappings: List[TaskMapping] = build_task_mappings(self.library_database)
        self.discovered_interfaces: Dict[str, Dict[str, Any]] = {}

    def analyze_task_and_map_libraries(self, natural_request: str) -> List[LibraryInterface]:
        """Rank matching libraries using ``library_router()`` BM25-lite scoring."""
        logger.info("Analizowanie zadania i mapowanie bibliotek...")
        matched_libraries: List[LibraryInterface] = []
        for lib_key, score in library_router().rank(natural_request):
            lib = self.library_database.get(lib_key)
            if lib is not None and lib not in matched_libraries:
                matched_libraries.append(lib)
                logger.info(f"Znaleziono bibliotekę: {lib.name} (score: {score:.3f})")
        return matched_libraries

    def _get_library_priority(self, library_name: str) -> int:
        return LIBRARY_PRIORITIES.get(library_name, 1)

    def discover_cli_interface(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Inspect callable functions/signatures on ``package_name`` if importable."""
        if package_name in self.discovered_interfaces:
            return self.discovered_interfaces[package_name]

        module_name = dist_to_module(package_name)
        if not is_module_available(module_name):
            logger.warning(f"Pakiet {package_name} ({module_name}) nie jest zainstalowany")
            return None

        try:
            module = importlib.import_module(module_name)
            cli_info = self._analyze_module_for_cli(module)
            if cli_info:
                self.discovered_interfaces[package_name] = cli_info
                logger.success(f"Odkryto interfejs CLI dla {package_name}")
                return cli_info
        except (ImportError, OSError, RuntimeError, AttributeError) as exc:
            logger.warning(f"Błąd analizy {package_name}: {exc}")
        return None

    def _analyze_module_for_cli(self, module: Any) -> Optional[Dict[str, Any]]:
        main_functions: List[Dict[str, Any]] = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith("_"):
                try:
                    sig = inspect.signature(obj)
                except (TypeError, ValueError):
                    continue
                params = [
                    {
                        "name": param_name,
                        "type": str(param.annotation)
                        if param.annotation != param.empty
                        else "Any",
                        "default": param.default if param.default != param.empty else None,
                        "required": param.default == param.empty,
                    }
                    for param_name, param in sig.parameters.items()
                ]
                main_functions.append(
                    {"name": name, "parameters": params, "docstring": obj.__doc__}
                )
        if not main_functions:
            return None
        return {
            "has_cli": True,
            "main_functions": main_functions,
            "cli_commands": [],
            "parameters": [],
        }

    def interactive_parameter_collection(self, library: LibraryInterface) -> Dict[str, Any]:
        """Interactively prompt for required and optional parameters of ``library``."""
        logger.info(f"Zbieranie parametrów dla: {library.name}")
        print(f"\nKONFIGURACJA: {library.name}")
        print("=" * 50)

        if library.param_descriptions:
            for param, desc in library.param_descriptions.items():
                kind = "wymagany" if param in library.required_params else "opcjonalny"
                print(f"   * {param} ({kind}): {desc}")

        if library.examples:
            print("\nPrzykład konfiguracji:")
            for key, value in library.examples[0].items():
                print(f"   {key} = {value}")

        collected_params: Dict[str, Any] = {}
        for param in library.required_params:
            collected_params[param] = self._collect_single_parameter(param, library, required=True)

        if library.optional_params:
            print("\nParametry opcjonalne:")
            for param in library.optional_params:
                if self._ask_yes_no(f"Czy chcesz skonfigurować {param}?"):
                    collected_params[param] = self._collect_single_parameter(
                        param, library, required=False
                    )
        return collected_params

    def _collect_single_parameter(
        self,
        param_name: str,
        library: LibraryInterface,
        required: bool = True,
    ) -> Any:
        param_upper = param_name.upper()
        pkg_upper = dist_to_module(library.package).upper()
        env_variants = [
            param_upper,
            f"{pkg_upper}_{param_upper}",
            f"DUN_{param_upper}",
            f"DUNE_{param_upper}",
        ]
        env_value = None
        env_source = None
        for env_var in env_variants:
            env_value = os.getenv(env_var)
            if env_value:
                env_source = env_var
                break

        param_desc = library.param_descriptions.get(param_name, "")
        param_type = library.param_types.get(param_name, "str")
        prompt = f"{param_name}" + (f" ({param_desc})" if param_desc else "")
        if not required:
            prompt += " [opcjonalny]"

        if env_value and env_source:
            if self._ask_yes_no(f"Użyć wartości z {env_source}?", default=True):
                return self._convert_type(env_value, param_type)

        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                if not user_input and not required:
                    return None
                if not user_input and required:
                    print("Ten parametr jest wymagany!")
                    continue
                return self._convert_type(user_input, param_type)
            except KeyboardInterrupt:
                print("\nPrzerwano przez użytkownika")
                sys.exit(1)
            except (ValueError, json.JSONDecodeError) as exc:
                print(f"Błąd: {exc}. Spróbuj ponownie.")

    def _convert_type(self, value: str, param_type: str) -> Any:
        if param_type == "int":
            return int(value)
        if param_type == "bool":
            return value.lower() in {"true", "1", "yes", "tak", "y"}
        if param_type == "float":
            return float(value)
        if param_type == "list":
            return value.split(",")
        if param_type == "dict":
            return json.loads(value)
        if param_type == "tuple" and "," in value:
            return tuple(map(int, value.split(",")))
        return value

    def _ask_yes_no(self, question: str, default: Optional[bool] = None) -> bool:
        suffix = "[T/n]" if default is True else "[t/N]" if default is False else "[t/n]"
        while True:
            try:
                answer = input(f"{question} {suffix}: ").strip().lower()
                if not answer and default is not None:
                    return default
                if answer in {"t", "tak", "y", "yes", "1", "true"}:
                    return True
                if answer in {"n", "nie", "no", "0", "false"}:
                    return False
                print("Odpowiedz 't' (tak) lub 'n' (nie)")
            except KeyboardInterrupt:
                print("\nPrzerwano przez użytkownika")
                sys.exit(1)

    def generate_runtime_config(
        self,
        libraries: List[LibraryInterface],
        collected_params: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build runtime package and env var configuration from collected params."""
        required_pkgs = list(dict.fromkeys(lib.package for lib in libraries))
        required_env: List[str] = []
        optional_env: List[str] = []

        for library in libraries:
            lib_params = collected_params.get(library.name, {})
            pkg_prefix = dist_to_module(library.package).upper()
            for param_name in lib_params:
                env_var = f"{pkg_prefix}_{param_name.upper()}"
                target = required_env if param_name in library.required_params else optional_env
                if env_var not in target:
                    target.append(env_var)

        return {
            "runtime": {
                "type": "docker",
                "base_image": "python:3.11-slim",
                "python_packages": {"required": required_pkgs, "optional": []},
                "environment": {"required": required_env, "optional": optional_env},
            },
            "collected_parameters": collected_params,
        }

    def save_parameters_to_env(
        self,
        collected_params: Dict[str, Dict[str, Any]],
        env_file: str = ".env",
    ) -> None:
        """Persist collected parameters into ``env_file`` using ``DUN_`` prefix."""
        logger.info(f"Zapisywanie parametrów do {env_file}")
        env_path = Path(env_file)
        existing_vars: Dict[str, str] = {}
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if "=" in stripped and not stripped.startswith("#"):
                        key, value = stripped.split("=", 1)
                        existing_vars[key] = value

        new_vars: Dict[str, str] = {}
        for params in collected_params.values():
            for param_name, value in params.items():
                if value is not None:
                    new_vars[f"DUN_{param_name.upper()}"] = str(value)

        all_vars = {**existing_vars, **new_vars}
        with env_path.open("w", encoding="utf-8") as handle:
            handle.write("# Dun Configuration\n")
            handle.write("# Auto-generated parameters\n\n")
            for key, value in sorted(all_vars.items()):
                handle.write(f"{key}={value}\n")
        logger.success(f"Parametry zapisane do {env_file}")

    def run_interactive_mapping(self, natural_request: str) -> Dict[str, Any]:
        """Run end-to-end interactive library discovery and parameter collection."""
        libraries = self.analyze_task_and_map_libraries(natural_request)
        if not libraries:
            print("Nie znaleziono pasujących bibliotek dla tego zadania")
            return {}

        collected_params: Dict[str, Dict[str, Any]] = {}
        for library in libraries:
            if self._ask_yes_no(f"\nKonfigurować {library.name}?", default=True):
                collected_params[library.name] = self.interactive_parameter_collection(library)

        runtime_config = self.generate_runtime_config(libraries, collected_params)
        if collected_params and self._ask_yes_no("\nZapisać parametry do .env?", default=True):
            self.save_parameters_to_env(collected_params)

        return {
            "libraries": libraries,
            "parameters": collected_params,
            "runtime_config": runtime_config,
            "natural_request": natural_request,
        }
