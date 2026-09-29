#!/usr/bin/env python3
"""Install a repository-owned pure-Python package into the active venv.

This deliberately avoids pip/build isolation so islanded packages can be
installed with zero registry/network access. It supports arbitrary source
directories and zero or more console-script launchers.
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
    p.add_argument(
        "--source-root",
        default=".",
        help="root used to resolve --source-dir (default: current directory)",
    )
    p.add_argument(
        "--source-dir",
        default=None,
        help="package source directory relative to --source-root (default: src/PACKAGE)",
    )
    p.add_argument("--entry", action="append", default=[], type=parse_entry)
    args = p.parse_args()

    source_root = Path(args.source_root)
    source_dir = Path(args.source_dir) if args.source_dir else Path("src") / args.package
    src = source_root / source_dir
    if not src.is_dir():
        raise SystemExit(f"missing pure-Python package source: {src}")

    candidates = [Path(x) for x in site.getsitepackages()]
    if not candidates:
        raise SystemExit("unable to locate venv site-packages")
    target_root = candidates[0]
    target_root.mkdir(parents=True, exist_ok=True)
    target = target_root / args.package
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    python_path = Path(sys.executable).absolute()
    bin_dir = python_path.parent
    installed_launchers: list[Path] = []
    for script, module, func in args.entry:
        launcher = bin_dir / script
        launcher.write_text(
            "#!" + str(python_path) + "\n"
            f"from {module} import {func} as _entry\n"
            "raise SystemExit(_entry())\n",
            encoding="utf-8",
        )
        launcher.chmod(
            launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        installed_launchers.append(launcher)

    spec = importlib.util.find_spec(args.package)
    if spec is None:
        raise SystemExit(f"installed package is not importable: {args.package}")
    print(f"installed {args.package} -> {target}")
    for launcher in installed_launchers:
        print(f"installed launcher -> {launcher}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
