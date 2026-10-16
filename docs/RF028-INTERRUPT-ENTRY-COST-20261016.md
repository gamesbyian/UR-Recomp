# RF-028: the 65816 interrupt-entry sequence costs nothing in Baldosa (2026-10-16)

**Scope:** CPU-lane follow-through after [RF-026/027](RF026-SPC-BUS-CYCLE-20261016.md) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`). Compact evidence: [`analysis/data/rf028-interrupt-entry-cost-20261016.json`](../analysis/data/rf028-interrupt-entry-cost-20261016.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Cause

On hardware, taking NMI or IRQ runs a bus sequence before the handler's first instruction (bsnes `CPU::interrupt`):

1. a dummy read at the interrupted PC;
2. one internal cycle;
3. pushes of PB (native mode only), PCH, PCL and P;
4. two vector reads.

On SlowROM Uniracers with the stack in WRAM this costs 8 + 6 + 4 × 8 + 2 × 8 = **62 master clocks**. Baldosa's beam driver pushes the frame with unpaced `cpu_write8` and reads the vector untimed, so every handler starts about 62 clocks early against the beam.

## How it was found (RF-027)

On Switcher Race B, native reached the post-race `80:FAC9` VBlank wait 770 clocks early and ended the event one frame early, though Snes9x and bsnes agree byte-for-byte. A Snes9x per-instruction trace and a Baldosa block observer over one race field showed:

- **NMI entry.** Snes9x's last poll-loop instruction runs at V225 H2 and the NMI handler `00:8588` starts at V225 H82. Native starts the handler 18 clocks after V=225, which is block-end overshoot with no entry cost.
- **Constant offset.** The beam offset is −150…−210 clocks through the whole field and does not grow, so it is set at the NMI. The general-DMA starts in the handler add about −6 each: native charges a 12-clock sync where Snes9x charges 18.
- **Into the loader.** Each race field re-locks to NMI, but the last field's offset carries into the NMI-disabled post-race loader. The driver upload then widens it.

In an observer build:

- charging 60 or 62 clocks per interrupt makes the Switcher dense comparison (+4600…+4710) equal to Snes9x at every frame;
- the bsnes-style exact DMA sync, alone or together with the interrupt charge, overshoots (13 differing frames), so it is **not** adopted;
- with 62, Dragster dense and the attract are unchanged (still matching).

## Correction

[`tools/baldosa_interrupt_entry_cost_patch.py`](../tools/baldosa_interrupt_entry_cost_patch.py) charges the sequence in `beam_frame_driver.c::run_interrupt`, just before the frame push. It adds the region speed of the interrupted PC, 6 internal clocks, one region-speed access per pushed byte at the live stack pointer, and the two bank-0 vector reads. The regression test checks staging, rejection of tampering, and a compiled harness giving 62 clocks in native mode and 54 in emulation mode.

## Result: the full staged candidate

The stage order is:

1. RF-015…019 tools;
2. `baldosa_spc_power_on_patch.py --anchor 0`;
3. `baldosa_spc_frame_clock_patch.py` (requires RF-016);
4. `baldosa_spc_bus_cycle_patch.py`;
5. `baldosa_interrupt_entry_cost_patch.py`.

Executables: 1P `8dde89b4…`, 2P `bf4a66cb…`.

| Witness | RF-015…019 base | RF-015…028 candidate |
| --- | --- | --- |
| Zoom Zoo | +5163 = +5163 | +5163 = +5163; all follow-through and SRAM pairs equal |
| Bowl | +3365 = +3365 | same |
| Dragster Race A | +2080 vs +2081 | **+2081 = +2081**; dense low WRAM equal +2040…+2100 |
| Switcher Race B | +4703 vs +4704 (+4664) | **+4704 = +4704**; dense low WRAM equal +4600…+4710 |
| 2P, 18 pairs | 14 exact; 50048000 one field early vs both; two reference knife-edges | **16 exact**; 50036056 (bsnes 5236) and 50024004 (Snes9x 5123) remain, where Snes9x and bsnes disagree and native equals one of them |
| Attract census (bsnes) | 5/5 loads | 5/5 loads |

All four 1P producer cases are `paired_event_candidate` with all named follow-through and fresh-SRAM pairs equal. **Every witness on which Snes9x and bsnes agree now matches.** No parameter was tuned: the power-on anchor is the exact-age value, and the interrupt cost comes from the hardware sequence.

## Boundary

- These are research candidates. QA-01 decides acceptance, after hosted re-execution of the full stage.
- None of RF-021…028 is in the Windows bridge. Hosted staging: `qa01-event-campaign` input `baldosa_spc_interrupt_stage` (which requires the five RF-015…019 inputs) stages RF-021 `--anchor 0`, RF-023/024, RF-026 and RF-028 in this order; GitHub allows 25 dispatch inputs (since 2025-12-04).
- Known approximations:
  - RF-026 places all of an SPC opcode's accesses on its last cycle.
  - RF-019 prices HDMA once per field.
  - General-DMA sync stays at the pinned 12 clocks; the exact bsnes model overshot Switcher.
  - Interrupt latency (finishing the current instruction) is approximated by native's block-boundary delivery.
