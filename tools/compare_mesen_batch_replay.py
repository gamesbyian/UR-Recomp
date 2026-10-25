#!/usr/bin/env python3
"""Compare exact pinned MesenCE per-frame and opt-in batched controller replays.

All source WRAM checkpoints must match exactly. No native or release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from run_fixture_mesen import parse_fixture

DUMP_LOG = re.compile(r"^dump ([A-Za-z0-9_-]+): frame=(\d+) bytes=(\d+)$", re.M)
SHA40 = re.compile(r"[a-f0-9]{40}\Z")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checkpoints(script: Path) -> list[str]:
    commands = parse_fixture(script)
    names = [c["tag"] for c in commands if c["op"] == "dump"]
    require(len(names) >= 6 and len(set(names)) == len(names),
            "expected at least six unique genuine source checkpoints")
    return names


def log_frames(path: Path, expected: list[str]) -> dict[str, int]:
    rows = DUMP_LOG.findall(path.read_text(encoding="utf-8"))
    require([r[0] for r in rows] == expected,
            "wrong/missing/duplicated source dump sequence in " + str(path))
    require(all(int(size) == 131072 for _, _, size in rows),
            "noncanonical 128 KiB source WRAM observation")
    frames = {name: int(frame) for name, frame, _ in rows}
    require(all(a < b for a, b in zip(frames.values(), list(frames.values())[1:])),
            "source guest observations not monotonic")
    return frames


def elapsed(path: Path) -> float:
    raw = path.read_text(encoding="ascii").strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError("elapsed-seconds file is invalid") from error
    require(math.isfinite(value) and 0 < value < 1800, "invalid replay elapsed seconds")
    return value


def compare(*, source_sha: str, rom: Path, mesen: Path, inp: Path,
            script: Path, legacy: Path, batched: Path,
            legacy_log: Path, batched_log: Path,
            legacy_time: Path, batched_time: Path) -> dict:
    require(bool(SHA40.fullmatch(source_sha)), "invalid exact source commit")
    for path in (rom, mesen, inp, script, legacy_log, batched_log, legacy_time, batched_time):
        require(path.is_file() and not path.is_symlink(), "missing/redirected immutable input " + str(path))
    require(legacy.is_dir() and batched.is_dir() and
            legacy.resolve() != batched.resolve(), "replay outputs not isolated")
    tags = checkpoints(script)
    old = log_frames(legacy_log, tags)
    new = log_frames(batched_log, tags)
    require(old == new, "original/batched source host frame milestones changed")
    require(all(0 <= frame <= 30000 for frame in old.values()),
            "source guest frames outside bounded fixture")
    listed = {tag + ".wram.bin" for tag in tags}
    require({p.name for p in legacy.glob("*.wram.bin")} == listed,
            "missing/excessive original source dumps")
    require({p.name for p in batched.glob("*.wram.bin")} == listed,
            "missing/excessive batched source dumps")
    rows, first_diff = [], None
    for tag in tags:
        a = legacy / (tag + ".wram.bin")
        b = batched / (tag + ".wram.bin")
        require(a.is_file() and b.is_file() and
                not a.is_symlink() and not b.is_symlink(),
                "missing/redirected source snapshot for " + tag)
        aa, bb = a.read_bytes(), b.read_bytes()
        require(len(aa) == 131072 and len(bb) == 131072,
                "invalid full source WRAM snapshot for " + tag)
        different = next((i for i, (x, y) in enumerate(zip(aa, bb)) if x != y), None)
        if first_diff is None and different is not None:
            first_diff = {"tag": tag, "offset": different,
                          "legacy_byte": aa[different], "batched_byte": bb[different]}
        rows.append({"tag": tag, "frame": old[tag], "bytes": len(aa),
                     "legacy_sha256": hashlib.sha256(aa).hexdigest(),
                     "batched_sha256": hashlib.sha256(bb).hexdigest(),
                     "identical": different is None})
    old_time, new_time = elapsed(legacy_time), elapsed(batched_time)
    return {
        "schema": "ur-mesence-batch-ab/1",
        "source_sha": source_sha,
        "original_rom_sha256": sha(rom),
        "mesen_binary_sha256": sha(mesen),
        "controller_script_sha256": sha(inp),
        "observation_script_sha256": sha(script),
        "legacy_seconds": old_time,
        "batched_seconds": new_time,
        "replay_only_percent_time_reduction": round(100 * (old_time - new_time) / old_time, 2),
        "source_observations": rows,
        "first_wram_difference": first_diff,
        "exact_original_batched_parity": first_diff is None,
        "independent_snes9x_hardware_or_native_parity": False,
        "release_gate_credit": 0,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("source-sha", "rom", "mesen", "input", "script", "legacy", "batched",
                 "legacy-log", "batched-log", "legacy-time", "batched-time", "out"):
        p.add_argument("--" + flag, required=True,
                       type=str if flag == "source-sha" else Path)
    args = p.parse_args()
    result = compare(source_sha=args.source_sha, rom=args.rom, mesen=args.mesen,
                     inp=args.input, script=args.script, legacy=args.legacy,
                     batched=args.batched, legacy_log=args.legacy_log,
                     batched_log=args.batched_log, legacy_time=args.legacy_time,
                     batched_time=args.batched_time)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Original-vs-batched exact WRAM: {sum(x['identical'] for x in result['source_observations'])}/"
          f"{len(result['source_observations'])}; replay-only elapsed "
          f"{result['legacy_seconds']}s vs {result['batched_seconds']}s.")
    return 0 if result["exact_original_batched_parity"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
