#!/usr/bin/env python3
"""Reproducibly fetch and optionally build pinned UR-Recomp research tools.

Installs into ignored .tools/. This script never uses sudo, a shell command
interpreter, or system package mutation. Use --list before installing a group.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("toolchain.json")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    if not cmd or not all(isinstance(x, str) and x for x in cmd):
        raise ValueError(f"invalid command vector: {cmd!r}")
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def load_manifest() -> dict:
    with MANIFEST.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != 2:
        raise ValueError(
            f"unsupported toolchain schema {manifest.get('schema_version')!r}; expected 2"
        )

    install_root = manifest.get("install_root")
    if not isinstance(install_root, str) or not install_root:
        raise ValueError("install_root must be a non-empty string")
    install_path = Path(install_root)
    if install_path.is_absolute() or ".." in install_path.parts:
        raise ValueError("install_root must stay inside the repository")

    tools = manifest.get("tools")
    if not isinstance(tools, list):
        raise ValueError("tools must be a list")

    seen: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ValueError(f"tool entry {index} must be an object")
        tool_id = tool.get("id")
        if not isinstance(tool_id, str) or not ID_RE.fullmatch(tool_id):
            raise ValueError(f"tool entry {index} has invalid id {tool_id!r}")
        if tool_id in seen:
            raise ValueError(f"duplicate tool id {tool_id!r}")
        seen.add(tool_id)

        revision = tool.get("revision")
        if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
            raise ValueError(f"{tool_id}: revision must be a full lowercase 40-hex commit")

        url = tool.get("url")
        if not isinstance(url, str):
            raise ValueError(f"{tool_id}: url must be a string")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise ValueError(f"{tool_id}: tool source must be pinned to https://github.com")

        group = tool.get("group")
        purpose = tool.get("purpose")
        if not isinstance(group, str) or not group:
            raise ValueError(f"{tool_id}: group must be a non-empty string")
        if not isinstance(purpose, str) or not purpose:
            raise ValueError(f"{tool_id}: purpose must be a non-empty string")

        mode = tool.get("install_mode")
        if mode not in {"build", "manual"}:
            raise ValueError(f"{tool_id}: install_mode must be 'build' or 'manual'")

        build = tool.get("build", [])
        if not isinstance(build, list):
            raise ValueError(f"{tool_id}: build must be a list")
        if mode == "build" and not build:
            raise ValueError(f"{tool_id}: build-mode tool has no build commands")
        if mode == "manual" and build:
            raise ValueError(f"{tool_id}: manual tool must not declare build commands")
        artifacts = tool.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise ValueError(f"{tool_id}: artifacts must be a list")
        for artifact_index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                raise ValueError(f"{tool_id}: artifact {artifact_index} must be an object")
            rel = artifact.get("path")
            kind = artifact.get("kind")
            if not isinstance(rel, str) or not rel:
                raise ValueError(f"{tool_id}: artifact {artifact_index} path must be non-empty")
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise ValueError(f"{tool_id}: artifact {rel!r} must stay inside checkout")
            if kind not in {"executable", "shared-library"}:
                raise ValueError(f"{tool_id}: artifact {rel!r} has invalid kind {kind!r}")

        for cmd_index, cmd in enumerate(build):
            if (
                not isinstance(cmd, list)
                or not cmd
                or not all(isinstance(arg, str) and arg for arg in cmd)
            ):
                raise ValueError(
                    f"{tool_id}: build command {cmd_index} must be a non-empty argv list"
                )
            for arg in cmd:
                unknown = re.findall(r"{([^{}]+)}", arg)
                if any(name not in {"jobs", "python"} for name in unknown):
                    raise ValueError(
                        f"{tool_id}: unsupported build placeholder(s) in {arg!r}: {unknown}"
                    )


def expand_command(command: list[str], *, jobs: int, python: Path | None) -> list[str]:
    values = {
        "jobs": str(jobs),
        "python": str(python) if python is not None else sys.executable,
    }
    return [arg.format(**values) for arg in command]


def canonical_git_url(url: str) -> str:
    return url.rstrip("/").removesuffix(".git")


def ensure_checkout(tool: dict, src_root: Path) -> Path:
    dest = src_root / tool["id"]
    if not dest.exists():
        run(["git", "clone", "--filter=blob:none", "--no-checkout", tool["url"], str(dest)])
    if not (dest / ".git").exists():
        raise SystemExit(f"{dest} exists but is not a git checkout")

    origin = subprocess.check_output(
        ["git", "remote", "get-url", "origin"], cwd=dest, text=True
    ).strip()
    if canonical_git_url(origin) != canonical_git_url(tool["url"]):
        raise SystemExit(
            f"{tool['id']}: existing checkout origin {origin!r} != manifest {tool['url']!r}"
        )

    revision = tool["revision"]
    run(["git", "fetch", "--depth", "1", "origin", revision], cwd=dest)
    run(["git", "checkout", "--detach", "--force", revision], cwd=dest)
    run(["git", "reset", "--hard", revision], cwd=dest)
    # .tools/ is disposable. Remove both ordinary and ignored build residue so a
    # previous local build cannot contaminate a supposedly pinned rebuild.
    run(["git", "clean", "-ffdqx"], cwd=dest)

    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
    if actual != revision:
        raise SystemExit(f"{tool['id']}: expected {revision}, got {actual}")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=dest, text=True
    ).strip()
    if dirty:
        raise SystemExit(f"{tool['id']}: checkout is dirty after reset/clean")
    return dest


def verify_artifacts(tool: dict, dest: Path) -> None:
    problems: list[str] = []
    for spec in tool.get("artifacts", []):
        rel = spec["path"]
        kind = spec["kind"]
        path = dest / rel
        if not path.is_file():
            problems.append(f"{rel}: missing")
            continue
        if path.stat().st_size == 0:
            problems.append(f"{rel}: empty")
            continue
        if kind == "executable" and not os.access(path, os.X_OK):
            problems.append(f"{rel}: not executable")
            continue
        if kind == "shared-library":
            head = path.read_bytes()[:4]
            if os.name == "nt":
                ok = head[:2] == b"MZ"
            elif sys.platform == "darwin":
                ok = head in {
                    b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf",
                    b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe",
                }
            else:
                ok = head == b"\x7fELF"
            if not ok:
                problems.append(f"{rel}: does not look like a native shared library")
    if problems:
        raise SystemExit(f"{tool['id']}: invalid build artifact(s): " + "; ".join(problems))


def ensure_venv(root: Path, tool_id: str) -> Path:
    venv = root / "venvs" / tool_id
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
    parser.add_argument("--validate", action="store_true", help="Validate manifest and exit")
    args = parser.parse_args()

    if args.jobs < 1:
        raise SystemExit("--jobs must be at least 1")

    if args.validate:
        print(f"toolchain manifest valid ({len(manifest['tools'])} tools)")
        return 0

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

    for tool in selected:
        python: Path | None = None
        print(f"\n== {tool['id']} ==")
        dest = ensure_checkout(tool, src_root)
        if args.clone_only:
            continue
        if tool["install_mode"] == "manual":
            print(f"{tool['id']}: source checkout pinned; manual build/install required")
            continue
        for command in tool.get("build", []):
            if any("{python}" in arg for arg in command) and python is None:
                python = ensure_venv(install_root, tool["id"])
            expanded = expand_command(command, jobs=args.jobs, python=python)
            run(expanded, cwd=dest)
        verify_artifacts(tool, dest)

    print("\nPinned toolchain operation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
