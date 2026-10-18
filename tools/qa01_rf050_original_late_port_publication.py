#!/usr/bin/env python3
"""RF050: original S9xAPUWritePort visibility after RF049 late sound stores.

Opt-in observer in pinned disposable original Snes9x apu/apu.cpp, inserted
AFTER authoritative SNES::cpu.port_write and existing RF037 source logger.
Records real V159 CPU beam-window 2142/2143 publications above the old RF037
source-age cut. Does not infer ICPU.Frame from apu.cpp, issue a second write,
read a second port, run an SPC instruction, or change source CPU/APU timing.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf037_upstream_writer_observer as upstream

MARK="UR_QA01_RF050_LATE_SOUND_PUBLICATION"
FILE=Path("apu/apu.cpp")
EXTRA=r"""    /* UR_QA01_RF050_LATE_SOUND_PUBLICATION: after one true CPU port write. */
    if (getenv("UR_QA01_RF050_LATE_SOUND_PUBLICATION") &&
        (port & 3) >= 2 &&
        SNES::ur_qa01_rf030_spc_age >= 104200000ull &&
        SNES::ur_qa01_rf030_spc_age <= 106500000ull &&
        (unsigned)::CPU.V_Counter == 159u &&
        (int)::CPU.Cycles >= 850 && (int)::CPU.Cycles <= 1200) {
        static unsigned rf050_events;
        if (rf050_events++ < 2048u)
            fprintf(stderr,
                "QA01RF050ORIGAPU seq=%u age=%llu v=%u h=%d port=%u val=%02X\n",
                rf050_events,
                (unsigned long long)SNES::ur_qa01_rf030_spc_age,
                (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
                (unsigned)(port & 3), (unsigned)byte);
        else if (rf050_events == 2049u)
            fprintf(stderr, "QA01RF050ORIGAPU_TRUNCATED\n");
    }
"""

def patch_original(src:str)->str:
    if MARK in src:
        if src.count(EXTRA)!=1:
            raise ValueError("RF050 original CPU port observation partly staged/tampered")
        return src
    if src.count(upstream.NEW_ORIG)!=1:
        raise ValueError("RF050 requires exact post-authoritative RF037 source port stage")
    new=src.replace(upstream.NEW_ORIG,upstream.NEW_ORIG+EXTRA,1)
    if new.count("SNES::cpu.port_write(port & 3, byte);")!=1:
        raise ValueError("RF050 would alter/duplicate authoritative original CPU publication")
    return new

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    args=p.parse_args()
    target=args.root.resolve()/FILE
    if not target.is_file():p.error("missing original Snes9x apu/apu.cpp")
    old=target.read_text(encoding="utf8")
    new=patch_original(old)
    if new!=old:target.write_text(new,encoding="utf8")
    print("RF050 source original late APU writer:",
          "already staged" if new==old else "staged read-only")
    return 0
if __name__=="__main__":raise SystemExit(main())
