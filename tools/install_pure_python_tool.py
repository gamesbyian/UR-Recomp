#!/usr/bin/env python3
"""Install a dependency-free src-layout Python tool into the active venv.

This deliberately avoids pip/build isolation so repository-island tools with no
runtime dependencies can be installed with zero registry/network access.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import shutil
import site
import stat
import sys


def parse_entry(value: str) -> tuple[str, str, str]:
    try:
        script, target = value.split("=", 1)
        module, func = target.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "entry must be SCRIPT=module:function"
        ) from exc
    if not script or not module or not func:
        raise argparse.ArgumentTypeError("entry fields must be non-empty")
    return script, module, func


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--package", required=True)
    p.add_argument("--entry", required=True, type=parse_entry)
    args = p.parse_args()

    src = Path("src") / args.package
    if not src.is_dir():
        raise SystemExit(f"missing src-layout package: {src}")

    candidates = [Path(x) for x in site.getsitepackages()]
    if not candidates:
        raise SystemExit("unable to locate venv site-packages")
    target_root = candidates[0]
    target_root.mkdir(parents=True, exist_ok=True)
    target = target_root / args.package
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    script, module, func = args.entry
    bin_dir = Path(sys.executable).resolve().parent
    launcher = bin_dir / script
    launcher.write_text(
        "#!" + str(Path(sys.executable).resolve()) + "\n"
        f"from {module} import {func} as _entry\n"
        "raise SystemExit(_entry())\n",
        encoding="utf-8",
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    spec = importlib.util.find_spec(args.package)
    if spec is None:
        raise SystemExit(f"installed package is not importable: {args.package}")
    print(f"installed {args.package} -> {target}")
    print(f"installed launcher -> {launcher}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
