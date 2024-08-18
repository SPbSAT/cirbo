"""Subpackage contains methods that help store and read a collection (database) of
circuits, and especially helps to work with provided database of (nearly) optimal small
circuits."""

from .db import CircuitsDatabase

__all__ = [
    'CircuitsDatabase',
]
