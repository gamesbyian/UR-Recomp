#!/usr/bin/env python3
"""QA-01 original/native Zoo return-handoff, bounded *executed* evidence.

Evaluate new 25-frame dense guest+5048..5072 window against measured source
Snes9x original and native host-script ticks. PPU forced blank is a presentation
signal, not a race finish instruction; historical PAL return PCs are leads
until a pinned USA original emulator actually executes one. No event credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

FRAME_WINDOW = tuple(range(5001, 5050))
SOURCE_PC_LEADS = ("83:C8DD", "83:C8E0", "80:A09A", "83:987D", "80:951C")
ORIGINAL_RECEIPT = re.compile(
    r"fb=256x224 RGB565 sram=8192 ppuw=\d+(?: \(truncated\))?")
DUMP = re.compile(r"^script f=(\d+) dump ([\w-]+) (.+)$", re.MULTILINE)
PC_RECEIPT = re.compile(
    r"^ZOOPCRETURN f=(\d+) v=(\d+) pc=([0-9A-F]{6})$", re.MULTILINE)
PPU_RECEIPT = re.compile(
    r"^ZOOPPUWRITE f=(\d+) v=(\d+) pc=([0-9A-F]{6}) "
    r"old=([0-9A-F]{2}) new=([0-9A-F]{2})$", re.MULTILINE)
SCHEMA = "UR-QA01-ZOO-SOURCE-PC-RETURN-PPU-BRACKET/1"


def full(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing or symlinked source/native guest file: " + str(path))
    return path.read_bytes()


def transcript(log: Path, side: str) -> tuple[int, dict[int, int]]:
    raw = full(log).decode("utf-8")
    matches = {}
    for f, label, detail in DUMP.findall(raw):
        if label != "scene-entered" and not label.startswith("boundary-"):
            continue
        good = (ORIGINAL_RECEIPT.fullmatch(detail) is not None
                if side == "original" else detail == "ok")
        if not good:
            raise ValueError(f"{side} unqualified real host-script receipt {label}")
        matches.setdefault(label, []).append(int(f))
    entry = matches.get("scene-entered", [])
    if len(entry) != 1 or entry[0] <= 0:
        raise ValueError(f"{side} missing/duplicated source scene-entry receipt")
    entry_frame = entry[0]
    out = {}
    for relative in (5000, *FRAME_WINDOW, 5100):
        label = f"boundary-{relative:05d}"
        frames = matches.get(label, [])
        if len(frames) != 1 or frames[0] != entry_frame + relative:
            raise ValueError(f"{side} missing/mistimed/duplicated {label} receipt")
        out[relative] = frames[0]
    return entry_frame, out


def original_pc_receipts(text: str, scene_host: int) -> list[dict]:
    found = []
    for match in PC_RECEIPT.finditer(text):
        frame, v, pc = match.groups()
        name = pc[:2] + ":" + pc[2:]
        if name not in SOURCE_PC_LEADS:
            raise ValueError("source PC out of bounded static candidate set")
        frame = int(frame)
        if not scene_host + 4998 <= frame <= scene_host + 5052:
            raise ValueError("source PC marker outside qualified return scope")
        found.append({
            "original_icpu_frame": frame,
            "source_v_counter": int(v),
            "usa_source_pc_observed_executing": name,
        })
    if len(found) > 100:
        raise ValueError("unbounded source PC occurrences")
    return found


def original_inidisp_cpu_writes(text: str, scene_host: int) -> list[dict]:
    """Executed Snes9x pre/post-opcode PPU $2100 changes, not static leads."""
    out = []
    for f, v, pc, old, new in PPU_RECEIPT.findall(text):
        frame = int(f)
        if not scene_host + 4998 <= frame <= scene_host + 5052:
            raise ValueError("original CPU PPU writer outside bounded return trace")
        before, after = int(old, 16), int(new, 16)
        if before == after:
            raise ValueError("original opcode PPU register delta is not a change")
        out.append({
            "original_icpu_frame": frame, "source_v_counter": int(v),
            "usa_source_pc_observed_executing": pc[:2] + ":" + pc[2:],
            "old_2100": old, "new_2100": new,
            "newly_entered_forced_blank": not bool(before & 0x80)
                                              and bool(after & 0x80),
        })
    if len(out) > 1000:
        raise ValueError("unbounded original PPU source writes")
    return out


def states(folder: Path, ticks: dict[int, int], side: str) -> dict[int, dict]:
    observed = {}
    for relative, host in ticks.items():
        label = f"boundary-{relative:05d}"
        wram = full(folder / (label + ".wram.bin"))
        if len(wram) != 131072:
            raise ValueError(f"{side} incomplete 128-KiB WRAM at +{relative}")
        regs_bytes = full(folder / (label + ".regs.json"))
        regs = json.loads(regs_bytes)
        if side == "original":
            if regs.get("snesref_dbg_version") != 1:
                raise ValueError("not source-qualified pinned Snes9x PPU register snapshot")
            raw_inidisp = regs.get("fillram", {}).get("2100")
            if type(raw_inidisp) is not str or not re.fullmatch(r"[0-9A-Fa-f]{2}", raw_inidisp):
                raise ValueError("original INIDISP missing/invalid")
            inidisp = int(raw_inidisp, 16)
        else:
            inidisp = regs.get("inidisp")
            if type(inidisp) is not int or not 0 <= inidisp <= 255:
                raise ValueError("native INIDISP missing/invalid")
        if any((int.from_bytes(wram[p:p+2], "little")) != q for p, q in
               ((0x0EF1, 0), (0x1199, 1), (0x119D, 1))):
            raise ValueError(f"{side} unexpectedly different finished-course counters")
        observed[relative] = {
            "scene_relative_frame": relative,
            "actual_guest_host_dump_frame": host,
            "inidisp_raw": f"{inidisp:02X}",
            "forced_blank_bit": bool(inidisp & 0x80),
            "wram_sha256": hashlib.sha256(wram).hexdigest(),
            "ppu_regs_sha256": hashlib.sha256(regs_bytes).hexdigest(),
        }
    if observed[5000]["inidisp_raw"] != "0F" or observed[5100]["inidisp_raw"] != "80":
        raise ValueError(f"{side} does not straddle real Zoo visible-to-blank return")
    return observed


def analyze(original_dir: Path, native_dir: Path,
            original_log: Path, native_log: Path, original_pc_log: Path) -> dict:
    entry = {}
    ticks = {}
    rows = {}
    for side, folder, log in (("original", original_dir, original_log),
                               ("native", native_dir, native_log)):
        entry[side], ticks[side] = transcript(log, side)
        rows[side] = states(folder, ticks[side], side)
    source_pc_raw = full(original_pc_log).decode("utf-8")
    pcs = original_pc_receipts(source_pc_raw, entry["original"])
    ppu_writes = original_inidisp_cpu_writes(source_pc_raw, entry["original"])
    source_forced_blank = next((x for x in ppu_writes
                                if x["newly_entered_forced_blank"]), None)
    crossings = {}
    for side in ("original", "native"):
        t = rows[side]
        last_lit = max((f for f in FRAME_WINDOW if not t[f]["forced_blank_bit"]),
                       default=None)
        first_blank = next((f for f in FRAME_WINDOW if t[f]["forced_blank_bit"]), None)
        crossings[side] = {
            "last_nonblank_dense_sample": last_lit,
            "first_forced_blank_dense_sample": first_blank,
            "first_forced_blank_actual_host_frame":
                ticks[side].get(first_blank) if first_blank is not None else None,
            "first_forced_blank_independently_observed":
                first_blank is not None,
            "monotonic_blank_after_first": (
                all(t[f]["forced_blank_bit"] for f in FRAME_WINDOW
                    if first_blank is not None and f >= first_blank)
                if first_blank is not None else None),
        }
    o = crossings["original"]["first_forced_blank_actual_host_frame"]
    n = crossings["native"]["first_forced_blank_actual_host_frame"]
    return {
        "schema": SCHEMA,
        "guest_original_movie_unmodified": True,
        "source_original_pc_candidate_list": SOURCE_PC_LEADS,
        "source_original_pc_executed_receipts": pcs,
        "source_executed_inidisp_cpu_write_scopes": ppu_writes,
        "source_original_first_executing_cpu_pc_setting_forced_blank": source_forced_blank,
        "source_cpu_opcode_scope_does_not_prove_native_execution_phase": True,
        "historical_pal_pc_candidates_missing_are_not_source_negative_proof": True,
        "source_pc_receipt_log_sha256": hashlib.sha256(
            source_pc_raw.encode()).hexdigest(),
        "independent_guest_entry_host": entry,
        "source_original_native_guest_frames": rows,
        "forced_blank_observation": crossings,
        "native_minus_original_first_blank_absolute_host": (
            n - o if n is not None and o is not None else None),
        "first_source_original_guest_finish_instruction_identified": False,
        "cpu_beam_nmi_phase_equivalence_proven": False,
        "this_is_ppu_return_presentation_not_gameplay_finish": True,
        "complete_event_qa_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("original-dir", "native-dir", "original-log", "native-log",
                 "original-pc-log", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.original_dir, a.native_dir, a.original_log,
                     a.native_log, a.original_pc_log)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "forced_blank_observation": result["forced_blank_observation"],
        "source_pc_observed": result["source_original_pc_executed_receipts"],
        "complete_event_qa_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
