# List of Python standard library modules (partial, most common for data/workflow)
# This can be extended or replaced with sys.stdlib_module_names in Python 3.10+
PYTHON_STDLIB = set([
    'abc', 'argparse', 'array', 'asyncio', 'base64', 'binascii', 'calendar', 'collections', 'concurrent',
    'contextlib', 'copy', 'csv', 'ctypes', 'datetime', 'decimal', 'difflib', 'dis', 'email', 'enum',
    'functools', 'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac', 'imaplib',
    'importlib', 'inspect', 'io', 'itertools', 'json', 'logging', 'lzma', 'math', 'multiprocessing',
    'os', 'pathlib', 'pickle', 'platform', 'plistlib', 'queue', 'random', 're', 'sched', 'secrets',
    'shutil', 'signal', 'site', 'smtplib', 'socket', 'sqlite3', 'ssl', 'stat', 'statistics', 'string',
    'struct', 'subprocess', 'sys', 'tempfile', 'textwrap', 'threading', 'time', 'timeit', 'traceback',
    'types', 'typing', 'unicodedata', 'uuid', 'warnings', 'weakref', 'xml', 'zipfile',
])

def is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    return module_name.split('.')[0] in PYTHON_STDLIB
