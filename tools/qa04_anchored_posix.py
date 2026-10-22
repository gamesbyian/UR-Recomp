"""POSIX-only descriptor-anchored evidence hash experiment, not Windows QA04 acceptance.

Refuses symbolic links at every directory component, hardlinked leaves, nonregular
files, and mutations visible in fstat. No path is reopened after preflight.
Windows needs equivalent native CreateFileW/reparse/FileIdInfo review.
"""
from __future__ import annotations
import hashlib
import os
import stat
from pathlib import Path


def sha256_anchored(root: Path, relative: str, expected_size: int) -> str:
    if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
        raise NotImplementedError('POSIX descriptor pilot only; Windows native handles required')
    if type(relative) is not str or not relative or '\\' in relative or '\x00' in relative:
        raise ValueError('invalid relative evidence path')
    parts = relative.split('/')
    if len(parts) > 6 or any(p in ('', '.', '..') for p in parts):
        raise ValueError('relative path alias')
    if type(expected_size) is not int or not 0 < expected_size <= 32*1024*1024:
        raise ValueError('invalid expected attachment size')
    absolute = os.path.abspath(os.fspath(root))
    if not absolute.startswith('/'):
        raise ValueError('absolute root required')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors = []
    try:
        current = os.open('/', flags)
        descriptors.append(current)
        for component in [x for x in absolute.split('/') if x] + parts[:-1]:
            current = os.open(component, flags, dir_fd=current)
            descriptors.append(current)
        leaf_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(parts[-1], leaf_flags, dir_fd=current)
        descriptors.append(fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != expected_size:
            raise ValueError('nonregular, hardlinked or unexpected-size evidence')
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, 1024*1024)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_size:
                raise ValueError('evidence grew during read')
            digest.update(chunk)
        after = os.fstat(fd)
        fields = ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_nlink')
        if total != expected_size or any(getattr(before,f) != getattr(after,f) for f in fields):
            raise ValueError('attachment changed during anchored read')
        return digest.hexdigest()
    finally:
        for fd in reversed(descriptors):
            os.close(fd)
