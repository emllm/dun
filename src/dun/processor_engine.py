"""Główny silnik procesora danych z dynamicznym zarządzaniem bibliotekami."""

import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from loguru import logger
from pydantic import BaseModel

from dun.packages import dist_to_module, is_module_available, module_to_dist
from dun.processor_engine_stdlib import is_stdlib_module


class ProcessorConfig(BaseModel):
    """Konfiguracja procesora danych."""

    name: str
    description: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    code_template: str


class DynamicPackageManager:
    """Menedżer dynamicznego instalowania pakietów."""

    def __init__(self):
        self.installed_packages = set()

    def install_package(self, package_name: str) -> bool:
        """Instaluje pakiet jeśli nie jest zainstalowany lub dostępny."""
        if package_name in self.installed_packages:
            return True
        if is_stdlib_module(package_name):
            logger.info(f"Pominięto instalację pakietu standardowej biblioteki: {package_name}")
            self.installed_packages.add(package_name)
            return True
        module_name = dist_to_module(package_name)
        if is_module_available(module_name):
            logger.info(
                f"Pominięto instalację dostępnego pakietu: {package_name} ({module_name})"
            )
            self.installed_packages.add(package_name)
            return True
        try:
            logger.info(f"Instalowanie pakietu: {package_name}")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.installed_packages.add(package_name)
            logger.success(f"Pakiet {package_name} zainstalowany pomyślnie")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd instalacji pakietu {package_name}: {e}")
            return False

    def import_module(self, module_name: str):
        """Importuje moduł po ewentualnej instalacji."""
        try:
            return importlib.import_module(module_name)
        except ImportError:
            dist_name = module_to_dist(module_name)
            if self.install_package(dist_name):
                return importlib.import_module(module_name)
            raise


class ProcessorEngine:
    """Główny silnik procesora danych."""

    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        self.package_manager = DynamicPackageManager()
        
        # Get output directory from environment or use default
        output_dir = os.getenv("OUTPUT_DIR")
        if not output_dir:
            # Default to ./output in current working directory
            self.output_dir = Path.cwd() / "output"
        else:
            self.output_dir = Path(output_dir)
            
        # Create directory and parents if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_natural_request(self, request: str) -> Dict[str, Any]:
        """Przetwarza żądanie w języku naturalnym."""

        # 1. Przeanalizuj żądanie za pomocą LLM
        logger.info("Analizowanie żądania za pomocą LLM...")
        processor_config = self.llm_analyzer.analyze_request(request)

        # 2. Zainstaluj wymagane biblioteki
        logger.info("Instalowanie wymaganych bibliotek...")
        for dependency in processor_config.dependencies:
            self.package_manager.install_package(dependency)

        # 3. Wykonaj kod procesora
        logger.info("Wykonywanie procesora danych...")
        return self._execute_processor(processor_config)

    def _execute_processor(self, config: ProcessorConfig) -> Dict[str, Any]:
        """Wykonuje procesor danych na podstawie konfiguracji."""

        # Prepare execution context with all necessary modules and variables
        execution_context = {
            'os': os,
            'sys': sys,
            'pd': pd,
            'Path': Path,
            'logger': logger,
            'output_dir': str(self.output_dir),
            'package_manager': self.package_manager,
            'result': None,  # Will store the final result
        }

        # Add environment variables to context
        for key, value in os.environ.items():
            if key.startswith(('IMAP_', 'EMAIL_', 'SMTP_')):
                execution_context[key.lower()] = value

        # Wykonaj kod
        try:
            exec(config.code_template, execution_context)

            # Pobierz wynik z kontekstu
            result = execution_context.get('result', {'status': 'completed'})
            return result

        except Exception as e:
            logger.error(f"Błąd wykonania procesora: {e}")
            raise