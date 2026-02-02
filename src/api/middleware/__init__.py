"""
API middleware components.
"""

from .error_handlers import setup_error_handlers
from .cors import setup_cors

__all__ = ["setup_error_handlers", "setup_cors"]
