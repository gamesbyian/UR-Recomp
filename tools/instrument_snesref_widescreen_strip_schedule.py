#!/usr/bin/env python3
"""Inject a disposable +8 preparation-only camera bias and narrow descriptor trace.

The diagnostic patch temporarily biases WRAM camera X at a runtime-selected
instruction inside the representative camera/preparation routine and restores it
immediately after the strip builder returns at 81:A59D. The workflow first
discovers a post-camera-update, pre-edge-derivation hook from a stock trace.

Set URRECOMP_WS_MARGIN=8 to enable the bias. URRECOMP_WS_HOOK_PC selects the
16-bit bank-81 hook PC (default 0xA52F). Any other margin is the matched control.
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
				static int ur_ws_hook_pc = []() -> int {
					const char *s = getenv("URRECOMP_WS_HOOK_PC");
					return s ? (int)strtol(s, nullptr, 0) : 0xA52F;
				}();
				static bool ur_ws_bias_a = []() -> bool {
					const char *t = getenv("URRECOMP_WS_BIAS_TARGET");
					return t && (t[0] == 'A' || t[0] == 'a');
				}();
				static uint16 ur_ws_saved_a = 0;
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

				static bool ur_ws_boundary_trace = []() -> bool {
					return getenv("URRECOMP_WS_BOUNDARY_TRACE") != nullptr;
				}();
				if (ur_ws_boundary_trace && Registers.PB == 0x81 &&
				    ur_ws_pcw >= 0xA52F && ur_ws_pcw <= 0xA59D &&
				    ICPU.Frame >= 1178 && ICPU.Frame <= 1192)
				{
					fprintf(stderr,
						"WSBND frame=%u v=%u cycles=%d pc=%06X op=%02X "
						"a=%04X x=%04X y=%04X d=%04X p=%04X "
						"camx=%u camy=%u camdx=%d camdy=%d "
						"edgex=%u edgex2=%u edgey=%u edgey2=%u "
						"cnt=%u,%u,%u,%u\n",
						(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
						(unsigned)ur_ws_pc, (unsigned)Op,
						(unsigned)Registers.A.W, (unsigned)Registers.X.W,
						(unsigned)Registers.Y.W, (unsigned)Registers.D.W,
						(unsigned)Registers.P.W,
						(unsigned)ur_ws_w16(0x0419), (unsigned)ur_ws_w16(0x041D),
						(int16)ur_ws_w16(0x04F5), (int16)ur_ws_w16(0x04F9),
						(unsigned)ur_ws_w16(0x0505), (unsigned)ur_ws_w16(0x0509),
						(unsigned)ur_ws_w16(0x050D), (unsigned)ur_ws_w16(0x0511),
						(unsigned)ur_ws_w16(0x052B), (unsigned)ur_ws_w16(0x052F),
						(unsigned)ur_ws_w16(0x0533), (unsigned)ur_ws_w16(0x0537));
				}

				/* Defensive recovery: never carry a temporary bias across entries. */
				if (Registers.PB == 0x81 && ur_ws_pcw == 0xA52F && ur_ws_camera_shifted)
				{
					if (ur_ws_bias_a)
						Registers.A.W = ur_ws_saved_a;
					else
						ur_ws_set16(0x0419, (uint16)(ur_ws_w16(0x0419) - 8));
					ur_ws_camera_shifted = false;
					fprintf(stderr, "WSPATCH stale-bias-recovered frame=%u target=%c\n",
						(unsigned)ICPU.Frame, ur_ws_bias_a ? 'A' : 'W');
				}

				if (ur_ws_margin == 8 && Registers.PB == 0x81 && ur_ws_pcw == ur_ws_hook_pc)
				{
					if (ur_ws_bias_a)
					{
						ur_ws_saved_a = Registers.A.W;
						Registers.A.W = (uint16)(Registers.A.W + 8);
					}
					else
						ur_ws_set16(0x0419, (uint16)(ur_ws_w16(0x0419) + 8));
					ur_ws_camera_shifted = true;
				}

				/* A59D is reached after the A59A JSR to the proven strip builder. */
				if (Registers.PB == 0x81 && ur_ws_pcw == 0xA59D && ur_ws_camera_shifted)
				{
					if (ur_ws_bias_a)
						Registers.A.W = ur_ws_saved_a;
					else
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
						(int16)ur_ws_w16(0x04F5), (int16)ur_ws_w16(0x04F9),
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
