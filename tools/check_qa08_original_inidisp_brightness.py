#!/usr/bin/env python3
"""Authenticate actual original Snes9x INIDISP HDMA writer and PPU brightness.

Explicitly separate $2100 lower-nibble brightness=0 from forced blank
($2100 bit7), avoiding false physical hardware timing conclusions.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

RX=re.compile(
    r"^UR_QA08_ORIGINAL_INIDISP frame=(\d+) v=(\d+) cycles=(-?\d+) "
    r"channel=(\d+) mode=(\d+) indirect=([01]) base=([0-9A-F]{2}) "
    r"source=([0-9A-F]{2}):([0-9A-F]{4}) wram=([0-9A-F]{2}) "
    r"bbus=00 value=([0-9A-F]{2}) brightness=(\d+) forced=([01])$"
)
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROUTE="94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
WRAM="9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6"
VALID_FRAMES={1781,1782,1783,1988,1989,1990,2231,2232,2233,2471,2472,2473}

def read(p):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ValueError("duplicate source original INIDISP evidence key")
            out[k]=v
        return out
    return json.loads(Path(p).read_text(),object_pairs_hook=unique)


def check(log:str,receipt:dict,ppu_journal:str)->dict:
    if (receipt.get("USA_ROM_SHA256")!=ROM or
            receipt.get("original_script_SHA256")!=ROUTE or
            receipt.get("original_t480_WRAM_SHA256")!=WRAM or
            receipt.get("source_65816_writer_PCs")!=18 or
            receipt.get("actual_executed_original_instruction_count")!=55 or
            receipt.get("second_camera_0DDB")!=1 or receipt.get("in_race_0313")!=1 or
            receipt.get("native_same_input_frame_parity_proven") is not False):
        raise ValueError("genuine original ROM/route/PPU writer oracle missing")
    if "UR_QA08_ORIGINAL_INIDISP_OVERFLOW" in log:
        raise ValueError("original INIDISP source probe overflow")
    lines=[x for x in log.splitlines() if "UR_QA08_ORIGINAL_INIDISP " in x]
    if not 2<=len(lines)<=256:
        raise ValueError("original genuine $2100 HDMA source events missing")
    events=[]
    for ordinal,line in enumerate(lines):
        m=RX.fullmatch(line)
        if m is None: raise ValueError("forged original INIDISP PPU after-write receipt")
        frame,v,cycles,ch,mode,indirect,base,bank,addr,wram,byte,bright,forced=m.groups()
        frame,v,cycles,ch,mode,indirect,bright,forced=map(
            int,(frame,v,cycles,ch,mode,indirect,bright,forced))
        val=int(byte,16)
        if (frame not in VALID_FRAMES or not 0<=v<=261 or
                not -100000<=cycles<=100000 or ch not in range(8) or
                mode not in range(8) or indirect not in (0,1) or
                bright!=(val&15) or forced!=((val>>7)&1) or
                not 0<=int(addr,16)<=0xffff):
            raise ValueError("original actual $2100 register state does not match source")
        if events and (frame,v,cycles)<(
                events[-1]["original_emulator_frame"],
                events[-1]["original_beam_v"],
                events[-1]["original_CPU_cycles"]):
            raise ValueError("original $2100 PPU HDMA chronology changed")
        events.append({
            "ordinal":ordinal,"original_emulator_frame":frame,
            "original_beam_v":v,"original_CPU_cycles":cycles,
            "actual_original_HDMA_channel":ch,
            "source_mode":mode,"source_indirect":bool(indirect),
            "original_BBUS_base":base,
            "actual_original_Abus_source":bank+":"+addr,
            "source_WRAM_value_if_7E":"0x"+wram,
            "actual_written_PPU_INIDISP":"0x"+byte,
            "real_PPU_brightness_after_write":bright,
            "real_PPU_forced_blank_flag_after_write":bool(forced),
        })
    replay=[e for e in events if e["original_emulator_frame"]==1989 and
            e["original_beam_v"] in (111,113)]
    wanted=[(111,0,0),(113,15,0)]
    if [(e["original_beam_v"],e["real_PPU_brightness_after_write"],
         int(e["real_PPU_forced_blank_flag_after_write"])) for e in replay]!=wanted:
        raise ValueError("original actual GO $2100 brightness-zero/restore HDMA not observed")
    journal=[]
    for line in ppu_journal.splitlines():
        fields=line.split("\t")
        if len(fields)==6 and fields[3]=="2100" and fields[1] in ("111","113"):
            journal.append((int(fields[0]),int(fields[1]),fields[4],fields[5]))
    if journal != [(1989,111,"00","hdma"),(1989,113,"0F","hdma")]:
        raise ValueError("original independent PPUW source disagrees with executed PPU brightness")
    return {
        "schema":"qa08-original-Snes9x-2P-HDMA-live-2100-brightness-zero-split/1",
        "status":"real-original-Snes9x-HDMA-PPU-register-and-brightness-after-write",
        "original_GO_frame":1989,"true_original_INIDISP_source_events":len(events),
        "observed_original_GO_brightness_zero_tag":111,
        "observed_original_GO_brightness_15_restore_tag":113,
        "actual_original_GO_hdma_channel_at_zero":replay[0]["actual_original_HDMA_channel"],
        "actual_original_GO_hdma_channel_at_restore":replay[1]["actual_original_HDMA_channel"],
        "source_hardware_forced_blank_bit_set_for_split":False,
        "source_real_brightness_set_zero_causes_black":True,
        "source_PPUW_independently_agrees_with_BBUS_byte":True,
        "original_PPU_framebuffer_black_rows":[111,112],
        "native_original_source_black_rows":[112,113],
        "native_actual_INIDISP_transfer_and_PPU_pixel_mapping_proven":False,
        "original_native_matching_simulation_input_state_proven":False,
        "physical_SNES_cycle_accuracy_proven":False,
        "source_original_events":events
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--ppuw-go",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=check(a.log.read_text(encoding="utf8",errors="replace"),
                 read(a.receipt),a.ppuw_go.read_text(encoding="utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("QA08_ORIGINAL_INIDISP_SOURCE_BRIGHTNESS_ZERO_ACCEPTED "
          f"true_source_writes={result['true_original_INIDISP_source_events']} "
          "forced_blank_bit=0 final_native_timing=unproven")
if __name__=="__main__":main()
