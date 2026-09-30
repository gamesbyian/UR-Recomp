#!/usr/bin/env python3
"""Measure the repository file closure consumed by a compiler depfile build.

The first consumer is the pinned Snes9x libretro build. The build is performed
separately with compiler dependency emission enabled, then this tool converts
the resulting .d files into a stable repository-relative closure manifest.

Only paths rooted inside --source-root are retained. System headers and build
outputs are excluded. Explicit --include paths cover non-compiled build inputs
such as Makefiles, linker scripts and licenses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex


def parse_depfile(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    text = text.replace("\\\n", " ")
    deps: list[str] = []
    for logical in text.splitlines():
        if not logical.strip() or ":" not in logical:
            continue
        _, rhs = logical.split(":", 1)
        deps.extend(shlex.split(rhs, posix=True))
    return deps


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(
    source_root: Path,
    depfiles: list[Path],
    explicit: list[str],
    dependency_base: Path | None = None,
) -> dict:
    root = source_root.resolve()
    dep_base = (dependency_base or source_root).resolve()
    files: set[Path] = set()

    def add(candidate: Path) -> None:
        try:
            resolved = candidate.resolve()
            rel = resolved.relative_to(root)
        except (OSError, ValueError):
            return
        if resolved.is_file():
            files.add(rel)

    for depfile in depfiles:
        for token in parse_depfile(depfile):
            candidate = Path(token)
            if not candidate.is_absolute():
                candidate = dep_base / candidate
            add(candidate)

    for item in explicit:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = root / candidate
        add(candidate)

    records = []
    total_bytes = 0
    for rel in sorted(files, key=lambda p: p.as_posix()):
        path = root / rel
        size = path.stat().st_size
        total_bytes += size
        records.append(
            {
                "path": rel.as_posix(),
                "size": size,
                "sha256": sha256(path),
            }
        )

    closure_digest = hashlib.sha256()
    for record in records:
        closure_digest.update(record["path"].encode("utf-8"))
        closure_digest.update(b"\0")
        closure_digest.update(record["sha256"].encode("ascii"))
        closure_digest.update(b"\n")

    return {
        "schema_version": 1,
        "file_count": len(records),
        "source_bytes": total_bytes,
        "closure_sha256": closure_digest.hexdigest(),
        "files": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--dep-root", type=Path, required=True)
    parser.add_argument(
        "--dependency-base",
        type=Path,
        help="working directory relative dependency paths in depfiles are based on",
    )
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    depfiles = sorted(args.dep_root.rglob("*.d"))
    if not depfiles:
        raise SystemExit(f"no compiler depfiles found under {args.dep_root}")

    result = collect(
        args.source_root,
        depfiles,
        args.include,
        dependency_base=args.dependency_base,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "closure: {} files, {} bytes, sha256={}".format(
            result["file_count"], result["source_bytes"], result["closure_sha256"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
