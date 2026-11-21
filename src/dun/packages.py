"""Canonical PyPI distribution to import-module resolution helpers."""
from __future__ import annotations

import importlib.util
import re
import sys

__all__ = [
    "DIST_TO_MODULE",
    "MODULE_TO_DIST",
    "parse_requirement_name",
    "dist_to_module",
    "module_to_dist",
    "is_stdlib_module",
    "is_module_available",
]

DIST_TO_MODULE: dict[str, str] = {
    "beautifulsoup4": "bs4",
    "python-dotenv": "dotenv",
    "pillow": "PIL",
    "pyyaml": "yaml",
    "python-dateutil": "dateutil",
    "python-magic": "magic",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
    "opencv-python-headless": "cv2",
    "pydantic-settings": "pydantic_settings",
    "email-validator": "email_validator",
    "psycopg2-binary": "psycopg2",
    "mysql-connector-python": "mysql",
    "imaplib2": "imaplib2",
}

MODULE_TO_DIST: dict[str, str] = {
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "pil": "Pillow",
    "yaml": "PyYAML",
    "dateutil": "python-dateutil",
    "magic": "python-magic",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "pydantic_settings": "pydantic-settings",
    "email_validator": "email-validator",
    "psycopg2": "psycopg2-binary",
}

_REQ_SPLIT_RE = re.compile(r"[=<>!~;\s\[]")


def parse_requirement_name(requirement: str) -> str:
    """Strip extras and version constraints from a PEP 508 requirement string."""
    cleaned = requirement.strip()
    if not cleaned:
        return ""
    return _REQ_SPLIT_RE.split(cleaned, maxsplit=1)[0].strip()


def dist_to_module(dist_or_requirement: str) -> str:
    """Map a PyPI distribution name/requirement to its importable Python module."""
    name = parse_requirement_name(dist_or_requirement)
    if not name:
        return ""
    normalized = name.lower().replace("_", "-")
    if normalized in DIST_TO_MODULE:
        return DIST_TO_MODULE[normalized]
    lowered = name.lower()
    if lowered in DIST_TO_MODULE:
        return DIST_TO_MODULE[lowered]
    return name.replace("-", "_")


def module_to_dist(module_name: str) -> str:
    """Map an importable Python module name to its PyPI distribution name."""
    top = module_name.strip().split(".")[0]
    if not top:
        return ""
    if top in MODULE_TO_DIST:
        return MODULE_TO_DIST[top]
    lowered = top.lower()
    if lowered in MODULE_TO_DIST:
        return MODULE_TO_DIST[lowered]
    return top


def is_stdlib_module(name: str) -> bool:
    """Return True when ``name`` (or its mapped top-level module) is in Python stdlib."""
    stdlib_names = getattr(sys, "stdlib_module_names", frozenset())
    top = parse_requirement_name(name).split(".")[0]
    mapped = dist_to_module(name).split(".")[0]
    return top in stdlib_names or mapped in stdlib_names


def is_module_available(module_or_dist: str) -> bool:
    """Return True when a stdlib module or installed importable distribution exists."""
    top = dist_to_module(module_or_dist).split(".")[0]
    if not top:
        return False
    if is_stdlib_module(top):
        return True
    try:
        return importlib.util.find_spec(top) is not None
    except (ImportError, ValueError, AttributeError):
        return False
