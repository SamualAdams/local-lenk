"""Lenk project package (Django-like layout).

Exports the viewer app's main entry points for convenience.
"""

from .apps.viewer.app import FileViewer, main

__all__ = ["FileViewer", "main"]
