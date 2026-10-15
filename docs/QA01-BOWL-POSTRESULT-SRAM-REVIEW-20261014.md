# QA-01/07: independent read-only classification of Bowl post-result SRAM continuation

**Date:** 2026-10-14 (Calgary; UTC execution 2026-10-15). **Status:** completed hosted research, *not* an accepted complete USA event, *not* a release-ledger change.

## Exact producer identity

- **Research PR:** [#1625](https://github.com/gamesbyian/UR-Recomp/pull/1625), one-shot branch head `2ec7151c599fc4317a4e0a47e50b37e940e9991d`. The branch adds `--source-followthrough` to existing `.github/workflows/qa01-bowl-stunt-2014.yml` only. **Do not merge that temporary research switch** into the automatic workflow.
- **Actual hosted run:** [38667744452](https://github.com/gamesbyian/UR-Recomp/actions/runs/38667744452), job `116203460329`, completed **success**. Bounded source artifact `qa01-bowl-scored-stunt-diagnostics`, GitHub artifact ID `11943222369`, nominal size 32,396 bytes. The log displays the source-qualified structured report; **the archive bytes were not separately downloaded and hashed in this read-only review**, so archive-content claims below retain the producer-reported source tier, not independent raw-byte audit status.
- **Inputs:** existing pinned original Snes9x and native Baldosa USA guest execution, genuine archived 2014 controller movie and embedded source SRAM, fresh independent original/native Crawler Bowl Stunt entry. No input shift, guest-state intervention, saved-player substitution or emulator correction was introduced by the one-shot.
- **Reuse:** current three-project preflight favours UR's original/native trace and checkpoint/evidence chain; it does not authorize a new emulator, result comparator or release gate. [Bowl history](QA01-2014-COMPLETE-EVENT-TRANSPLANT.md), [authoritative course census](ORIGINAL-COURSE-EVENT-CENSUS.md).

## Observed outcomes, read from the completed actual job log

The original/native producer reports a positive genuine Bowl scored result, **MIKE 764**, matching settled visible score text, and an original result-onset phase difference still present: original guest-relative terminal frame **3365**, Baldosa **3364**. Its summary explicitly says `full_event_frame_parity_candidate=false`, `one_frame_stunt_phase_observed=true`, `diagnostic_success_not_admission=true`, and `official_admitted_usa_events=0`.

The source-original movie's six post-tally samples at offsets **+8, +16, +24, +32, +64 and +72** are preserved separately from the *fresh replay* host timeline. At each corresponding fresh original/native offset, the producer reports:

| Offset | Archived movie host frame | Fresh original/native host frame | Original/native menu | Crawler ranked Stunt records | Full SRAM and record equality |
|---|---:|---:|---|---|---|
| +8 | 11993 | 4357 / 4357 | 24 / 24 | 764, 0, 0 / 764, 0, 0 | true / true |
| +16 | 12001 | 4365 / 4365 | 246 / 246 | 764, 0, 0 / 764, 0, 0 | true / true |
| +24 | 12009 | 4373 / 4373 | 246 / 246 | 764, 0, 0 / 764, 0, 0 | true / true |
| +32 | 12017 | 4381 / 4381 | 246 / 246 | 764, 0, 0 / 764, 0, 0 | true / true |
| +64 | 12049 | 4413 / 4413 | 22 / 22 | 764, 0, 0 / 764, 0, 0 | true / true |
| +72 | 12057 | 4421 / 4421 | 22 / 22 | 764, 0, 0 / 764, 0, 0 | true / true |

The original movie changes track **2 → 3** between +32 and +64; at +64/+72 both fresh guests are in menu 22. The live host frames above are replay-local and **must not be substituted for the archived 2014 movie frames**. The producing report states `original_vs_native_named_equal=true`, `original_vs_native_sram_equal=true`, `original_vs_native_crawler_records_equal=true`, `samples=6` and **`cold_process_persistence_proven=false`**.

## Interpretation and acceptance boundary

This result materially narrows the **post-result persistence hypothesis**: the observed one-frame stunt result-phase discrepancy did **not** produce a detected divergence in the six producer-compared full 8-KiB SRAM images or the three scored Crawler records through the next-menu handoff. It does not identify the cause of the one-frame phase error or prove that *all intervening frames* were strictly equivalent. A six-point positive source-SRAM census is also not a fresh-process store recovery or a full 45-course correctness result.

**No gate promotion.** The exact original/native terminal phase is still unequal, raw SRAM images have not been independently reproduced from the artifact in this review, and no physical Windows player or replay-store witness is supplied. Official course census remains **0/45 complete, 4 partial, 41 unverified**; QA-01/07 and the release ledger remain unchanged.

## Next consequential action

Consume this successful source producer as a *bounded completed experiment*. Preserve the one-shot branch run and archive; **close PR #1625 unmerged** after this receipt is integrated. Integrate the separately owned RF-015 DRAM-refresh correction only after its hosted original/native campaign is independently checked, and revisit Bowl's remaining one-frame timing only if the correction or another source-backed observation changes the actual strict release decision. Do not run more Bowl SRAM sweeps merely to increase sample count.
