# QA-01: one RF-018-only treatment of the original/native Zoo +5040 discrepancy

**Executed 2026-10-16; scientific result negative for Zoo-to-Bowl strict progression, despite a real sound-state improvement.** Not a CPU/APU implementation endorsement, and **0/45** USA courses admitted.

A single source-qualified [GitHub Actions run 38861174758](https://github.com/gamesbyian/UR-Recomp/actions/runs/38861174758) built an original Snes9x reference and Baldosa native with **RF-015+RF-017+RF-018**, but **not RF-016 or RF-019**, on temporary [PR #1692](https://github.com/gamesbyian/UR-Recomp/pull/1692). All four workflow stages completed successfully. QA independently downloaded the 62,318-byte original/native case ZIP (artifact `12029426494`), SHA-256 `f8391d7bfaab1505f89c801ed33b5138598829c833879bd79bf828a7ca38734b`, and verified the full producer-report bytes, SHA-256 `a709eea6d623d89f58642937e26d179cc49c8df4070f0f8f3bf19067f4fdf0d7`. Archived USA ROM, 2014 source SMV, original source SRAM, original controller window and reference replay script hashes match the independent RF-018-off [#1690 baseline](../analysis/data/qa01-zoo-dp5040-independent-two-run-review-20261016.json) exactly. The newly built native ELF differs by design; separate original Snes9x executable SHAs differ between runs, but all **78 original 128-KiB WRAM image hashes** agree cross-run. Complete compact [machine receipt](../analysis/data/qa01-zoo-rf018-only-treatment-review-20261016.json) preserves those hashes and frame values.

## What RF-018 changed

| Source-qualified field | RF-015+017 control | RF-015+017+018 treatment |
| --- | --- | --- |
| Fresh original/native scene entry hosts | 1017 / 1019 | **1017 / 1017** |
| Zoo Circuit result from own entry | +5163 / +5163 | +5163 / +5163 |
| Next Bowl active from Zoo result (original movie / fresh original / native) | +267 / +267 / +267 | **+267 / +267 / +265** |
| 78 sampled whole-WRAM original/native byte-exact pairs | 45 | **46** |
| Total differing WRAM-byte occurrences across those 78 pairs | 109 | **105** |
| At Zoo +5040, `$63` sound pointer original/native (hex) | `73/4D` (delta 38) | **`73/64` (delta 15)** |
| At Zoo +5040, `$69` transfer counter original/native (hex) | `BE/97` (delta 39) | **`BE/AE` (delta 16)** |
| Original/native full SRAM equal across six result-followthrough samples | 6/6 | **4/6** |
| Original/native full SRAM equal across eleven Zoo-to-Bowl samples | 11/11 | **0/11** |
| Result-return sampled named-state differences | none | **menu at result+16** |

At Zoo relative **+5039**, both experiments have all 131,072 WRAM bytes equal. From **+5040 to +5046**, both still show different sound pointer and upload counter bytes in *every adjacent guest-relative frame*. The original-side 78 sampled WRAM SHA-256 values are identical across control/treatment. Only **8 of 78** native WRAM image hashes changed under RF-018: the entry image at +0 and the seven +5040..+5046 images. This is a bounded observation; unsampled frames were not compared and no bytes were masked.

## What failed after the source-authentic result

The native result text and primary +5163 onset remain matched, so the producer's primary result classifier remains `strict_candidate`. **That label does not admit the course:** its independent postresult consumer detected real native-versus-original `menu` mismatch by result +16, first full SRAM difference at +64 (one byte `0x10A7`, original `0C`, native `0D`), and the genuine next Bowl becomes active at **+265 native** rather than **+267 original/source**, with unequal WRAM and exactly **three unequal battery-SRAM bytes** at each of eleven later samples (offsets `0x0F31`, `0x0F33`, `0x10A7`). The original Crawler ranked records, holders and record checksum remain equal. Imported source labels `0x10A7` as `sCutsceneTimer2`; the source-verified writer/consumer of the other bytes is not established. These differences prove failure of strict sampled event return/progression, **not** corrupted ranked records or Windows on-disk persistence.

## Disposition and next action

This *single-treatment* A/B falsifies the hypothesis that **RF-018 alone** cures +5040 and can be carried into Zoo's corrected progression pipeline without additional source adjudication. Its partial +5040 pointer/counter improvement (roughly 23 fewer counts of discrepancy at onset) is a valuable causal lead for CPU/APU, but the exact SPC executed writer/port handshake, frame/beam clock and unintended +265 Bowl advancement remain to explain. Handed to [CPU/APU issue #1689](https://github.com/gamesbyian/UR-Recomp/issues/1689), with [shipping RF-017 mismatch #1686](https://github.com/gamesbyian/UR-Recomp/issues/1686) still separate. Do **not** move input frames, suppress byte differences, treat research-run green as a fidelity pass, or promote RF-018 into Windows shipping source based on this experiment.

The temporary PR-triggered experiment workflow was deleted after execution. This document and its compact receipt are retained, not another automatic CI workflow. **0/45 USA complete-event admissions.**
