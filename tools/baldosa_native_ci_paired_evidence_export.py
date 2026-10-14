#!/usr/bin/env python3
"""Export ONLY this Windows test's throwaway, source-earned paired data.

This module has no authority to create player state, results, achievements,
or to accept a source event. The existing native Windows integration has
already played, committed, reopened and validated a single original-guest
match. This producer copies the exact on-disk file bytes for independent QA.

Never export a ROM, package, real user profile, or recursively copy a root.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

MAX_SINGLE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
ALLOWED_STOCK_PLAYERS = ("mike", "martin")
ALLOWED_STATE_PATHS = (
    "host-state-v1.txt",
    "profiles-v1.txt",
    "saves/profile-mike/host-profile.txt",
    "saves/profile-mike/save.srm",
    "saves/profile-martin/host-profile.txt",
    "saves/profile-martin/save.srm",
)
OPTIONAL_BOOTSTRAP = "saves/save.srm"
EVIDENCE_FOLDER = "ci-owned-raw-artifacts"
PRE_RECORDS_FOLDER = "ci-owned-pre-records-pair"


def _read_owned_file(root: Path, relative: str) -> bytes:
    parts = PurePosixPath(relative).parts
    if (not parts or any(p in ("", ".", "..") for p in parts) or
            PurePosixPath(relative).is_absolute() or
            "\\" in relative or ":" in relative):
        raise ValueError("Unsafe exported CI member name")
    target = root
    for part in parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("CI member or ancestor is a symlink: " + relative)
    if not target.is_file():
        raise ValueError("Missing ordinary CI member: " + relative)
    if target.stat().st_size < 1 or target.stat().st_size > MAX_SINGLE_BYTES:
        raise ValueError("Unsafe CI member size: " + relative)
    return target.read_bytes()


def export_ci_created_pair(user: Path, out: Path) -> dict[str, object]:
    """Copy exactly one named original-guest pair plus canonical profile files.

    No recursive traversal of unknown files. Restrict to a fresh user folder
    minted by the native player-created acceptance in THIS out directory.
    Enforce strict member equality, input bounds, non-symlinked paths and
    after-copy checksums to prevent silently retaining a different pair.
    """
    if (out.is_symlink() or user.is_symlink() or
            not out.is_dir() or not user.is_dir() or
            user.parent != out or user.name != "New Player-Created Named Racers"):
        raise ValueError("Not a disposable generated native CI user root")
    archive = user / "multiplayer-runs"
    if archive.is_symlink() or not archive.is_dir():
        raise ValueError("Missing canonical ordinary CI 2P pair archive")
    entries = sorted(archive.iterdir(), key=lambda p: p.name)
    if len(entries) != 2 or any(p.is_symlink() or not p.is_file() for p in entries):
        raise ValueError("Exactly two ordinary source-earned pair entries required")
    run = [p for p in entries if p.name.endswith(".urrun")]
    if len(run) != 1 or {p.name for p in entries} != {
            run[0].name, run[0].name + ".urmatch"}:
        raise ValueError("Canonical .urrun/.urmatch pair name mismatch")
    members = list(ALLOWED_STATE_PATHS)
    anon = user / OPTIONAL_BOOTSTRAP
    if anon.is_symlink():
        raise ValueError("Anonymous bootstrap redirected")
    if anon.exists():
        members.append(OPTIONAL_BOOTSTRAP)
    members.extend("multiplayer-runs/" + p.name for p in entries)
    if any("rom" in x.lower() or x.endswith(".sfc") or x.endswith(".exe")
           for x in members):
        raise ValueError("ROM or executable is not a CI record member")
    evidence = out / EVIDENCE_FOLDER
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("Refuse stale or replaced evidence export root")
    # Read every source BEFORE creating any copies. A missing or redirected
    # member cannot leave an apparently valid partial archive.
    content = {name: _read_owned_file(user, name) for name in members}
    total = sum(len(data) for data in content.values())
    if total > MAX_TOTAL_BYTES:
        raise ValueError("CI export exceeds bounded result evidence budget")
    for name in ALLOWED_STATE_PATHS:
        if name.endswith("save.srm") and len(content[name]) != 8192:
            raise ValueError("Named source SRAM is not exactly 8192 bytes")
    if OPTIONAL_BOOTSTRAP in content and len(content[OPTIONAL_BOOTSTRAP]) != 8192:
        raise ValueError("Anonymous bootstrap source SRAM is not 8192 bytes")
    evidence.mkdir()
    manifest: dict[str, dict[str, object]] = {}
    for name, data in sorted(content.items()):
        destination = evidence.joinpath(*PurePosixPath(name).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        if hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
            raise ValueError("Copied CI-only source pair changed in export")
        manifest[name] = {"sha256": sha, "bytes": len(data)}
    report: dict[str, object] = {
        "schema": "baldosa-native-disposable-source-pair-v1",
        "scope": "one-throwaway-Windows-CI-user-only",
        "source_profiles": list(ALLOWED_STOCK_PLAYERS),
        "source_pair": [p.name for p in entries],
        "members": manifest,
        "includes_rom": False,
        "includes_executable": False,
        "release_gate_credit": 0,
    }
    (evidence / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def export_ci_pre_records_pair(user: Path, out: Path) -> dict[str, object]:
    """Copy original guest pair bytes before the first fresh Records viewer.

    The post-Records exporter captures a second independently stored pair.
    Neither source-stage evidence nor this test utility awards game results.
    """
    if (out.is_symlink() or user.is_symlink() or
            not out.is_dir() or not user.is_dir() or
            user.parent != out or user.name != "New Player-Created Named Racers"):
        raise ValueError("Not a disposable generated native CI user root")
    archive = user / "multiplayer-runs"
    if archive.is_symlink() or not archive.is_dir():
        raise ValueError("Missing canonical pre-Records pair archive")
    entries = sorted(archive.iterdir(), key=lambda p: p.name)
    if len(entries) != 2 or any(p.is_symlink() or not p.is_file()
                                for p in entries):
        raise ValueError("Pre-Records source pair must contain exactly two files")
    runs = [p for p in entries if p.name.endswith(".urrun")]
    if len(runs) != 1 or {p.name for p in entries} != {
            runs[0].name, runs[0].name + ".urmatch"}:
        raise ValueError("Pre-Records .urrun/.urmatch names do not pair")
    paths = ["multiplayer-runs/" + p.name for p in entries]
    content = {name: _read_owned_file(user, name) for name in paths}
    if sum(map(len, content.values())) > MAX_TOTAL_BYTES:
        raise ValueError("Pre-Records source pair exceeds export budget")
    evidence = out / PRE_RECORDS_FOLDER
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("Refuse stale or replaced pre-Records evidence")
    evidence.mkdir()
    manifest: dict[str, dict[str, object]] = {}
    for name, data in sorted(content.items()):
        dest = evidence.joinpath(*PurePosixPath(name).parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        if hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
            raise ValueError("Copied pre-Records source pair changed")
        manifest[name] = {"sha256": sha, "bytes": len(data)}
    report: dict[str, object] = {
        "schema": "baldosa-native-pre-records-pair-v1",
        "stage": "after-real-play-before-first-records-viewer",
        "scope": "one-throwaway-Windows-CI-user-only",
        "source_profiles": list(ALLOWED_STOCK_PLAYERS),
        "source_pair": [p.name for p in entries],
        "members": manifest,
        "includes_rom": False,
        "includes_executable": False,
        "release_gate_credit": 0,
    }
    (evidence / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
