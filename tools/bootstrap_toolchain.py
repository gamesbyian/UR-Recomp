#!/usr/bin/env python3
"""Reproducibly fetch and optionally build pinned UR-Recomp research tools.

Installs into ignored .tools/. This script never uses sudo and never mutates
system packages. Use --list before installing a new group.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("toolchain.json")


def run(cmd: list[str] | str, *, cwd: Path | None = None, shell: bool = False) -> None:
    shown = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"+ {shown}")
    subprocess.run(cmd, cwd=cwd, shell=shell, check=True)


def load_manifest() -> dict:
    with MANIFEST.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_checkout(tool: dict, src_root: Path) -> Path:
    dest = src_root / tool["id"]
    if not dest.exists():
        run(["git", "clone", "--filter=blob:none", "--no-checkout", tool["url"], str(dest)])
    if not (dest / ".git").exists():
        raise SystemExit(f"{dest} exists but is not a git checkout")
    revision = tool["revision"]
    run(["git", "fetch", "--depth", "1", "origin", revision], cwd=dest)
    run(["git", "checkout", "--detach", revision], cwd=dest)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
    if actual != revision:
        raise SystemExit(f"{tool['id']}: expected {revision}, got {actual}")
    return dest


def ensure_venv(root: Path) -> Path:
    venv = root / "venv"
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        run([sys.executable, "-m", "venv", str(venv)])
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    return python


def main() -> int:
    manifest = load_manifest()
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List pinned tools and exit")
    parser.add_argument("--group", action="append", default=[], help="Install a named group (default: core)")
    parser.add_argument("--tool", action="append", default=[], help="Install one tool by id")
    parser.add_argument("--clone-only", action="store_true", help="Fetch exact sources but skip builds/installs")
    parser.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--system-packages", action="store_true", help="Print recommended Ubuntu packages and exit")
    args = parser.parse_args()

    if args.system_packages:
        print(" ".join(manifest.get("system_packages_ubuntu", [])))
        return 0

    tools = manifest["tools"]
    if args.list:
        for tool in tools:
            print(f"{tool['id']:20} {tool['group']:12} {tool['revision']}  {tool['purpose']}")
        return 0

    wanted_ids = set(args.tool)
    wanted_groups = set(args.group or (["core"] if not wanted_ids else []))
    selected = [t for t in tools if t["id"] in wanted_ids or t["group"] in wanted_groups]
    missing = wanted_ids - {t["id"] for t in selected}
    if missing:
        raise SystemExit("Unknown tool id(s): " + ", ".join(sorted(missing)))
    if not selected:
        raise SystemExit("No tools selected")

    install_root = ROOT / manifest.get("install_root", ".tools")
    src_root = install_root / "src"
    src_root.mkdir(parents=True, exist_ok=True)

    python: Path | None = None
    for tool in selected:
        print(f"\n== {tool['id']} ==")
        dest = ensure_checkout(tool, src_root)
        if args.clone_only:
            continue
        for command in tool.get("build", []):
            if "{python}" in command and python is None:
                python = ensure_venv(install_root)
            expanded = command.format(jobs=args.jobs, python=str(python) if python else sys.executable)
            run(expanded, cwd=dest, shell=True)

    print("\nPinned toolchain operation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
