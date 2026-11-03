#!/usr/bin/env python3
"""Local-only, source-keyed native analyzer cache for trusted HP gameplay science.

A fresh patched SNESRecomp tree remains authoritative. Only its Rust analyzer
binary is reused; the v2 emitter still verifies its own generator inputs and
regenerates exact ROM-derived C on *every* research run. Invalid cache entries
never reach the generator. All cache failures revert to the original build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

RECIPE = "ur-hp-native-analyzer-release-v1"
BINARY = "snesrecomp-analyze.exe"
BUILD_ENV = (
    "CARGO_BUILD_TARGET", "CARGO_ENCODED_RUSTFLAGS", "CARGO_PROFILE_RELEASE_CODEGEN_UNITS",
    "CARGO_PROFILE_RELEASE_DEBUG", "CARGO_PROFILE_RELEASE_LTO",
    "CARGO_PROFILE_RELEASE_OPT_LEVEL", "CARGO_PROFILE_RELEASE_PANIC",
    "CARGO_PROFILE_RELEASE_STRIP", "CARGO_TARGET_DIR", "RUSTC_BOOTSTRAP",
    "RUSTC_WRAPPER", "RUSTFLAGS", "RUSTUP_TOOLCHAIN",
)


def digest_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest()


def redirected(path: Path) -> bool:
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def require_plain_parents(path: Path) -> None:
    if any(redirected(p) for p in (path, *path.parents)):
        raise ValueError("redirected input/cache path")


def crate_digest(crate: Path) -> str:
    """Hash all Rust crate inputs, rejecting links instead of silently omitting them."""
    require_plain_parents(crate)
    if not crate.is_dir():
        raise ValueError("native analyzer crate unavailable")
    digest = hashlib.sha256()
    stack = [crate]
    seen = 0
    while stack:
        for path in sorted(stack.pop().iterdir()):
            if path.name == "target" and path.parent == crate:
                if path.exists() and (redirected(path) or not path.is_dir()):
                    raise ValueError("redirected native target directory")
                continue
            if redirected(path):
                raise ValueError("redirected crate entry")
            if path.is_dir():
                stack.append(path)
            elif path.is_file():
                digest.update(path.relative_to(crate).as_posix().encode("utf-8") + b"\x00")
                digest.update(bytes.fromhex(digest_file(path)))
                seen += 1
            else:
                raise ValueError("unsupported crate entry")
    if not seen or not (crate / "Cargo.lock").is_file() or not (crate / "Cargo.toml").is_file():
        raise ValueError("incomplete Rust crate")
    return digest.hexdigest()


def identity(framework: Path, environment: dict[str, str] | None = None) -> dict:
    env = dict(os.environ if environment is None else environment)
    if env.get("CARGO_TARGET_DIR"):
        raise ValueError("unexpected Cargo target override")
    rustc = subprocess.check_output(
        ["rustc", "--version", "--verbose"], text=True, timeout=15).strip()
    cargo = subprocess.check_output(
        ["cargo", "--version", "--verbose"], text=True, timeout=15).strip()
    return {
        "recipe": RECIPE,
        "crate_sha256": crate_digest(framework / "recompiler-rs"),
        "rustc": rustc,
        "cargo": cargo,
        "build_environment": {k: env.get(k, "") for k in BUILD_ENV},
        "platform": sys.platform,
    }


def cache_key(fingerprint: dict) -> str:
    raw = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def verified_binary(entry: Path, fingerprint: dict) -> Path | None:
    try:
        require_plain_parents(entry)
        if not entry.is_dir() or {p.name for p in entry.iterdir()} != {"manifest.json", BINARY}:
            return None
        manifest = entry / "manifest.json"
        binary = entry / BINARY
        if redirected(manifest) or redirected(binary) or not binary.is_file():
            return None
        record = json.loads(manifest.read_text("utf-8"))
        if (record.get("fingerprint") != fingerprint or
                record.get("binary_sha256") != digest_file(binary) or
                record.get("size") != binary.stat().st_size or
                binary.stat().st_size < 1024):
            return None
        with binary.open("rb") as handle:
            if handle.read(2) != b"MZ":
                return None
        return binary
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def publish(cache_root: Path, entry: Path, built: Path, fingerprint: dict) -> Path:
    if entry.exists() or redirected(entry):
        raise ValueError("refusing to replace existing cache entry")
    require_plain_parents(cache_root)
    pending = Path(tempfile.mkdtemp(prefix=".staging-", dir=cache_root))
    try:
        target = pending / BINARY
        shutil.copyfile(built, target)
        with target.open("rb") as handle:
            magic = handle.read(2)
        if target.stat().st_size < 1024 or magic != b"MZ":
            raise ValueError("native analyzer output does not look like a Windows executable")
        record = {
            "fingerprint": fingerprint,
            "binary_sha256": digest_file(target),
            "size": target.stat().st_size,
        }
        (pending / "manifest.json").write_text(json.dumps(record, sort_keys=True) + "\n", "utf-8")
        pending.rename(entry)
    finally:
        if pending.exists():
            shutil.rmtree(pending)
    result = verified_binary(entry, fingerprint)
    if result is None:
        raise ValueError("native analyzer cache verification failed after publication")
    return result


def trusted_hp_science(env: dict[str, str]) -> bool:
    return (env.get("GITHUB_REPOSITORY") == "gamesbyian/UR-Recomp" and
            env.get("GITHUB_REF") == "refs/heads/main" and
            env.get("GITHUB_EVENT_NAME") in ("schedule", "workflow_dispatch") and
            env.get("RUNNER_NAME") == "hpmini-ur-recomp")


def prepare(framework: Path, cache_root: Path, github_env: Path,
            *, env: dict[str, str] | None = None, build=None) -> str:
    env = dict(os.environ if env is None else env)
    if not trusted_hp_science(env):
        return "refused_untrusted"
    try:
        require_plain_parents(framework)
        require_plain_parents(cache_root)
        require_plain_parents(github_env)
        fingerprint = identity(framework, env)
        cache_root.mkdir(parents=True, exist_ok=True)
        entry = cache_root / cache_key(fingerprint)
        binary = verified_binary(entry, fingerprint)
        status = "hit"
        if binary is None:
            if entry.exists() or redirected(entry):
                return "invalid_fallback"
            if build is None:
                subprocess.run(
                    [sys.executable, str(framework / "tools/build_native_analyzer.py")],
                    cwd=framework, check=True, timeout=300)
            else:
                build(framework)
            built = framework / "recompiler-rs/target/release" / BINARY
            binary = publish(cache_root, entry, built, fingerprint)
            status = "miss_built"
        # Set the downstream native analyzer only after byte verification.
        # The emitter also hashes the binary and generator sources itself.
        with github_env.open("a", encoding="utf-8") as out:
            out.write("SNESRECOMP_NATIVE_ANALYZER=" + str(binary.absolute()) + "\n")
        return status
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        # Never replace a source build with an unverifiable binary.
        return "source_fallback"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--github-env", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.framework, args.cache_root, args.github_env)
    print("HP_NATIVE_ANALYZER_CACHE=" + result)
    return 2 if result == "refused_untrusted" else 0


if __name__ == "__main__":
    raise SystemExit(main())
