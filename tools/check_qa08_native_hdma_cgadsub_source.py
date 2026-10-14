#!/usr/bin/env python3
"""Strict original-native $2131 companion-source witness to HDMA $2132.

This verifies genuine PPU writes after the native BBUS transfer. The guest,
raster, input, original 26-pixel compositor and 2473 CRC witnesses remain
independent. Six original Snes9x WRAM source values are reference context,
not assumed same-input native acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

RX = re.compile(
    r"^UR_QA08_HDMA_CGADSUB frame=(\d+) tagframe=(\d+) line=(-?\d+) "
    r"channel=(\d+) bbus=([0-9A-F]{2}) value=([0-9A-F]{2}) "
    r"src=([0-9A-F]{2}):([0-9A-F]{4}) mode=(\d+) indirect=([01]) "
    r"table=([0-9A-F]{4}) bank=([0-9A-F]{2}) cgadsub=([0-9A-F]{2})$"
)
# Independently observed executed original USA Snes9x WRAM writer PCs
# at frame1781, recorded in analysis/data/qa08-original-snes9x-2p-
# channel5-eighteen-writer-PCs.json. Actual $2131 first-byte source
# addresses, not the abandoned +1 $2133 hypothesis.
OBSERVED_ORIGINAL_WRAM = {
    0x2085: 0x04, 0x2088: 0x04, 0x208B: 0x04,
    0x208E: 0x04, 0x2091: 0x04, 0x2094: 0x04,
}

def check(log: Path, native_coldata: Path, native_text26: Path) -> dict:
    colour=json.loads(native_coldata.read_text(encoding="utf8"))
    text=json.loads(native_text26.read_text(encoding="utf8"))
    if (colour.get("schema")!="qa08-native-HDMA-COLDATA-original-source-provenance/1"
            or colour.get("guest_frame")!=2208
            or colour.get("direct_native_HDMA_COLDATA_written_bytes")!=7
            or colour.get("HDMA_channels_recorded")!={"5":7}
            or len(colour.get("records",[]))!=7):
        raise ValueError("strict original-native COLDATA channel-5 authority missing")
    if (text.get("guest_frame")!=2208
            or text.get("native_compositor_pixel_records")!=78
            or text.get("guest_CRC_entries_equal")!=2473
            or text.get("stock_native_BG3_main_OBJ_subscreen")!=26
            or text.get("front_removed_native_empty_subscreen")!=26):
        raise ValueError("strict original-native 26-pixel PPU/guest source gate missing")
    raw=log.read_text(encoding="utf8",errors="replace").splitlines()
    if any("UR_QA08_HDMA_CGADSUB_OVERFLOW" in s for s in raw):
        raise ValueError("real native CGADSUB source probe overflow")
    lines=[s for s in raw if "UR_QA08_HDMA_CGADSUB" in s]
    if len(lines)!=7:
        raise ValueError("not precisely seven genuine original-native CGADSUB write records")
    rows=[]
    for ordinal,(line,reference) in enumerate(zip(lines,colour["records"])):
        match=RX.fullmatch(line)
        if match is None:
            raise ValueError("malformed native CGADSUB BBUS source record")
        frame,tagframe,tagline,channel=map(int,match.group(1,2,3,4))
        bbus=int(match.group(5),16)
        val=int(match.group(6),16)
        bank=int(match.group(7),16)
        address=int(match.group(8),16)
        mode=int(match.group(9))
        indirect=int(match.group(10))
        cursor=int(match.group(11),16)
        table_bank=int(match.group(12),16)
        live=int(match.group(13),16)
        original_address=int(reference["A_bus_source"].split(":")[1],16)
        if (frame!=2208 or tagframe!=reference["reported_native_journal_frame"] or
                tagline!=reference["journal_scanline_tag"]
                or bbus!=0x31 or channel!=5 or mode!=1 or indirect!=0
                or bank!=0x7e or table_bank!=0x7e
                or address!=original_address-1
                or cursor!=original_address or reference["HDMA_channel"]!=5
                or reference["DMA_mode"]!=1 or reference["HDMA_indirect"] is not False
                or reference["PPU_register"]!="$2132"
                or live!=val):
            raise ValueError("genuine paired CGADSUB address/channel/PPU state differs")
        source_value=OBSERVED_ORIGINAL_WRAM.get(address)
        rows.append({
            "ordinal":ordinal,
            "native_original_guest_frame":frame,
            "native_source_journal_tag":tagline,
            "native_HDMA_channel":channel,
            "native_HDMA_mode":mode,
            "native_WRAM_source":f"7E:{address:04X}",
            "native_CGADSUB_written_byte":f"0x{val:02X}",
            "native_PPU_CGADSUB_after_write":f"0x{live:02X}",
            "paired_native_COLDATA_source":reference["A_bus_source"],
            "paired_native_COLDATA_byte":reference["COLDATA_written_byte"],
            "original_Snes9x_observed_WRAM_value":
                f"0x{source_value:02X}" if source_value is not None else None,
            "byte_matches_original_Snes9x_if_observed":
                val==source_value if source_value is not None else None,
        })
    first=[r for r in rows if r["native_source_journal_tag"]==0]
    if len(first)!=1 or [r["native_source_journal_tag"] for r in rows]!=[0,2,3,4,113,114,115]:
        raise ValueError("native $2131 source chronology unexpectedly changed")
    source_locations = {int(r["native_WRAM_source"].split(":")[1],16) for r in rows}
    actual_source_values = {int(r["native_WRAM_source"].split(":")[1],16):
                            int(r["native_CGADSUB_written_byte"],16) for r in rows}
    unique_source_matches = sum(actual_source_values.get(a) == v
                                for a,v in OBSERVED_ORIGINAL_WRAM.items())
    return {
        "schema":"qa08-original-native-channel5-mode1-CGADSUB-companion/1",
        "status":"original-native-source-observed-seven-channel5-CGADSUB-writes",
        "original_native_guest_frame":2208,
        "original_native_guest_CRC_entries_equal":2473,
        "observed_native_CGADSUB_companion_records":len(rows),
        "paired_native_COLDATA_records":7,
        "native_WRAM_companion_byte_values_are_actually_measured":True,
        "native_register_after_write_matches_BBUS_value":True,
        "original_executed_2P_unique_WRAM_source_addresses_observed":len(OBSERVED_ORIGINAL_WRAM),
        "native_distinct_CGADSUB_source_addresses":len(source_locations),
        "original_executed_2P_unique_WRAM_source_values_matching_native":unique_source_matches,
        "original_executed_2P_WRAM_source_values_observed":len(OBSERVED_ORIGINAL_WRAM),
        "original_executed_2P_WRAM_source_comparison_matches":
            sum(x["byte_matches_original_Snes9x_if_observed"] is True for x in rows),
        "full_original_native_same_input_parity_proven":False,
        "physical_SNES_hardware_timing_proven":False,
        "HD_character_likeness_approved":False,
        "samples":rows,
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-log",type=Path,required=True)
    p.add_argument("--coldata-report",type=Path,required=True)
    p.add_argument("--text26-report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=check(a.native_log,a.coldata_report,a.text26_report)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("QA08_NATIVE_HDMA_CGADSUB_SOURCE_ACCEPTED guest=2208 bytes=7 "
          f"original5matching={result['original_executed_2P_WRAM_source_comparison_matches']} "
          "full_native_CRC=2473 original_hardware=0 art_approved=0")

if __name__=="__main__":
    main()
