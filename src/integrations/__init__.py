"""
Integraciones con servicios externos
"""

from .alegra.client import AlegraClient
from .alegra.reports import AlegraReports
from .nanobot.client import NanobotClient

__all__ = ['AlegraClient', 'AlegraReports', 'NanobotClient']

