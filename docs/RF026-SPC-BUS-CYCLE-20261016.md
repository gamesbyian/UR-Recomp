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
- **Switcher** (+4703 vs +4704, first disagreement +4664) is unchanged by RF-016…026; it is traced as RF-027 below.
- Stage order for QA-01:
  1. RF-015…019 tools;
  2. `baldosa_spc_power_on_patch.py --anchor 0`;
  3. `baldosa_spc_frame_clock_patch.py` (requires RF-016);
  4. `baldosa_spc_bus_cycle_patch.py`.
- No campaign input exists yet: the dispatch form already has 10 inputs. None of these corrections is in the Windows bridge.

## RF-027: Switcher's root step is a VBlank edge after the post-race loader

On the RF-026 candidate, dense dumps of the Switcher replay (+4600…+4710) show the following:

- **References agree.** Snes9x and bsnes are byte-identical in low WRAM at every frame.
- **First difference.** Native's full 128 KiB WRAM, stack excluded, equals them through +4662. At +4663 (host 5742) only `$C6` (13 vs 14) and the `$0BDD/$0BDE/$0BFE/$0C68…` cursor counters differ.
- **Re-convergence, then the terminal.** Everything re-converges at +4665, and the terminal follows one frame early at +4702.

`$C6` is decremented at `80:FAE2`, right after the two-edge VBlank wait `80:FAC9`. That is the RF-015/RF-017 class of witness.

PC-filtered traces (Snes9x per instruction, Baldosa block observer):

| Point | Snes9x | native | native − Snes9x (master clocks) |
| --- | --- | --- | --- |
| Race fields, arrival at the frame wait `82:D4E9` (54 fields) | | | −62 … −306 per field (typically −160) |
| Post-race SPC-reset loader exit (`82:809C`, host 5659) | V245 H1092 | V245 H988 | −104 |
| Next reset `82:8082` (host 5669) | V87 H588 | V87 H112 | −476 |
| Its exit `82:809C` | V124 H944 | V124 H410 | −534 |
| Last reset `82:8082` (host 5670) | V211 H1350 | V211 H718 | −632 |
| Its exit | V249 H324 | V248 H994 | −694 |
| Arrival at `80:FAC9` (host 5741) | V224 H522 | V223 H1116 | **−770** |

FAC9 → FACD takes 1,002 clocks on both engines. Native's first VBlank check therefore reads at V224 H754, before VBlank, passes, and leaves at V=225. The references read at V225 H160, inside VBlank, and wait a whole field.

The 770 clocks build up in two stages:

1. **Race fields.** Each race field ends ~160 clocks early on native, about 0.045% of the CPU-bound field. The NMI re-locks every field, so this does not accumulate during the race, but the last field's offset carries into the NMI-disabled loader.
2. **Driver upload.** The upload between hosts 5659 and 5669 adds ~370 more. That is the same CPU/SPC handshake drift RF-026 reduced but did not remove.

The SPC resets themselves match: the host-5659 driver tick comes 711 SPC cycles after the CPU's write on native, 684 on Snes9x.

**Next experiment:** a per-field cost breakdown of one race field against bsnes, covering general-DMA sync (RF-020's probe: 12-clock sync is −64, Snes9x's 18 is +50), HDMA mid-field repricing (RF-019's walk prices tables once at V=0) and refresh placement. Then a per-access SMP model for the upload drift.
