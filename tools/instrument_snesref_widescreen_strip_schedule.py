#!/usr/bin/env python3
"""Inject a disposable +8 preparation-only camera bias and narrow descriptor trace.

The diagnostic patch temporarily biases WRAM camera X at the entry to the
representative camera/preparation routine (81:A52F) and restores it immediately
after the strip builder returns at 81:A59D.  The authoritative camera value is
therefore unchanged outside that preparation window.

Set URRECOMP_WS_MARGIN=8 to enable the bias.  Any other value is the matched
stock control.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();"""

SNIPPET = r'''			/* UR-Recomp disposable Widescreen strip-scheduling experiment. */
			{
				static int ur_ws_margin = []() -> int {
					const char *s = getenv("URRECOMP_WS_MARGIN");
					return s ? atoi(s) : 0;
				}();
				static bool ur_ws_camera_shifted = false;
				auto ur_ws_w16 = [](uint16 a) -> uint16 {
					return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
				};
				auto ur_ws_set16 = [](uint16 a, uint16 v) {
					Memory.RAM[a] = (uint8)(v & 0xff);
					Memory.RAM[a + 1] = (uint8)(v >> 8);
				};
				uint16 ur_ws_pcw = Registers.PCw;
				uint32 ur_ws_pc = ((uint32)Registers.PB << 16) | ur_ws_pcw;

				/* Defensive recovery: never carry a temporary bias across entries. */
				if (Registers.PB == 0x81 && ur_ws_pcw == 0xA52F && ur_ws_camera_shifted)
				{
					ur_ws_set16(0x0419, (uint16)(ur_ws_w16(0x0419) - 8));
					ur_ws_camera_shifted = false;
					fprintf(stderr, "WSPATCH stale-bias-recovered frame=%u\n", (unsigned)ICPU.Frame);
				}

				if (ur_ws_margin == 8 && Registers.PB == 0x81 && ur_ws_pcw == 0xA52F)
				{
					ur_ws_set16(0x0419, (uint16)(ur_ws_w16(0x0419) + 8));
					ur_ws_camera_shifted = true;
				}

				/* A59D is reached after the A59A JSR to the proven strip builder. */
				if (Registers.PB == 0x81 && ur_ws_pcw == 0xA59D && ur_ws_camera_shifted)
				{
					ur_ws_set16(0x0419, (uint16)(ur_ws_w16(0x0419) - 8));
					ur_ws_camera_shifted = false;
				}

				if ((Registers.PB == 0x81 && ur_ws_pcw == 0xA59D) ||
				    (Registers.PB == 0x82 && ur_ws_pcw == 0xD19B))
				{
					fprintf(stderr,
						"WSDMA margin=%d frame=%u v=%u cycles=%d pc=%06X "
						"camx=%u camy=%u camdx=%d camdy=%d px=%u py=%u xs=%d ys=%d pitch=%u "
						"contact=%u laps=%u checkpoint=%u finish=%u edgex=%u edgey=%u desc=",
						ur_ws_margin, (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
						(unsigned)ur_ws_pc,
						(unsigned)ur_ws_w16(0x0419), (unsigned)ur_ws_w16(0x041D),
						(unsigned)ur_ws_w16(0x0411), (unsigned)ur_ws_w16(0x0415),
						(int16)ur_ws_w16(0x04B7), (int16)ur_ws_w16(0x04BB),
						(unsigned)ur_ws_w16(0x04C7), (unsigned)ur_ws_w16(0x0E95),
						(unsigned)ur_ws_w16(0x0EF1), (unsigned)ur_ws_w16(0x1199),
						(unsigned)ur_ws_w16(0x119D), (unsigned)ur_ws_w16(0x0505),
						(unsigned)ur_ws_w16(0x050D));
					for (unsigned i = 0; i < 8; i++)
					{
						uint16 o = (uint16)(i * 2);
						uint16 ready = ur_ws_w16((uint16)(0x03B9 + o));
						uint16 dest = ur_ws_w16((uint16)(0x03C9 + o));
						uint16 src = ur_ws_w16((uint16)(0x0399 + o));
						uint16 size = ur_ws_w16((uint16)(0x03A9 + o));
						uint16 vmain = ur_ws_w16((uint16)(0x03D9 + o));
						fprintf(stderr, "%s%u:%u:%04X:%04X:%04X:%04X:",
							i ? "," : "", i, (unsigned)ready, (unsigned)dest,
							(unsigned)src, (unsigned)size, (unsigned)vmain);
						unsigned payload = ready ? (unsigned)(size < 0x40 ? size : 0x40) : 0;
						for (unsigned j = 0; j < payload; j++)
							fprintf(stderr, "%02X", (unsigned)Memory.RAM[(uint16)(src + j)]);
					}
					fprintf(stderr, "\n");
				}
			}
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")
    if "UR-Recomp disposable Widescreen strip-scheduling experiment" in text:
        return 0
    if MARKER not in text:
        raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
    args.source.write_text(text.replace(MARKER, SNIPPET + "\n" + MARKER, 1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
