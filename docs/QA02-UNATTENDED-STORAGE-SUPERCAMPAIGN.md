# QA-02/03 unattended storage supercampaign

**Purpose:** launch both existing production-store stress families with **one manual Actions dispatch**, without building yet another fixture, adding automatic triggers or repeating agent-led steps. This is CI/research infrastructure, not a completed Windows player-journey or independent game fidelity release gate. Authoritative source validators remain [C12 coordinator race](QA02-C12-PROCESS-RACE-CAMPAIGN.md) and [real-process recovery](QA02-REAL-PROCESS-RECOVERY-CAMPAIGN.md); their individual receipts, errors and test contracts stay unchanged.

**Workflow:** [QA-02 unattended storage supercampaign](../.github/workflows/qa02-unattended-storage-batch.yml). Choose `trials_per_scenario` 10, 100 or 500. Optionally vary bounded numeric `c12_seed` and `recovery_seed` between independent dispatches. The parent invokes the **existing** manual C12 and recovery workflows as GitHub Actions reusable workflows at the **same exact source commit**, in parallel. Their own binaries are intentionally *different native fixtures* with separate source-owned compile steps, not a fabricated cross-fixture shared game executable.

| Choice | C12 independently synchronized real two-process races | C09/C14/C15/C16/QA03 OS-process fault/recovery journeys | Entire population |
| --- | ---: | ---: | ---: |
| Smoke 10 | 4 shards × 10 = 40 | 5 shards × 10 = 50 | **90** |
| Batch 100 | 4 × 100 = 400 | 5 × 100 = 500 | **900** |
| Extended 500 | 4 × 500 = 2,000 | 5 × 500 = 2,500 | **4,500** |

The two child workflows each bound case parallelism to two runners, with independent deadlines, fault limits and fresh user-data roots. Thus the parent may consume up to four concurrent Linux case runners; it does not create 4,500 Actions jobs. At most nine bounded matrix shards execute real producer fixtures, then two original aggregators and one parent summary. The original single-case workflows remain independently dispatchable. Account-level Actions concurrency and runner minutes should be reviewed before dispatching the extended cohort.

**Result handling:** The parent downloads the two **original aggregate result artifacts**, not text log claims, and validates their source SHA, exact requested/observed/passed population, all required shard/suite coverage, original binary hashes, both original `completed_positive` dispositions, absence of missingness and zero fake release credit. It also requires the child reusable workflow jobs to have succeeded. Failed, cancelled, skipped, omitted, tampered or mismatched results produce a non-green parent aggregate, a bounded issue summary and a machine `qa02-storage-supercampaign-aggregate` receipt. It never uploads the native private data roots, raw ROM, SRAM, controller input files or synthetic user data.

**First execution:** dispatch **10** at an exact nominated revision. Confirm the parent receipt says 90/90 (not simply that some child jobs are green), and verify actual elapsed time and runner capacity before using **100**, then **500**. A green 4,500-case storage stress campaign certifies only the established production-store OS-process fault contracts. It is **not a substitute** for a genuine Baldosa 1P/2P Windows session with fresh-process Records, hardware storage crash/power-cut, QA-01 45-course acceptance or physical graphics/audio/gamepad testing. All release ledgers remain unchanged.

**Stop/revisit:** once the full cohort has no defects, retain this manual orchestration as a selective regression instrument. If any shard fails, use the named original producer and seed/index to reproduce/fix the actual invariant. Never relax the underlying C12 single-winner or recovery one-receipt assertions to force a green result.
