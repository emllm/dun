"""Dun - Dynamiczny Procesor Danych.

Ten moduł zapewnia funkcjonalność do dynamicznego przetwarzania danych
z wykorzystaniem modeli językowych do interpretacji żądań w języku naturalnym.
"""

from .llm_analyzer import LLMAnalyzer
from .processor_engine import ProcessorEngine, ProcessorConfig, DynamicPackageManager

__all__ = [
    'LLMAnalyzer',
    'ProcessorEngine',
    'ProcessorConfig',
    'DynamicPackageManager'
]

__version__ = '0.1.1'