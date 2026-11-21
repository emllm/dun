"""Smart environment variable detection and validation manager for Dun."""
from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from loguru import logger

from dun.env_definitions import ALLOWED_URL_SCHEMES, EnvVariable, load_env_definitions

_PATH_RE = re.compile(r"^[a-zA-Z0-9._/\\:-]+$")


class SmartEnvManager:
    """Detect, interactively collect, and validate environment variables."""

    def __init__(self) -> None:
        self.env_definitions: Dict[str, EnvVariable] = load_env_definitions()
        self.auto_detected: Dict[str, str] = {}
        self.user_provided: Dict[str, str] = {}

    def auto_detect_environment_variables(self, required_vars: List[str]) -> Dict[str, str]:
        """Attempt auto-detection for each variable name present in definitions."""
        logger.info("Automatyczne wykrywanie zmiennych środowiskowych...")
        detected: Dict[str, str] = {}
        for var_name in required_vars:
            env_var = self.env_definitions.get(var_name)
            if env_var is None:
                continue
            value = self._auto_detect_single_var(env_var)
            if value:
                detected[var_name] = value
                self.auto_detected[var_name] = value
                logger.success(f"Auto-wykryto {var_name}")
        return detected

    def _auto_detect_single_var(self, env_var: EnvVariable) -> Optional[str]:
        if not env_var.auto_detect_methods:
            return None
        for method in env_var.auto_detect_methods:
            try:
                value = self._run_detection_method(method, env_var)
                if value and self._validate_env_value(value, env_var):
                    return value
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                logger.debug(f"Błąd detekcji {method} dla {env_var.name}: {exc}")
        return None

    def _run_detection_method(self, method: str, env_var: EnvVariable) -> Optional[str]:
        dispatch = {
            "git_config": self._detect_from_git_config,
            "system_user": self._detect_from_system_user,
            "common_providers": self._detect_common_providers,
            "dns_lookup": self._detect_via_dns,
            "docker_compose": self._detect_from_docker_compose,
            "local_services": self._detect_local_services,
            "current_directory": self._detect_from_current_dir,
            "common_paths": self._detect_common_paths,
            "env_file": self._detect_from_env_files,
            "keyring": self._detect_from_keyring,
        }
        handler = dispatch.get(method)
        return handler(env_var) if handler else None

    def _detect_from_git_config(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.type != "email":
            return None
        try:
            result = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (subprocess.SubprocessError, OSError):
            return None
        return None

    def _detect_from_system_user(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.type != "email":
            return None
        username = os.getenv("USER") or os.getenv("USERNAME")
        if not username:
            return None
        for domain in ("gmail.com", "outlook.com", "company.com"):
            candidate = f"{username}@{domain}"
            if self._validate_env_value(candidate, env_var):
                return candidate
        return None

    def _detect_common_providers(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.name != "IMAP_SERVER":
            return None
        common_servers = (
            "imap.gmail.com",
            "imap.outlook.com",
            "imap.mail.yahoo.com",
            "localhost",
        )
        for server in common_servers:
            if self._test_server_connectivity(server, 993) or self._test_server_connectivity(
                server, 143
            ):
                return server
        return None

    def _detect_via_dns(self, _env_var: EnvVariable) -> Optional[str]:
        return None

    def _detect_from_docker_compose(self, _env_var: EnvVariable) -> Optional[str]:
        for compose_file in ("docker-compose.yml", "docker-compose.yaml"):
            path = Path(compose_file)
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as handle:
                    compose_data = yaml.safe_load(handle) or {}
                services = compose_data.get("services", {})
                for service_name, service_config in services.items():
                    image = str((service_config or {}).get("image", "")).lower()
                    name_lower = service_name.lower()
                    if "postgres" in name_lower or image.startswith("postgres"):
                        return "postgresql://user:password@localhost:5432/dbname"
                    if "mysql" in name_lower or image.startswith("mysql"):
                        return "mysql://user:password@localhost:3306/dbname"
            except (OSError, yaml.YAMLError, AttributeError):
                continue
        return None

    def _detect_local_services(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.name != "DATABASE_URL":
            return None
        db_ports = (
            (5432, "postgresql://user:password@localhost:5432/dbname"),
            (3306, "mysql://user:password@localhost:3306/dbname"),
            (6379, "redis://localhost:6379"),
        )
        for port, url in db_ports:
            if self._test_server_connectivity("localhost", port):
                return url
        return None

    def _detect_from_current_dir(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.type != "path":
            return None
        current_dir = Path.cwd()
        candidates_map = {
            "INPUT_DIR": ("input", "data", "src/data", "inputs"),
            "OUTPUT_DIR": ("output", "results", "out", "outputs"),
        }
        candidates = candidates_map.get(env_var.name)
        if candidates is None:
            return str(current_dir)
        for candidate in candidates:
            path = current_dir / candidate
            if path.exists():
                return str(path)
        if env_var.default_value:
            return str(current_dir / env_var.default_value.lstrip("./"))
        return None

    def _detect_common_paths(self, env_var: EnvVariable) -> Optional[str]:
        if env_var.type != "path":
            return None
        if platform.system() == "Windows":
            common_paths = (r"C:\Data", r"C:\Users\%USERNAME%\Documents")
        else:
            common_paths = ("/home/$USER/data", "/tmp", "/var/data")
        for template in common_paths:
            expanded = os.path.expandvars(template)
            if Path(expanded).exists():
                return expanded
        return None

    def _detect_from_env_files(self, env_var: EnvVariable) -> Optional[str]:
        for env_file in (".env", ".env.local", ".env.example"):
            path = Path(env_file)
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        stripped = line.strip()
                        if stripped.startswith(f"{env_var.name}="):
                            return stripped.split("=", 1)[1]
            except OSError:
                continue
        return None

    def _detect_from_keyring(self, env_var: EnvVariable) -> Optional[str]:
        try:
            import keyring
        except ImportError:
            return None
        try:
            return keyring.get_password("dun", env_var.name) or keyring.get_password(
                "dune", env_var.name
            )
        except (RuntimeError, OSError):
            return None

    def _test_server_connectivity(self, host: str, port: int, timeout: int = 3) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                return sock.connect_ex((host, port)) == 0
        except OSError:
            return False

    def _validate_env_value(self, value: str, env_var: EnvVariable) -> bool:
        if not value:
            return False
        if env_var.validation_pattern and not re.match(env_var.validation_pattern, value):
            return False
        if env_var.type == "int":
            try:
                int(value)
            except ValueError:
                return False
        elif env_var.type == "bool":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
                return False
        elif env_var.type == "path":
            if not _PATH_RE.match(value):
                return False
        elif env_var.type == "url":
            if not value.startswith(ALLOWED_URL_SCHEMES):
                return False
        return True

    def interactive_env_collection(
        self,
        required_vars: List[str],
        optional_vars: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Collect required and optional environment variables interactively."""
        auto_detected = self.auto_detect_environment_variables(required_vars)
        collected: Dict[str, str] = {}
        for var_name in required_vars:
            value = self._collect_single_env_var(
                var_name, auto_detected.get(var_name), required=True
            )
            if value:
                collected[var_name] = value
        if optional_vars:
            for var_name in optional_vars:
                if self._ask_yes_no(f"Skonfigurować {var_name}?"):
                    value = self._collect_single_env_var(
                        var_name, auto_detected.get(var_name), required=False
                    )
                    if value:
                        collected[var_name] = value
        return collected

    def _collect_single_env_var(
        self,
        var_name: str,
        auto_value: Optional[str],
        required: bool = True,
    ) -> Optional[str]:
        env_def = self.env_definitions.get(
            var_name,
            EnvVariable(var_name, f"Zmienna {var_name}", "str", required),
        )
        current_value = os.getenv(var_name) or auto_value
        prompt = f"{var_name} ({env_def.description})"
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                if not user_input:
                    if current_value:
                        return current_value
                    if env_def.default_value:
                        return env_def.default_value
                    if not required:
                        return None
                    print("Ta zmienna jest wymagana!")
                    continue
                if self._validate_env_value(user_input, env_def):
                    return user_input
                print(f"Nieprawidłowa wartość dla {env_def.type}")
            except KeyboardInterrupt:
                print("\nPrzerwano przez użytkownika")
                return None

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
            except KeyboardInterrupt:
                return False

    def save_to_env_file(self, env_vars: Dict[str, str], filename: str = ".env") -> None:
        """Merge and persist variables to ``filename``."""
        logger.info(f"Zapisywanie zmiennych do {filename}")
        path = Path(filename)
        existing_vars: Dict[str, str] = {}
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if "=" in stripped and not stripped.startswith("#"):
                        key, value = stripped.split("=", 1)
                        existing_vars[key] = value
        all_vars = {**existing_vars, **env_vars}
        with path.open("w", encoding="utf-8") as handle:
            handle.write("# Dun Environment Configuration\n\n")
            for key, value in sorted(all_vars.items()):
                handle.write(f"{key}={value}\n")
        logger.success(f"Zapisano {len(env_vars)} zmiennych do {filename}")

    def validate_environment(self, required_vars: List[str]) -> Tuple[bool, List[str]]:
        """Return ``(all_valid, missing_or_invalid_descriptions)`` for ``required_vars``."""
        missing_vars: List[str] = []
        for var_name in required_vars:
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(var_name)
                continue
            env_def = self.env_definitions.get(var_name)
            if env_def and not self._validate_env_value(value, env_def):
                missing_vars.append(f"{var_name} (nieprawidłowa wartość)")
        return len(missing_vars) == 0, missing_vars
