"""
Root conftest.py — ensures the project root is on sys.path before
any test or nested conftest.py is imported.

This is the most reliable cross-environment way to make `import backend`
work regardless of the directory pytest is invoked from (local, CI, etc.).
"""
import sys
from pathlib import Path

# Insert project root (directory containing this file) at front of sys.path.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
