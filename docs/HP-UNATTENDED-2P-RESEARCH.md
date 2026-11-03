# HP unattended research: source-bound seeded native 2P gameplay

**Purpose:** keep producing new, independently checkable real Windows game
evidence between source changes, without reserving a sixth LLM agent.
The five existing hourly generalist agents and their work queue are unchanged.

### November 3 forensic discovery: distinct inputs, timestamp-equivalent binaries

Four **read-only, ROM-free** exact-run HP evidence archives were downloaded
and compared against their actual GitHub artifact SHA-256 digests:

| Run / origin | Source SHA | Real Windows game executable SHA-256 prefix | New worker-first seeds | Cases / processes |
| --- | --- | --- | --- | --- |
| [#41544730154](https://github.com/gamesbyian/UR-Recomp/actions/runs/41544730154), dispatch | `041319d9a7e4` | `cd976fe15059` | 8 | 8 / 32 |
| [#41549934055](https://github.com/gamesbyian/UR-Recomp/actions/runs/41549934055), genuine cron | `041319d9a7e4` | `52009de770ec` | 8 | 8 / 32 |
| [#41565550358](https://github.com/gamesbyian/UR-Recomp/actions/runs/41565550358), dispatch | `2d7d0ea1f444` | `4a3864d7ca40` | 8 | 8 / 32 |
| [#41573163644](https://github.com/gamesbyian/UR-Recomp/actions/runs/41573163644), dispatch | `2d7d0ea1f444` | `97931d873f33` | 8 | 8 / 32 |

All four real Windows jobs passed normal packaging/boot/QA, the science receipt
self-hash, run/source/candidate binding, ZIP CRC, eight seed namespace checks,
and reported zero collector issues, with no original/native or release credit.
The **32 observed first-worker seeds are unique** (a source can repeat while
new input experiments continue). All four compiled executable files are
**5,446,656 bytes**. Their raw full-file SHA-256 values differ, but all four
share a single **COFF timestamp-neutral** SHA-256
`364c0103717c0f1597d7e4e1422a9c4dc81447889b8b3ef65586b31de46c1a2a`.
Byte-for-byte comparison of the two `2d7d0e` builds found **only two differing
bytes**, at PE offset `0x80`, inside the four-byte COFF timestamp. Thus
*different Git source epochs and different full binary hashes* need not imply
that the game executable's code or resources have changed.

The existing archive auditor now **adds** a strictly bounded optional
`pe_coff_timestamp_neutral_executable_sha256` and
`worker_first_seeds`, without altering mandatory full executable SHA-256,
source, run, seal and fixture verification. Only the four PE timestamp
bytes are neutralized; comparable hash equality does **not** prove semantic
equivalence of source changes, game fidelity, deterministic build identity
in general, or independence of all within-worker case inputs. This
is evidence for evaluating **future reuse of a previously qualified binary**
during unchanged executable epochs, after separately designing invalidation
criteria for game code, toolchain, canonical controller/audio/storage QA,
assets, native runtime dependencies and failure recovery. No cache/reuse
workflow has been enabled by this discovery.

Observed priority interaction: [research #41480568113](https://github.com/gamesbyian/UR-Recomp/actions/runs/41480568113)
was executing 16:21–16:30 UTC when
[main product HP push #41481409141](https://github.com/gamesbyian/UR-Recomp/actions/runs/41481409141)
arrived 16:26 UTC. Its first observed HP job output was at 16:30:42,
after the research completed, and product QA passed by 16:35:33.
This demonstrates a **real research-induced priority queue delay of several
minutes**, not a proven violation of the separately documented 10-minute
rollback condition. Do not conflate workflow creation and actual runner
pickup or claim zero build contention. The second priority build
[#41509060392](https://github.com/gamesbyian/UR-Recomp/actions/runs/41509060392)
also passed. Keep the local 60-minute pilot under observation.

### Physical HP confirmation: 60-minute pilot in operation

The owner confirmed the installed Python source's complete SHA-256 changed
from the previously verified 90-minute version
`5756e12471d2241300915abbb06eabaef087007eb54f58e2ee557aa96e91d64b`
to the reviewed 60-minute version
`316cfe232d476fed5af65d0e72543b16f506150c638b428edb31df7a89db629d`
after performing the bounded local one-line update without downloading
the quarantined ZIP. In Windows PowerShell, Task Scheduler reported
**LastRunTime November 2 14:50:50 MST, LastTaskResult 0, NextRunTime
15:05:05 MST** for the existing
`UR-Recomp HP Research Missed-Schedule Fallback` task.

The owner's actual `last-status.json` from **2026-11-02 21:50:47.884 UTC**
reported `decision=skip:recent-research`, `dispatched=false`,
`dry_run=false`, and latest research run
[#41522940636](https://github.com/gamesbyian/UR-Recomp/actions/runs/41522940636).
GitHub created that successful run at **20:50:57 UTC**, **59 minutes
50 seconds before** the task check. The 60-minute cutoff was therefore
working correctly, **not** an API timestamp anomaly. The next local
check window yielded successful
[dispatch #41534266867](https://github.com/gamesbyian/UR-Recomp/actions/runs/41534266867)
at 22:05:58 UTC, followed by successful dispatches
[#41544730154](https://github.com/gamesbyian/UR-Recomp/actions/runs/41544730154)
at 23:20:57,
[#41557456296](https://github.com/gamesbyian/UR-Recomp/actions/runs/41557456296)
at 01:05:59 November 3 (after a separate real cron run),
[#41565550358](https://github.com/gamesbyian/UR-Recomp/actions/runs/41565550358)
at 02:21:00 and
[#41573163644](https://github.com/gamesbyian/UR-Recomp/actions/runs/41573163644)
at 03:35:58. GitHub `workflow_dispatch` does not label its client:
this is strong timing evidence of local unattended operation plus a genuine
successful local Task Scheduler receipt, rather than definitive per-run
client attribution.

**Observed fallback-only dispatch intervals are about 75 minutes**, not
60, because a task checking every 15 minutes often tests just before the
60-minute boundary. The pilot's 192 cases/day ceiling assumes perfect
hourly eligibility and is **not** actual accepted throughput. Priority
Windows product [push #41481409141](https://github.com/gamesbyian/UR-Recomp/actions/runs/41481409141)
was created at 16:26:01 UTC while research
[#41480568113](https://github.com/gamesbyian/UR-Recomp/actions/runs/41480568113)
was occupying the HP. The product job reached its first recorded HP
output only at 16:30:42 after research completed, then passed at 16:35:33.
So the pilot has a real several-minute priority queue cost to monitor.
Do not describe priority queue delay as zero or relax full product QA.

No future Defender allowlisting or ZIP reinstallation is authorized by this
confirmation. Source hash identity and successful Task Scheduler status
are not malware-clearance verdicts.

**Read-only cross-run tool:** After [#3072](https://github.com/gamesbyian/UR-Recomp/pull/3072),
the existing independent archive auditor accepts a second pair of
`--compare-artifact path.zip --compare-run-json run.json`. It first
audits **both** exact GitHub-run-bound archives, then prints the two
receipts plus a `comparison` containing same-source, same-fixture,
full-binary SHA-256 equality, timestamp-neutral PE equality, verified
initial worker seed collisions/novelty, and an explicit
`safe_to_skip_build_or_product_qa: false`. No background API requests,
downloads, additional host workload, automated release promotion or binary
reuse happen. The result is intended to make a source-bound **reuse shadow
study** repeatable with controlled historical artifacts, while retaining
all current Windows product/QA gates.

### November 3: bounded HP two-variant native-process pilot

The first successful science run after the seven-step economy change (#3079) was scheduled #41591727338 on integrated source aa75ad2542eb. It completed 8 distinct seeds/32 real game executions in 211.937 seconds of research and 386 seconds of whole HP occupancy. The interval-averaged HP CPU load was about 71.3% during the real research window, with at least 6,159 MiB free physical memory. Those observations justify testing additional concurrency, not predicting a speed gain.

The HP-only canary runs at most two of each worker's four independent source-owned native guest variants together, for a maximum of 16 simultaneous game processes across the existing eight workers. Every variant has separate controller, process, config, user-data and dump directories; only exact immutable executable, original ROM and script inputs are shared read-only. Treatment, identical replay and independent P1/P2 ablation must still pass the same original guest-WRAM oracle, and all child processes are joined before result publication. Linux/other QA02 callers retain serial execution. A two-wave guest deadline replaces four-wave division only for this bounded HP canary; the unchanged 360/600-second wall budgets and failure-stop rules remain.

The HP summary's SHA-256 self-sealed source receipt declares variant_parallelism=2; its independent offline ROM-free evidence auditor validates 1 or 2, treating historical missing mode as serial. The first post-integration scheduled/manual trusted-main HP run must establish accepted cases per HP occupied minute, negative/timeout count, ROM/executable/fixture identity and priority Windows queue delay. If nondeterminism, timeouts, host instability, or worse useful yield appear, revert the HP setting to 1 without relaxing the oracle. Neither native determinism nor higher case count awards original/native event, real physical pad, or formal Windows release QA credit.

## Active first lane

[HP unattended seeded 2P gameplay research](../.github/workflows/owner-hp-seeded-2p-research.yml)
uses GitHub's UTC cron `11,41 * * * *` (twice hourly, 48 nominal
opportunities a day), plus optional owner manual dispatch. GitHub scheduled runs are
best-effort: they may start late or be dropped under load. Counting expected
cron slots is not equivalent to counting real source-qualified HP runs. This
is a deterministic bounded compute pipeline, not a guarantee that the PC
stays busy during every interval.
**Observed schedule delivery, November 1 UTC (source and Actions API):**
The former hourly `:17` schedule produced genuine successful **eight-worker**
Windows runs at [09:40 UTC #41294161998](https://github.com/gamesbyian/UR-Recomp/actions/runs/41294161998)
(source `d19b03a4635e0ba9a750f38d8d440a42e888aeb8`: **8 cases, 32
real Windows processes, 201.766 seconds** science) and
[16:23 UTC #41326050521](https://github.com/gamesbyian/UR-Recomp/actions/runs/41326050521)
(source `9460b811a8ad4b6419bf65399912fe2dcba6a743`: **8 cases,
32 processes, 201.031 seconds**). Both passed normal Windows package/QA,
verified Ninja, SDL3 cache and boot fanout. The `:41` schedule re-registration
then produced a successful [20:48 UTC #41348698814](https://github.com/gamesbyian/UR-Recomp/actions/runs/41348698814)
(source `2fb65e7469053bca6e4e7b788669f8b0620d30ae`: **8 cases, 32
processes, 218.953 seconds**, zero collector issues). These three real
`event=schedule` runs contain **24 run-distinct source-owned seeded cases
and 96 real Windows guest executions** across distinct source commits. The
last run's retained ROM-free artifact passed a separate complete 76-member
CRC, receipt self-hash, PE/binding and GitHub API digest audit; the earlier
two runs have passing source-owned job logs, but no independent byte-level
artifact audit recorded here. The older genuine four-worker scheduled run
remains distinct historical evidence.

**Twice-hourly pilot, integrated in [#3001](https://github.com/gamesbyian/UR-Recomp/pull/3001):**
the one existing schedule expression is `11,41 * * * *`, still using one
serialized trusted-main HP job, eight cohorts, canonical Windows package/QA
and a 360-second scheduled research horizon. **As of the November 1 22:24 UTC
repository-wide schedule census, no new HP research run had arrived after
20:48 UTC**, despite the first three nominal `:11/:41` slots since merge;
other repository cron workloads were observed at 22:13 UTC. This is a
delivery concern, not a science run failure or proof of a disabled workflow.
GitHub scheduling is best-effort: 48 theoretical opportunities/day neither
guarantee delivery nor earn 48 source-qualified experiments.

**Non-LLM recovery:** the existing [owner-installable Windows Task Scheduler
fallback](HP-RESEARCH-FALLBACK.md) checks for missed GitHub runs every
15 minutes and, after a 60-minute **pilot** gap with no priority HP Windows job and
no unresolved same-source failure, can dispatch the **same** tested main-only
workflow using the owner's authenticated GitHub CLI. The
[historical installer, retired pending Defender investigation](HP-RESEARCH-FALLBACK.md)
was owner-installed on the physical HP on November 1. The initially
installed version ran but failed closed on valid historical off-main
benchmark jobs; [merged #3012](https://github.com/gamesbyian/UR-Recomp/pull/3012)
repaired that narrow validation and rebuilt the exact-source installer ZIP.
The corrected installed Python script passed the owner's real GitHub
`--dry-run` and then an explicitly owner-executed `--once` reported
`dispatched: true` at **November 2 00:34:44 UTC**, pinned to main
`edd4c3b5f06be3b54bddb12374fe1c5d75a8e795`. Genuine Actions
[manual dispatch #41367902448](https://github.com/gamesbyian/UR-Recomp/actions/runs/41367902448)
began **nine seconds later** on that exact source and **PASSED** at
00:44 UTC: eight accepted seeded cases, 32 real Windows guest processes,
229.953 seconds research, canonical Windows package/boot/QA and zero
collector issues. The retained [artifact #13107779955](https://github.com/gamesbyian/UR-Recomp/actions/runs/41367902448/artifacts/13107779955)
passed independent 76-member ZIP CRC, exact outer GitHub digest,
receipt self-hash, source/seed, PE/binding-byte and ROM-free-content checks
(see [HP throughput issue #2885](https://github.com/gamesbyian/UR-Recomp/issues/2885)
for precise SHA-256 receipts). This proves **the installed script's deliberate
`--once` path**, not yet the automatically recurring Task Scheduler invocation
on the new version. A subsequent independent recurring task receipt or a
distinct later eligible automatic dispatch is still required. The script
retained its 90-minute cooldown at that historical run; the later **60-minute cooldown pilot** preserves physical HP priority-build checks and
360-second default. It never creates another HP runner or relaxes product QA.

**Monitoring after fallback qualification:** [merged #3014](https://github.com/gamesbyian/UR-Recomp/pull/3014)
adds a separate `dispatched_2p` read-only status alongside the
`unattended_2p` genuine cron status, using the **same** GitHub API census
without new polling. [Snapshot #41368607284](https://github.com/gamesbyian/UR-Recomp/actions/runs/41368607284)
actually reported the recovery run `IN_FLIGHT` while GitHub cron stayed
`SCHEDULE_OVERDUE`, both workflow registrations `active`. GitHub Actions
cannot determine whether an individual `workflow_dispatch` was sent by
an owner or the local Windows fallback merely from its event name.

**Additional November 2 dispatch evidence and 60-minute local-fallback pilot:**
After the owner-triggered #41367902448, a genuine
[GitHub scheduled #41368786920](https://github.com/gamesbyian/UR-Recomp/actions/runs/41368786920)
at 00:44 UTC passed on `590a99af78792c4c9641a551a5000a9a4417c935`
(**8 cases, 32 real processes, 228.125s research, about 570s full HP job**).
An additional distinct [workflow_dispatch #41377239423](https://github.com/gamesbyian/UR-Recomp/actions/runs/41377239423)
at 02:20 UTC passed on `aeee259ad25c5402d5a47cf98445e8471ef7dedb`
(**8 cases, 32 processes, 209.156s research, about 553s HP job**).
Both independently downloaded 76-member artifacts passed actual outer SHA-256
against GitHub, ZIP CRC/path, eight unique seed-namespace, self-hash,
PE/binding bytes and stock original-route fixture SHA checks, as documented
on [throughput issue #2885](https://github.com/gamesbyian/UR-Recomp/issues/2885).
The later dispatch arrived roughly 106 minutes after the owner's explicit
`--once` and is consistent with a working recurring 15-minute Windows task
after the former 90-minute cooldown. GitHub's `workflow_dispatch` event
cannot prove which client sent it; a later physical HP task-history/local
receipt would give conclusive recurrence attribution.

With observed science jobs occupying approximately nine to ten minutes each
and GitHub cron still irregular, this pilot lowers **only** the owner-installed
local fallback's missing-research cooldown from **90 to 60 minutes**. With
the unchanged 15-minute checks and eight positive cases/run, its
*theoretical* fallback-only ceiling rises from 128 to 192 seeded cases/day
under uninterrupted eligibility (+50%). Neither rate is an empirical
throughput claim: real cron events, build priority, source-bound failures,
Windows session logoff and offline periods all restrict dispatch.
The GitHub cron schedule remains `11,41 * * * *`; the workflow still uses
the same eight cohorts and 360-second research cap. The owner-comment
manual gateway keeps its independent 90-minute deduplication guard.
The downloadable ZIP has been withdrawn after Defender flagged it. The owner
can optionally perform the documented SHA-256-verified local one-line patch
instead, without re-registering the task. Until then the installed script
retains the working 90-minute setting.
**Rollback:** restore the last validated 90-minute installer if extra
fallback HP occupancy demonstrably queues a priority main Windows build
over 10 minutes, causes repeated research contention or lowers source-bound
accepted cases per occupied HP hour. Do not interpret normal GitHub schedule
delay as that evidence.

**Health/stop conditions:** [watchdog PR #3003](https://github.com/gamesbyian/UR-Recomp/pull/3003)
shortens the *read-only* missing-schedule alert from eight to **two hours**
(four nominal half-hourly opportunities), retaining the existing daily
snapshot and its one-shot trusted-main watcher-source trigger. It does
not dispatch jobs. Compare actual arrivals, distinct accepted cases/hour,
total HP job occupancy, CPU/memory receipts and source-to-HP product-build
queue delays before changing workers or research horizons. On a repeated
source-bound science failure or material delay to product builds, restore
hourly `:41` and retain all experiment evidence. No original/native
full-event, physical pad or release gate credit follows from the seeded
native-only research.

It reuses the **canonical trusted-main HP Windows x64 build/packaging/QA**
rather than creating another compiler toolchain, backend or private
release-candidate producer. The exact original game ROM is read locally
and never uploaded.

Each run:

1. Checks out exact main on the known `hpmini-ur-recomp` runner; requires
   the exact repository/ref and a schedule or deliberate manual dispatch.
   PRs, forks, arbitrary labels and other branches cannot reach this job.
2. Compiles actual game using owner receipt-verified Ninja when available,
   or explicitly selects the retained Visual Studio fallback. The existing
   package integrity, main-menu, real Win32 renderer, QA-09 pad/menu,
   5/5 QA-05 audio/Restart, same-run race-result, user-state, and startup
   checks must pass *before* the scientific workload can run.
3. Runs **eight independent source-owned QA02 native 2P cohorts** with unique
   private root, controller input, rendered script, per-variant game process,
   user state and 128-KiB WRAM checkpoints. Every seeded case includes an
   actual treatment, identical replay, muted P1 and muted P2, using the
   same `tools/qa02_native_2p_seeded_endurance.py` four-way invariants
   already used for Linux native research. On Windows the source-owned
   guest is invoked directly with SDL offscreen/dummy instead of Linux
   `xvfb-run`. No comparison oracle is rewritten.
4. Uses an exact per-run seed namespace derived from GitHub's numeric run
   identity, with disjoint paired shard offsets. No manual prompt, guessed
   LLM scenario or repeated fixed control stream is needed. Per cohort:
   nominal 15-minute admissible budget, shortened by a strict 360-second
   research wall horizon for every genuine scheduled run or default manual
   dispatch. An explicitly owner-selected 600-second manual experiment may
   widen that horizon without changing `schedule`. Every cohort still has
   up to 12 unique plans and up to 90 seconds for
   each real Windows guest process. Eight cohorts execute concurrently and
   the coordinator **joins all** even if one fails. The canonical job's
   existing 45-minute deadline remains authoritative.
5. Validates all eight upstream source-owned signed receipts, same actual
   game executable/ROM/controller fixture/source identity, distinct
   control stream digests, replay determinism and both seat-response
   checks. Any missing or invalid cohort fails the research step; a
   failed real guest is *not* converted to a green campaign.
6. Emits an exact, hashed, ROM-free `hp-seeded-2p-research-receipt.json`
   inside the existing seven-day evidence artifact and a readable Actions
   job summary. The signed receipt remains authoritative; the summary
   reports bounded typed failure categories or, on a positive campaign,
   research-only cases/processes per minute and per-worker case counts.
   Neither raw ROM, guest log, gameplay dump, source build, user data nor
   proprietary game asset enters this receipt or summary. The existing
   strict upload allowlist includes this one JSON pathname only.

The scheduled runs do **not** claim physical pad testing, historical
emulator/original parity, full-course completion, or any of the 12 release
gates or 45 authentic USA original/native events. The four-way test is
native guest-input determinism and independent-seat reachability research.
Treat a failure as an exact reproducible seed and first failure to debug,
not a verified regression in authentic SNES behavior by itself.

## Manual-only 600-second throughput pilot: actual Windows result

The trusted-main [HP two-player research workflow](../.github/workflows/owner-hp-seeded-2p-research.yml)
offers `research_wall_seconds` of **360** (default) or **600** through deliberate
`workflow_dispatch`. The exact owner-only PR comment
`/ur-ci hp-research 600` also selects the 600-second manual trial using
the established global owner gateway and 90-minute deduplication guard;
`/ur-ci hp-research` without the argument uses 360. A genuine GitHub
`schedule` event and the [owner-installed local missed-cron fallback](HP-RESEARCH-FALLBACK.md)
always use **360**. The source-owned research validator rejects a scheduled
600-second horizon. During the historic November 1 trial both routes
performed the complete Windows product checks. Since merged #3079, the
science-only route retains source-built Windows executable, verified ROM
and portable ZIP, clean package boot and three independent HP boot tests,
but skips seven repeated product-specific Win32/audio/storage acceptance
steps. The normal product Windows workflows still execute every check,
and the existing 45-minute HP job cap remains unchanged.

**First real 600-second positive result, November 1 UTC:** [owner-authorized
Windows run #41286835360](https://github.com/gamesbyian/UR-Recomp/actions/runs/41286835360)
is an actual `event=workflow_dispatch` at
`6c23045ee244ded3c5d51365b6448bbe54a15392`, not a scheduled
delivery. Its Windows job and all required package/QA checks passed.
Eight independent workers each accepted **two distinct four-process
treatment/replay/P1-muted/P2-muted cases**: **16 accepted seeds, 64 actual
Windows game processes, 0 research issues, 452.282 seconds** of research.
The 600-second budget is included in the source-owned SHA-256 receipt
*self-hash*, not independently signed by a trusted key. The retained
[76-member ZIP artifact #13076395136](https://github.com/gamesbyian/UR-Recomp/actions/runs/41286835360/artifacts/13076395136)
was inspected for member CRCs, unique names, matched Actions run/source
identity and independently checked ROM-free executable/binding SHA-256;
no ROM or player-data upload and no physical/original-parity acceptance.

**Measured capacity:** research-phase accepted cases/minute were **2.123**
for the 600-second trial, versus **2.149** for [the earlier 360-second
manual run #41272207332](https://github.com/gamesbyian/UR-Recomp/actions/runs/41272207332)
which accepted 8 cases/32 real processes in 223.390 research seconds.
The actual raw Windows job log spans were approximately **784 seconds
(16 cases, 73.5 cases per whole HP job-hour)** versus **578 seconds
(8 cases, 49.8 per whole HP job-hour)**: **+47% observed overall
yield**, largely by amortizing the same ~5–6-minute build/QA overhead.
These are **different source SHAs, distinct seed populations and run
epochs**. This is an operational observation, **not** a controlled
same-source speedup or proof that a third case per worker is admissible.
The first 600-second run's GitHub API job `completed_at` showed a
one-hour discrepancy relative to its last actual UTC job step and raw
log across the local DST fallback. Use the verified raw log/step times,
not the inconsistent run-level end, for this bounded comparison;
[CI timing correction PR #2979](https://github.com/gamesbyian/UR-Recomp/pull/2979)
tracks the measurement issue separately.

**Decision:** retain **360** for cron/default/local fallback. Any
promotion to a longer unattended horizon requires repeated source-bound
science with acceptable priority Windows-build queue latency, accurate
CPU/memory and whole-job accounting, a same-source comparison where
practical, and genuine reliable automatic dispatch. Do not change the
five hourly LLM agents or create a second HP job. No 1/45 original/native
USA event, physical pad verification or formal release gate follows
from seeded *native-only* research.

## Read-only offline archive audit

`python -m tools.hp_science_archive_audit --artifact windows-native-smoke.zip --run-json hp-run.json` independently checks the retained GitHub Actions ZIP CRCs, safe member paths, source/run/event identity in the separately retrieved **GitHub Actions run API JSON**, the collector's self-hash and eight/four-cohort seed/case totals, the ROM-free PE's **actual bytes** against both the source-owned science candidate and the independent Windows PE binding, and the stock input/script file digests from this checkout. Nothing is executed or uploaded, and source/fixture differences fail closed. Fetch the run's actual `/repos/gamesbyian/UR-Recomp/actions/runs/RUN_ID` API JSON independently; the ZIP by itself **cannot prove** that GitHub delivered a scheduled event.

The SHA-256 research receipt is **self-hashed, not cryptographically signed by an independent trusted key**. Even a valid archive audit cannot reconstruct the 4-way guest traces absent from the retained compact summary or grant 1/45 genuine original/native events, physical gamepad checks or release gates. The audit's positive result must be paired with the trusted Actions run and its successful producer job. Compare historical run rates only with labeled source/epoch, total wall time and accepted cases; never describe the four-to-eight worker shift as an eight-to-sixteen-case gain.

## Safeguards and source integration

- The main HP source-push workflow remains separate and automatic, including
  its independent concurrency scope; normal product and agent CI are not
  canceled by this scheduler. GitHub routes one job at a time to the
  owner's single self-hosted runner. A research run may queue behind a main
  build or briefly delay a newly arrived main build; its eight-cohort
  research horizon and overall timeout bound this effect. Do not add a second HP
  runner or let scheduled execution check out PR source.
- Work roots are unique per run ID/attempt. Research never mutates the
  installed Ninja, SDL3 cache, repo history, machine settings, service
  credentials or player files. It refuses stale scratch output.
- The scientific post-QA phase is opt-in only through `hp_seeded_2p=true`;
  the regular HP/hosted/main/PR routes remain unchanged.
- The normal `tools/ci/check_windows_smoke_upload_policy.py` continues
  to require exactly one artifact upload and an exact literal allowlist.
  Research failures remain visible. This is not a production QA waiver.

## Decisions and next research lanes

1. **Eight-worker manual and three genuine Nov 1 scheduled successes acquired; twice-hourly cadence remains a delivery pilot:** the owner-authorized [manual HP run #41264488130](https://github.com/gamesbyian/UR-Recomp/actions/runs/41264488130) at source `d6eb79fc` completed all Windows package/QA checks and **eight real concurrent source-owned cohorts**, accepting **8 distinct cases, 32 Windows guest processes in 200.718 s** with zero collector issues. The retained [four-worker genuine scheduled run #41244390541](https://github.com/gamesbyian/UR-Recomp/actions/runs/41244390541) at different source `fde3b6c3` accepted **8 cases, 32 processes in 289.282 s**; it is **not** an eight-worker throughput receipt. Research-only observed rates were **2.391 vs 1.659 accepted cases/min**, a 44.1% increase, but unlike-source cohorts and changed parallel load preclude a controlled speedup claim. The manual eight-worker canary does **not** prove true GitHub `schedule` delivery. The actual eight-worker `event=schedule` job #41348698814 establishes schedule delivery and positive source-owned eight-worker execution; the artifact still requires independent byte-level review. Twice-hourly frequency must earn its own measured yield and priority-queue observations. Neither trial earns gameplay/physical-pad/release credit.
2. **Value measurement:** quantify distinct valid seeded cases/day, actual
   native Windows process count, host CPU/memory/time, whether source/fixture
   identity was maintained, failure reproducibility and delay to normal
   HP builds. More CPU usage without distinct accepted cases is not a win.
3. **Other deterministic candidates:** reusable read-only native title/2P
   journey permutations, Win32 C++ codec/storage fault-injection at safe
   private scratch roots, source-bound screenshot atlas verification and
   original/native first-causal-divergence experiments. Do not copy Linux
   pipelines with `/proc`/xvfb/glibc dependencies into Windows unchanged.
   Move each only after a minimal physical HP acceptance and shared artifact
   contract. The existing seven-family cumulative-research coordinator
   remains manual-only due its earlier scheduler/admission failures;
   silently switching its costly Linux job matrix to HP is not appropriate.
4. **When to stop or reschedule:** halt an unproductive/failing research
   population, an actual credential/ROM provenance mismatch, evidence
   leakage, source-binding error or repeated priority-build delay.
   Revert only the scheduled caller or set its cron less frequent. Maintain
   the five agents and existing authoritative release pipeline.

The [HP throughput tracking issue](https://github.com/gamesbyian/UR-Recomp/issues/2885)
owns measured rollout figures, while `docs/WORK-QUEUE.md` owns shipping
priority. This page is an execution contract, not a rival work queue.
