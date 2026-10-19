#!/usr/bin/env python3
"""RF061: exact read-only native *executing* Bowl IPL sound-call return stamps.

Strictly patch only disposable pinned Baldosa checkout:
  generated src/gen/bank03_part09_v2.c actual Race_Main_CA91_M0X0
  runner/src/desktop/host_main.c input-tick host-frame stamp

Source CPU original is separately proved by merged RF060. The generated
physical bank03 is the FastROM alias of original retail-USA bank83; targeting
bank83 generated files would miss this actual function. No guest CPU/APU port
read/write, SNES cycles, input, RAM, SPC, render or production change.
"""
from __future__ import annotations
import argparse
from pathlib import Path

HOST_MARK="static uint32 TickScript(void) {\n"
HOST_ADDITION=r"""/* RF061 QA ONLY: current actual guest host input-frame clock.
 * Source- and runtime-scoped; never alter the controller mask or SNES cycles. */
uint32 ur_rf061_native_host_frame = 0xffffffffu;
static uint32 TickScript(void) {
  ur_rf061_native_host_frame = (uint32)snes_frame_counter;
"""
GEN_MARK="RecompReturn Race_Main_CA91_M0X0(CpuState *cpu) {"
GEN_PRIOR="case 0: _r = Snd_UploadBlockListLong_M0X0(cpu); break;"
GEN_RETURN="L_CAB3_M0X0:\n    cpu_trace_block(cpu, 0x03CAB3);"
HEADER_MARK='#include "funcs.h"\n'
EXTERN='extern uint32 ur_rf061_native_host_frame; /* RF061 actual TickScript clock */\n'

# At the physically correct Mode M0X0 callsite to original JSL $82:82A5.
# Keep _r handling exactly as original, only logging before and after.
CASE_REWRITE=r"""case 0: {
          static unsigned ur_rf061_sound_call_count=0u;
          const unsigned ur_rf061_id=++ur_rf061_sound_call_count;
          fprintf(stderr,
            "QA01RF061NATIVE phase=before call=%u frame=%u master=%llu pb=%02X p=%02X m=%u xflag=%u a=%04X x=%04X y=%04X s=%04X scope=Race_Main_CA91_M0X0 target=Snd_UploadBlockListLong_M0X0\n",
            ur_rf061_id, (unsigned)ur_rf061_native_host_frame,
            (unsigned long long)cpu->master_cycles,(unsigned)cpu->PB,
            (unsigned)cpu->P,(unsigned)cpu->m_flag,(unsigned)cpu->x_flag,
            (unsigned)cpu->A,(unsigned)cpu->X,(unsigned)cpu->Y,
            (unsigned)cpu->S);
          _r = Snd_UploadBlockListLong_M0X0(cpu);
          fprintf(stderr,
            "QA01RF061NATIVE phase=returned call=%u frame=%u master=%llu pb=%02X p=%02X m=%u xflag=%u a=%04X x=%04X y=%04X s=%04X result=%d scope=Race_Main_CA91_M0X0 target=Snd_UploadBlockListLong_M0X0\n",
            ur_rf061_id,(unsigned)ur_rf061_native_host_frame,
            (unsigned long long)cpu->master_cycles,(unsigned)cpu->PB,
            (unsigned)cpu->P,(unsigned)cpu->m_flag,(unsigned)cpu->x_flag,
            (unsigned)cpu->A,(unsigned)cpu->X,(unsigned)cpu->Y,
            (unsigned)cpu->S,(int)_r);
          break;
        }"""
LABEL_REWRITE=r"""L_CAB3_M0X0:
    cpu_trace_block(cpu, 0x03CAB3);
    {
      static unsigned ur_rf061_cab3_count=0u;
      ++ur_rf061_cab3_count;
      fprintf(stderr,
        "QA01RF061NATIVE phase=cab3 entry=%u frame=%u master=%llu pb=%02X p=%02X m=%u xflag=%u a=%04X x=%04X y=%04X s=%04X physical=03:CAB3 original=83:CAB3 scope=Race_Main_CA91_M0X0\n",
        ur_rf061_cab3_count,(unsigned)ur_rf061_native_host_frame,
        (unsigned long long)cpu->master_cycles,(unsigned)cpu->PB,
        (unsigned)cpu->P,(unsigned)cpu->m_flag,(unsigned)cpu->x_flag,
        (unsigned)cpu->A,(unsigned)cpu->X,(unsigned)cpu->Y,
        (unsigned)cpu->S);
    }"""

def patch_host(s:str)->str:
    if "ur_rf061_native_host_frame" in s:
        if s.count(HOST_ADDITION)!=1:
            raise ValueError("RF061 native input host-frame observer partially staged")
        return s
    if s.count(HOST_MARK)!=1:
        raise ValueError("RF061 pinned Baldosa TickScript insertion point missing")
    return s.replace(HOST_MARK,HOST_ADDITION,1)

def patch_generated(s:str)->str:
    if "QA01RF061NATIVE" in s:
        if (s.count(CASE_REWRITE)!=1 or s.count(LABEL_REWRITE)!=1
            or s.count(EXTERN)!=1):
            raise ValueError("RF061 mode-qualified native CPU observer partially installed")
        return s
    if (s.count(GEN_MARK)!=1 or s.count(GEN_RETURN)!=1
        or s.count(HEADER_MARK)!=1):
        raise ValueError("RF061 pinned physical bank03 M0X0 IPL/RTL code changed")
    # Fail closed on wrong generated function despite an identical symbol in
    # another generated function or wrong M/X variant.
    start=s.index(GEN_MARK)
    end=s.find("\nRecompReturn ",start+len(GEN_MARK))
    if end<0:end=len(s)
    section=s[start:end]
    if section.count(GEN_PRIOR)!=1 or section.count(GEN_RETURN)!=1:
        raise ValueError("RF061 target code is not inside actual Race_Main_CA91_M0X0")
    replaced=section.replace(GEN_PRIOR,CASE_REWRITE,1)
    replaced=replaced.replace(GEN_RETURN,LABEL_REWRITE,1)
    out=s[:start]+replaced+s[end:]
    out=out.replace(HEADER_MARK,HEADER_MARK+EXTERN,1)
    if out.count("Snd_UploadBlockListLong_M0X0(cpu)")!=s.count("Snd_UploadBlockListLong_M0X0(cpu)"):
        raise AssertionError("RF061 changed guest sound upload call count")
    return out

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host",required=True,type=Path)
    p.add_argument("--generated",required=True,type=Path)
    a=p.parse_args()
    if not a.host.is_file() or not a.generated.is_file():
        p.error("RF061 source-pinned Baldosa native checkout files absent")
    for file,fn in ((a.host,patch_host),(a.generated,patch_generated)):
        old=file.read_text(encoding="utf8")
        new=fn(old)
        if new!=old:file.write_text(new,encoding="utf8")
        print("RF061",file,"already staged" if old==new else "staged")

if __name__=="__main__":main()
