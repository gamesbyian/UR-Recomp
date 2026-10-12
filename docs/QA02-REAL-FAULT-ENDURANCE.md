# QA-02 real OS-process fault endurance campaign

**Scope:** independent reliability research through the existing production-store native fixture. Not a guest-played complete event, original/native differential parity, physical power loss, or release certification. [Manual workflow](../.github/workflows/qa02-real-fault-endurance.yml). Original authority: [production recovery cohort](../.github/workflows/qa02-recovery-cohort.yml), `tools/qa02_recovery_campaign.py`, and its `tests/native/qa02_fixture_hardkill_process.cpp` plus owner-written `test_qa02_fixture_hardkill_process.py`.

## Why another long-running campaign?

The existing storage supercampaign passes thousands of process trials in minutes; a one-shot fixed-size batch doesn't sample much of the long-tail of OS scheduling. This *time-budgeted* campaign repeatedly exercises the original source-derived recovery oracles with distinct deterministic micro-scheduling jitter and fresh user-data roots. Unlike the seeded Linux 2P guest campaign, this investigates **persistent-record consistency and failure/recovery interleavings**, not gameplay motion. Unlike the Windows Baldosa bridge soak, it stresses the real C09/C14/C15/C16/QA03 storage fixture directly, not Windows launcher/profile UI.

Every manual dispatch compiles **one** production-store native fixture from the already established source manifest under Ubuntu 22.04, SHA-256 binds the artifact and fans it out to five independent fault-suite shards. There is no second storage implementation and no simulated database/service. All process invocations in the producer remain real OS subprocesses with their original exact exit codes, synchronization barriers, actual SIGKILL, immutable run/receipt checks and fresh-process restore assertions.

## Five separate failure hypotheses

| Shard | Original source-owned behavior |
| --- | --- |
| `c09-orphan` | Death between run/sidecar publication, orphan rejection, subsequent valid publication |
| `c14-c15-receipt` | Death between record pair, credit/pending recovery and corrupt receipt refusal |
| `qa03-midseries` | Tournament interruption, six distinct credits, preserved standings and history |
| `hardkill-owner` | Actual OS kill at synchronized ownership barrier, lock release and successful retry |
| `c16-storage-outage` | Real concurrent process and receipt-storage outage, refusal while offline and single credit after restoration |

Each seed selects a deterministic sequence of *0–8 ms interprocess boundary delays* in the original fixture. Each 10-trial chunk receives a new derived seed and **10 newly created private data roots**. Successful private roots are destroyed; failed roots remain only within the ephemeral runner, not in Actions artifacts. Time jitter diversity is evidenced through the same 9-bucket histogram as the source oracle, not invented new scenarios. This is not 10 different courses; the source fault scenarios remain fixed.

## Dispatch and runtime

Select `wall_minutes_per_shard` **15, 60 or 120**, plus a reproducible `base_seed` of at most eight digits. The default **15** verifies the whole orchestration before longer use. Three Linux shards run at once; five suites therefore run in **two waves**, meaning a 60-minute budget can occupy approximately two hours wall-clock and a 120-minute budget approximately four hours, plus native build/setup and queue delay. Exactly **one** native production fixture is built. A 145-minute per-shard runner cap is enforced; the action does not idle to fill the budget. Each shard runs until its wall deadline, its bounded 20,000-chunk ceiling, or the *first* original-production failure. Actual time, number of 10-process-fault-journey batches and precise termination reason are recorded.

The suite checks its wall deadline before each new 10-trial batch. Intermediate source-linked JSON is saved every 25 batches so OS timeout or runner loss leaves **explicitly incomplete evidence**, never a green aggregate. The downstream aggregator requires all five named receipts, one exact source/binary SHA, complete original source-signature-bound producer receipts, strictly monotonically seeded chunks, correct 10-journey counts, authentic timing histogram, and no borrowed hardware, complete-event or release credit. Unexpected artifacts, partial source failure, corrupted receipts and missing suites are red. Only compact JSON is retained for 14 days, never ROM, private user saves or WRAM. This is not a hardware power-cut witness.

## Evidence, maintenance, and escalation

After a 15-minute run, inspect actual unique timing schedules, 9-bin jitter distribution, fault-journey throughput and runtime. On genuine positive source receipts, advance to 60 or 120. An early stop after reaching 20,000 chunks must be reported as **case cap**, not a claimed two-hour duration. Any source invariant failure must reproduce its exact suite, shard source commit, binary SHA, seed and batch/trial index; do not modify or weaken original `qa02_recovery_campaign.py` acceptance to make a long test green.

**No release acceptance upgrade:** no live game controller journey, no power-disconnected physical device, no complete original-native Race/Circuit/Stunt, and no independent Windows certification. The work is restricted to CI orchestration around the existing production-store fixture. Future Windows-specific native storage fault investigation should remain with the owning product/independent QA lanes.
