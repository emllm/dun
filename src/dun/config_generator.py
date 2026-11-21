"""Natural-language YAML Task Configuration generator for Dun."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger

from dun.routing import keyword_hits, task_router

_WORD_RE = re.compile(r"\b\w+\b")
_STOP_WORDS = frozenset({"jest", "będzie", "oraz", "które", "wszystkie", "danych"})

_REQUIREMENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"pobierz.*email|pobierz.*wiadomoś|download.*email"), "download_emails"),
    (re.compile(r"zapisz.*folder|organizuj.*folder|monthly folders"), "organize_files"),
    (re.compile(r"połącz.*imap|łącz.*imap"), "connect_imap"),
    (re.compile(r"filtruj.*dat|sortuj.*dat"), "filter_by_date"),
    (re.compile(r"utwórz.*raport|generuj.*raport|generate.*report"), "generate_report"),
    (re.compile(r"analizuj.*treść|analyze"), "analyze_content"),
    (re.compile(r"wyślij.*email|send.*email"), "send_email"),
    (re.compile(r"pobierz.*załącznik|extract attachments"), "download_attachments"),
)

_ADDITIONAL_PACKAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pandas": ("csv", "excel", "xlsx", "dataframe", "tabela", "arkusz"),
    "requests": ("http", "https", "api", "rest", "endpoint", "strona", "website"),
    "beautifulsoup4": ("html", "scraping", "scrape", "parsuj"),
    "sqlalchemy": ("sql", "database", "baza", "bazie", "postgres", "postgresql", "mysql"),
    "matplotlib": ("wykres", "chart", "charts", "plot"),
    "numpy": ("obliczenia", "matematyka", "array", "statystyki", "statistics"),
    "pillow": ("pil", "image", "images", "obraz", "obrazy", "zdjęcie", "zdjęcia", "jpg", "png"),
}

_ADDITIONAL_ENV_KEYWORDS: dict[str, tuple[str, ...]] = {
    "API_KEY": ("api", "token", "oauth"),
    "DATABASE_URL": ("database", "baza", "bazie", "sql", "postgresql", "postgres", "mysql", "sqlite"),
    "WEBHOOK_URL": ("webhook", "callback"),
    "PROXY_URL": ("proxy",),
    "TIMEOUT": ("timeout",),
}


def _dedupe_extend(target: list[str], extra: list[str], exclude: set[str]) -> None:
    for item in extra:
        if item not in exclude and item not in target:
            target.append(item)


def _canonical_digest(config: Dict[str, Any]) -> str:
    payload = copy.deepcopy(config)
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("created", None)
        metadata.pop("id", None)
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TaskConfigGenerator:
    """Generate deterministic ``dun.io/v1`` YAML task configurations from NLP."""

    def __init__(self, llm_analyzer: Any = None) -> None:
        self.llm_analyzer = llm_analyzer
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """Load clean immutable base templates for supported task types."""
        return {
            "email_processing": {
                "runtime": {
                    "python_packages": {
                        "required": ["imaplib2", "email-validator", "python-dotenv", "loguru"],
                        "optional": ["beautifulsoup4", "chardet"],
                    },
                    "environment": {
                        "required": ["IMAP_SERVER", "IMAP_USERNAME", "IMAP_PASSWORD"],
                        "optional": ["IMAP_PORT", "IMAP_USE_SSL", "OUTPUT_DIR"],
                    },
                },
                "services": {
                    "dependencies": [
                        {
                            "name": "imap-server",
                            "type": "imap",
                            "required": True,
                            "connection": {
                                "host": "${IMAP_SERVER}",
                                "port": "${IMAP_PORT:-143}",
                                "ssl": "${IMAP_USE_SSL:-false}",
                            },
                            "health_check": {"type": "tcp_connect", "timeout": "10s"},
                        }
                    ],
                    "managed_services": [],
                },
            },
            "database_processing": {
                "runtime": {
                    "python_packages": {
                        "required": ["sqlalchemy", "pandas", "python-dotenv"],
                        "optional": ["psycopg2-binary", "pymysql"],
                    },
                    "environment": {
                        "required": ["DATABASE_URL"],
                        "optional": ["DB_POOL_SIZE", "DB_TIMEOUT"],
                    },
                },
                "services": {
                    "dependencies": [
                        {
                            "name": "database",
                            "type": "sql",
                            "required": True,
                            "connection": {"url": "${DATABASE_URL}"},
                            "health_check": {
                                "type": "sql_query",
                                "query": "SELECT 1",
                                "timeout": "30s",
                            },
                        }
                    ],
                    "managed_services": [],
                },
            },
            "file_processing": {
                "runtime": {
                    "python_packages": {
                        "required": ["pandas", "openpyxl", "python-dotenv"],
                        "optional": ["xlrd", "chardet", "python-magic"],
                    },
                    "environment": {
                        "required": ["INPUT_DIR", "OUTPUT_DIR"],
                        "optional": ["FILE_PATTERN", "ENCODING"],
                    },
                }
            },
            "web_scraping": {
                "runtime": {
                    "python_packages": {
                        "required": ["requests", "beautifulsoup4", "python-dotenv"],
                        "optional": ["selenium", "lxml", "html5lib"],
                    },
                    "environment": {
                        "required": ["TARGET_URL"],
                        "optional": ["USER_AGENT", "REQUEST_DELAY", "PROXY_URL"],
                    },
                }
            },
            "api_processing": {
                "runtime": {
                    "python_packages": {
                        "required": ["requests", "python-dotenv"],
                        "optional": ["aiohttp"],
                    },
                    "environment": {
                        "required": ["API_BASE_URL"],
                        "optional": ["API_KEY", "TIMEOUT", "OUTPUT_DIR"],
                    },
                }
            },
            "data_analysis": {
                "runtime": {
                    "python_packages": {
                        "required": ["pandas", "numpy", "python-dotenv"],
                        "optional": ["matplotlib", "openpyxl"],
                    },
                    "environment": {
                        "required": ["INPUT_DIR", "OUTPUT_DIR"],
                        "optional": ["LOG_LEVEL"],
                    },
                }
            },
        }

    def generate_config_from_nlp(self, natural_request: str) -> Dict[str, Any]:
        """Generate a complete ``dun.io/v1`` task configuration dictionary."""
        logger.info("Analizowanie żądania w celu wygenerowania konfiguracji...")
        task_type = self._detect_task_type(natural_request)
        requirements = self._extract_requirements(natural_request)
        packages = self._detect_required_packages(natural_request, task_type)
        env_vars = self._detect_environment_variables(natural_request, task_type)
        services = self._detect_services(natural_request, task_type)
        return self._build_base_config(
            natural_request,
            task_type,
            requirements,
            packages,
            env_vars,
            services,
        )

    def _detect_task_type(self, request: str) -> str:
        """Classify natural request via offline BM25-lite lexical router."""
        return task_router().best(request, default="generic_processing") or "generic_processing"

    def _extract_requirements(self, request: str) -> List[str]:
        """Extract structured requirement labels using compiled regexes."""
        request_lower = request.lower()
        found = [label for pattern, label in _REQUIREMENT_PATTERNS if pattern.search(request_lower)]
        return found if found else ["process_data"]

    def _detect_required_packages(self, request: str, task_type: str) -> Dict[str, List[str]]:
        """Resolve required and optional PyPI distributions without alias mutation."""
        base = self.templates.get(task_type, {})
        raw_pkgs = base.get(
            "runtime",
            {},
        ).get("python_packages", {"required": ["python-dotenv", "loguru"], "optional": []})
        packages: Dict[str, List[str]] = copy.deepcopy(raw_pkgs)
        hits = keyword_hits(request, _ADDITIONAL_PACKAGE_KEYWORDS)
        _dedupe_extend(packages["optional"], hits, set(packages["required"]))
        return packages

    def _detect_environment_variables(self, request: str, task_type: str) -> Dict[str, List[str]]:
        """Resolve required and optional environment variables without substring traps."""
        base = self.templates.get(task_type, {})
        raw_env = base.get(
            "runtime",
            {},
        ).get("environment", {"required": [], "optional": ["OUTPUT_DIR"]})
        env_vars: Dict[str, List[str]] = copy.deepcopy(raw_env)
        hits = keyword_hits(request, _ADDITIONAL_ENV_KEYWORDS)
        _dedupe_extend(env_vars["optional"], hits, set(env_vars["required"]))
        return env_vars

    def _detect_services(self, request: str, task_type: str) -> Dict[str, Any]:
        """Detect service dependencies using token matching on template copies."""
        base = self.templates.get(task_type, {})
        raw_services = base.get("services", {"dependencies": [], "managed_services": []})
        services: Dict[str, Any] = copy.deepcopy(raw_services)
        service_hits = set(
            keyword_hits(
                request,
                {
                    "redis": ("redis",),
                    "elasticsearch": ("elasticsearch", "elastic"),
                },
            )
        )
        if "redis" in service_hits:
            services["dependencies"].append(
                {
                    "name": "redis",
                    "type": "cache",
                    "required": False,
                    "connection": {"host": "${REDIS_HOST:-localhost}", "port": "6379"},
                    "health_check": {"type": "tcp_connect", "timeout": "5s"},
                }
            )
        if "elasticsearch" in service_hits:
            services["dependencies"].append(
                {
                    "name": "elasticsearch",
                    "type": "search",
                    "required": False,
                    "connection": {"url": "${ELASTICSEARCH_URL:-http://localhost:9200}"},
                    "health_check": {
                        "type": "http_get",
                        "endpoint": "/_cluster/health",
                        "timeout": "10s",
                    },
                }
            )
        return services

    def _build_base_config(
        self,
        request: str,
        task_type: str,
        requirements: List[str],
        packages: Dict[str, List[str]],
        env_vars: Dict[str, List[str]],
        services: Dict[str, Any],
    ) -> Dict[str, Any]:
        task_name = self._generate_task_name(request, task_type)
        created_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        description = f"{request[:200]}..." if len(request) > 200 else request

        config: Dict[str, Any] = {
            "apiVersion": "dun.io/v1",
            "kind": "TaskConfiguration",
            "metadata": {
                "name": task_name,
                "description": description,
                "version": "1.0",
                "created": created_utc,
                "tags": [task_type, "auto-generated"],
            },
            "task": {
                "natural_language": request,
                "requirements": requirements,
                "expected_output": {"type": "file_structure", "pattern": "output/**/*"},
            },
            "runtime": {
                "type": "docker",
                "base_image": "python:3.11-slim",
                "python_packages": packages,
                "environment": env_vars,
            },
            "services": services,
            "validation": {
                "pre_execution": [
                    {
                        "type": "service_connectivity",
                        "services": [
                            dep["name"]
                            for dep in services.get("dependencies", [])
                            if dep.get("required")
                        ],
                    },
                    {"type": "environment_variables", "required": env_vars.get("required", [])},
                    {
                        "type": "file_permissions",
                        "paths": ["${OUTPUT_DIR:-./output}"],
                        "permissions": ["read", "write"],
                    },
                    {"type": "disk_space", "minimum": "100MB", "path": "${OUTPUT_DIR:-./output}"},
                ],
                "post_execution": [
                    {
                        "type": "output_verification",
                        "expected_files": {"pattern": "output/**/*", "minimum_count": 1},
                    },
                    {"type": "directory_structure", "expected": ["output"]},
                ],
            },
            "monitoring": {
                "logs": {
                    "level": "${LOG_LEVEL:-INFO}",
                    "destinations": [
                        {"type": "file", "path": "logs/task-execution.log"},
                        {"type": "stdout", "format": "json"},
                    ],
                },
                "metrics": [
                    {
                        "name": "execution_time",
                        "type": "histogram",
                        "description": "Czas wykonania zadania",
                    },
                    {
                        "name": "errors_count",
                        "type": "counter",
                        "description": "Liczba błędów",
                    },
                ],
            },
            "security": {
                "network": {
                    "allowed_outbound": ["*:80", "*:443"],
                    "blocked_outbound": ["*:22", "*:3389"],
                },
                "filesystem": {
                    "read_only_paths": ["/etc", "/usr"],
                    "writable_paths": ["${OUTPUT_DIR:-./output}", "/tmp", "logs/"],
                },
            },
            "pipeline": {
                "stages": [
                    {
                        "name": "validation",
                        "type": "validation",
                        "config": {"run_pre_execution_checks": True},
                    },
                    {
                        "name": "environment_setup",
                        "type": "setup",
                        "config": {"install_packages": True, "create_directories": True},
                    },
                    {
                        "name": "llm_analysis",
                        "type": "llm_processing",
                        "config": {"analyze_natural_language": True, "generate_code": True},
                    },
                    {
                        "name": "task_execution",
                        "type": "execution",
                        "config": {"run_generated_code": True, "capture_output": True},
                    },
                    {
                        "name": "post_validation",
                        "type": "validation",
                        "config": {"run_post_execution_checks": True},
                    },
                    {
                        "name": "cleanup",
                        "type": "cleanup",
                        "config": {"remove_temp_files": True},
                    },
                ]
            },
            "environments": {
                "development": {
                    "managed_services_enabled": True,
                    "log_level": "DEBUG",
                    "validation_strict": False,
                },
                "testing": {
                    "managed_services_enabled": True,
                    "log_level": "INFO",
                    "validation_strict": True,
                },
                "production": {
                    "managed_services_enabled": False,
                    "log_level": "WARNING",
                    "validation_strict": True,
                    "security_enhanced": True,
                },
            },
        }
        config["metadata"]["id"] = f"dun:{_canonical_digest(config)}"
        return config

    def _generate_task_name(self, request: str, task_type: str) -> str:
        words = _WORD_RE.findall(request.lower())
        key_words = [w for w in words if len(w) > 3 and w not in _STOP_WORDS][:3]
        stem = "-".join(key_words) if key_words else task_type.replace("_", "-")
        return f"{stem}-processor"

    def save_config_to_file(
        self,
        config: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> str:
        """Write generated YAML config to ``filename`` or ``configs/<task_name>.yaml``."""
        target = Path(filename) if filename else Path("configs") / f"{config['metadata']['name']}.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            yaml.dump(config, handle, default_flow_style=False, allow_unicode=True, indent=2)
        logger.success(f"Konfiguracja zapisana do: {target}")
        return str(target)


ConfigGenerator = TaskConfigGenerator
