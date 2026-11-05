"""Atomically publish one report file without replacing any existing path.

A staged regular file is hard-linked into the destination name.  Unlike
Path.write_text or POSIX rename, link creation refuses an existing regular
file, symlink, or directory, including one created after staging began.
Filesystems without same-directory hardlink support fail closed.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile


def publish_text_once(destination: Path, content: str) -> None:
    """Publish a complete UTF-8 report at a new name or raise without clobbering.

    The parent must already exist. The temporary file is on the destination
    filesystem; the atomic link exposes only a completely written report.
    """
    destination = Path(destination)
    fd, staged = tempfile.mkstemp(prefix=".ur-report-stage-", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(staged, destination)
    finally:
        os.unlink(staged)
