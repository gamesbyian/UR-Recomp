#!/usr/bin/env python3
"""Opt-in HP/hosted canary for a relocatable, source-pinned *static* SDL3 install.

The game's SNESRecomp CMake invokes find_package(SDL3 CONFIG) before its
source fallback. This helper builds the SAME pinned SDL3 release once with
ClangCL/static CRT and atomically publishes a validated local install. No
GitHub cache, networking, or compiled executable is downloaded. On a genuine
HP cache-provisioning failure, the caller may choose the unchanged source build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SDL_ARCHIVE_SHA = "12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785"
RECIPE = "sdl3-3.4.10-clangcl-static-crt-release-install-v1"
OPTIONS = (
    "-DSDL_SHARED=OFF", "-DSDL_STATIC=ON", "-DSDL_TEST_LIBRARY=OFF",
    "-DSDL_TESTS=OFF", "-DSDL_EXAMPLES=OFF", "-DSDL_INSTALL=ON",
    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    """Content, not modification times, identifies the staged source tree."""
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in files):
        raise ValueError("missing source files or unsupported source symlink")
    digest = hashlib.sha256()
    for p in files:
        digest.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256(p)))
    return digest.hexdigest()


def manifest_for_stage(stage: Path) -> dict[str, str]:
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    if any(p.is_symlink() for p in files):
        raise ValueError("symlink in cache stage")
    return {p.relative_to(stage).as_posix(): sha256(p) for p in files}


def validate_stage(entry: Path, fingerprint: dict) -> Path | None:
    try:
        manifest = json.loads((entry / "manifest.json").read_text("utf-8"))
        if manifest.get("fingerprint") != fingerprint:
            return None
        stage = entry / "stage"
        observed = manifest_for_stage(stage)
        if not observed or observed != manifest.get("files"):
            return None
        configs = list(stage.rglob("SDL3Config.cmake"))
        archives = list(stage.rglob("SDL3-static.lib"))
        # Fail closed if the installed package could refer to shared SDL.
        if len(configs) != 1 or len(archives) != 1 or list(stage.rglob("SDL3.dll")):
            return None
        return configs[0].parent
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def command_output(argv: list[str]) -> str:
    return subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT, timeout=20).strip()


def visual_studio_root() -> Path:
    program_x86 = os.environ.get("ProgramFiles(x86)")
    if not program_x86:
        raise ValueError("Visual Studio installer location unavailable")
    vswhere = Path(program_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    root = Path(command_output([str(vswhere), "-latest", "-products", "*", "-property", "installationPath"]))
    if not root.is_dir():
        raise ValueError("Visual Studio 2022 not installed")
    return root


def fingerprint(source: Path, archive: Path, vs: Path) -> dict:
    if sha256(archive) != SDL_ARCHIVE_SHA:
        raise ValueError("pinned SDL3 source archive SHA-256 mismatch")
    if not (source / "CMakeLists.txt").is_file():
        raise ValueError("staged SDL3 source missing")
    clang_candidates = [vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe", vs / "VC/Tools/Llvm/bin/clang-cl.exe"]
    clang = next((p for p in clang_candidates if p.is_file()), None)
    msbuild = vs / "MSBuild/Current/Bin/MSBuild.exe"
    cmake = shutil.which("cmake")
    if not clang or not msbuild.is_file() or not cmake:
        raise ValueError("pinned ClangCL/MSBuild/CMake toolset not found")
    sdk = Path(os.environ.get("ProgramFiles(x86)", "")) / "Windows Kits/10/Include"
    sdk_dirs = sorted(p.name for p in sdk.iterdir() if p.is_dir()) if sdk.is_dir() else []
    if not sdk_dirs:
        raise ValueError("Windows 10 SDK unavailable")
    return {
        "recipe": RECIPE,
        "source_archive_sha256": SDL_ARCHIVE_SHA,
        "staged_source_tree_sha256": tree_digest(source),
        "visual_studio_path": str(vs.resolve()),
        "clang_cl_sha256": sha256(clang),
        "msbuild_sha256": sha256(msbuild),
        "cmake_sha256": sha256(Path(cmake)),
        "windows_sdk_include_versions": sdk_dirs,
        "cmake_options": list(OPTIONS),
    }


def cache_key(identity: dict) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]



def discard_invalid_entry(entry: Path) -> None:
    """Recover one invalid, private, derived cache entry without touching peers.

    The cache is deliberately a direct hex-key child of a private directory.
    Never delete a symlink/junction (including a nested Windows reparse point),
    an arbitrary caller-provided path, or any non-directory cache occupant.
    An atomic move frees the key before deletion; if cleanup is interrupted,
    the next attempt can still rebuild, and the orphan remains visibly named.
    """
    import re
    import uuid

    if not re.fullmatch(r"[0-9a-f]{24}", entry.name):
        raise ValueError("invalid SDL3 cache entry key")
    if entry.parent.is_symlink() or getattr(entry.parent, "is_junction", lambda: False)():
        raise ValueError("refuse cache repair through a reparse-point root")
    if not entry.is_dir() or entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
        raise ValueError("refuse cache repair on non-directory or reparse point")
    for child in entry.rglob("*"):
        if child.is_symlink() or getattr(child, "is_junction", lambda: False)():
            raise ValueError("refuse cache repair with nested reparse points")
    quarantine = entry.with_name(".invalid-" + entry.name + "-" + uuid.uuid4().hex)
    entry.rename(quarantine)
    # The only recursively deleted tree is the exact private derived entry
    # just renamed inside the same cache root, never a user-controlled target.
    shutil.rmtree(quarantine)


def build_stage(entry: Path, source: Path, identity: dict, jobs: int) -> Path:
    """Publish only a finished, byte-manifested, standalone install."""
    entry.parent.mkdir(parents=True, exist_ok=True)
    if entry.exists():
        raise ValueError("existing invalid cache entry; refusing to overwrite")
    with tempfile.TemporaryDirectory(prefix=".sdl3-build-", dir=str(entry.parent)) as temp:
        root = Path(temp)
        stage = root / "stage"
        build = root / "build"
        args = ["cmake", "-S", str(source), "-B", str(build),
                "-G", "Visual Studio 17 2022", "-A", "x64", "-T", "ClangCL",
                *OPTIONS, "-DCMAKE_INSTALL_PREFIX=" + str(stage)]
        for cmd in (args, ["cmake", "--build", str(build), "--config", "Release", "--parallel", str(jobs)],
                    ["cmake", "--install", str(build), "--config", "Release"]):
            subprocess.run(cmd, check=True, timeout=360)
        files = manifest_for_stage(stage)
        configs = list(stage.rglob("SDL3Config.cmake"))
        archives = list(stage.rglob("SDL3-static.lib"))
        if not files or len(configs) != 1 or len(archives) != 1 or list(stage.rglob("SDL3.dll")):
            raise ValueError("SDL3 static install incomplete or includes shared DLL")
        # The build/ tree is NOT cached. Installed CMake package files must
        # resolve relocatably after the finished entry is published.
        shutil.rmtree(build)
        (root / "manifest.json").write_text(json.dumps({"fingerprint": identity, "files": files}, sort_keys=True), "utf-8")
        os.replace(root, entry)
    result = validate_stage(entry, identity)
    if result is None:
        raise ValueError("installed SDL3 package failed post-publish validation")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--github-env", required=True, type=Path)
    parser.add_argument("--jobs", default=6, type=int)
    parser.add_argument("--required", action="store_true", help="Fail the hosted canary instead of silently using source fallback")
    parser.add_argument("--hp", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.jobs <= 6:
        parser.error("jobs must be 1..6")
    if os.environ.get("GITHUB_REPOSITORY") != "gamesbyian/UR-Recomp":
        parser.error("unexpected repository")
    if args.hp and (os.environ.get("RUNNER_NAME") != "hpmini-ur-recomp"
                    or os.environ.get("GITHUB_REF") != "refs/heads/main"
                    or os.environ.get("GITHUB_EVENT_NAME") not in ("push", "workflow_dispatch")):
        parser.error("HP static cache requires trusted main and exact owner runner")
    # Host canary is explicitly hosted-only on same-repo PRs. It never
    # authorizes a PR checkout on the personal runner.
    try:
        identity = fingerprint(args.source, args.archive, visual_studio_root())
        entry = args.cache_root / cache_key(identity)
        package_dir = validate_stage(entry, identity)
        state = "hit" if package_dir else "miss"
        if package_dir is None:
            if entry.exists() or entry.is_symlink():
                discard_invalid_entry(entry)
                state = "recovered"
            package_dir = build_stage(entry, args.source, identity, args.jobs)
        # GITHUB_ENV is appended only after successful complete validation.
        with args.github_env.open("a", encoding="utf-8") as f:
            f.write("UR_SDL3_PREBUILT_DIR=" + package_dir.as_posix() + "\n")
        print(f"HP_SDL3_CACHE={state} version=3.4.10 source_sha256={SDL_ARCHIVE_SHA} fingerprint={entry.name}")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"HP_SDL3_CACHE=unavailable reason={type(exc).__name__}", file=sys.stderr)
        return 1 if args.required else 0


if __name__ == "__main__":
    raise SystemExit(main())
