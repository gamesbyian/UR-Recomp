# Independent QA-01: exploratory SPC/interrupt-stage three-event original/native review

**2026-10-16. Three genuine source-backed primary result candidates, 0/45 complete USA events admitted.** Source-qualified research only, **not** integrated main or shipping Windows. The independently downloaded and SHA-256 verified [three-event machine receipt](../analysis/data/qa01-combined-spc-three-source-event-review-20261016.json) retains the source, plan, three case ZIP/report SHA-256s, case identity and falsifiable timings. The completed [GitHub Actions run 38879846733](https://github.com/gamesbyian/UR-Recomp/actions/runs/38879846733) has **3/3** `strict_candidate`, 0 strict divergences, 0 producer errors, 0 missing artifacts and explicitly **0 release admissions**.

## Why this result matters

All three authentic events were extracted from the unchanged 2014 movie, USA ROM and source SRAM and replayed on **the same pinned research native ELF**. Original reference and fresh Baldosa entry host frames are independently calibrated and equal, but these are not the original movie's reset-host frames.

| Case | Original movie relative result | Fresh Snes9x/native result | Source-relative clock difference | Matching result text |
| --- | ---: | ---: | ---: | --- |
| Zoo, Circuit A | +5163 | **+5163 / +5163** | 0 / 0 | MIKE 1:16.46; best lap 0:25.10 |
| Bowl, Stunt | +3365 | **+3365 / +3365** | 0 / 0 | MIKE 764; qualify 68 |
| Switcher, Race B | **+4703** | **+4704 / +4704** | **+1 / +1** | MIKE 1:08.81 |

Zoo and Bowl have newly reproduced exact fresh original/native result-relative timing; Bowl improves on the prior RF-015+017 native one-frame-early terminal result. Switcher also fixes the prior *fresh original/native* two-frame phase mismatch, but its **archived source movie itself** shows a +4703 result interval, not fresh +4704. The original movie clock, fresh original clock and native clock must remain distinct. This is observed timing, not authorization to retime original input or proof of a one-frame emulation fault.

Each case reproduces all six source/original/native **named** sampled states at result +8,+16,+24,+32,+64,+72, with six paired entire **8192-byte in-memory SRAM images equal**, matching earned ranked records and record checksums. But **all six paired complete 128-KiB WRAM snapshots differ** for each case. None was run with Zoo `--zoo-next-bowl` or dense `--zoo-dp-window` enabled, so the source-authentic +267 Bowl handoff and +5040 SPC-pointer discrepancy **have not been retested on this candidate ELF**. A `strict_candidate` is a result-only research classification and must not be upgraded to full-course parity or Windows acceptance.

## Patch ownership and scientific limits

This campaign ran from **non-main** source commit `d9134a6e5da87145f1ad38e02382cce067fe6ec3` on transient branch `ccr-ffd0127f-owy9hb`. The native ELF is SHA-256 `9a3bd17afd8377a4c83e76c05cd57dfdae2488e498aa4bea1b90a2baa018bb48`. Build logs confirm **all RF-015, RF-016, RF-017, RF-018, RF-019** enabled and a subsequent composite SPC/interrupt stage: SPC power-on anchor 0, SPC frame clock, SPC bus-cycle and interrupt-entry cost, in that order. No single stage is causally identified by this combined experiment. In particular, RF-018 *alone* previously produced an unacceptable Zoo +265 next-Bowl regression (merged [RF-018-only negative](QA01-ZOO-RF018-ONLY-TREATMENT-20261016.md)), which this result-onset-only experiment **does not clear**.

The original USA ROM SHA-256 is `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; movie `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442`; original SRAM seed `a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828`. Source and reference executable ZIP/case/report SHA identities are recorded in the machine receipt. Provenance does not equate this exploratory native ELF to any nominated Windows PE or prove cold OS disk persistence.

## Next minimal independent adjudication

1. **One Zoo-only, same correction bundle, same source movie** (rather than a repeated three-case campaign), enabling genuine `zoo_next_bowl`, `zoo_race_mesh`, `zoo_dp_window`, `zoo_terminal_phase` and `source_followthrough`. Confirm original/movie/fresh native Bowl **+267**, 11 actual complete SRAM pairs and all unmasked WRAM differences; compare sound DP `$63/$69` across relative +5039..+5046. Treat changed candidate ELF source hash and native phase as identity, never casually substitute a different binary.
2. In parallel, source-owner CPU/APU should separate the new SPC and interrupt stages with source-pinned A/B only if the preceding Zoo full-return requirement passes. The *exact* live original/native PC/SPC/beam writer trace remains needed to explain the original +5040 sound-upload difference.
3. Do not update the release ledger or award any USA course until original complete-event clocks/progression, source vs fresh relative timing (especially Switcher +4703 versus +4704), real Windows executable parity and applicable persistence gates are independently accepted.

Three-project reuse completed: the existing UR source-original/native producer, the pinned Baldosa research emitter and Malmazuke's archived-controller provenance. No new automatic workflow or gameplay emulator is introduced by this QA review. **Release admissions 0/45.**
