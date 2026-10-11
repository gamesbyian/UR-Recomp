# QA-02/03 unattended real-process recovery campaign

**Class:** manual research and adversarial production-store acceptance, **not a shipping or original/native gameplay release gate**. Entrypoint: [QA-02/03 real-process recovery cohort](../.github/workflows/qa02-recovery-cohort.yml). Owner is the existing independent data-integrity QA lane. See [bounded release campaign](QA-BOUNDED-RELEASE-CAMPAIGN.md), [player journeys](QA-PLAYER-JOURNEYS.md) (J-07/J-08), and the [CI workflow policy](CI-WORKFLOW-BEST-PRACTICES.md). This campaign reuses the already maintained `tests/native/qa02_fixture_hardkill_process.cpp` **without introducing a new emulator, writer, storage API, fixture semantics or persistent service**.

## Decision and baseline

The existing `test_qa02_fixture_hardkill_process.py` runs real C09/C14/C15/C16 and QA-03 fresh-process, process-death, interrupted 2P result/receipt flows once. Source C++ is coupled to the production store and coordinator; its assertions include actual durable outputs, precise OS process termination points and fresh restoration. The remaining repeatable risk is **timing-dependent and repeated player-data integrity**, not the one-frame Switcher/Zoom Zoo emulator result phase. The cheapest discriminator is independent repetition of the *same authoritative fault scenarios* with randomized bounded synchronization jitter, fresh filesystem roots and exact-build identity.

One manual dispatch compiles that original production-store fixture **once**, pins the executable SHA-256, then fans out **five separately isolated suites**, at most two runners in parallel. `10`, `100` or `500` trials **per suite** produce 50, 500 or 2,500 actual fault-and-recovery journeys; the upper choice is intended to run unattended for potentially hours, within 240-minute per-job bounds. Do not claim a specific runtime before an actual timed campaign. No cron, push, PR auto-trigger, force push, file writes to main or auto-cancel.

| Suite | Real production-store OS-process journey | Oracle |
| --- | --- | --- |
| `c09-orphan` | Hard-exit after immutable match sidecar claim but before paired run claim; reopen twice; retry valid pair | Orphan awards zero, legitimate later paired run saved, sidecars intact |
| `c14-c15-receipt` | Die after real run+match but before receipt; restore twice; die after immutable fixture receipt but before launch retirement; corrupt and restore receipt | First attempt uncredited, exactly one later award, existing records preserved, corrupt receipt rejected |
| `qa03-midseries` | Start real coordinator three-entrant round robin, cancel, credit first fixture, die after second run/match but before its receipt, resume all remaining fixtures and replace event | Six durable fixture credits, seven saved ordinary runs including one uncredited orphan, standings restored and previous history preserved |
| `hardkill-owner` | Kill a genuinely still-running OS process holding the fixture lease; reenter through new process | Kernel-released ownership, two legitimate distinct saved runs, one credited receipt |
| `c16-storage-outage` | One live owner loses receipt path after publishing real pair; other live process observes fail-closed outage; restore path and retry | One immutable pair, exactly one credited receipt, no phantom interim award |

Every trial has its own root and genuinely separate executable invocations. Only **millisecond synchronization jitter** varies, not game rules, recorded player results, qualifying checks or storage semantics. Native C++ sources are derived from and checked against the existing source manifests, rejecting fixture drift. A run with three failures within one suite stops that suite early, retaining only a bounded failure description in its receipt; private player-data roots are never uploaded.

## Dispatch and interpretation

From Actions, select **QA-02/03 real-process recovery cohort** on a reviewed commit and choose `iterations_per_scenario` and a bounded numeric `seed`. For the first actual invocation choose **10** and verify that all five scenarios complete and the aggregate is green before choosing 100 or 500. Each run is intentionally manual.

The aggregate checks the five named scenario receipts, exact source SHA, shared native executable digest, suite-specific seed, exact counts, integrity digests, expected error classifications and no unexpected cohort directories. Missing, truncated, invalid or failed runs **stay red**. Results upload as `qa02-recovery-<suite>/result.json`, plus `qa02-recovery-aggregate/result.json` and concise Actions summaries. A green run means `completed_positive` production-store process recovery evidence, not that a full game was played. No evidence is fabricated for unavailable machine states. Runtime faults preserve a reproducible suite + seed + trial index, with private roots left on the ephemeral runner only.

**Explicit exclusions:** no actual 1P/2P guest gameplay, full integrated Modern Windows ZIP, controllers, audio, GUI, physical SSD power loss or exact-hardware certification. Historical fixtures are generated synthetic match data run against the real production storage/coordinator code. No QA-01/45-course, QA-09 physical or release ledger admission. New release-level claims require the separately owned exact-build integrated player-journey and hardware proof.

**Stop rule:** one short smoke followed by one full chosen cohort provides a bounded stress population. If failures recur, isolate the first production-code invariant and hand its minimal case/seed to the product owner. Do not rerun thousands of trials merely to obtain green or silence a deterministic defect.
