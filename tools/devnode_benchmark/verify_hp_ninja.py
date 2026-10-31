#!/usr/bin/env python3
"""Read-only HP preflight for the owner-installed, pinned Ninja tool.

Never installs software or changes PATH. A controlled main-only workflow
calls this before opting into the otherwise untouched Windows smoke.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

INSTALLER_ID = "UR-Recomp-HP-Ninja-OneClick/1"
ARCHIVE_SHA256 = "07fc8261b42b20e71d1720b39068c2e14ffcee6396b76fb7a795fb460b78dc65"
INSTALL_ROOT = Path("C:/DevNode/runner-tools/Ninja/v1.13.2")
VERSION = "1.13.2"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def has_reparse_point(path: Path) -> bool:
    try:
        return path.is_symlink() or getattr(path, "is_junction", lambda: False)()
    except OSError:
        return True


def verify(root: Path, *, run_version: bool = True) -> str:
    """Return a validated executable path; any ambiguity must fail closed."""
    # Path.is_dir() follows redirected *ancestors*. Checking only the final
    # v1.13.2 component is insufficient when runner-tools or Ninja is a
    # Windows junction / symbolic link. Walk lexically, never resolve first.
    # Keep the synthetic tests portable: verify() checks any supplied root,
    # while main() separately enforces the immutable owner HP install path.
    for component in (root, *root.parents):
        if has_reparse_point(component):
            raise ValueError("redirected owner Ninja installation or ancestor")
    if not root.is_dir():
        raise ValueError("missing owner Ninja installation")
    receipt = root / "ur-recomp-ninja-install.json"
    exe = root / "ninja.exe"
    if any(has_reparse_point(p) or not p.is_file() for p in (receipt, exe)):
        raise ValueError("missing, redirected or non-file Ninja metadata/binary")
    files = {item.name for item in root.iterdir()}
    if files != {receipt.name, exe.name}:
        raise ValueError("unknown files in managed Ninja installation")
    record = json.loads(receipt.read_text(encoding="utf-8-sig"))
    if not isinstance(record, dict):
        raise ValueError("malformed Ninja install receipt")
    for field, expected in (("installer_id", INSTALLER_ID),
                            ("version", VERSION),
                            ("archive_sha256", ARCHIVE_SHA256)):
        if record.get(field) != expected:
            raise ValueError("Ninja installation provenance mismatch")
    expected_bin_hash = record.get("binary_sha256")
    if not isinstance(expected_bin_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_bin_hash):
        raise ValueError("invalid Ninja executable hash in receipt")
    if file_hash(exe) != expected_bin_hash:
        raise ValueError("Ninja executable differs from installed receipt")
    if run_version:
        version = subprocess.run([str(exe), "--version"], capture_output=True,
                                 text=True, timeout=15, check=True)
        if version.stdout.strip() != VERSION:
            raise ValueError("Ninja executable returned unexpected version")
    return str(exe)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=INSTALL_ROOT)
    parser.add_argument("--allow-trusted-main-push", action="store_true",
                        help="Only the pinned owner HP main-push caller may opt into automatic Ninja")
    args = parser.parse_args()
    event = os.environ.get("GITHUB_EVENT_NAME")
    event_allowed = (event == "workflow_dispatch" or
                     (event == "push" and args.allow_trusted_main_push))
    if (os.environ.get("RUNNER_NAME") != "hpmini-ur-recomp"
            or os.environ.get("GITHUB_REPOSITORY") != "gamesbyian/UR-Recomp"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or not event_allowed):
        parser.error("HP Ninja requires the exact owner runner and trusted main dispatch/push")
    if args.root != INSTALL_ROOT:
        parser.error("HP Ninja installation root must be exact and immutable")
    try:
        exe = verify(args.root)
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print("HP_NINJA_CANARY=unavailable reason=" + type(error).__name__, file=sys.stderr)
        return 1
    print("HP_NINJA_CANARY=verified executable_sha256=" + file_hash(Path(exe)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
