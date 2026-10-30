#!/usr/bin/env python3
"""Fail closed when an audio package differs from its selected CI producer SHA.

Run after the existing archive and extracted-package integrity verification.
This is a provenance check, not a substitute for those byte-level checks.
"""

import argparse
import json
import re
from pathlib import Path

SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")


def verify_source_binding(manifest_path: Path, expected_source_sha: str) -> str:
    """Require a full canonical producer commit SHA in the verified manifest."""
    if not isinstance(expected_source_sha, str) or not SOURCE_SHA.fullmatch(expected_source_sha):
        raise ValueError("selected producer source SHA must be 40 lowercase hex characters")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read selected audio package manifest") from exc
    if not isinstance(manifest, dict):
        raise ValueError("selected audio package manifest must be an object")
    observed = manifest.get("source_revision")
    if observed != expected_source_sha:
        raise ValueError(
            "selected audio package source revision mismatch: "
            f"producer={expected_source_sha} manifest={observed!r}"
        )
    return expected_source_sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-source-sha", required=True)
    args = parser.parse_args()
    try:
        sha = verify_source_binding(args.manifest, args.expected_source_sha)
    except ValueError as exc:
        parser.exit(1, f"WINDOWS_AUDIO_SOURCE_BINDING FAIL: {exc}\n")
    print(f"WINDOWS_AUDIO_SOURCE_BINDING PASS source_sha={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
