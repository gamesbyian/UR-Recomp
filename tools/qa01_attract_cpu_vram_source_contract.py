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
BANK80 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 80.txt"
BANK82 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 82.txt"
BANK81 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 81.txt"
BANK83 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 83.txt"
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


# Direct original-USA caller path into the first-load *candidate* stores.
# Archived opcodes 22 are long calls even where the historical listing spells
# them JSR. Do not infer execution from a source xref.
ORIGINAL_HUD_CALLER_ANCHORS = {
    "bank81_wrapper": (
        "81/CCE6: 20 07 CD     JSR $CD07",
        "81/CCE9: 6B           RTL",
    ),
    "bank82_race_setup": (
        "82/DBF7: 8D F1 0E     STA $0EF1",
        "82/DBFA: 8D F3 0E     STA $0EF3",
        "82/DC13: 22 05 C6 81  JSR $81C605",
        "82/DC17: 20 1F DC     JSR $DC1F",
        "82/DC1A: 22 E6 CC 81  JSR $81CCE6",
        "82/DC1E: 60           RTS",
    ),
}


def hud_direct_caller_source_contract(bank81: str, bank82: str) -> dict:
    for label, source in (("bank81_wrapper", bank81),
                          ("bank82_race_setup", bank82)):
        listing = source.splitlines()
        offsets = []
        for line in ORIGINAL_HUD_CALLER_ANCHORS[label]:
            matches = [i for i, actual in enumerate(listing)
                       if actual.startswith(line)]
            if len(matches) != 1:
                raise ValueError(f"missing/duplicate/changed original HUD caller: {line}")
            offsets.append(matches[0])
        if offsets != sorted(set(offsets)):
            raise ValueError(f"original HUD caller order changed: {label}")
    # This pins the static chain, not a total xref census for every indirect
    # dispatch in all regions/ROM mirrors or a host-frame execution receipt.
    return {
        "source_wrapper_pc": "81:CCE6",
        "source_wrapper_target_pc": "81:CD07",
        "source_race_setup_caller_pc": "82:DC1A",
        "race_setup_lap_initialization_pcs": ["82:DBF7", "82:DBFA"],
        "race_setup_before_hud_call_pcs": ["82:DC13", "82:DC17"],
        "original_cpu_executed_hud_in_host_248_to_278_proven": False,
        "hud_path_exclusive_vram_writer_in_first_load_proven": False,
        "all_indirect_callers_excluded": False,
    }


# The original menu/logo load has its own direct upload call chain. This
# is not an executed-PC receipt or an assertion that the first dark run was
# necessarily produced by either function.
ORIGINAL_ATTRACT_UPLOAD_ANCHORS = {
    "bank80_attract": (
        "80/93FB: E2 20        SEP #$20",
        "80/9400: A9 80        LDA #$80",
        "80/9402: 8D 00 21     STA $2100",
        "80/9419: A9 4E        LDA #$4E",
        "80/941B: 22 D8 B1 82  JSR $82B1D8",
        "80/9422: A9 48        LDA #$48",
        "80/9424: 22 D8 B1 82  JSR $82B1D8",
    ),
    "bank80_logo": (
        "80/B0A4: A9 50        LDA #$50",
        "80/B0A6: 22 D8 B1 82  JSR $82B1D8",
        "80/B0AD: A9 4A        LDA #$4A",
        "80/B0AF: 22 D8 B1 82  JSR $82B1D8",
        "80/B0C3: 20 C9 FA     JSR $FAC9",
    ),
    "bank82_cpu_upload": (
        "82/B1D8: 08           PHP",
        "82/B1DB: E2 20        SEP #$20",
        "82/B1DD: 8E 16 21     STX $2116",
        "82/B1E9: A5 4D        LDA $4D",
        "82/B1EB: C9 80        CMP #$80",
        "82/B1ED: F0 19        BEQ $B208",
        "82/B1F2: 20 93 B2     JSR $B293",
        "82/B1F5: 8F 18 21 00  STA $002118",
        "82/B1F9: 20 93 B2     JSR $B293",
        "82/B1FC: 8F 19 21 00  STA $002119",
        "82/B200: CA           DEX",
        "82/B201: CA           DEX",
        "82/B202: D0 EE        BNE $B1F2",
        "82/B216: 22 89 BB 81  JSR $81BB89",
    ),
    "bank81_decompress_cpu_upload": (
        "81/BB89: C2 39        REP #$39",
        "81/BCEE: 8F 19 21 00  STA $002119",
        "81/BCF4: 8F 18 21 00  STA $002118",
    ),
}


def attract_upload_direct_source_contract(bank80: str, bank81: str,
                                          bank82: str) -> dict:
    sources = {
        "bank80_attract": bank80,
        "bank80_logo": bank80,
        "bank82_cpu_upload": bank82,
        "bank81_decompress_cpu_upload": bank81,
    }
    for label, anchor_lines in ORIGINAL_ATTRACT_UPLOAD_ANCHORS.items():
        actual = sources[label].splitlines()
        positions = []
        for anchor in anchor_lines:
            matches = [i for i, line in enumerate(actual)
                       if line.startswith(anchor)]
            if len(matches) != 1:
                raise ValueError(f"missing/duplicate/altered original upload source: {anchor}")
            positions.append(matches[0])
        if positions != sorted(set(positions)):
            raise ValueError(f"original upload caller/store ordering changed: {label}")
    return {
        "source_attract_entry_pc": "80:93FB",
        "source_attract_upload_call_pcs": ["80:941B", "80:9424"],
        "source_logo_upload_call_pcs": ["80:B0A6", "80:B0AF"],
        "source_cpu_upload_entry_pc": "82:B1D8",
        "source_byte_upload_loop_pcs": ["82:B1F2", "82:B1F5", "82:B1F9",
                                       "82:B1FC", "82:B200", "82:B201",
                                       "82:B202"],
        "source_compressed_branch_pc": "82:B1ED",
        "source_compressed_call_pc": "82:B216",
        "source_decompress_entry_pc": "81:BB89",
        "source_decompress_byte_store_pcs": ["81:BCEE", "81:BCF4"],
        "source_upload_m8_mode": "82:B1DB SEP #$20",
        "full_source_upload_word_count_executed_proven": False,
        "actual_original_host_248_278_writer_pcs_observed": False,
        "selected_original_compression_branch_dynamically_observed": False,
        "original_memory_speed_at_upload_proven": False,
        "full_first_load_timing_causality_proven": False,
    }


def conditional_long_store_master_clocks(width_bytes: int, memsel: int) -> dict:
    """One STA long to SNES PPU I/O; does not assume observed CPU mode."""
    if width_bytes not in (1, 2):
        raise ValueError("STA long requires 8-bit or 16-bit data width")
    if memsel not in (0, 1):
        raise ValueError("MEMSEL must be 0 or 1")
    code_speed = 6 if memsel else 8  # bank 82:$B1xx or bank 81:$BBxx
    fetch_bytes = 4  # STA long opcode plus 24-bit operand
    old = (fetch_bytes + width_bytes) * code_speed
    paced = fetch_bytes * code_speed + width_bytes * 6  # bank00 PPU I/O
    return {
        "width_bytes": width_bytes,
        "memsel": memsel,
        "old_uniform_master_clocks": old,
        "baldosa_paced_master_clocks": paced,
        "old_minus_paced_master_clocks": old - paced,
        "actual_source_pc_executed_in_host_window": False,
        "first_load_timing_causality_proven": False,
    }


MEMSEL_ORIGINAL_OPCODE_ANCHORS = {
    "bank80_boot_fastrom_set": (
        "80/91E8: A9 01        LDA #$01",
        "80/91EA: 8D 0D 42     STA $420D",
    ),
    "bank80_boot_slowrom_reset": (
        "80/92E8: 9C 0D 42     STZ $420D",
        "80/9311: 4C 5B 88     JMP $885B",
    ),
    "bank83_game_fastrom_set": (
        "83/CC6D: A9 01        LDA #$01",
        "83/CC6F: 8D 0D 42     STA $420D",
    ),
    "bank83_other_slowrom_reset": (
        "83/FA39: 9C 0D 42     STZ $420D",
    ),
}


def memsel_direct_source_writers(bank80: str, bank83: str) -> dict:
    # Direct absolute source writes only; no dynamic control-flow guarantee.
    origins = {
        "bank80_boot_fastrom_set": bank80,
        "bank80_boot_slowrom_reset": bank80,
        "bank83_game_fastrom_set": bank83,
        "bank83_other_slowrom_reset": bank83,
    }
    result = {}
    for name, lines in MEMSEL_ORIGINAL_OPCODE_ANCHORS.items():
        source = origins[name].splitlines()
        offsets = []
        for line in lines:
            hits = [i for i, actual in enumerate(source) if actual.startswith(line)]
            if len(hits) != 1:
                raise ValueError(f"missing/duplicate/changed original MEMSEL opcode: {line}")
            offsets.append(hits[0])
        if offsets != sorted(set(offsets)):
            raise ValueError(f"original MEMSEL source ordering changed: {name}")
        writer_line = next(line for line in lines if "$420D" in line)
        result[name] = writer_line.split(":", 1)[0].replace("/", ":")
    for bank, source in (("80", bank80), ("83", bank83)):
        writers = [x.split(":", 1)[0].replace("/", ":") for x in source.splitlines()
                   if x.startswith(bank + "/") and "$420D" in x]
        if len(writers) != 2:
            raise ValueError(f"unexpected original bank-{bank} direct MEMSEL writer count")
    result["all_memsel_writers_dynamically_executed_in_first_load_proven"] = False
    result["first_load_memsel_value_proven"] = False
    result["original_unobserved_indirect_memsel_writers_excluded"] = False
    return result


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
    result["original_attract_upload_direct_source"] = attract_upload_direct_source_contract(
        BANK80.read_text(encoding="utf-8"),
        BANK81.read_text(encoding="utf-8"),
        BANK82.read_text(encoding="utf-8"),
    )
    result["conditional_sta_long_ppu_clock_scenarios"] = [
        conditional_long_store_master_clocks(width, memsel)
        for memsel in (0, 1) for width in (1, 2)
    ]
    result["original_hud_direct_caller_source"] = hud_direct_caller_source_contract(
        BANK81.read_text(encoding="utf-8"),
        BANK82.read_text(encoding="utf-8"),
    )
    result["original_direct_memsel_source_writers"] = memsel_direct_source_writers(
        BANK80.read_text(encoding="utf-8"),
        BANK83.read_text(encoding="utf-8"),
    )
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
