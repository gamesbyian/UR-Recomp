# Fifteen-frame native source diagnostics (research epoch)

**Status:** proposed research instrumentation. No new original/native comparison result or accepted event is claimed here. This adds an *observability audit*, not more semantic fingerprint states and not a change to guest, renderer, Modern product or independent QA.

## Why this is the next experiment

The accepted [10,000-case postmortem](QA-FRONTIER-10000-POSTMORTEM-20261013.md) showed that 19,980 normalized source-state fingerprints were generated at just three checkpoints: one identical at frame 1740, 9,987 distinct at 2580 and 9,992 distinct at 3420. The completed [100-case corrected-policy smoke](https://github.com/gamesbyian/UR-Recomp/actions/runs/38438864232) executed all five legal input arms, accepted exactly 200 additional fingerprint identities, and increased the cumulative exact union to **20,379**. Its original three-checkpoint counts remained zero for both-air-raw, offscreen-register-nonzero and split-register-changes.

However, the native first-race observer already saves 128-KiB WRAM frames **1740, 1860, ..., 3420** (15 total, every 120 frames) for *each real native case*. Until this change, the frontier feature classifier read only 1740, 2580 and 3420. A transient event or mode transition in any of the twelve ignored snapshots was invisible to its classifier. The retained receipts do **not** include the twelve intermediate dumps, so this cannot be retroactively computed from previous aggregate files. No missing-data interpolation is authorized.

## Two distinct measurement contracts

| Measure | Existing three-checkpoint experiment | New fifteen-frame diagnostic |
| --- | --- | --- |
| Frames | 1740 / 2580 / 3420 | All 15 captured frames, 120-frame cadence |
| Eight source-derived feature predicates | **Unchanged** `source_feature_counts` | `dense_feature_counts`, split by input arm |
| Identity / reproducibility | Exact 96-bit projected-state fingerprints and per-case `seed/arm/shard` | Per-feature first-observed **frame**, `seed/arm/shard` |
| Raw register evidence | Only feature predicates at 3 checkpoints | For 5 raw 8-bit fields: minimum, maximum, nonzero-frame and transition counts per case; aggregated bounded per-field summaries |
| Independent original SNES comparison | **None** | **None** |
| New emulator processes | Existing 1 + 3 metamorphic verifications per selected case | **Zero** additional processes |
| Exact cumulative fingerprint epoch | Unchanged | **Does not enter the union** |

The dense epoch is `native-2p-source-field-120-frame-trace-v1`; it is not a backward-compatible substitute for the historical three-frame feature count or for `qa_frontier_coverage.EPOCH`. All source shards must contain complete signed-by-checksum (not cryptographically signed) per-case diagnostic objects with 15 real source checkpoints; the aggregator fails closed on missing or contradictory summaries, unsupported raw values or forged feature witnesses. The cumulative coordinator retains both views under separate names and rejects internally inconsistent aggregates. A failed experiment still consumes its reserved seed window, without credit.

The explicitly tracked *raw source offsets* come from `tools/summarize_paired_player_slots.py`: P1 air candidate `0x0545` and P2 `0x0547`; split-screen mode candidate `0x0DDB`; P1/P2 offscreen candidates `0x121B`/`0x121D`. These are original-named WRAM slots but their complete gameplay semantics, direction of causality and relationship to PPU/OBJ rendering are **not** independently established. Register nonzero and change predicates are not synonymous with actual airborne physics, visibility, screen splitting or graphics correctness.

**New reports deliberately distinguish three possibilities:**

1. A feature appears at an intermediate checkpoint despite zero three-frame cases. This is an observed sampling blind spot; reproduce its first exact seed, arm, shard and frame before testing an original emulator hypothesis.
2. The feature never appears in any of the fifteen snapshots, but individual source fields vary or have nonzero maxima. Investigate the predicate (e.g., simultaneous air on the *same* frame) or field meaning; do not declare the original gameplay mechanism absent.
3. The raw fields are invariant or zero across the whole 15-frame horizon. Investigate whether these controller inputs, this first race, or the 120-frame cadence ever reaches a relevant transition. A zero remains a **bounded non-observation**.

## Reproduction and next decision

After this instrumentation passes unit tests and merges, use [the serialized cumulative campaign](../.github/workflows/qa-cumulative-research.yml) to run **100 frontier cases on `main`**. The coordinator must pass with 112 actual native processes, all five strategies represented, exact 3-frame fingerprint union/dedup unchanged in definition, and a new `dense_observer_epoch` and eight valid `dense_feature_counts`. Inspect first-source frames and by-arm comparisons for the three formerly zero categories. Keep no-release-credit fields false, and preserve original/ROM/build hashes.

If 100 cases give interpretable source-category witnesses, pass those precise seed/arm/shard/frame packets to QA-01/07 gameplay and QA-08/10 original PPU owners for independent emulator validation. If 100 cases remain uninformative, inspect the source-observer interpretation and controller input reachability *before* another large seed sweep. **Do not run 10,000 cases merely to expand normalized coordinate-hash counts.**

Unit tests exercise an artificial transient dual-air/offscreen/split change visible in the intermediate 15-frame scan but absent at the three historical frames; they are **synthetic parser tests**, not proof the actual native game exhibits those signals.
