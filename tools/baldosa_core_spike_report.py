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
    return 0 if data["upstream_tree_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
