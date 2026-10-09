#!/usr/bin/env python3
"""Summarize real pinned Baldosa route evidence without manufacturing QA passes.

Only route exit status and actual created checkpoints are recorded. The report
never declares a matched original/native event or a 45-course release pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROUTES = ("race_1p", "race_2p_split", "zoomzoo_progress")
GAME_PIN = "10b864b9d14a7b7416dd909eb7b054c88faef101"
FRAMEWORK_PIN = "075fbe4c8e0d97b0013be541795c39cb644a9709"


# Exact USA-retail per-player offsets, independently pinned in
# QA01-NONDRAGSTER-ENTRY-PROGRESSION and the historical Snes9x Zoo trace.
# These sparse snapshots measure *states*, not every intervening contact.
ZOO_SAMPLES = ("go", "after_first_left", "before_long_left", "after_drive")


def zoo_sample(path: Path, name: str) -> dict:
    image = path.read_bytes()
    if len(image) != 0x20000:
        raise ValueError(f"{name}: expected 128 KiB WRAM, got {len(image)} bytes")
    u16 = lambda offset: int.from_bytes(image[offset:offset + 2], "little")
    return {
        "name": name,
        "nmi_handler_0053": f"0x{u16(0x0053):04X}",
        "menu_009f": image[0x009F],
        # The 0313 byte also has other meanings on result screens: only
        # exact 1 plus course ID 1 constitutes active Zoom Zoo here.
        "race_flag_0313": image[0x0313],
        "track_id_00ce": image[0x00CE],
        "active_zoo": image[0x0313] == 1 and image[0x00CE] == 1,
        "p1_world_xy": [u16(0x0411), u16(0x0415)],
        "p1_stored_contact": u16(0x0E95),
        "p1_next_checkpoint": u16(0x1199),
        "p1_finish_gate": u16(0x119D),
        "p1_laps_remaining": u16(0x0EF1),
        "race_stopwatch_raw": [image[o] for o in (
            0x0E0F, 0x0E13, 0x0E17, 0x0E1B, 0x0E1F)],
    }


def zoom_zoo_progression(dumps: Path) -> dict:
    missing = [name for name in ZOO_SAMPLES
               if not (dumps / f"{name}.wram.bin").is_file()]
    if missing:
        return {"complete_samples": False, "missing": missing,
                "scope": "No course-completion or original/native parity credited"}
    rows = [zoo_sample(dumps / f"{name}.wram.bin", name)
            for name in ZOO_SAMPLES]
    differences = []
    for previous, current in zip(rows, rows[1:]):
        if not (previous["active_zoo"] and current["active_zoo"]):
            continue
        changes = {
            field: [previous[field], current[field]]
            for field in ("p1_next_checkpoint", "p1_finish_gate",
                          "p1_laps_remaining", "p1_stored_contact")
            if previous[field] != current[field]
        }
        if changes:
            differences.append({"from": previous["name"],
                                "to": current["name"], "changes": changes})
    return {
        "complete_samples": True,
        "samples": rows,
        "sampled_active_zoo_count": sum(row["active_zoo"] for row in rows),
        "sampled_progress_changes": differences,
        "after_drive_active_zoo": rows[-1]["active_zoo"],
        "after_drive_terminal_menu_gate_f60c": (
            rows[-1]["nmi_handler_0053"] == "0xF60C"),
        "independent_original_emulator_comparison": False,
        "original_native_terminal_result_admitted": False,
        "scope": ("Sparse state readouts under the *upstream* Baldosa driving "
                  "script. A difference between samples does not establish "
                  "which input/contact caused it; absence does not prove "
                  "none occurred between samples. The archived Snes9x 2014 "
                  "Zoom Zoo route is a DIFFERENT input trace. Do not "
                  "interpret the menu-handler F60C wait as a settled result."),
    }


def summarize(evidence: Path) -> dict:
    observed = []
    for name in ROUTES:
        target = evidence / name
        code_path = evidence / f"{name}.exit"
        try:
            exit_code = int(code_path.read_text().strip())
        except (FileNotFoundError, ValueError):
            exit_code = None
        raw = sorted((target / "dump").glob("*.wram.bin"))
        oam = sorted((target / "dump").glob("*.oam.bin"))
        sram = sorted((target / "dump").glob("*.sram.bin"))
        after_drive = target / "dump/after_drive.wram.bin"
        progress = None
        if after_drive.is_file():
            frame = after_drive.read_bytes()
            if len(frame) == 0x20000:
                progress = {
                    "nmi_handler_0053": f"0x{int.from_bytes(frame[0x53:0x55], 'little'):04X}",
                    "go_tick_0e1f": int(frame[0x0E1F]),
                    "terminal_result_admitted": False,
                }
        log = target / "log.txt"
        crc_file = target / "fd/crc.txt"
        crcs = crc_file.read_text(encoding="utf-8").splitlines() if crc_file.is_file() else []
        observed.append({
            "route": name,
            "exit_code": exit_code,
            "ran_and_exited_cleanly": exit_code == 0 and log.is_file(),
            "wram_checkpoints": [p.name for p in raw],
            "oam_checkpoints": [p.name for p in oam],
            "sram_checkpoint_count": len(sram),
            "nonterminal_progress_wram": progress,
            "zoom_zoo_progression": (zoom_zoo_progression(target / "dump")
                                      if name == "zoomzoo_progress" else None),
            "recorded_frame_crc_count": len(crcs),
            "last_frame_crc": crcs[-1] if crcs else None,
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None,
            "original_native_terminal_result_admitted": False,
            "complete_event_qa_credit": 0,
        })
    return {
        "schema_version": 1,
        "source_game_pin": GAME_PIN,
        "source_framework_pin": FRAMEWORK_PIN,
        "test_backend": "SDL2/Xvfb scripted native AOT",
        "meaning": "Baldosa-own-route execution only; independent original/native result parity not established",
        "routes": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = summarize(args.evidence)
    data["upstream_tree_present"] = (args.game / "src/gen/dispatch_v2.c").is_file()
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))
    zoo = next(r for r in data["routes"] if r["route"] == "zoomzoo_progress")
    # A route exit is not enough: retain four genuine valid WRAM snapshots.
    return 0 if (data["upstream_tree_present"] and
                 zoo["zoom_zoo_progression"]["complete_samples"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
