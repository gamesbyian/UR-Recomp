# Native frontier: full existing-checkpoint raw-source probe (2026-10-13)

**Purpose:** Resolve whether the three historically unobserved *raw source-field* categories are absent from the native 2P experiments or simply missed by the old three-checkpoint observer. **No SNES gameplay/original-emulator parity, PPU acceptance, physical controls, result completion or release credit is implied by these diagnostics.**

## What the finished 100-case policy smoke established

The post-PR-1398 cumulative [100-case run #38438864232](https://github.com/gamesbyian/UR-Recomp/actions/runs/38438864232), source `d379efcd09fdd73aa817eca24e92263f5a217996`, completed successfully and the append-only `research/qa-cumulative-ledger` accepted it. It executed 100 new cases, 112 genuine compiled-native processes, four replay/seat-removal verification cases and **all five input arms**. The original 10k cohort had starved alternating and rotation; this run assigned **49 alternating, 34 rotation, 5 balanced, 6 P1-focus and 6 P2-focus**.

It measured **201 distinct fingerprint identities**, of which **200** were not already in the cumulative catalog, increasing the exact normalized 96-bit fingerprint union **20,179 → 20,379** across 10,200 successful frontier cases. As before, each case contributed the same fixed `endurance-1740` token and one individual token per `endurance-2580` and `endurance-3420` snapshot. The exact three-frame per-run distribution was **1 / 100 / 100**. These are source-field fingerprints, not distinct complete gameplay behaviours.

**Additional archived 100-case receipt audit:** all four retained shard `result.json` files were independently inspected, and every content SHA-256 matched its original source receipt. At the original frames, each legal-input arm showed exactly one common starting token and then a *unique fingerprint per case* at both later checkpoints:

| Input arm | Source cases | Distinct frames 1740 / 2580 / 3420 | Opposing X-motion cases | Both rotation registers changed |
| --- | ---: | --- | ---: | ---: |
| Balanced | 5 | 1 / 5 / 5 | 5 | 4 |
| P1-focused | 6 | 1 / 6 / 6 | 1 | 6 |
| P2-focused | 6 | 1 / 6 / 6 | 4 | 6 |
| Alternating | 49 | 1 / 49 / 49 | 36 | 47 |
| Rotation | 34 | 1 / 34 / 34 | 18 | 34 |

The only three cases without *both* tracked rotation registers varying across those sparse checkpoints were **50024009/balanced/shard 0**, **50024066/alternating/shard 2**, and **50024098/alternating/shard 3**. All source features remain native raw-field predicates, not independently checked original-game behaviour. This breakdown further confirms the strategy fix: the previously starved arms were genuinely exercised, even though none produced one of the three still-missing sparse features.

The sparse feature census was **100 both-moving**, **100 checkpoint-pointer changes**, **97 both-rotation-register changes**, **64 opposing X-motion**, and **100 split-register-nonzero** cases. Zero cases exhibited a sampled simultaneous nonzero pair of air fields, nonzero offscreen register values, or split-register changes **among the original three frames**. This is a *negative measurement*, not a finding that these mechanics are absent or incorrect. The 100-case aggregate remains immutable. This document captures the follow-up method, not a fabricated result from an unexecuted full-trace experiment.

## The surprisingly inexpensive next experiment

The source producer `tools/qa02_native_2p_seeded_endurance.py` already captures **15 full 128-KiB native WRAM images per original input process** at frames **1740, 1860, 1980, 2100, 2220, 2340, 2460, 2580, 2700, 2820, 2940, 3060, 3180, 3300 and 3420**. It also records a pre-stimulus `two-player-both-post-1620` control snapshot.

Before this change, `tools/qa_adaptive_frontier.py` read only three of those existing dumps (`endurance-1740`, `endurance-2580`, `endurance-3420`) to calculate both the exact semantic-fingerprint census and the eight source feature booleans. The other 12 WRAM snapshots existed but were **unused** by the source-feature classifier. All three negative categories could represent brief phenomena between the selected samples.

The new `full-existing-15-wram-frames-raw-fields-v1` diagnostic **reuses all already-created files**, with no extra native process, run length, ROM instrumentation or changed controller input:

* Apply the exact same eight raw source-field predicates to all 15 snapshots while leaving the prior three-frame results unchanged and comparable.
* Retain per-case feature labels and the *earliest sampled source frame* at which each label becomes true. For temporal predicates, this is the first checkpoint where the **sampled evidence so far** establishes a changed register, not the exact hardware clock cycle of a transition.
* Preserve sorted distinct **raw 8-bit** register values observed across the full native cohort for slot-1 `air_effective` (WRAM `0x0545`), slot-2 `air` (`0x0547`), P1/P2 offscreen candidates (`0x121B`, `0x121D`) and split-mode candidate (`0x0DDB`). These are source-indexed candidates, not established display semantics.
* Emit two independent population counts per feature: **all-15** and **all-15 but missed by old three**. For a positive missed count, retain the first genuine `seed, arm, shard, first sampled frame` as a handoff witness.
* Validate all 15 original 128-KiB source snapshots for every input; do not silently substitute generated guesses for missing checkpoints or promote samples from a failed process.
* Reject malformed/contradictory per-case traces in the source aggregate and reject noncanonical, missing, inconsistent, or unbound counts/witnesses in the cumulative coordinator. The SHA-256-checksummed source-receipt and canonical experimental plan remain the accountability chain; no release credit changes.

The projected exact-fingerprint *extraction epoch and population stay unchanged*: **three frames per native case**, the same normalized fields, the same persisted 96-bit hash identities, and the same HLL historical comparator. The denser **feature observer is separate**. Replacing the canonical semantic fingerprint population with all 15 frames would break cross-run comparability and therefore requires a deliberate new census epoch, not an accidental schema drift.

## Hypotheses and decisive readings

| Observation from a future real run | What it supports | What it does **not** show |
| --- | --- | --- |
| `both-air-raw` appears only in all-15 | Brief overlap in the two *tracked* native air fields between the old frames | That both racers truly left the ground in the original game |
| `offscreen-register-nonzero` appears only in all-15 | Raw source slot changes between old checkpoints | That the original PPU hid an OBJ or that graphics are correct |
| `split-register-changes` appears only in all-15 | Candidate split register had a transient state or transition | The visible split-screen presentation's exact timing |
| All three remain zero, and the associated raw field unions are all zero / invariant | A stronger *15-frame sampled negative* for this actual input cohort | Proof that the fields are constant between frames or that the game lacks the mechanics |
| Individual air fields vary but simultaneous nonzero pair remains zero | Both candidate air registers may activate separately, but not on one observed frame | That the source flags mean actual airborne gameplay |
| New observable category but no original comparison | A reproducible native source-state hypothesis for the owning QA lane | A validated original/native fidelity discrepancy |

These distinctions matter. Checking a raw bit **once every 120 emulated frames** is a more capable survey than every 840 frames, but it is still not continuous, and a native guest trace alone cannot validate the original SNES's behaviour.

## Experiment selection

**After source+unit CI is green and this PR merged**, run just **one 100-case `frontier` cumulative campaign** on `main` using the normal seven-lane [research coordinator](../.github/workflows/qa-cumulative-research.yml). Check the ledger's `full_trace_feature_counts`, `full_trace_only_feature_counts` and `full_trace_raw_field_values` against the legacy `source_feature_counts`. Do **not** launch 10,000 more cases until the narrower sampling question has been tested.

If a missing category appears, preserve the matching source SHA, ROM/executable hashes, input seed, arm, shard and sampled frame from `full_trace_only_feature_witnesses`; then have QA-01/07 or QA-08/10 compare that exact case to its authentic original-USA CPU/PPU data with independent timing/oracle authority. If no category appears, inspect the five raw register-value distributions, revisit source offsets/conditions and consider a *narrow, deliberately chosen* finer-cadence original/native probe. Never call a zero count evidence that the mechanic does not exist.

**Owner boundary:** this patch touches research-only producer, coordinator, handoff, tests and documentation. It does not modify gameplay simulation, graphics, Modern frontend, storage, independent QA comparator, ROM or release ledger.
