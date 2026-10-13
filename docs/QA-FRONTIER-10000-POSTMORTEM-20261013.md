# Adaptive frontier: first 10,000-case exact-source census (2026-10-13)

**Disposition:** completed observational research; **zero** original/native event admissions or release credit. This document is a durable, reviewed-summary candidate of the [10,000-case coordinator run](https://github.com/gamesbyian/UR-Recomp/actions/runs/38306802282), its [source producer aggregate artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/38306802282/artifacts/11814737360), and the append-only [research evidence ledger](https://github.com/gamesbyian/UR-Recomp/blob/research/qa-cumulative-ledger/.github/qa-cumulative/ledger.json). The corresponding machine-readable snapshot is [`analysis/data/frontier-10000-postmortem-20261013.json`](../analysis/data/frontier-10000-postmortem-20261013.json). The ledger is authoritative and can continue to advance; this dated snapshot must **not** be represented as a live count.

## What genuinely ran

The pinned native two-player harness executed **10,000 different post-entry legal-controller case scripts** (40 independent shards × 250), plus identical-replay and separate P1/P2-mute checks on **400** cases (three extra native processes per verification case). That is **11,200 real compiled-native process executions**. All 40 source-receipt shards were present, internally coherent, and independently aggregated. The research coordinator classified the result `completed_positive` and appended a signed ledger record; the source producer classified it `completed_observational`. The producer had **no recorded evidence issues**. A green workflow indicates successful experiments and recording, **not** correctness versus the original SNES.

| Exact observation (new fingerprint epoch) | Count |
| --- | ---: |
| First 100-case accepted baseline ([run 38304551380](https://github.com/gamesbyian/UR-Recomp/actions/runs/38304551380)) | 201 distinct normalized fingerprints |
| 10,000-case run: distinct normalized fingerprints **within this run** | 19,980 |
| Previously observed identities overlapping this run | 2 |
| **New fingerprints** in the 10,000-case run | **19,978** |
| **Exact cumulative union** over both accepted runs | **20,179** |
| Completed source-frontier inputs across both runs | 10,100 |
| Strict original/native complete-event acceptance credited | **0** |

Each fingerprint is a **96-bit truncated SHA-256 identity of a deliberately normalized subset of native WRAM source fields** at three predetermined checkpoint frames (1740, 2580, 3420). Exact identity counting means deduplicating those persisted 96-bit values exactly, subject to theoretical digest collision risk; it cannot imply 20,179 distinct underlying full-memory states or gameplay behaviours. Original-SNES comparison was **not** performed. The approximate HyperLogLog result of 20,280 is retained only as legacy telemetry and should not replace the exact cumulative count.

**Immutable provenance:** source commit `7f3fbff42673ff43b23f3fc74034acd6f5873a30`; native executable SHA-256 `28501fa3268f82d83672122cddbd2628ce5b2458e625f46d93766f50befbe515`; USA ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; original input SHA-256 `28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490`; original script SHA-256 `ebac1a3505281e9793c8197006081c5d88f6ab3383df48f23ba2475159e9e6e3`. Producer plan SHA-256 `751bbd5962614a48097e67fa196c8a3e9c4d3bf6123dd62c8c8301047dbf0451`; unsigned aggregate receipt SHA-256 `22dbcdc32e998865bc26e01deacb34943050cdbf4883717cb4dbbafbfa57c4a8`; full aggregate object SHA-256 `71267ab4cd9105ea45c82237bd2dd330087d88e5833b03746ffd2768260cf2fe`. Inputs were seeds **50,012,000–50,021,999** inclusive. These are reproduction identities, not authorization to distribute ROM bytes.

Wall-clock workflow: **2026-10-12 20:50:24 UTC to 2026-10-13 12:44:35 UTC**, or **15h 54m 11s**, with individual shard execution from ~56 to ~107 minutes (180-minute per-shard hard cap). Avoid linear extrapolation from the 100-case run without accounting for shared build overhead, worker scheduling and per-shard execution.

## Follow-up forensic audit: all 40 signed shard receipts

After the initial coordinator success, every original `research-frontier-0` through `research-frontier-39` artifact was independently retrieved and each source-owned `result.json` checksum was checked against its aggregate shard receipt SHA-256. **All 40 matched.** The 10,000 cases were then regrouped by the **three real checkpoint frames**, instead of treating every token as an indistinguishable discovery:

| Actual sampled checkpoint | Exact distinct fingerprints | Interpretation |
| --- | ---: | --- |
| `endurance-1740` | **1** | Same `b49fd909c5fd16ae947c3b55` signature on **all 10,000 inputs** |
| `endurance-2580` | **9,987** | Wide normalized variation after input mutations |
| `endurance-3420` | **9,992** | Wide later normalized variation |
| **Exact union** | **19,980** | No collisions *between the three sampled checkpoint populations* |

Within **every** 250-case shard, there was one fingerprint at frame 1740 and exactly 250 distinct fingerprints at each of frames 2580 and 3420. The fewer than 10,000 global distinct fingerprints at the later frames come from repetition **across shards**. The first checkpoint is behaving as a common starting-state/control witness, not a useful diversity signal. The first checkpoint's invariance does **not** by itself establish pre-entry source parity or anything about the original ROM emulator.

This sharper decomposition means that the headline **19,978 newly observed** fingerprints are overwhelmingly varied **late-state projected position, velocity, rotation and progress records**. High cardinality alone is a weak proxy for discovering new behaviours. Future aggregates now calculate and report exact **per-checkpoint** unique counts alongside the deduplicated union, so a broad random exploration campaign cannot obscure how much novelty comes from a fixed observation point.

The audited per-arm breakdown also shows that each of the three exercised strategies had one fixed first-frame fingerprint. At frame 2580 / 3420, respectively: `balanced` **5,752 / 5,755**, `p1-focus` **2,837 / 2,840**, and `p2-focus` **1,400 / 1,400** distinct values. Across the real cases, opposing X motion occurred in **3,990 / 5,760** balanced cases, **1,702 / 2,840** P1-focus cases and **862 / 1,400** P2-focus cases. These are descriptive counts, not controlled original-game physics comparisons.

## Source-observed feature census

The following categories are **case counts** (a case may satisfy several categories) computed solely from already-indexed guest WRAM observations, not independent CPU/PPU ground truth:

| Raw category | Cases / 10,000 |
| --- | ---: |
| Both moving | 10,000 |
| Checkpoint/progress pointer tuple changes | 10,000 |
| Both tracked rotation registers change | 9,689 |
| Opposing horizontal speed signs | 6,554 |
| Split-register nonzero at sampled snapshots | 10,000 |
| **Both tracked air fields nonzero together** | **0** |
| **Offscreen register nonzero** | **0** |
| **Split register changes between sampled snapshots** | **0** |

The last three zeros require **observer qualification** before a gameplay conclusion: only three frames are sampled, and a register that is permanently nonzero across all three samples can satisfy `split-register-nonzero` in every case while never satisfying `split-register-changes`. Similarly, zero dual-air/offscreen *observations* does not demonstrate those mechanisms are absent or broken. Before spending another large native batch, the owning lane should inspect the actual source-field offsets and capture higher-cadence source/original observations across a deliberate transition, then determine whether the selected controller scripts can exercise that feature. Do not change graphics, guest rules or acceptance on these counts.

Recorded reproducible first-source witnesses for the five observed positive categories all start at **seed 50012000 / arm `balanced` / shard 0**. For exact fingerprint replay selection, the handoff artifact provides 24 example `(fingerprint, seed, arm, shard)` packets and the cumulative exact ledger retains a source-linked earliest witness for **every** known fingerprint. Example: `01bcd277a449aa4653b77b56` was seen at seed **50012019**, arm `balanced`, shard 0. Use the `qa_frontier_exact.py` lookup command documented in [QA-ADAPTIVE-RESEARCH-FRONTIER.md](QA-ADAPTIVE-RESEARCH-FRONTIER.md) with the evidence branch, retrieve the source-matched plan/artifact, and reproduce with the pinned binary. **Do not** identify a native fingerprint with an original-SNES state until an independent original emulator supplies the corresponding qualified observation.

## Why two legal input strategies were starved

| Native controller arm | 100-case baseline trials | 10,000-case trials |
| --- | ---: | ---: |
| Balanced | 84 | 5,760 |
| P1-focused | 4 | 2,840 |
| P2-focused | 4 | 1,400 |
| Alternating | 4 | **0** |
| Rotation-focused | 4 | **0** |

This is a **research policy failure, not a native gameplay failure**. The selector's local five-arm warm-up used combined `local_attempts + cumulative_prior_attempts`. Because all arms had already been attempted four times in the 100-case baseline, the 10,000-case run skipped fresh warm-up and the upper-confidence scorer never selected alternating or rotation. Therefore **10,000 cases did not exercise all five planned populations**. The evidence remains valid for the three arms that ran; it must not be generalized to the two absent arms.

The follow-up patch records the policy as `fresh-five-arm-warmup-plus-decile-v1` in the reproducible plan: every shard tries every arm once in its first five cases, followed by a deterministic rotating forced arm every tenth case. All other cases retain the historical-prior UCB scorer. The source aggregate rejects a planned forced-arm identity that does not match its real recorded case, and synthetic tests cover 100, 1,000, and 10,000-case planning and a strongly skewed historical prior. This is an **exploration guarantee**, not evidence that the five arms reach distinct gameplay states.

## Decision, next experiments and ownership

1. **Keep the original run's successful evidence unchanged.** The signed exact ledger and source artifacts remain the authority; do not rerun the original seeds as if they were new experiments.
2. **Qualify the new policy cheaply.** Once merged, dispatch a **100-case** cumulative frontier run from `main` and verify all five arms receive new trials, plan/aggregate signatures match, fresh-case reproducibility passes and the exact union updates without fabricated source-parity credit. Only scale to 1,000 or 10,000 if the new evidence justifies it.
3. **Investigate the feature zeros as specific hypotheses.** A source-observer/graphics owner should identify known original cases with dual-air/offscreen or split transitions and validate slot semantics at higher temporal resolution. Feed genuinely qualified states to the existing QA-01/07 original/native comparator, rather than count hash novelty as gameplay correctness.
4. **Promote verified discrepancies into focused regression tests.** Preserve original and native source SHA, ROM, movie, exact frame alignment and event-specific terminal result. Official USA complete-event acceptance remains **0/45** until the strict owning authority admits an event.

A separate coordinator window [run 38306716093](https://github.com/gamesbyian/UR-Recomp/actions/runs/38306716093) was canceled and recorded as an incomplete **Windows** research run. It is not part of the 10,000-case success or exact-frontier numerator. The evidence ledger correctly retains it with no positive credit.

**Stop condition:** broad novelty alone is not a reason for another costly 10,000-case batch. The next expensive dispatch must have a qualified question, a real observer/source oracle, and a planned comparison or new semantic feature worth finding.
