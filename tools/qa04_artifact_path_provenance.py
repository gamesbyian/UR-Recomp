#!/usr/bin/env python3
"""Additional independent path-provenance guard for immutable hosted artifacts.

A symlinked parent does not invalidate externally SHA-pinned bytes, but must
not be silently treated as a canonical, direct evidence path in a handoff.
"""
from pathlib import Path

def assert_direct_regular_file(path: Path) -> Path:
    if not isinstance(path,Path):raise TypeError('expected pathlib.Path')
    if not path.is_file() or path.is_symlink():
        raise ValueError('artifact missing or symlinked')
    if path.absolute()!=path.resolve(strict=True):
        raise ValueError('artifact path contains redirected ancestor')
    return path
