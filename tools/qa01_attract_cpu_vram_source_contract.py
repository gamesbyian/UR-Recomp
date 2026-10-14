#!/usr/bin/env python3
"""QA-01: static original USA CPU-to-VRAM writer and AOT timing preflight.

This is a source contract for the independently observed old-native first-load
slowdown (research RF-014). The *executed* 738-word/frame claim is external
candidate evidence; 65816 source bytes alone cannot measure any host frames,
CPU cycles, live M flags or the guest's exact instruction participation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK81 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 81.txt"
BALDOSA_BANK00 = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/recomp/bank00.cfg"
BALDOSA_BANK81 = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/recomp/bank81.cfg"
SCHEMA = "UR-QA01-ORIGINAL-CPU-VRAM-FIRST-LOAD-SOURCE/1"
SOURCE_SPAN = (0xCD70, 0xD09C)
INSTRUCTION = re.compile(r"^81/([0-9A-F]{4}): ([0-9A-F]{2}(?: [0-9A-F]{2})*)\s{2,}(.+)$")

# These are exact opcode-level anchors, not runtime PC observations.
SOURCE_ANCHORS = (
    "81/CD43: C2 30        REP #$30",
    "81/CD51: 4C 7F CE     JMP $CE7F",
    "81/CD6D: 8C 16 21     STY $2116",
    "81/CD70: 8D 18 21     STA $2118",
    "81/CD7A: 8C 16 21     STY $2116",
    "81/CD7D: 8D 18 21     STA $2118",
    "81/D09C: 8D 18 21     STA $2118",
    "81/BB89: C2 39        REP #$39",
    "81/BCEE: 8F 19 21 00  STA $002119",
    "81/BCF4: 8F 18 21 00  STA $002118",
)
EXPECTED_STORES = {"$2116": 28, "$2118": 29}


def original_rows(source: str) -> dict[int, tuple[str, str]]:
    rows: dict[int, tuple[str, str]] = {}
    for line in source.splitlines():
        m = INSTRUCTION.match(line)
        if not m:
            continue
        pc = int(m.group(1), 16)
        if pc in rows:
            raise ValueError(f"duplicate archived original PC: 81:{pc:04X}")
        rows[pc] = (m.group(2), m.group(3).strip())
    if not rows:
        raise ValueError("original bank-81 archive missing")
    return rows


def _attest_line(source: str, line: str) -> None:
    if len([x for x in source.splitlines() if x.startswith(line)]) != 1:
        raise ValueError(f"missing, duplicated or changed original opcode: {line}")


# Conditional model transcribed from the two pinned emitter variants:
# legacy emit_function charges each 65816 CPU cycle at its *code* bus
# speed; Baldosa's opt-in paced_bus charges operand fetch bytes at code
# speed and each guest data-store byte at the destination's region speed.
# See baldosa/snesrecomp@075fbe4 recompiler/v2/emit_function.py (the
# _paced_block_master path) and recompiler/snes_cycles.py::region_speed.
# This is a single STA/STY absolute instruction scenario, not the complete
# runtime or a measurement of which MEMSEL/M/X state was active in RF-014.
def conditional_abs_store_master_clocks(width_bytes: int, memsel: int) -> dict:
    if width_bytes not in (1, 2):
        raise ValueError("STA/STY absolute data width must be one or two bytes")
    if memsel not in (0, 1):
        raise ValueError("MEMSEL must be 0 or 1, not inferred from a host frame")
    code_region_speed = 6 if memsel else 8  # bank 81:CDxx
    ppu_io_speed = 6  # $00:2116/$00:2118 and next byte
    fetch_bytes = 3  # STA/STY absolute opcode + 16-bit address
    static_cpu_cycles = fetch_bytes + width_bytes  # 4 (8-bit), 5 (16-bit)
    legacy = static_cpu_cycles * code_region_speed
    paced = fetch_bytes * code_region_speed + width_bytes * ppu_io_speed
    return {
        "accumulator_or_index_width_bits": width_bytes * 8,
        "memsel": memsel,
        "code_region_speed": code_region_speed,
        "ppu_io_region_speed": ppu_io_speed,
        "static_cpu_cycles": static_cpu_cycles,
        "old_uniform_code_speed_master_clocks": legacy,
        "baldosa_paced_bus_master_clocks": paced,
        "old_minus_paced_master_clocks": legacy - paced,
        "actually_executed_first_load_width_or_memsel_proven": False,
        "entire_frame_clock_discrepancy_explained": False,
    }


def report(bank81: str, bank00_cfg: str, bank81_cfg: str) -> dict:
    rows = original_rows(bank81)
    for line in SOURCE_ANCHORS:
        _attest_line(bank81, line)
    stores: dict[str, list[str]] = {x: [] for x in EXPECTED_STORES}
    for pc, (hexbytes, mnemonic) in rows.items():
        if not SOURCE_SPAN[0] <= pc <= SOURCE_SPAN[1]:
            continue
        if mnemonic not in ("STA $2116", "STY $2116", "STA $2118"):
            continue
        # These CPU writes must be absolute-mode stores to the PPU I/O ports,
        # not inferred DMA bursts or automatically word-width stores.
        dest = mnemonic.split("$")[1]
        expected = "8D 18 21" if dest == "2118" else (
            "8C 16 21" if mnemonic.startswith("STY") else "8D 16 21"
        )
        if hexbytes != expected:
            raise ValueError(f"wrong original CPU PPU-store bytes at 81:{pc:04X}")
        stores["$" + dest].append(f"81:{pc:04X}")
    for port, expected_count in EXPECTED_STORES.items():
        if len(stores[port]) != expected_count:
            raise ValueError(f"wrong original {port} site count: "
                             f"{len(stores[port])} != {expected_count}")
    if stores["$2118"][0] != "81:CD70" or stores["$2118"][-1] != "81:D09C":
        raise ValueError("original source upload region boundaries changed")
    if stores["$2116"][0] != "81:CD7A":
        # First selected write is at 81:CD7A because span starts at CD70.
        raise ValueError("original source VMAIN address writer boundary changed")

    def cfg_line(cfg: str, directive: str) -> None:
        found = [x.strip() for x in cfg.splitlines()
                 if x.strip() and not x.lstrip().startswith("#")
                 and x.split("#", 1)[0].strip() == directive]
        if len(found) != 1:
            raise ValueError(f"missing/duplicate Baldosa source config: {directive}")
    cfg_line(bank00_cfg, "paced_bus")
    cfg_line(bank81_cfg, "symbol 81cd07 Hud_InitRace_FastRom")
    cfg_line(bank81_cfg, "symbol 81bb89 Decomp_ToVram")

    return {
        "schema": SCHEMA,
        "source_rom": "archived USA bank-81 disassembly",
        "candidate_load_window_host": [248, 278],
        "original_static_span": ["81:CD70", "81:D09C"],
        "source_family": "Hud_InitRace_FastRom",
        "direct_cpu_ppu_address_sites": stores["$2116"],
        "direct_cpu_ppu_data_sites": stores["$2118"],
        "direct_cpu_ppu_address_site_count": 28,
        "direct_cpu_ppu_data_site_count": 29,
        "separate_decompress_to_vram_source": "81:BB89",
        "separate_decompress_ppu_low_byte_writer": "81:BCF4",
        "separate_decompress_ppu_high_byte_writer": "81:BCEE",
        "conditional_cpu_store_clock_scenarios": [
            conditional_abs_store_master_clocks(width, memsel)
            for memsel in (0, 1) for width in (1, 2)
        ],
        "baldosa_config_has_paced_bus": True,
        "paced_bus_is_globally_requested_via_bank00": True,
        "source_instruction_width_per_executed_site_proven": False,
        "actual_original_vram_writes_per_host_frame_proven": False,
        "host_frame_248_original_pc_execution_proven": False,
        "native_old_vs_baldosa_master_cycle_parity_proven": False,
        "upstream_clock_correction_caused_rf014_proven": False,
        "strict_usa_complete_event_acceptances": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("refuse to overwrite prior source result")
    result = report(BANK81.read_text(encoding="utf-8"),
                    BALDOSA_BANK00.read_text(encoding="utf-8"),
                    BALDOSA_BANK81.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "cpu_ppu_port_sites": result["direct_cpu_ppu_data_site_count"],
        "baldosa_paced_bus_configured": True,
        "dynamic_clock_loss_causality_proven": False,
        "release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
