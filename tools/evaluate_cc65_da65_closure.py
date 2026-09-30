#!/usr/bin/env python3
"""Measure and validate a reduced cc65/da65 source closure.

This script is intentionally dependency-free. It takes a pinned cc65 checkout,
copies only the build metadata, license, src/da65, and src/common into a new
closure, builds da65 there, and emits a machine-readable size/file inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


KEEP = ("LICENSE", "src/Makefile", "src/da65", "src/common")


def copy_item(src_root: Path, dst_root: Path, rel: str) -> None:
    src = src_root / rel
    dst = dst_root / rel
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def inventory(root: Path) -> dict:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    total = sum(p.stat().st_size for p in files)
    h = hashlib.sha256()
    rows = []
    for p in files:
        rel = p.relative_to(root).as_posix()
        data = p.read_bytes()
        h.update(rel.encode("utf-8") + b"\0")
        h.update(hashlib.sha256(data).digest())
        rows.append({"path": rel, "size": len(data)})
    return {
        "file_count": len(files),
        "total_bytes": total,
        "tree_sha256": h.hexdigest(),
        "files": rows,
    }


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("closure", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--jobs", type=int, default=2)
    args = ap.parse_args()

    source = args.source.resolve()
    closure = args.closure.resolve()
    if closure.exists():
        shutil.rmtree(closure)
    closure.mkdir(parents=True)

    for rel in KEEP:
        copy_item(source, closure, rel)

    before = inventory(closure)
    run(["make", "da65", f"-j{args.jobs}"], closure / "src")

    da65 = closure / "bin" / "da65"
    if not da65.is_file():
        raise SystemExit("reduced closure did not produce bin/da65")

    run([str(da65), "--version"], closure)
    # da65 accepts 65816 as the cpu identifier; parsing a byte is enough to
    # prove the intended CPU table is present in the reduced source closure.
    fixture = closure / "ur-recomp-da65-smoke.bin"
    fixture.write_bytes(bytes([0xEA]))
    output = closure / "ur-recomp-da65-smoke.s"
    with output.open("w", encoding="utf-8") as fp:
        subprocess.run(
            [str(da65), "--cpu", "65816", str(fixture)],
            cwd=closure,
            check=True,
            stdout=fp,
        )

    report = {
        "schema_version": 1,
        "kept_roots": list(KEEP),
        "source_file_count": before["file_count"],
        "source_total_bytes": before["total_bytes"],
        "source_tree_sha256": before["tree_sha256"],
        "artifact": {
            "path": "bin/da65",
            "size": da65.stat().st_size,
            "sha256": hashlib.sha256(da65.read_bytes()).hexdigest(),
        },
        "smoke_output": output.read_text(encoding="utf-8", errors="replace"),
    }

    text = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
