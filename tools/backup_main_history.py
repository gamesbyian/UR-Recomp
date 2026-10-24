#!/usr/bin/env python3
"""Create and self-restore a main-branch full-history git bundle.

Not a backup of GitHub issues, PR metadata, Actions artifacts, other unmerged
branches, LFS payloads, submodule repositories or external cloud accounts.
Drive transfer and a separate Drive readback must happen after this job.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_REF = "refs/heads/ur-restorable-main"
MIB = 1024 * 1024

def git(repo, *args):
    run = subprocess.run(["git", "-C", str(repo), *args], check=True,
                         capture_output=True, text=True, timeout=900)
    return run.stdout.strip()

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def create(repo, out_dir, *, max_mib=650, part_mib=None):
    repo, out_dir = Path(repo).resolve(), Path(out_dir).resolve()
    if type(max_mib) is not int or not 1 <= max_mib <= 1024:
        raise ValueError("invalid MiB budget")
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("refuse partial shallow history: fetch full main first")
    sha = git(repo, "rev-parse", "HEAD")
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise ValueError("invalid source git SHA")
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = out_dir / "UR-Recomp-main-history.bundle"
    # Dedicated new ref avoids rewriting a working or protected main branch.
    git(repo, "update-ref", BACKUP_REF, sha)
    git(repo, "bundle", "create", str(bundle), BACKUP_REF)
    git(repo, "bundle", "verify", str(bundle))
    size = bundle.stat().st_size
    if size > max_mib * MIB:
        bundle.unlink()
        raise ValueError(f"bundle {size} bytes exceeds explicit {max_mib} MiB budget")
    with tempfile.TemporaryDirectory(prefix="ur-restore-") as temp:
        dest = Path(temp) / "restored"
        subprocess.run(["git", "clone", "--quiet", "--branch", "ur-restorable-main",
                        str(bundle), str(dest)], check=True, capture_output=True,
                       text=True, timeout=900)
        restored_sha = git(dest, "rev-parse", "HEAD")
        if restored_sha != sha:
            raise ValueError("restore git HEAD SHA does not match source")
        git(dest, "fsck", "--no-reflogs", "--connectivity-only")
        source_count = git(repo, "rev-list", "--count", sha)
        restored_count = git(dest, "rev-list", "--count", "HEAD")
        if source_count != restored_count:
            raise ValueError("restore ancestry count does not match source")
    manifest = {
        "schema": "ur-git-main-backup/1",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_main_sha": sha,
        "recovered_main_sha": restored_sha,
        "history_commit_count": int(source_count),
        "bundle_ref": BACKUP_REF,
        "bundle_file": bundle.name,
        "bundle_bytes": size,
        "bundle_sha256": digest(bundle),
        "full_main_git_history": True,
        "self_restore_verified": True,
        "independent_drive_copy_verified": False,
        "exclusions": [
            "unmerged secondary Git branches and tags",
            "GitHub PR/issue metadata, reviews and comments",
            "GitHub Actions runs, logs, retained build artifacts and release assets",
            "any git-lfs backing objects, submodule content, and uncommitted work",
            "ChatGPT schedules and Google Drive vault contents",
        ],
    }
    if part_mib is not None:
        manifest["transfer_parts"] = split_transfer(bundle, out_dir / "transfer", part_mib)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    return manifest


def split_transfer(bundle, destination, part_mib):
    """Produce independently hashed, under-100MiB transfer units.

    Each part is uploaded separately as one GitHub artifact ZIP: do not wrap
    all parts in a single large artifact, which the Drive connector cannot read.
    """
    if type(part_mib) is not int or not 1 <= part_mib <= 80:
        raise ValueError("transfer part size must be 1..80 MiB")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("refuse nonempty transfer destination")
    rows = []
    recombined = hashlib.sha256()
    with bundle.open("rb") as source:
        while True:
            block = source.read(part_mib * MIB)
            if not block:
                break
            if len(rows) >= 12:
                raise ValueError("too many transfer parts")
            name = f"UR-Recomp-main-history.part-{len(rows)+1:02d}"
            target = destination / name
            target.write_bytes(block)
            if target.stat().st_size != len(block) or digest(target) != hashlib.sha256(block).hexdigest():
                raise ValueError("part readback mismatch")
            recombined.update(block)
            rows.append({"file": name, "bytes": len(block),
                         "sha256": hashlib.sha256(block).hexdigest()})
    if not rows or recombined.hexdigest() != digest(bundle):
        raise ValueError("transfer concatenation does not match bundle")
    return rows

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-mib", type=int, default=650)
    p.add_argument("--part-mib", type=int, help="generate Drive-friendly transfer parts, max 80 MiB each")
    a = p.parse_args()
    output = create(a.repo, a.out, max_mib=a.max_mib, part_mib=a.part_mib)
    print(f"RESTORE VERIFIED: {output['source_main_sha']} "
          f"({output['history_commit_count']} commits; "
          f"{output['bundle_bytes']} bytes)")
    print("Drive copy: NOT VERIFIED (requires independent connector handoff)")

if __name__ == "__main__":
    main()
