#!/usr/bin/env python3
"""RF087: audit existing pinned native dump metadata and paired raw WRAM.

The pinned snes_state_dump already emits .info.json with master_clock, vpos,
and hpos for every scripted .wram.bin. Retain and join those actual files
rather than inserting a second guest-side clock observer. This establishes
native snapshot provenance only, never original/native clock parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TAG_FRAMES = (("scene-05039", 6058), ("scene-05040", 6059))
LOG = re.compile(r"^script f=(\d+) dump ([a-z0-9-]+) (ok|partial)$")


def audit(native_dir: Path, native_log: bytes) -> dict:
    if not native_dir.is_dir() or native_dir.is_symlink():
        raise ValueError("actual native dump directory missing/symlinked")
    log_lines = native_log.decode("utf-8", errors="strict").splitlines()
    observed = {}
    for line in log_lines:
        m = LOG.fullmatch(line)
        if m and m.group(2) in dict(TAG_FRAMES):
            tag = m.group(2)
            if tag in observed:
                raise ValueError("duplicate native snapshot log tag")
            observed[tag] = (int(m.group(1)), m.group(3))
    rows = []
    hashes = {}
    for tag, host in TAG_FRAMES:
        if observed.get(tag) != (host, "ok"):
            raise ValueError("native snapshot log missing, partial or wrong host frame")
        info_path = native_dir / (tag + ".info.json")
        wram_path = native_dir / (tag + ".wram.bin")
        if (not info_path.is_file() or info_path.is_symlink() or
                not wram_path.is_file() or wram_path.is_symlink()):
            raise ValueError("actual native snapshot metadata/WRAM missing or symlinked")
        info_raw, wram = info_path.read_bytes(), wram_path.read_bytes()
        if len(wram) != 131072:
            raise ValueError("native snapshot WRAM must contain exactly 128 KiB")
        try:
            info = json.loads(info_raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("native snapshot metadata malformed") from exc
        if (not isinstance(info, dict) or
                type(info.get("frame")) is not int or info["frame"] != host or
                type(info.get("master_clock")) is not int or info["master_clock"] < 0 or
                type(info.get("vpos")) is not int or not 0 <= info["vpos"] <= 312 or
                type(info.get("hpos")) is not int or not 0 <= info["hpos"] <= 1364 or
                info.get("source") != "snesrecomp"):
            raise ValueError("native snapshot metadata frame/clock/source invalid")
        if rows and info["master_clock"] < rows[-1]["native_master_at_cut"]:
            raise ValueError("native snapshot master clock reversed")
        hashes[tag] = {
            "info_sha256": hashlib.sha256(info_raw).hexdigest(),
            "wram_sha256": hashlib.sha256(wram).hexdigest(),
        }
        rows.append({
            "tag": tag, "frame": host,
            "native_master_at_cut": info["master_clock"],
            "native_vpos_at_cut": info["vpos"],
            "native_hpos_at_cut": info["hpos"],
            "pointer16_at_cut": int.from_bytes(wram[0x63:0x65], "little"),
            "counter8_at_cut": wram[0x69],
        })
    return {
        "schema_version": 2,
        "work_id": "UR-CPU-CAUSE-20261026",
        "native_log_sha256": hashlib.sha256(native_log).hexdigest(),
        "native_cut_rows": rows,
        "native_dump_member_hashes": hashes,
        "cut_source": "pinned snes_state_dump .info.json + .wram.bin",
        "native_snapshot_master_and_wram_observed": True,
        "original_native_clock_registration_proven": False,
        "observer_off_control_proven": False,
        "release_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--native-log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.native_log.is_file() or args.native_log.is_symlink():
        parser.error("actual native replay log missing or symlinked")
    args.out.write_text(json.dumps(audit(args.native_dir, args.native_log.read_bytes()),
                                   sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("QA01_RF087_NATIVE_SNAPSHOT_CUT=" + args.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
