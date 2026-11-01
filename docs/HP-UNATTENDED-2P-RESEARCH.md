# HP unattended research: source-bound seeded native 2P gameplay

**Purpose:** keep producing new, independently checkable real Windows game
evidence between source changes, without reserving a sixth LLM agent.
The five existing hourly generalist agents and their work queue are unchanged.

## Active first lane

[HP unattended seeded 2P gameplay research](../.github/workflows/owner-hp-seeded-2p-research.yml)
uses GitHub's UTC cron `17 * * * *` (hourly, 24 nominal opportunities a
day), plus optional owner manual dispatch. GitHub scheduled runs are
best-effort: they may start late or be dropped under load. Counting expected
cron slots is not equivalent to counting real source-qualified HP runs. This
is a deterministic bounded compute pipeline, not a guarantee that the PC
stays busy during every interval.
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
   research wall horizon, up to 12 unique plans and up to 90 seconds for
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

## Safeguards and source integration

- The main HP source-push workflow remains separate and automatic, including
  its independent concurrency scope; normal product and agent CI are not
  canceled by this scheduler. GitHub routes one job at a time to the
  owner's single self-hosted runner. A research run may queue behind a main
  build or briefly delay a newly arrived main build; its four-cohort
  horizon and overall timeout bound this effect. Do not add a second HP
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

1. **Eight-worker production proof pending:** [#2922](https://github.com/gamesbyian/UR-Recomp/pull/2922)
   integrated the eight-worker implementation after full tooling, real
   Windows QA and independent review. The latest verified genuine
   scheduled success, [run #41244390541](https://github.com/gamesbyian/UR-Recomp/actions/runs/41244390541),
   ran the preceding four-worker source, yielding eight distinct seeded
   plans and 32 actual guest processes in approximately 289 seconds of
   research time. It is **not** an eight-worker throughput receipt. Inspect
   the next successful real scheduled eight-worker signed receipt and
   preserve its exact source, run ID, worker count and research-only elapsed
   before comparing rates. Never infer an eight-worker speedup from
   code integration or the different-source four-worker baseline.
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
