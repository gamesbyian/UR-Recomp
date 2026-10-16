# RF-026: SPC700 bus accesses on their hardware cycle (2026-10-16)

**Scope:** CPU/APU-lane follow-through after [RF-023/024/025](RF023-025-SPC-FRAME-CLOCK-20261016.md) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`). Compact evidence: [`analysis/data/rf026-spc-bus-cycle-20261016.json`](../analysis/data/rf026-spc-bus-cycle-20261016.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Result

The pinned SPC700 is LakeSnes-derived. `apu_cycle` executes a whole opcode on its **first** cycle and then idles for the rest of its cycle count. Every port read, port echo write, timer read and `$F1` timer enable therefore lands 1–7 SPC cycles before the bus cycle where hardware performs it. Snes9x's bapu SMP and bsnes are cycle-stepped.

[`tools/baldosa_spc_bus_cycle_patch.py`](../tools/baldosa_spc_bus_cycle_patch.py) waits out each opcode's base cycle count and executes it on its **last** cycle. Its reads then see CPU port writes and timer ticks up to that cycle, and its writes appear from it. Branch extra cycles follow as idle cycles, the countdown uses the Apu's reserved `pad` bytes, and DSP, timers and the CPU side are untouched.

Staged on RF-015…019 + RF-023/024 with the **exact-age power-on anchor 0** (executables: 1P `8c9b4e19…`, 2P `85a20b92…`), with no tuned parameter, the candidate matches **every witness on which Snes9x and bsnes agree, except Switcher**:

| Witness | RF-015…019 base | RF-023/024, anchor 0 | + RF-026, anchor 0 |
| --- | --- | --- | --- |
| 2P seed 50048000 | one field early (5052) | exact vs both | exact vs both |
| other 17 2P pairs | 15 exact + two reference knife-edges (50036056 vs bsnes 5236, 50024004 vs Snes9x 5123) | identical | identical |
| Dragster Race A | +2080 vs +2081 | +2080 vs +2081 | **+2081 = +2081**, paired candidate, all named follow-through pairs and SRAM equal; dense low WRAM equals Snes9x at every frame +2040…+2100 |
| Zoom Zoo | +5163 = +5163, follow-through equal | follow-through and SRAM differ | **+5163 = +5163, follow-through and SRAM equal** |
| Bowl | +3365 = +3365 | same | same |
| Switcher Race B | +4703 vs +4704 (+4664) | same | same |
| Attract (bsnes) | 5/5 loads (1423–1546; bsnes 1547, Snes9x 1546) | three loads one frame early | **5/5 loads**, as base |

In an observer build, RF-026 gives the same attract and Dragster matches with anchor 2,446. With RF-026 staged, the witnesses no longer depend on the anchor, so RF-025's hazard is resolved: the exact-age anchor 0, which RF-023/024 call for, is the one to use.

## Why it moves the knife-edges

All figures are on the Dragster replay with movie SRAM, anchor 0, against Snes9x.

- **Boot IPL upload, 4,450 exchanges.** Native's drift falls from −1,824 to −666 master clocks out of 3,353,894. The exchanges shorter than any reference exchange (632–684 clocks) disappear.
- **CPU write positions at the seven SPC resets.** By SPC age they now differ by −10 to −66 SPC cycles; without RF-026 the spread was −14 to −324.
- **Host-849 reset.** The sound driver's stale timer-2 tick comes 322 SPC cycles after the CPU's `$FF` write (Snes9x 351); without RF-026 it came at 149.
- **Host-2902 reset.** The tick comes at 120 (Snes9x 257), and the following tick is consumed at 3,325 vs 3,406. That is still close enough that the loader leaves after VBlank, as on the references.

So the host-2902 handshake is still the closest margin: about 80 SPC cycles of timer phase.

## Approximation and remaining work

- Every access of an opcode is placed on its last cycle. On hardware, read-modify-write and multi-operand forms read one or more cycles earlier. A per-access SMP model, bsnes-style, would remove the rest of the upload drift (−666 clocks) and of the host-2902 phase gap.
- **Switcher** (+4703 vs +4704, first disagreement +4664) is unchanged by RF-016…026. It is the next witness to trace; earlier work attributes its two-frame-late race entry to a separate mechanism.
- Stage order for QA-01:
  1. RF-015…019 tools;
  2. `baldosa_spc_power_on_patch.py --anchor 0`;
  3. `baldosa_spc_frame_clock_patch.py` (requires RF-016);
  4. `baldosa_spc_bus_cycle_patch.py`.
- No campaign input exists yet: the dispatch form already has 10 inputs. None of these corrections is in the Windows bridge.
