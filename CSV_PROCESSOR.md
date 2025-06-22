# CSV Processing in Dun - Technical Documentation

## Overview
This document explains how the CSV processing functionality works in the Dun project, including the flow of execution, key components, and logging details.

## Table of Contents
1. [Architecture](#architecture)
2. [Execution Flow](#execution-flow)
3. [Key Components](#key-components)
4. [Logging](#logging)
5. [Error Handling](#error-handling)
6. [Example Usage](#example-usage)
7. [Troubleshooting](#troubleshooting)

## Architecture

The CSV processing system consists of several key components:

1. **LLMAnalyzer** - Analyzes natural language requests and returns the appropriate processor configuration
2. **CSV Processor** - Handles the actual CSV file processing and merging
3. **ProcessorEngine** - Executes the processor with the given configuration
4. **Dynamic Package Manager** - Installs required Python packages on-demand

## Execution Flow

1. **Request Analysis**
   - User submits a natural language request (e.g., "Przeanalizuj pliki CSV")
   - `LLMAnalyzer.analyze_request()` processes the request
   - If LLM is unavailable, falls back to the default CSV processor

2. **Processor Initialization**
   - `_get_csv_processor()` creates a `ProcessorConfig` with:
     - Required dependencies (pandas)
     - Default parameters (input_dir, output_file)
     - The actual Python code to execute

3. **Dependency Installation**
   - `ProcessorEngine` checks for required packages
   - Missing packages are installed automatically via pip

4. **CSV Processing**
   - The processor code is executed in a sandboxed environment
   - It performs the following steps:
     1. Validates input directory and permissions
     2. Recursively searches for CSV files
     3. Reads and combines all found CSV files
     4. Saves the result to the output file
     5. Returns processing statistics

5. **Result Handling**
   - The combined CSV is saved to the specified location (or temporary directory)
   - Processing statistics are returned to the user

## Key Components

### LLMAnalyzer
- `analyze_request()`: Entry point for processing natural language requests
- `_get_csv_processor()`: Creates the CSV processor configuration
- `_get_default_imap_processor()`: Fallback processor selection

### ProcessorConfig
- `name`: Identifier for the processor
- `description`: Human-readable description
- `dependencies`: List of required Python packages
- `parameters`: Configuration parameters
- `code_template`: The actual Python code to execute

### ProcessorEngine
- `process_natural_request()`: Main entry point for processing requests
- `_execute_processor()`: Executes the processor code in a sandboxed environment
- `install_package()`: Handles dynamic package installation

## Logging

The system uses the following log levels:

- `DEBUG`: Detailed debug information
- `INFO`: General processing information
- `WARNING`: Non-critical issues
- `ERROR`: Processing errors
- `SUCCESS`: Successful operations

### Key Log Messages

#### CSV Processing
```
[INFO] Szukam plików CSV w katalogu: data/
[INFO] Znaleziono pliki CSV: ['data/sample1.csv']
[INFO] Przetwarzanie pliku: data/sample1.csv
[INFO]   Wczytano 2 wierszy i 3 kolumn
[INFO] Połączono dane: 2 wierszy i 3 kolumn
[SUCCESS] Zapisano połączony zbiór danych do: /tmp/.../combined.csv
```

#### Error Handling
```
[WARNING] Nie można zapisać w docelowej lokalizacji, używam katalogu tymczasowego
[ERROR] Błąd podczas przetwarzania pliku: [error details]
[ERROR] Nie udało się wczytać żadnych danych z plików CSV
```

## Error Handling

The system handles various error conditions:

1. **Missing Input Files**
   - Error if no CSV files found in input directory
   - Warning if input directory doesn't exist

2. **Permission Issues**
   - Falls back to temporary directory if output directory is not writable
   - Detailed error messages for permission-related failures

3. **Data Processing Errors**
   - Continues processing other files if one file fails
   - Provides detailed error messages for data-related issues

## Example Usage

### Basic Usage
```bash
poetry run dun "Przeanalizuj wszystkie pliki CSV w folderze data/"
```

### With Custom Parameters
```bash
export INPUT_DIR=my_data
export OUTPUT_FILE=results/combined.csv
poetry run dun "Przetwórz pliki CSV"
```

### Expected Output
```
[INFO] Processing CSV files in: data/
[INFO] Found 2 CSV files
[INFO] Processing file: data/file1.csv
[SUCCESS] Combined data saved to: /tmp/.../combined.csv

==================================================
Processed 2 CSV files
Total rows: 100
Columns: id, name, value
Output file: /tmp/.../combined.csv
==================================================
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure the output directory is writable
   - The system will fall back to a temporary directory if needed

2. **No CSV Files Found**
   - Verify the input directory exists and contains CSV files
   - Check file extensions (.csv or .CSV)

3. **Missing Dependencies**
   - The system should automatically install required packages
   - Check internet connection if installation fails

### Debugging

Enable debug logging for more detailed information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files
Check the application logs for detailed error messages and processing information.
