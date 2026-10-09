# Baldosa Zoom Zoo progression discriminator (QA-01/07)

Status: experimental original-Baldosa-only readout; **0/45 USA original/native complete-event pairs**. The pinned Baldosa Zoom Zoo route is a different controller input source from Dessyreqt's original 2014 Snes9x movie. Its terminal gate `until16 0053 == F60C` is a **menu-return wait**, not independent proof of a completed circuit. A forced process exit or timeout never earns credit.

## Narrow executable change

The already-running `baldosa-core-spike.yml` workflow retains the same pinned external AOT game, USA ROM, SRAM isolation, upstream menu input sequence and all **7960 original drive-input frames**. The existing `tools/baldosa_zoo_progress_probe.py` now inserts **frame-neutral diagnostic `dump` requests** at four positions only: just after the GO gate; after the first 300-frame left block; before the last 6000-frame left block; and after that last block. All `press` and `wait` commands remain unchanged, including the uninterrupted 6000-frame press. If an upstream script changes those anchors, generation fails rather than silently manipulating a new course. Recheck actual final frame count/CRC against the previous 9784-frame bounded witness because neutral-dump behavior must itself be measured, not presumed.

The existing `tools/baldosa_core_spike_report.py` report now includes `zoom_zoo_progression`, decoded from real 128 KiB WRAM checkpoints. Its values are raw USA retail: NMI handler at 0053, menu scratch 009F, `in_race` flag 0313, track 00CE, P1 X/Y 0411/0415, stored contact 0E95, next checkpoint 1199, finish gate 119D, laps 0EF1 and raw stopwatch bytes 0E0F/0E13/0E17/0E1B/0E1F. Only `0313 == 1` together with `00CE == 1` is labeled active Zoom Zoo; the result-state reuse of 0313 is intentionally excluded. The report lists changes *between observed snapshots*, not interpolated contact events or inferred completions. Corrupt or missing 128 KiB dumps fail the experiment.

This small diagnostic uses the **existing route runner and experiment workflow**, not a new universal gameplay framework, and changes no guest, emulator, product, renderer, save or controller code.

## Decisions enabled by an actual run

- If the first two samples show no checkpoint/lap movement, examine steering/controller alignment or a wrong starting-state hypothesis before inventing a physics bug.
- If lap/gate/checkpoint values progress but the end remains NMI `8610`, the likely first blocker is insufficient driving/loop traversal or a false menu-return expectation; count neither as proven until the original emulator runs the *same* input route.
- If all observed laps/finish conditions complete but no result appears, inspect at frame or instruction time with exact P1/P2 contact, `81:8050` course handler and `82:8C32` dispatch ordering. Separately verify result `009F == BC` persists at least eight guest frames and the decoded results show the expected real race time.
- If original Snes9x with the **same Baldosa driving inputs and starting SRAM** completes while Baldosa does not, rebase to each runner's observed GO/course-entry frame and compare first divergent checkpoint, lap, contact and result. An original mismatch in absolute menu-entry frames cannot be labeled a gameplay regression.
- The 2014 movie's independent original-only original result at frame 8353 (MIKE 1:16.46, best lap 0:25.10) is an **oracle for that movie input**, not an expected time under this separate Baldosa script. The same movie also shows `3→0` checkpoint wrap without lap decrement at 4722 and subsequent `0→1` with `3→2` lap at 4911. Preserve that semantic distinction in later comparisons.

A legitimate first Circuit acceptance requires matching *completed* original/native settled results under identical source input, independently established course identity and complete lap/checkpoint progression. Race and 45-second Stunt each need analogous end-to-end witnesses; no evidence here upgrades those event families.


## Executed original-emulator discriminator (2026-10-09)

PR #1075 **merged**, native AOT workflow [37994315986](https://github.com/gamesbyian/UR-Recomp/actions/runs/37994315986) green. It produced exactly **9,784 frames**, the same final guest WRAM CRC `0x92632636` as the earlier bounded native run, even with two added diagnostic dumps. PR #1077 **merged**, original pinned Snes9x libretro workflow [37995000742](https://github.com/gamesbyian/UR-Recomp/actions/runs/37995000742) green, independently executing the same input with the Baldosa-pinned `snesref`, same USA ROM and original upstream route; only the host-only `turbo` line was removed. Its green confirmation rerun is [37995217647](https://github.com/gamesbyian/UR-Recomp/actions/runs/37995217647).

**4/4 independent original/native sampled guest states agree, all 48/48 named scalar-or-vector field groups match, and zero sampled guest-state differences were observed.** The compared groups include course and active flags, NMI handler, menu scratch, P1 world XY, stored contact, next checkpoint, finish gate, laps remaining, and all five raw stopwatch digits.

| Input phase | Native AND original P1 XY | Native AND original checkpoint / finish gate / laps |
| --- | --- | --- |
| GO tick | `9200,1563` | `0 / 0 / 4` |
| after 300 left frames | `6226,2158` | `1 / 1 / 3` |
| before final 6000 left frames | `6158,2153` | `1 / 1 / 3` |
| after final 6000 left frames | `6217,2155` | `1 / 1 / 3` |

This is **strong evidence the existing Zoom Zoo route itself does not complete the Circuit on authoritative original Snes9x**, irrespective of Baldosa's native AOT correctness. The inputs achieve the initial 4→3 lap decrement and 0→1 checkpoint/gate advancement but stay in the same approximate geometry for thousands of left-held frames. Original Snes9x and Baldosa both remain in `8610` gameplay after driving. The full run's **every-frame original/native fidelity is not measured**: the 9,784 native per-frame WRAM CRCs have not been matched to original Snes9x; only four readouts were compared. Sparse equal endpoints cannot exclude transient differences. No complete Circuit result is admitted.

The archived *different-input* Dessyreqt 2014 movie did authentically reach a settled Zoo result at original movie frame 8353, MIKE total 1:16.46 and best lap 0:25.10. PR #1079 therefore attempts to transplant that exact source-movie controller scene after each engine independently reaches active Zoo, under the same embedded 8 KiB SRAM. This next scene is an experiment, not an assumed completed result. Raw PPU result text and aligned native/original times must still agree before QA-01 can award any of 45 USA complete-course credits.
