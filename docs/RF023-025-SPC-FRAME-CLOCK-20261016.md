# RF-023/024/025: SPC frame clock, the short scanline and the power-on anchor (2026-10-16)

**Scope:** CPU/APU-lane follow-through after [RF-020/021/022](RF020-022-SPC-PHASE-KNIFE-EDGES-20261016.md) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`). The base is the full RF-015…019 candidate. Evidence comes from SPC-side port/timer logs (a disposable Snes9x core and a Baldosa observer build), the four 1P producer cases, the 18 2P seed × reference pairs and the attract census. Compact evidence: [`analysis/data/rf023-025-spc-frame-clock-20261016.json`](../analysis/data/rf023-025-spc-frame-clock-20261016.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Summary

| Finding | Cause in the pinned runtime | Stage tool |
| --- | --- | --- |
| RF-023 | `rtl_apu_clock_finish` gives every host iteration at least one field of SPC time ("WAI still advances a hardware frame"), so every iteration shorter than a field inflates the SPC timeline against the CPU | [`baldosa_spc_frame_clock_patch.py`](../tools/baldosa_spc_frame_clock_patch.py) |
| RF-024 | Every native field is 357,368 master clocks; NTSC hardware shortens scanline 240 by 4 clocks on alternate fields (average 357,366), so the SPC gains 2 clocks per field on the CPU | same tool |
| RF-025 | With RF-023/024 fixed, the RF-021 power-on anchor that reproduces the reference SPC age (anchor 0) loses the attract and Dragster matches; the anchor that keeps them (2,446) leaves the SPC 2,460 cycles younger than the references | [`baldosa_spc_power_on_patch.py --anchor`](../tools/baldosa_spc_power_on_patch.py) |

The combined candidate is RF-015…019 + RF-021 (anchor 2,446) + RF-023/024 (executables: 1P scene shim `cb3e5f35…`, 2P research shim `de6605fd…`). It matches the references on **every witness where Snes9x and bsnes agree, except Switcher**:

| Witness | RF-015…019 | Candidate |
| --- | --- | --- |
| 2P seed 50048000 (vs Snes9x and vs bsnes) | one field early (5052) | **exact field agreement** |
| other 16 2P pairs | 14 exact; 50036056 vs bsnes and 50024004 vs Snes9x are reference knife-edges | identical |
| Dragster Race A | `strict_divergence` +2080 vs +2081; follow-through named pairs differ | **+2081 = +2081, paired candidate, all named follow-through pairs equal**; dense low WRAM equals Snes9x at every frame +2040…+2100 |
| Zoom Zoo | +5163 = +5163, all follow-through pairs equal | identical (RF-022's power-on regression does not occur) |
| Bowl | +3365 = +3365 | identical |
| Switcher Race B | +4703 vs +4704, first disagreement +4664 | identical |
| Attract census (bsnes) | 5/5 loads; 1423–1546 vs bsnes 1547 (Snes9x 1546) | identical; low WRAM equals bsnes at every frame of 2300–2400 and 3625–3770 |

RF-025 qualifies this result: it rests on a power-on anchor chosen empirically, inside a window of about 37 SPC cycles (anchor 2,409 fails the attract, 2,446 passes).

## RF-023: the one-field minimum inflates SPC time

The RF-016 frame clock keeps the guest SPC timeline in master clocks. Each host iteration adds `master_now − start_master`, then clamps it to at least one field:

```c
uint64_t minimum = clock->start_timeline + RTL_MASTER_CYCLES_PER_FRAME;
if (end < minimum) end = minimum;  /* WAI still advances a hardware frame. */
```

The beam frame driver already advances parked/WAI time on the CPU master clock (`advance_parked`), so the clamp adds time on top of it. A native iteration overshoots its field boundary by a varying amount, so the next one is often slightly short and is padded, while the CPU clock is not. The SPC ages at the Dragster replay's seven SPC resets, relative to Snes9x (SPC cycles; native frame labels run one behind):

| Reset (Snes9x host) | 35 | 44 | 46 | 849 | 859 | 862 | 2902 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Snes9x SPC age | 586,459 | 747,216 | 772,390 | 14,472,600 | 14,638,861 | 14,698,686 | 49,501,155 |
| clamp, anchor 2,446, no short line | 0 | −74 | −84 | +1,617 | −145 | −181 | +3,393 |
| RF-023/024, anchor 2,446 | −2,460 | −2,551 | −2,553 | −2,458 | −2,674 | −2,714 | −2,457 |
| RF-023/024, anchor 0 | −14 | −102 | −114 | −14 | −286 | −324 | −12 |

The clamp added about 2,460 SPC cycles during the first 35 boot fields. By host 2902 it had added about 3,100 more, roughly 23 master clocks per field. That 0.006% excess cannot be fixed with a constant. RF-021 tuned anchor 2,446 against this inflated boot, which is why it matched the first handshake exactly.

The correction removes the clamp. The SPC timeline then follows the CPU master clock exactly, apart from the RF-024 pauses. Without the clamp, a short iteration reports a fractional frame period. `RtlLastFramePeriods` already varies around 1.0 per field and the audio servo absorbs ±0.5%.

## RF-024: the NTSC short scanline

In non-interlaced NTSC, scanline 240 of every other field is 1,360 clocks instead of 1,364 (bsnes `PPUcounter`; Snes9x models it too). Fields therefore alternate 357,368 and 357,364 clocks. The Snes9x log confirms it. Its SPC ages between resets fit the 15664/328125 rate over 357,366-clock fields within ±3 SPC cycles over 2,867 fields; 357,368 would be off by +271, and 357,364 by −277. The pinned beam always uses 1,364-clock lines. The CPU is frame-locked, so this does not move CPU work within a field, but the SPC gains 2 master clocks per field on it.

The correction stays inside the APU frame clock. On alternate fields the SPC timeline pauses for 4 master clocks at the end of line 240, so the timeline never runs backwards. A host iteration that spans several fields, such as an NMI-disabled loader, pays one pause for each odd field it crosses. The beam, CPU, DMA/HDMA and IRQ timing are untouched. With both corrections the native SPC age tracks Snes9x to within 2 SPC cycles from host 35 to host 2902; the per-reset differences above are CPU write-position differences of at most about 5 lines.

## RF-025: the anchor is a knife-edge choice

Once the frame clock is exact, **anchor 0** reproduces the reference SPC age to 14 cycles at the boot handshake and at hosts 849 and 2902. Yet it loses the attract loads (941–1097, 1422–1545, 3631–3761 vs 1098/1546/3632) and Dragster (one field early again). **Anchor 2,446** keeps both, with an SPC 2,460 cycles younger than the references at every reset.

After each sound-driver restart, the driver's timing is re-anchored to CPU port writes. A constant age offset therefore matters mainly through the free-running timer prescalers: 2,460 mod 16 = 12 cycles of the timer-2 stage, and 2,460 mod 128 = 28 of the timer-0/1 stage. The decisive Dragster handshake shows it. At host 2902 the sound driver honours the `$FF` reset only after a fresh timer-2 tick. On Snes9x it consumes a stale tick 257 SPC cycles after the CPU's write, then waits a full period. On native the stale tick comes at 88 cycles (anchor 2,446) or 139 (anchor 0), while the CPU writes agree within 12 cycles. Native's driver timer phase relative to the CPU still differs by about 100–200 SPC cycles at the host-849 and host-2902 resets, whatever the anchor.

One candidate source is the native SPC700 core. It is LakeSnes-derived: `apu_cycle` runs each opcode atomically on its first cycle, so port reads, timer reads and `$F1` timer enables land 2–4 cycles before their hardware bus cycle. The references model per-cycle bus access. Each such offset is small, so it would have to act through the chain of port handshakes between a driver restart and its timer enable. That remains a hypothesis; no per-access trace was made.

**The full witness set under both anchors** (RF-015…019 + RF-023/024; anchor-0 executables: 1P `f202aebe…`, 2P `4a085e91…`):

| Witness | anchor 2,446 | anchor 0 (exact SPC age) |
| --- | --- | --- |
| 2P, 18 pairs | 16 exact; 50036056 vs bsnes and 50024004 vs Snes9x (reference knife-edges) | identical, including 50048000 exact against both references |
| Zoom Zoo | +5163 = +5163; all follow-through pairs and SRAM equal | +5163 = +5163; follow-through named pairs and SRAM **differ** (the RF-022 regression) |
| Bowl | +3365 = +3365 | identical |
| Switcher | +4703 vs +4704 (+4664) | identical |
| Dragster | +2081 = +2081; paired candidate | +2080 vs +2081 (**one field early**) |
| Attract (bsnes) | 941–1098, 1423–1546, 3632–3762 | 941–1097, 1422–1545, 3631–3761 (**three loads one frame early**) |

So the 2P improvement, seed 50048000, comes from RF-023/024 and holds under either anchor. The Zoom Zoo, Dragster and attract agreements depend on the anchor: they are RF-022's knife-edges, and the empirical anchor lands them on the reference side.

**Where the remaining phase comes from.** Disposable `$F1` (timer-control) logging was added to the Snes9x SMP and the native APU, with CPU-clock port-write logging, on the Dragster replay. The timer-2 phase that decides the host-2902 reset is set by the driver's last timer restart (`$F1 = $06`) at SPC cycle ~16.13M, near host 945. With anchor 0 the native driver performs that restart 128 SPC cycles early by SPC age, while the CPU writes before it land up to ~370 cycles early. From that restart to the host-2902 write, native's elapsed SPC time is 116 cycles longer, which is exactly the observed tick shift (257 → 139). Port-write positions also drift by about −200 master clocks per field during the boot IPL upload (hosts 35–44): native's CPU/SPC upload handshake runs ~0.06% fast. That agrees with RF-020's earlier count of 0.08% fewer polls in a later upload. The remaining error is therefore in CPU–SPC handshake timing, a few SPC cycles per exchange, not in the SPC clock rate or age.

## Harness correction for earlier Dragster dense evidence

The scratch dense-dump harness behind RF-020's Dragster tables seeded the movie SRAM next to the native executable but ran it from another directory. As `probe_original_event_complete.py` documents, the native then never reads the archived SRAM. With the SRAM seeded correctly the RF-015…019 base still first differs at +2040, with the same 20 differing frames, so RF-020's Dragster conclusion stands. Its SPC-log latencies were measured without movie SRAM, however, and the reset-census tables above supersede them. The producer runs, the attract census and the 2P pairs were never affected.

## Recommendation

- **RF-023/024** are hardware-correct and measured (SPC age within 2 cycles of Snes9x over 2,867 fields). They belong in any final timing model, together with RF-021.
- **RF-025:** QA-01 should treat the combined candidate as strong but knife-edge evidence. It is the first configuration to match every witness where the references agree except Switcher. That holds only with the empirical anchor, and the physically exact anchor loses two witnesses. Before accepting an event on this core, check it under both anchors.
- **Next research step:** measure the CPU/SPC upload handshake per exchange against bsnes (CPU port-write clock, SPC read and echo cycle). Then try a per-access SPC700 bus model (port and timer accesses at their hardware bus cycle), and re-run the `$F1` and reset census with anchor 0. If that closes the ~0.06% handshake drift and the driver-phase residual, the anchor stops being a free parameter.
- **Not staged:** no campaign input yet. The stage order is RF-015…019, then `baldosa_spc_power_on_patch.py [--anchor N]`, then `baldosa_spc_frame_clock_patch.py` (requires RF-016).
