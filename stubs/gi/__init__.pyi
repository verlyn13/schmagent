"""Type stubs for PyGObject (gi module)"""
from typing import Any

def require_version(namespace: str, version: str) -> None:
    """Specify a version to be used for a namespace."""
    ...

# Import repository module to make it available as gi.repository
from . import repository
