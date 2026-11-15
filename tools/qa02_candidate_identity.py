#!/usr/bin/env python3
"""Strict source-bound identity for QA-02 hosted candidate fault experiments.

Historical owner playtest pins are deliberately not modified. A new candidate
must provide an independently retained identity receipt, never guessed hashes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import zipfile

HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


@dataclass(frozen=True)
class CandidateIdentity:
    source_sha: str
    zip_sha256: str
    exe_sha256: str

    @classmethod
    def from_receipt(cls, path: Path) -> "CandidateIdentity":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {
            "source_sha", "zip_sha256", "exe_sha256"
        }:
            raise ValueError("QA-02 identity receipt requires exactly three fields")
        result = cls(data["source_sha"], data["zip_sha256"], data["exe_sha256"])
        if not all(isinstance(v, str) for v in vars(result).values()):
            raise ValueError("QA-02 identity fields must be strings")
        if not COMMIT.fullmatch(result.source_sha) or not all(
            HEX.fullmatch(v) for v in (result.zip_sha256, result.exe_sha256)
        ):
            raise ValueError("Invalid full source SHA or SHA-256 in QA-02 identity")
        return result

    def verify(self, archive: Path, exe_member: str) -> bytes:
        blob = archive.read_bytes()
        if hashlib.sha256(blob).hexdigest() != self.zip_sha256:
            raise ValueError("QA-02 nominated ZIP does not match independent receipt")
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or z.testzip() is not None:
                raise ValueError("Duplicate or corrupt QA-02 ZIP members")
            if exe_member not in names:
                raise ValueError("QA-02 executable missing from nominated ZIP")
            exe = z.read(exe_member)
        if hashlib.sha256(exe).hexdigest() != self.exe_sha256:
            raise ValueError("QA-02 executable does not match independent receipt")
        return exe
