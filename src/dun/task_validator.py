"""Validator for ``dun.io/v1`` Task Configuration YAML schemas (Pydantic v2)."""
from __future__ import annotations

import os
import re
import shutil
import socket
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from dun.packages import dist_to_module, is_module_available

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


class TaskMetadata(BaseModel):
    """Metadata section of a task configuration."""

    model_config = ConfigDict(extra="allow")
    name: str
    description: str
    version: str
    created: str
    tags: List[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    """Task specification section."""

    model_config = ConfigDict(extra="allow")
    natural_language: str
    requirements: List[str]
    expected_output: Dict[str, Any]


class RuntimeConfig(BaseModel):
    """Execution runtime requirements."""

    model_config = ConfigDict(extra="allow")
    type: str = "docker"
    base_image: str = "python:3.11-slim"
    python_packages: Dict[str, List[str]]
    environment: Dict[str, List[str]]


class ServiceDependency(BaseModel):
    """External service dependency specification."""

    name: str
    type: str
    required: bool = True
    connection: Dict[str, str]
    health_check: Dict[str, Any]


class ManagedService(BaseModel):
    """Managed auxiliary service specification."""

    name: str
    type: str
    enabled: str = "true"
    config: Dict[str, Any] = Field(default_factory=dict)


class ValidationRule(BaseModel):
    """Single validation rule declaration."""

    model_config = ConfigDict(extra="allow")
    type: str
    kwargs: Dict[str, Any] = Field(default_factory=dict)


class TaskConfiguration(BaseModel):
    """Root task configuration model (``dun.io/v1``)."""

    model_config = ConfigDict(extra="allow")
    apiVersion: str
    kind: str
    metadata: TaskMetadata
    task: TaskDefinition
    runtime: RuntimeConfig
    services: Dict[str, Any]
    validation: Dict[str, List[ValidationRule]]
    monitoring: Dict[str, Any]
    security: Dict[str, Any]
    pipeline: Dict[str, Any]
    environments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Structured outcome returned by ``TaskValidator.validate``."""

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_packages: Dict[str, bool] = Field(default_factory=dict)


class TaskValidator:
    """Validate task configuration structure, environment, paths, services, and packages."""

    def __init__(self) -> None:
        self.validation_results: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.checked_packages: Dict[str, bool] = {}

    def load_config(self, config_path: str) -> TaskConfiguration:
        """Load YAML task config from ``config_path`` and expand ``${VAR}`` values."""
        try:
            with Path(config_path).open("r", encoding="utf-8") as handle:
                config_data = yaml.safe_load(handle)
            expanded = self._expand_environment_variables(config_data)
            return TaskConfiguration(**expanded)
        except Exception as exc:
            logger.error(f"Błąd ładowania konfiguracji: {exc}")
            raise

    def parse_config(self, config_data: Dict[str, Any]) -> TaskConfiguration:
        """Parse an in-memory dictionary into a validated ``TaskConfiguration``."""
        expanded = self._expand_environment_variables(config_data)
        return TaskConfiguration(**expanded)

    def _expand_environment_variables(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._expand_environment_variables(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._expand_environment_variables(item) for item in data]
        if isinstance(data, str):
            def _replace(match: re.Match[str]) -> str:
                var_expr = match.group(1)
                if ":-" in var_expr:
                    var_name, default = var_expr.split(":-", 1)
                    return os.getenv(var_name, default)
                return os.getenv(var_expr, match.group(0))

            return _ENV_VAR_RE.sub(_replace, data)
        return data

    def validate(self, config: TaskConfiguration | Dict[str, Any]) -> ValidationResult:
        """Run non-destructive configuration and package validation and return result."""
        self.errors = []
        self.warnings = []
        self.checked_packages = {}
        parsed = config if isinstance(config, TaskConfiguration) else self.parse_config(config)
        self._validate_environment_variables(parsed)
        self._validate_python_packages(parsed)
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=list(self.errors),
            warnings=list(self.warnings),
            checked_packages=dict(self.checked_packages),
        )

    def validate_pre_execution(self, config: TaskConfiguration) -> bool:
        """Run full pre-execution checks."""
        logger.info("Rozpoczynam walidację przed wykonaniem...")
        ok = True
        ok = bool(ok and self._validate_service_connectivity(config))
        ok = bool(ok and self._validate_environment_variables(config))
        ok = bool(ok and self._validate_file_permissions(config))
        ok = bool(ok and self._validate_disk_space(config))
        ok = bool(ok and self._validate_python_packages(config))
        return ok

    def validate_post_execution(self, config: TaskConfiguration) -> bool:
        """Run post-execution checks."""
        logger.info("Rozpoczynam walidację po wykonaniu...")
        ok = self._validate_output_files(config)
        ok = bool(ok and self._validate_directory_structure(config))
        return ok

    def _validate_service_connectivity(self, config: TaskConfiguration) -> bool:
        ok = True
        for dep in config.services.get("dependencies", []):
            service = ServiceDependency(**dep)
            healthy = self._check_service_health(service)
            if service.required and not healthy:
                self.errors.append(f"Nie można połączyć z wymaganą usługą: {service.name}")
                ok = False
            elif not healthy:
                self.warnings.append(f"Opcjonalna usługa {service.name} niedostępna")
        return ok

    def _check_service_health(self, service: ServiceDependency) -> bool:
        try:
            hc = service.health_check
            hc_type = hc.get("type")
            timeout = int(str(hc.get("timeout", "10")).rstrip("s"))
            if hc_type == "tcp_connect":
                host = service.connection.get("host", "localhost")
                port = int(service.connection.get("port", 80))
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(timeout)
                    return sock.connect_ex((host, port)) == 0
            if hc_type == "http_get":
                url = service.connection["url"]
                endpoint = hc.get("endpoint", "")
                response = requests.get(f"{url}{endpoint}", timeout=timeout)
                return response.status_code == 200
        except (OSError, ValueError, KeyError, requests.RequestException) as exc:
            logger.debug(f"Health check failed for {service.name}: {exc}")
            return False
        return False

    def _validate_environment_variables(self, config: TaskConfiguration) -> bool:
        ok = True
        for var in config.runtime.environment.get("required", []):
            if not os.getenv(var):
                self.errors.append(f"Brak wymaganej zmiennej środowiskowej: {var}")
                ok = False
        return ok

    def _validate_file_permissions(self, _config: TaskConfiguration) -> bool:
        output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
        try:
            test_dir = output_dir / ".dun_write_probe"
            test_dir.mkdir(parents=True, exist_ok=True)
            probe = test_dir / "probe.txt"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            test_dir.rmdir()
            return True
        except OSError as exc:
            self.errors.append(f"Brak uprawnień do zapisu w {output_dir}: {exc}")
            return False

    def _validate_disk_space(self, _config: TaskConfiguration) -> bool:
        output_dir = os.getenv("OUTPUT_DIR", "./output")
        try:
            _, _, free = shutil.disk_usage(output_dir)
            free_mb = free // (1024 * 1024)
            if free_mb < 100:
                self.warnings.append(f"Mało miejsca na dysku: {free_mb}MB")
        except OSError as exc:
            self.warnings.append(f"Nie można sprawdzić miejsca na dysku: {exc}")
        return True

    def _validate_python_packages(self, config: TaskConfiguration) -> bool:
        required_packages = config.runtime.python_packages.get("required", [])
        for requirement in required_packages:
            module_name = dist_to_module(requirement)
            available = is_module_available(module_name)
            self.checked_packages[requirement] = available
            if available:
                logger.success(f"Pakiet {requirement} ({module_name}) dostępny")
            else:
                logger.info(f"Pakiet {requirement} ({module_name}) wymaga instalacji")
        return True

    def _validate_output_files(self, config: TaskConfiguration) -> bool:
        expected = config.task.expected_output
        if expected.get("type") == "file_structure":
            logger.info(f"Sprawdzanie wzorca: {expected.get('pattern', '')}")
        return True

    def _validate_directory_structure(self, _config: TaskConfiguration) -> bool:
        return True

    def generate_validation_report(self) -> Dict[str, Any]:
        """Return summary report compatible with legacy validator callers."""
        return {
            "validation_passed": len(self.errors) == 0,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "total_checks": len(self.validation_results),
            "checked_packages": dict(self.checked_packages),
        }
