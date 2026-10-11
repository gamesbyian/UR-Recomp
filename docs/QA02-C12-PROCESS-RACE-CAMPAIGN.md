# QA-02 C12 manual OS-process ownership campaign

Status: **bounded manual research and native-store QA**, never packaged Windows or independent release evidence. Authority: [cross-artifact fault campaign](QA02-CROSS-ARTIFACT-FAULT-CAMPAIGN.md), [native C12 fixture](../tests/native/qa02_coordinator_create_race_process.cpp), [existing process test](../tests/unit/test_qa02_coordinator_create_race_process.py), and [CI rules](CI-WORKFLOW-BEST-PRACTICES.md). The release ledger retains QA-02's actual acceptance status.

## Question

Can two game-store processes, each creating a valid but different tournament instance, ever both claim the same active event under repeated contention? Source baseline: the production coordinator fixture currently demonstrates exactly one successful creator and one loser in five isolated races. This campaign reuses **that identical fixture and its exact source-file compilation manifest**, then varies process launch order and barrier-release timing across a seeded cohort. There is no shadow state machine, altered production store, or second QA authority.

A trial creates a fresh disposable root, synchronizes the two actual OS processes, releases them simultaneously, and demands exactly one `Created`/0 and one `AlreadyExists`/6. Two further **independent OS-process restores** assert an authentic active archive matching the winning instance, zero fabricated fixture credit, no phantom pending launch, well-formed preserved event archives and unchanged active record bytes. Invariant failure retains the trial's filesystem and marks the shard negative. A fifth failure stops the shard early to avoid wasting compute on a reproducible systemic defect.

## Launch and bounded compute

In GitHub Actions open **QA-02 C12 bounded process-race campaign**, manually select an integrated ref, and choose 10, 100 or 500 races *per shard*. Four independently seeded shards produce 40, 400 or 2,000 fresh two-process contests in total. Default is 400. Maximum runner fan-out is two shards concurrently; each shard has a 120-minute deadline. One Ubuntu 22.04 build compiles the same native production coordinator fixture once and publishes a SHA-256-bound executable for all shards. Tests/CI run no automatic PR, push or schedule research workload.

Every successful private trial root is discarded; unsuccessful roots are retained temporarily in the failing shard and uploaded only on failed jobs. The per-shard JSON reports attempts, failures, requested count, source SHA, shared executable SHA and deterministic seed. The final `aggregate` job validates exactly four populated shards and their complete counts. The 14-day aggregate JSON and Actions Job Summary distinguish **completed_positive**, **observed_failure**, **incomplete** and **evidence_invalid** without converting an absent run or timeout into success.

Run the cheapest contract tests first:

```bash
python3 -m unittest discover -s tests/unit -p test_qa02_c12_campaign.py
python3 -m unittest discover -s tests/unit -p test_qa02_coordinator_create_race_process.py
```

The second test is the established five-contest production fixture (and compiles independently when run locally); the campaign CI compiles its same C++ source set once for the entire selected population.

## Evidence and stop rule

This campaign is a targeted **C12 native store-coordinator stress test**. It does not kill processes, simulate a power cut, exercise a real guest-raced 2P tournament, verify a Windows portable ZIP, prove source-original gameplay or satisfy hardware acceptance. Other fault cuts C04, C09, C14, C15 and C16/17 retain their own independent authority and existing harnesses.

If repeated 400-contest batches yield no new defect or actionable conditional timing hypothesis, stop launching larger cohorts. Promote one minimal reproducible failure and its exact seed/source/digest to the owning QA-02 implementation lane; do not keep increasing iteration count as a substitute for finding real product failure. Retire or manualize this harness if production changes make C12 no longer a decision-bearing risk. Do not automatically update `RELEASE-QUALITY-LEDGER.json`.
