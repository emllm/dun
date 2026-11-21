"""Unit tests for consolidated dune/uritime/bottlenecks functionality in dun."""
from __future__ import annotations

import builtins
import importlib
import importlib.util
import json
import subprocess
from unittest.mock import patch

import pytest

import dun
from dun.__main__ import main as cli_main
from dun.config_generator import ConfigGenerator, TaskConfigGenerator
from dun.dynamic_processor_mapper import DynamicProcessorMapper
from dun.env_definitions import ALLOWED_URL_SCHEMES, load_env_definitions
from dun.interactive_mapper import InteractiveMapper
from dun.library_catalog import LibraryInterface
from dun.packages import dist_to_module, is_module_available, module_to_dist, parse_requirement_name
from dun.processor_engine import DynamicPackageManager, ProcessorConfig, ProcessorEngine
from dun.routing import library_router, task_router
from dun.smart_env_manager import SmartEnvManager
from dun.task_validator import TaskValidator, ValidationResult


def test_public_exports_and_metadata() -> None:
    """Verify dun 0.2.0 metadata and consolidated exports."""
    assert dun.__version__ == "0.2.0"
    assert dun.__license__ == "Apache-2.0"
    for name in (
        "TaskConfigGenerator",
        "TaskValidator",
        "ValidationResult",
        "InteractiveMapper",
        "SmartEnvManager",
        "task_router",
        "library_router",
        "dist_to_module",
        "module_to_dist",
        "is_module_available",
    ):
        assert hasattr(dun, name)
        assert name in dun.__all__


def test_lexical_routing_inflection_and_anti_traps() -> None:
    """Verify PL+EN inflection matching and absence of substring false positives."""
    assert task_router().best("Pobierz wiadomości ze skrzynki Gmail") == "email_processing"
    assert task_router().best("Zapisz wyniki do pliku") == "file_processing"
    assert task_router().best("Rapidly save the output", default="generic") == "generic"
    assert library_router().rank("Zapisz konfigurację aplikacji") == []

    libs = library_router().rank("Zbierz linki ze strony www i zapisz je do pliku CSV")
    assert libs[0][0] == "requests"


def test_packages_canonical_resolution() -> None:
    """Verify distribution <-> module mappings and PEP 508 name parsing."""
    assert parse_requirement_name("beautifulsoup4>=4.12.0") == "beautifulsoup4"
    assert parse_requirement_name("uvicorn[standard]==0.24.0") == "uvicorn"
    assert dist_to_module("beautifulsoup4") == "bs4"
    assert dist_to_module("PyYAML>=6.0.1") == "yaml"
    assert dist_to_module("python-dotenv") == "dotenv"
    assert dist_to_module("Pillow") == "PIL"
    assert module_to_dist("bs4") == "beautifulsoup4"
    assert module_to_dist("yaml") == "PyYAML"
    assert module_to_dist("nonexistent_module") == "nonexistent_module"
    assert is_module_available("json") is True
    assert is_module_available("nonexistent_package_xyz_999") is False


def test_config_generator_determinism_canonical_id_and_no_aliasing(tmp_path) -> None:
    """Verify TaskConfigGenerator determinism, UTC timestamp, canonical ID, and isolation."""
    assert ConfigGenerator is TaskConfigGenerator
    gen = TaskConfigGenerator()
    cfg1 = gen.generate_config_from_nlp("Pobierz wiadomości IMAP i zapisz raport")
    cfg2 = gen.generate_config_from_nlp("Pobierz wiadomości IMAP i zapisz raport")
    cfg_fresh = TaskConfigGenerator().generate_config_from_nlp(
        "Pobierz wiadomości IMAP i zapisz raport"
    )

    assert cfg1["apiVersion"] == "dun.io/v1"
    assert cfg1["metadata"]["created"].endswith("Z")
    assert cfg1["metadata"]["id"].startswith("dun:")
    assert cfg1["metadata"]["id"] == cfg2["metadata"]["id"]
    assert cfg1["metadata"]["id"] == cfg_fresh["metadata"]["id"]
    assert "API_KEY" not in cfg1["runtime"]["environment"]["optional"]

    # Mutating one result must not corrupt shared generator templates.
    cfg1["runtime"]["python_packages"]["optional"].append("mutated-only-here")
    cfg3 = gen.generate_config_from_nlp("Pobierz wiadomości IMAP i zapisz raport")
    assert "mutated-only-here" not in cfg3["runtime"]["python_packages"]["optional"]

    saved = gen.save_config_to_file(cfg3, str(tmp_path / "task.yaml"))
    assert saved.endswith("task.yaml")


def test_task_validator_dist_resolution_and_validation_result(monkeypatch) -> None:
    """Verify Pydantic v2 TaskValidator resolves dist names via find_spec."""
    gen = TaskConfigGenerator()
    cfg = gen.generate_config_from_nlp("Połącz pliki CSV w folderze")
    cfg["runtime"]["python_packages"]["required"] = [
        "beautifulsoup4",
        "pyyaml",
        "python-dotenv",
    ]

    monkeypatch.setenv("INPUT_DIR", "/tmp")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp")

    attempted = []
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, package=None):
        if name in {"bs4", "yaml", "dotenv"}:
            attempted.append(name)
            return importlib.machinery.ModuleSpec(name, None)
        return real_find_spec(name, package)

    with patch.object(importlib.util, "find_spec", side_effect=fake_find_spec):
        validator = TaskValidator()
        res = validator.validate(cfg)

    assert isinstance(res, ValidationResult)
    assert res.valid is True
    assert set(["bs4", "yaml", "dotenv"]).issubset(set(attempted))


def test_package_manager_zero_duplicate_or_stdlib_pip_calls(tmp_path, monkeypatch) -> None:
    """Verify preinstalled dists and stdlib modules never invoke pip repeatedly."""
    fake_installed = set()
    pip_calls = []
    real_find_spec = importlib.util.find_spec
    real_import = importlib.import_module
    real_builtins_import = builtins.__import__

    def fake_find_spec(name: str, package=None):
        if name in {"bs4", "yaml"}:
            return (
                importlib.machinery.ModuleSpec(name, None)
                if name in fake_installed
                else None
            )
        return real_find_spec(name, package)

    def fake_import_module(name: str, package=None):
        if name == "bs4":
            if "bs4" in fake_installed:
                return object()
            raise ModuleNotFoundError(name)
        return real_import(name, package)

    def fake_check_call(cmd, **_kwargs):
        pkg = cmd[-1]
        pip_calls.append(pkg)
        fake_installed.add(dist_to_module(pkg))
        return 0

    class DummyAnalyzer:
        def analyze_request(self, _request: str) -> ProcessorConfig:
            return ProcessorConfig(
                name="bench",
                description="bench",
                dependencies=["beautifulsoup4", "pyyaml", "imaplib", "email"],
                parameters={},
                code_template="result = {'ok': True}",
            )

    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    with (
        patch.object(importlib.util, "find_spec", side_effect=fake_find_spec),
        patch.object(importlib, "import_module", side_effect=fake_import_module),
        patch.object(builtins, "__import__", real_builtins_import),
        patch.object(subprocess, "check_call", side_effect=fake_check_call),
    ):
        for _ in range(10):
            ProcessorEngine(DummyAnalyzer()).process_natural_request("test")

        mod = DynamicPackageManager().import_module("bs4")
        assert mod is not None

    assert pip_calls == ["beautifulsoup4", "pyyaml"]


def test_interactive_mapper_and_dun_dune_env_prefixes(monkeypatch, tmp_path) -> None:
    """Verify InteractiveMapper lexical ranking and DUN_/DUNE_ env resolution."""
    mapper = InteractiveMapper()
    libs = mapper.analyze_task_and_map_libraries("Przeanalizuj sprzedaż CSV i wykresy")
    assert any(lib.package == "pandas" for lib in libs)

    lib_iface = LibraryInterface(
        name="HTTP Client",
        package="requests",
        main_function="get",
        required_params=["token"],
        optional_params=[],
        param_types={"token": "str"},
        param_descriptions={},
        examples=[],
    )
    monkeypatch.setenv("DUN_TOKEN", "secret-dun-token")
    with patch.object(mapper, "_ask_yes_no", return_value=True):
        val = mapper._collect_single_parameter("token", lib_iface, required=True)
    assert val == "secret-dun-token"

    monkeypatch.delenv("DUN_TOKEN")
    monkeypatch.setenv("DUNE_TOKEN", "legacy-dune-token")
    with patch.object(mapper, "_ask_yes_no", return_value=True):
        val_legacy = mapper._collect_single_parameter("token", lib_iface, required=True)
    assert val_legacy == "legacy-dune-token"

    env_target = tmp_path / ".env"
    mapper.save_parameters_to_env({"HTTP Client": {"token": "abc"}}, str(env_target))
    assert "DUN_TOKEN=abc" in env_target.read_text(encoding="utf-8")


def test_smart_env_manager_accepts_database_and_http_urls() -> None:
    """Verify SmartEnvManager validates PostgreSQL/MySQL/SQLite/Redis and HTTP URLs."""
    mgr = SmartEnvManager()
    defs = load_env_definitions()
    assert "postgresql://" in ALLOWED_URL_SCHEMES
    assert mgr._validate_env_value(
        "postgresql://user:pass@localhost:5432/dbname",
        defs["DATABASE_URL"],
    )
    assert mgr._validate_env_value("sqlite:///data.db", defs["DATABASE_URL"])
    assert mgr._validate_env_value("https://api.example.com", defs["API_BASE_URL"])
    assert not mgr._validate_env_value("not-a-valid-url", defs["DATABASE_URL"])


def test_dynamic_processor_mapper_avoids_substring_traps() -> None:
    """Verify DynamicProcessorMapper uses lexical token routing safely."""
    mapper = DynamicProcessorMapper()
    assert mapper.detect_library("Zapisz wyniki do pliku") is None
    assert mapper.detect_library("Połącz pliki CSV w pandas") == "pandas"
    assert mapper.detect_library("Sprawdź wiadomości ze skrzynki IMAP") == "imaplib"
    assert mapper.detect_library("Wykonaj zapytanie SQL w bazie sqlite") == "sqlite3"


def test_cli_route_config_and_validate_subcommands(capsys, tmp_path, monkeypatch) -> None:
    """Verify dun CLI route, config, and validate subcommands."""
    with pytest.raises(SystemExit) as exc:
        cli_main(["route", "Pobierz wiadomości ze skrzynki IMAP"])
    assert exc.value.code == 0
    route_out = json.loads(capsys.readouterr().out)
    assert route_out["task_type"] == "email_processing"
    assert route_out["libraries"][0] == "imaplib"

    cfg_path = tmp_path / "task.yaml"
    with pytest.raises(SystemExit) as exc:
        cli_main(["config", "Połącz pliki CSV", "--output", str(cfg_path)])
    assert exc.value.code == 0
    capsys.readouterr()
    assert cfg_path.exists()

    monkeypatch.setenv("INPUT_DIR", str(tmp_path))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        cli_main(["validate", str(cfg_path)])
    assert exc.value.code == 0
    val_out = json.loads(capsys.readouterr().out)
    assert val_out["valid"] is True
