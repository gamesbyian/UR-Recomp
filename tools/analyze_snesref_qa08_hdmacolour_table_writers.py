#!/usr/bin/env python3
"""Group original emulator's *executed* WRAM colour-table writer candidates.

The writer probe is not a PPU colour-math oracle. It identifies the guest
instruction PC that changed an actual WRAM byte in an explicitly scoped
original Snes9x run. Independent same-input provenance is still required
to pair such PCs with the accepted pinned Baldosa native HDMA byte stream.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

RX = re.compile(
    r"^UR_QA08_COLDATA_TABLE_WRITER frame=(\d+) v=(\d+) "
    r"pc=([0-9A-F]{6}) addr=7E:([0-9A-F]{4}) "
    r"before=([0-9A-F]{2}) after=([0-9A-F]{2})$"
)
SOURCES = {"2086":"2F","2089":"40","208C":"80","208F":"20","2092":"53","2095":"80"}

def accepted_native_sources(native: Path) -> dict[str, str]:
    """Reconcile exact original-native source report OR its hash-bound handoff."""
    j = json.loads(native.read_text(encoding="utf8"))
    if j.get("schema") == "qa08-original-native-channel5-coldata-source-handoff/1":
        if (j.get("status") != "strict-native-AOT-coldata-source-provenance-accepted"
                or j.get("HDMA_channel") != 5 or j.get("HDMA_mode") != 1
                or j.get("HDMA_indirect") is not False
                or j.get("identical_original_guest_CRC_records") != 2473
                or j.get("source_overlay_BG3_OBJ_pixels_native_accepted") != 26
                or j.get("PPU_BBUS_register") != "$2132"
                or j.get("A_bus_WRAM_bank") != "$7E"
                or len(j.get("native_writes", [])) != 7):
            raise ValueError("accepted native channel5 source-byte handoff invalid")
        rows = j["native_writes"]
        if [r["ordinal"] for r in rows] != list(range(7)):
            raise ValueError("native channel5 write order invalid")
        if (len(j.get("downloaded_zip_sha256", "")) != 64 or
                len(j.get("original_source_report_sha256", "")) != 64):
            raise ValueError("native channel5 source archive provenance invalid")
        pairs = [
            (r["A_bus_byte_address"].split(":")[1],
             r["COLDATA_value"].removeprefix("0x"))
            for r in rows
            if r["A_bus_byte_address"].startswith("7E:")
        ]
        if len(pairs) != 7:
            raise ValueError("native channel5 writer bank changed")
        observed = dict(pairs)
    elif j.get("schema") == "qa08-native-HDMA-COLDATA-original-source-provenance/1":
        if (j.get("direct_native_HDMA_COLDATA_written_bytes") != 7
                or j.get("HDMA_channels_recorded") != {"5": 7}):
            raise ValueError("independently accepted native channel5 source-byte report required")
        observed = {
            x["A_bus_source"].split(":")[1]: x["COLDATA_written_byte"][2:]
            for x in j["records"]
        }
    else:
        raise ValueError("independently accepted native channel5 source-byte report required")
    if observed != SOURCES:
        raise ValueError("native observed colour-table byte identity changed")
    return observed


def report(log: Path, native: Path) -> dict:
    accepted_native_sources(native)
    text=log.read_text(encoding="utf8",errors="replace").splitlines()
    if any("UR_QA08_COLDATA_TABLE_WRITER_OVERFLOW" in line for line in text):
        raise ValueError("bounded guest writer trace truncated")
    lines=[x for x in text if "UR_QA08_COLDATA_TABLE_WRITER" in x]
    if not lines or len(lines)>4096:
        raise ValueError("missing or truncated original executed guest writer records")
    rows=[]
    for seq,line in enumerate(lines):
        m=RX.fullmatch(line)
        if m is None:
            raise ValueError("malformed original emulator guest writer record")
        frame,v=map(int,m.group(1,2))
        pc=m.group(3)
        addr=m.group(4)
        before=int(m.group(5),16)
        after=int(m.group(6),16)
        if (frame<0 or frame>500000 or v>261 or
                not (0x2084<=int(addr,16)<=0x2097) or before==after):
            raise ValueError("original guest writer trace frame/WRAM data invalid")
        rows.append({
            "record_index":seq,"original_emulator_frame":frame,
            "original_emulator_scanline_tag":v,
            "executed_guest_PC":pc,
            "WRAM_address":f"7E:{addr}",
            "previous_byte":f"0x{before:02X}",
            "written_byte":f"0x{after:02X}",
            "matches_native_COLDATA_source_value_at_address":
                addr in SOURCES and f"{after:02X}"==SOURCES[addr],
        })
    pc_counts=Counter(x["executed_guest_PC"] for x in rows)
    source_last={}
    for x in rows:
        addr=x["WRAM_address"].split(":")[1]
        if addr in SOURCES:
            source_last[addr]=x
    matching={k:x for k,x in source_last.items()
              if x["matches_native_COLDATA_source_value_at_address"]}
    return {
        "schema":"qa08-original-snes9x-executed-colour-HDMA-WRAM-table-writers/1",
        "source_original_emulator_log":log.name,
        "native_reference_source_frame":2208,
        "native_original_guest_CRC_equal":2473,
        "original_emulator_writer_events":len(rows),
        "distinct_executed_guest_PCs":dict(sorted(pc_counts.items())),
        "native_source_byte_values":SOURCES,
        "last_guest_writer_matching_native_source_value":matching,
        "all_six_native_table_source_bytes_matched_at_last_observed_write":
            set(matching)==set(SOURCES),
        "paired_identical_original_native_input_and_frame_verified":False,
        "ROM_PC_producer_causality_proven":False,
        "physical_hardware_HDMA_timing_proven":False,
        "events":rows,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",required=True,type=Path)
    p.add_argument("--native-source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=report(a.log,a.native_source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(f"QA08_ORIGINAL_COLDATA_TABLE_WRITER_CANDIDATES events={len(r['events'])} "
          f"matching_source_addresses={len(r['last_guest_writer_matching_native_source_value'])}/6 "
          "same_input_proven=0 physical_hardware=0")


if __name__=="__main__":
    main()
