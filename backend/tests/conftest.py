"""Pytest configuration and environment fixtures for SchemeSaathi tests."""

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Pre-load embeddings and torch runtime on Windows before FAISS
try:
    import app.embeddings  # noqa: F401
    import faiss  # noqa: F401
except ImportError:
    pass
