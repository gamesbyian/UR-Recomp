#!/usr/bin/env python3
"""QA-01: check *executed* original/native Zoo PPU fade steps on absolute hosts.

Replays the retained original Snes9x and Baldosa artifact from the green
source-calibrated real 2014 Zoo movie. No ROM/input patch, no guest re-run, no
inferred CPU/beam-phase alignment, no complete-event release admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ARCHIVE_SHA = "fa4257054694749d2519445008076a7924df0d951ead8a57b4be7c846cf51591"
ARCHIVE_RUN = 38511451553
ARCHIVE_ARTIFACT = 11870616073
ORIGINAL_ENTRY = 1604
NATIVE_ENTRY = 1606
PC_RECEIPT = "ZOOPCRETURN f=6636 v=248 pc=80A09A"
FADE = (2, 4, 6, 8, 10, 12, 14)
BLANK_SAMPLE = tuple(range(5032, 5036))
FADE_SAMPLE = tuple(range(5155, 5176))
SOURCE_LOG = "original-boundary.log"
NATIVE_LOG = "native-boundary/log.txt"
PC_LOG = "original-pc.log"
DUMP_LINE = re.compile(r"^script f=(\d+) dump ([A-Za-z0-9-]+) (.+)$", re.MULTILINE)
ORIGINAL_DUMP = re.compile(
    r"fb=256x224 RGB565 sram=8192 ppuw=\d+(?: \(truncated\))?")


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def member(z: zipfile.ZipFile, name: str) -> bytes:
    entries = [i for i in z.infolist() if i.filename == name]
    if len(entries) != 1 or entries[0].is_dir():
        raise ValueError("missing or duplicate original/native artifact " + name)
    if (entries[0].external_attr >> 16) & 0o170000 == 0o120000:
        raise ValueError("symlink not a source-authenticated archive member")
    return z.read(name)


def receipts(log: str, side: str) -> tuple[int, dict[int, int]]:
    required = set(BLANK_SAMPLE) | set(FADE_SAMPLE)
    entry = []
    pairs = []
    for label_frame, label, transport in DUMP_LINE.findall(log):
        if label == "scene-entered":
            entry.append(int(label_frame))
            continue
        if not label.startswith("boundary-"):
            continue
        if side == "original":
            valid = ORIGINAL_DUMP.fullmatch(transport) is not None
        else:
            valid = side == "native" and transport == "ok"
        if not valid:
            raise ValueError(side + " malformed real host dump receipt")
        try:
            relative = int(label.removeprefix("boundary-"))
        except ValueError as exc:
            raise ValueError("bad boundary label") from exc
        if relative in required:
            pairs.append((relative, int(label_frame)))
    expected_entry = ORIGINAL_ENTRY if side == "original" else NATIVE_ENTRY
    if entry != [expected_entry]:
        raise ValueError(side + " scene entry not independently attested")
    if set(pair[0] for pair in pairs) != required or len(pairs) != len(required):
        raise ValueError(side + " missing or duplicate fixed-frame source receipts")
    if pairs != sorted(pairs):
        raise ValueError(side + " original guest dump receipt order changed")
    if any(host != expected_entry + rel for rel, host in pairs):
        raise ValueError(side + " actual dump frame did not match source movie clock")
    return expected_entry, dict(pairs)


def sample_state(z: zipfile.ZipFile, side: str, frame: int, host: int) -> dict:
    prefix = ("original-boundary" if side == "original"
              else "native-boundary/dump")
    base = f"{prefix}/boundary-{frame:05d}"
    wram = member(z, base + ".wram.bin")
    if len(wram) != 131072:
        raise ValueError("not a real original/native 128-KiB guest RAM observation")
    reg_raw = member(z, base + ".regs.json")
    data = json.loads(reg_raw)
    if side == "original":
        if data.get("frame_tag") != host:
            raise ValueError("source original PPU register frame tag wrong")
        b = data.get("fillram", {}).get("2100")
        if not isinstance(b, str) or not re.fullmatch("[0-9A-Fa-f]{2}", b):
            raise ValueError("source original 2100 effective register byte not sampled")
        inidisp = int(b, 16)
    else:
        if data.get("frame") != host or type(data.get("inidisp")) is not int:
            raise ValueError("native PPU register sample did not attest real host frame")
        inidisp = data["inidisp"]
    if not 0 <= inidisp <= 255:
        raise ValueError("invalid source/native hardware PPU 2100 byte")
    if wram[0x0EF1] != 0 or wram[0x1199] != 1 or wram[0x119D] != 1:
        raise ValueError("source Zoo P1 circuit/lap/finish anchor invalid")
    return {
        "guest_relative_frame": frame,
        "actual_host_frame": host,
        "ppu_inidisp": inidisp,
        "ppu_regs_sha256": digest(reg_raw),
        "full_wram_sha256": digest(wram),
    }


def summarize(original: dict[int, dict], native: dict[int, dict]) -> dict:
    for name, rows in (("original", original), ("native", native)):
        if set(rows) != set(BLANK_SAMPLE) | set(FADE_SAMPLE):
            raise ValueError(name + " missing original/native exact phase samples")
        if any(rows[f]["ppu_inidisp"] != 0x0F for f in range(5032, 5034)):
            raise ValueError(name + " failed authentic pre-blank source brightness")
        if any(rows[f]["ppu_inidisp"] != 0x80 for f in range(5034, 5036)):
            raise ValueError(name + " failed original return forced-blank onset")
    fade_rows = {}
    for name, rows in (("original", original), ("native", native)):
        last, steps = 0x80, []
        for frame in FADE_SAMPLE:
            v = rows[frame]["ppu_inidisp"]
            if v == last:
                continue
            if last == 0x80 and v != FADE[0]:
                raise ValueError(name + " fade-in began with wrong PPU brightness")
            if v < last and last != 0x80:
                raise ValueError(name + " PPU fade brightness reversed")
            steps.append((frame, v))
            last = v
        expected = [((5166 if name == "original" else 5164) + i, v)
                    for i, v in enumerate(FADE)]
        if steps != expected:
            raise ValueError(name + " actual result fade source cadence drifted")
        fade_rows[name] = [
            {"brightness": v, "scene_relative_frame": f,
             "absolute_host_frame": rows[f]["actual_host_frame"]}
            for f, v in steps
        ]
    absolute = [
        {
            "ppu_brightness": FADE[i],
            "original_relative": fade_rows["original"][i]["scene_relative_frame"],
            "native_relative": fade_rows["native"][i]["scene_relative_frame"],
            "original_actual_host": fade_rows["original"][i]["absolute_host_frame"],
            "native_actual_host": fade_rows["native"][i]["absolute_host_frame"],
        }
        for i in range(len(FADE))
    ]
    identical_host = all(row["original_actual_host"] == row["native_actual_host"]
                         for row in absolute)
    if not identical_host:
        raise ValueError("actual original/native fade brightness absolute host drifted")
    if (original[5034]["actual_host_frame"],
            native[5034]["actual_host_frame"]) != (6638, 6640):
        raise ValueError("actual forced-blank source/native host offset drifted")
    return {
        "schema": "UR-QA01-ZOO-SOURCE-NATIVE-ABSOLUTE-HOST-PPU-FADE/1",
        "source_run": ARCHIVE_RUN,
        "source_artifact": ARCHIVE_ARTIFACT,
        "original_source_scene_entry": ORIGINAL_ENTRY,
        "native_scene_entry": NATIVE_ENTRY,
        "source_native_forced_blank_first_relative": {"original": 5034, "native": 5034},
        "source_native_forced_blank_first_absolute_host":
            {"original": 6638, "native": 6640},
        "first_result_fade_scene_relative": {"original": 5166, "native": 5164},
        "first_result_fade_absolute_host": {"original": 6770, "native": 6770},
        "each_result_fade_brightness_absolute_host_exact_match": identical_host,
        "seven_executed_source_native_brightness_steps": absolute,
        "original_source_usa_cpu_pc_return_scope": "80:A09A",
        "source_original_cpu_pc_frame": 6636,
        "source_original_cpu_pc_vcounter": 248,
        "source_original_cpu_pc_not_proven_direct_forced_blank_writer": True,
        "native_same_pc_or_CPU_beam_phase_not_proven": True,
        "source_result_text_guest_relative_5163_native_5162_remains_strict_divergence": True,
        "complete_original_native_usa_events_accepted": 0,
        "total_usa_events": 45,
    }


def analyze(path: Path, *, expected_sha: str = ARCHIVE_SHA) -> dict:
    raw = path.read_bytes()
    if digest(raw) != expected_sha:
        raise ValueError("not exactly the pinned original/native executed ZIP")
    with zipfile.ZipFile(path) as z:
        result = {}
        for side, log_name in (("original", SOURCE_LOG), ("native", NATIVE_LOG)):
            log = member(z, log_name).decode("utf-8")
            entry, ticks = receipts(log, side)
            if entry != (ORIGINAL_ENTRY if side == "original" else NATIVE_ENTRY):
                raise ValueError("entry marker changed")
            result[side] = {
                f: sample_state(z, side, f, ticks[f])
                for f in sorted(ticks)
            }
        pc_log = member(z, PC_LOG).decode("utf-8")
        if sum(x.strip() == PC_RECEIPT for x in pc_log.splitlines()) != 1:
            raise ValueError("original USA executing result-return source PC unverified")
    report = summarize(result["original"], result["native"])
    report["archive_zip_sha256"] = digest(raw)
    report["original_real_ppu_sample_count"] = len(result["original"])
    report["native_real_ppu_sample_count"] = len(result["native"])
    report["original_ppu_snapshot_source_hashes"] = {
        str(f): result["original"][f]["ppu_regs_sha256"] for f in sorted(result["original"])
    }
    report["native_ppu_snapshot_source_hashes"] = {
        str(f): result["native"][f]["ppu_regs_sha256"] for f in sorted(result["native"])
    }
    report["original_pc_transcript_sha256"] = digest(pc_log.encode("utf-8"))
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = analyze(args.artifact)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "seven_source_native_fade_hosts_aligned":
            result["each_result_fade_brightness_absolute_host_exact_match"],
        "official_complete_usa_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
