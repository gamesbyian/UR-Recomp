#!/usr/bin/env python3
"""Parse original native HDMA COLDATA writes without claiming hardware timing.

Requires a true guest2208 pinned native PPU/guest CRC receipt from the separate
strict two-pixel experiment. Reports actual source channel/table/byte sequence;
does not assign a channel to a specific image row without a beam crosswalk.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

RECORD = re.compile(
    r"^UR_QA08_HDMA_COLDATA frame=(\d+) tagframe=(\d+) line=(-?\d+) "
    r"channel=(\d+) bbus=([0-9A-F]{2}) value=([0-9A-F]{2}) "
    r"src=([0-9A-F]{2}):([0-9A-F]{4}) "
    r"mode=(\d+) indirect=([01]) table=([0-9A-F]{4}) "
    r"bank=([0-9A-F]{2}) fixed15=([0-9A-F]{4})$"
)
PREFIX = "UR_QA08_HDMA_COLDATA"


def parse(log: Path, accepted_two_point: Path) -> dict:
    prior = json.loads(accepted_two_point.read_text(encoding="utf8"))
    if (prior.get("guest_frame") != 2208 or
            prior.get("full_guest_CRC_equal") != 2473 or
            prior.get("native_render_live_fixed_RGB15_by_row") !=
            {"50":"0x000F","162":"0x0260"} or
            prior.get("native_main_BG3_subscreen_OBJ_palette_colour_confirmed_at_two_pixels")
            is not True):
        raise ValueError("authentic independent original-native pixel source gate missing")
    raw=log.read_text(encoding="utf8",errors="replace").splitlines()
    if any("UR_QA08_HDMA_COLDATA_OVERFLOW" in s for s in raw):
        raise ValueError("bounded source-provenance ring truncated")
    lines=[s for s in raw if PREFIX in s]
    if not lines or len(lines)>2048:
        raise ValueError("zero or truncated exact native HDMA COLDATA observations")
    seen=[]
    for ordinal,line in enumerate(lines):
        match=RECORD.fullmatch(line)
        if not match:
            raise ValueError("malformed actual native HDMA source byte")
        frame,tagframe,tagline,ch=map(int,match.group(1,2,3,4))
        bbus=int(match.group(5),16)
        val=int(match.group(6),16)
        bank=int(match.group(7),16)
        addr=int(match.group(8),16)
        mode=int(match.group(9))
        indirect=int(match.group(10))
        table=int(match.group(11),16)
        config_bank=int(match.group(12),16)
        fixed=int(match.group(13),16)
        if (frame!=2208 or tagframe not in (2208,2209) or
                not (0<=tagline<=261) or not (0<=ch<8) or bbus!=0x32 or
                not (0<=mode<8) or fixed>0x7fff):
            raise ValueError("native HDMA channel/register/frame source record invalid")
        seen.append({
            "ordinal":ordinal,
            "physical_emulator_frame":frame,
            "reported_native_journal_frame":tagframe,
            "journal_scanline_tag":tagline,
            "HDMA_channel":ch,
            "PPU_register":"$2132",
            "COLDATA_written_byte":f"0x{val:02X}",
            "selector_R_G_B":[bool(val&(1<<p)) for p in (5,6,7)],
            "A_bus_source":f"{bank:02X}:{addr:04X}",
            "DMA_mode":mode,
            "HDMA_indirect":bool(indirect),
            "current_table_cursor":f"0x{table:04X}",
            "HDMA_table_bank":f"0x{config_bank:02X}",
            "native_live_fixed_RGB15_after_write":f"0x{fixed:04X}",
        })
    channels=Counter(x["HDMA_channel"] for x in seen)
    return {
        "schema":"qa08-native-HDMA-COLDATA-original-source-provenance/1",
        "guest_frame":2208,
        "direct_native_HDMA_COLDATA_written_bytes":len(seen),
        "HDMA_channels_recorded":dict(sorted(channels.items())),
        "source_A_bus_byte_address_observed":True,
        "native_live_fixed_RGB15_observed_after_write":True,
        "two_point_native_PPU_guest_CRC_attested":2473,
        "pixel_row_to_specific_HDMA_channel_causality_proven":False,
        "physical_SNES_HDMA_timing_proven":False,
        "original_or_remastered_PPU_mutation":False,
        "records":seen,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",type=Path,required=True)
    p.add_argument("--accepted-pixels",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=parse(a.log,a.accepted_pixels)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("QA08_NATIVE_HDMA_COLDATA_SOURCE_BYTES_ACCEPTED "
          f"count={report['direct_native_HDMA_COLDATA_written_bytes']} "
          "hardware=0 pixel_to_channel=unknown")


if __name__ == "__main__":
    main()
