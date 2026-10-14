#!/usr/bin/env python3
"""Authenticate ORIGINAL Snes9x live PPU writes caused by HDMA, not CPU journal.

Presents actual Snes9x $2131/$2132 register readbacks at a real CPU/PPU
beam position. Unmatched original/native values stay empirical differences;
their host frames and raster algorithms are not presumed equivalent.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

MARK = "UR_QA08_ORIGINAL_HDMA_PPU"
RX = re.compile(
    r"^UR_QA08_ORIGINAL_HDMA_PPU frame=(\d+) v=(\d+) cycles=(-?\d+) "
    r"channel=(\d+) mode=(\d+) indirect=([01]) bbus=([0-9A-F]{2}) "
    r"base=([0-9A-F]{2}) source=([0-9A-F]{2}):([0-9A-F]{4}) "
    r"original_wram=([0-9A-F]{2}) byte=([0-9A-F]{2}) "
    r"cgadsub=([0-9A-F]{2}) cgwsel=([0-9A-F]{2}) fixed15=([0-9A-F]{4})$"
)
ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT = "94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
WRAM = "9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6"


def read(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError(f"duplicate original source evidence key {k}")
            result[k] = v
        return result
    out = json.loads(path.read_text(encoding="utf8"), object_pairs_hook=unique)
    if not isinstance(out, dict):
        raise ValueError("invalid original source evidence object")
    return out


def component_write(current: int, value: int) -> int:
    for bit, shift in ((0x20, 0), (0x40, 5), (0x80, 10)):
        if value & bit:
            current = current & ~(31 << shift) | ((value & 31) << shift)
    return current


def check(log: Path, receipt: dict, layout: dict) -> dict:
    if (layout.get("schema") != "qa08-original-2p-channel5-HDMA-executed-opcode-source-layout/1"
            or layout.get("original_USA_ROM_SHA256") != ROM
            or layout.get("original_2P_input_script_SHA256") != SCRIPT
            or layout.get("original_full_t480_WRAM_SHA256") != WRAM
            or layout.get("original_guest_frame") != 1781
            or layout.get("original_independently_executed_writer_PCs") != 18
            or layout.get("original_executed_instructions_captured") != 55
            or receipt.get("USA_ROM_SHA256") != ROM
            or receipt.get("original_script_SHA256") != SCRIPT
            or receipt.get("original_t480_WRAM_SHA256") != WRAM
            or receipt.get("source_65816_writer_PCs") != 18
            or receipt.get("second_camera_0DDB") != 1
            or receipt.get("in_race_0313") != 1
            or receipt.get("native_same_input_frame_parity_proven") is not False):
        raise ValueError("authentic original 2P ROM/input/WRAM/18-writer receipt required")
    if layout.get("full_original_native_same_input_frame_parity_proven") is not False:
        raise ValueError("unsupported full native frame parity claim")
    rows = layout.get("original_table_triplets")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("missing six executed original channel-5 HDMA descriptors")
    table = {}
    for i, row in enumerate(rows):
        start = 0x2084 + 3*i
        if (row.get("start") != f"7E:{start:04X}" or
                row.get("entry") != i or row.get("cgadsub") != "04" or
                row.get("line_count_byte") != ("6D" if i%3==2 else "01")):
            raise ValueError("original executed channel5 table descriptor differs")
        table[start + 1] = ("31", row["cgadsub"])
        table[start + 2] = ("32", row["coldata"])
    lines = log.read_text(encoding="utf8", errors="replace").splitlines()
    if any(MARK+"_OVERFLOW" in line for line in lines):
        raise ValueError("original live PPU source observation overflow")
    obs = [line for line in lines if MARK in line]
    if not 2 <= len(obs) <= 512:
        raise ValueError("original live channel5 register writes absent or overflowing")
    events = []
    for ordinal, text in enumerate(obs):
        m = RX.fullmatch(text)
        if m is None:
            raise ValueError("malformed true original Snes9x PPU HDMA event")
        (frame, v, cycles, channel, mode, indirect, bbus, base, bank, addr,
         wram, value, cgadsub, cgwsel, fixed) = m.groups()
        frame, v, cycles, channel, mode = [int(x) for x in (frame,v,cycles,channel,mode)]
        addr_int, byte, wram_byte, fixed_int = [int(x,16) for x in (addr,value,wram,fixed)]
        if (frame not in {1781,1782,1783,1988,1989,1990,2231,2232,2233,2471,2472,2473}
                or not 0 <= v <= 261
                or not -100000 <= cycles <= 100000 or channel != 5
                or mode != 1 or indirect != "0" or base != "31"
                or bank != "7E" or bbus not in ("31","32")
                or not 0 <= fixed_int <= 0x7fff
                or bbus == "31" and cgadsub != value):
            raise ValueError("original PPU HDMA source configuration/beam invalid")
        if events and (frame,v,cycles) < (
                events[-1]["original_emulator_frame"],
                events[-1]["original_beam_v"],
                events[-1]["cpu_cycles"]):
            raise ValueError("real original Snes9x PPU HDMA chronology regressed")
        source = table.get(addr_int)
        # If original emulator presents a different register/source,
        # this should remain visible as a source divergence, not be
        # silently transformed into native evidence.
        if source is None or source[0] != bbus:
            raise ValueError("source address/channel5 pair outside executed table")
        events.append({
            "ordinal":ordinal,"original_emulator_frame":frame,
            "original_beam_v":v,"cpu_cycles":cycles,
            "native_compatible_mode1_direct_channel5":True,
            "original_live_PPU_register":"$21"+bbus,
            "source":f"7E:{addr}",
            "observed_original_read_WRAM_byte":f"0x{wram_byte:02X}",
            "observed_original_HDMA_PPU_written_byte":f"0x{byte:02X}",
            "original_Wram_equals_BBus_value":byte==wram_byte,
            "original_source_table_expected_byte":"0x"+source[1],
            "observed_byte_matches_prior_executed_original_table":byte==int(source[1],16),
            "original_PPU_CGADSUB_after_write":"0x"+cgadsub,
            "original_PPU_CGWSEL_at_write":"0x"+cgwsel,
            "original_live_PPU_fixed_RGB15_after_write":f"0x{fixed_int:04X}",
            "original_COLDATA_register_is_live":bbus=="32",
        })
    pairs=[]
    if len(events) % 2:
        raise ValueError("one original channel5 HDMA register has no companion")
    for a, b in zip(events[::2], events[1::2]):
        if (a["original_live_PPU_register"] != "$2131"
            or b["original_live_PPU_register"] != "$2132"
            or a["original_emulator_frame"] != b["original_emulator_frame"]
            or a["original_beam_v"] != b["original_beam_v"]
            or a["source"][:-4] != b["source"][:-4]
            or int(b["source"].split(":")[1],16) !=
                 int(a["source"].split(":")[1],16)+1):
            raise ValueError("actual original PPU channel5 mode1 register pair broken")
        pairs.append({
            "original_emulator_frame":a["original_emulator_frame"],
            "beam_v":a["original_beam_v"],
            "source_first":a["source"],"source_second":b["source"],
            "original_CGADSUB":a["observed_original_HDMA_PPU_written_byte"],
            "original_COLDATA":b["observed_original_HDMA_PPU_written_byte"],
            "original_live_fixed15_after_COLDATA":
                b["original_live_PPU_fixed_RGB15_after_write"],
            "source_matches_original_executed_table":
                a["observed_byte_matches_prior_executed_original_table"]
                and b["observed_byte_matches_prior_executed_original_table"],
        })
    return {
        "schema":"qa08-original-Snes9x-executed-channel5-live-PPU-HDMA/1",
        "status":"actual-original-Snes9x-PPU-register-write-source-observed",
        "original_rom_sha256":ROM,"original_source_script_sha256":SCRIPT,
        "original_final_t480_WRAM_sha256":WRAM,
        "original_source_table_writers_executed_at_frame":1781,
        "original_emulator_observed_frame_windows":[[1781,1783],[1988,1990],[2231,2233],[2471,2473]],
        "actual_original_PPU_2131_2132_writes":len(events),
        "actual_original_channel5_register_pairs":len(pairs),
        "source_expected_byte_matches":sum(x["observed_byte_matches_prior_executed_original_table"] for x in events),
        "actual_WRAM_PPU_byte_matches":sum(x["original_Wram_equals_BBus_value"] for x in events),
        "native_accepted_COLDATA_write_count_separate_route":7,
        "source_event_records":events,"actual_mode1_pairs":pairs,
        "source_Snes9x_has_game_specific_OAM_emulation_behavior":True,
        "real_original_native_identical_frame_input_PPU_parity":False,
        "original_CPU_journal_is_live_PPU_HDMA":False,
        "actual_original_Snes9x_finished_PPU_RGB_pixels_sampled":False,
        "physical_SNES_accurate_HBlank_timing_proven":False,
        "HD_character_likeness_approved":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log",type=Path,required=True)
    p.add_argument("--original-receipt",type=Path,required=True)
    p.add_argument("--executed-table",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=check(a.original_log,read(a.original_receipt),read(a.executed_table))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(f"QA08_ORIGINAL_TRUE_PPU_HDMA_OBSERVED writes={report['actual_original_PPU_2131_2132_writes']} "
          f"mode1_pairs={report['actual_original_channel5_register_pairs']} "
          "same_frame_native=0 final_RGB=0")


if __name__ == "__main__":
    main()
