# Critical audit of plan and methodology (2026-10-15)

**Classification:** dated, adversarial owner-facing review. It is not a work queue and changes no gate status. [WORK-QUEUE.md](WORK-QUEUE.md) still owns assignments and [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) still owns gate status. Snapshot: `main` at `46080a6` (2026-10-14 22:14 MDT), plus merged #1608 and live GitHub PR/search data on 2026-10-15. All numbers below were measured for this review; re-measure them before quoting them later.

Earlier audits ([QA-AUDIT-OF-AUDIT-20261008](QA-AUDIT-OF-AUDIT-20261008.md), [CI-RESEARCH-APPARATUS-AUDIT-20261010](CI-RESEARCH-APPARATUS-AUDIT-20261010.md), [CI-ACCELERATION-EXECUTION-20261014](CI-ACCELERATION-EXECUTION-20261014.md)) already warned about a "self-amplifying test infrastructure programme". The pattern they described has **continued**. This report therefore concentrates on *mechanisms* that would actually change behaviour, rather than more advisory rules.

## 1. Executive summary

The project is producing an extraordinary volume of careful work. It is not converting that work into a playable, accepted product at a comparable rate.

| Measure (17 days, 2026-09-28 → 2026-10-14) | Value |
|---|---:|
| Merged PRs | **1,419** (808 in the last 7 days, ≈115/day) |
| Closed-unmerged PRs | 186 |
| Commits on `main` history | 7,531 |
| Release-ledger gates with **any** accepted witness | **0 / 12** (`witnesses: []` on every gate) |
| Ledger `candidate.commit_sha` / `zip_sha256` | `null` / `null` |
| USA courses admitted as complete original/native events | **0 / 45** |
| GitHub releases or tags (playable builds a human can download) | **0** |
| Native Modern destinations still unavailable | Practice, Options |

Lines **added** on `main` since 2026-10-08, by area:

| Area | Lines added | Share |
|---|---:|---:|
| `reference/` | 73,285 | 25% |
| `tools/` (Python) | 67,783 | 23% |
| `analysis/` | 62,855 | 21% |
| `tests/` | 59,267 | 20% |
| `docs/` | 27,927 | 9% |
| `.github/` | 10,963 | 4% |
| **`native/` (the shipping product)** | **10,478** | **≈3.5%** |

The repository holds 117k lines of Python tooling and 76k lines of Python tests, against 45k lines of first-party native C++. Of 915 PRs merged since 10-08, about 360 are titled `QA-*`/`qa*`, 146 `docs:`, 57 `CI:` and about 117 product/Windows/Integration. Roughly 240 titles describe preserving, classifying, receipting or independently re-validating evidence.

**Core diagnosis.** There are four problems, in order of cost:

1. **The gameplay acceptance oracle is mis-specified**, so the most important gate (QA-01) cannot pass even when the games agree (§2).
2. **The unit of work is "a PR carrying an evidence receipt"**, not "a defect fixed" or "a feature shipped". Throughput is measured in artifacts, and verification of verification has become a work stream of its own (§3).
3. **No human has a playable build.** Every L5 gate (physical controller, audio, 4K, soak) is starved. Meanwhile, agents produce L4 receipts about scripted SDL routes in ever finer detail (§4).
4. **Coordination overhead is growing faster than the product.** This covers mandatory context, documents, workflows and status copies (§5–§6).

The fastest path forward is mostly *subtraction*, plus three standard practices this project does not use yet: lockstep differential testing, a nightly playtest build, and upstreaming fixes.

---

## 2. The QA-01 oracle: the highest-leverage fix

### 2.1 What is happening

QA-01 admits a course only on *strict guest-relative host-frame parity* between Baldosa native and **one** reference emulator (Snes9x 2014 builds, sometimes Beetle-bsnes). Representative outcomes from [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md):

- **Zoom Zoo:** all 14 semantic fields agree at all active samples. The displayed results are byte-identical (MIKE 1:16.46, BRONSEN 1:20.07). The only difference is that result onset is **one frame** off (+5162 vs +5163). Verdict: not admitted.
- **Switcher:** identical MIKE 1:08.81 and identical result text at the same absolute host frame 5783. Guest-relative onset is +4704 vs +4702. Verdict: not admitted. At least five merged PRs (#1235 and the 10-10 entries above it) then traced the writer of stack byte `7E:01DD`. That is a dead stack slot below the live SP, the very case AGENTS.md rule 19 says is *not* a simulation mismatch.
- **#1608** (merged 2026-10-15) shows that **Snes9x and bsnes disagree with each other** in the same 5196/5197/5198 pattern that earlier work (#1537) had read as a native defect. It also found a real Baldosa timing bug: DRAM refresh charged per 1404 clocks instead of per 1364-clock line. With the one-line fix, Zoom Zoo becomes `strict_candidate`.

### 2.2 Why this is a methodology defect, not just slow progress

- **A single emulator is not ground truth for ±1-frame timing.** Snes9x is not cycle-accurate. When two reference emulators differ by one frame, a gate that requires exact equality with one of them can fail for reasons that are not native defects. Mature projects instead treat the highest-accuracy core (bsnes/higan, ares, Mesen2) as the timing reference. They treat agreement *within the envelope spanned by accurate cores* as the pass criterion, and use real-hardware test ROMs to break ties.
- **Host-frame alignment is the wrong clock for a static recompilation.** RF-012/013/014 show that the native/original lag is phase-dependent (2 or 3 frames) because waits and lag frames are quantised differently. Projects such as snesrev's `zelda3`/`sm`/`smw` compare RAM after each **game-logic frame** (NMI or main-loop iteration), with a liveness mask that excludes stack, scratch and free-running counters. They do not compare by wall-clock host frame. The census already counts vblank-wait passes (`$C6`, RF-014), so the right tick already exists.
- **The result is an unfalsifiable treadmill.** Each new receipt narrows a one-frame timing question and leaves 0/45 unchanged. This is exactly the "more evidence is not a deliverable" failure that rules 28–32 prohibit. The rules exist, but nothing enforces them.

### 2.3 Recommendations (owner decision required for R1)

- **R1 — Write down the equivalence relation and get owner sign-off.** One page, one decision. A suggested shape:
  - **Gameplay-authoritative state must match exactly at every game-logic tick.** This covers positions, velocities, rotation, contact, laps, timers, scores, RNG, progression and SRAM. Compare it under a declared liveness mask that excludes stack below SP, DMA scratch and cursor/animation counters.
  - **Presentation and transition timing must fall within the envelope of {bsnes/ares/Mesen2, Snes9x}.** Any difference outside that envelope must be root-caused, like #1608. A difference inside it is recorded, not blocking.
  - **Input-latency-affecting differences during interactive play must be exact.** Differences in non-interactive transitions such as result fades are tolerated within the envelope.
  - **The released product must be byte-exact on persisted SRAM and results.**

  Without this decision, QA-01 has no stopping condition.
- **R2 — Build one lockstep first-divergence harness and route all event work through it.** Run the reference interpreter (snesref or an accurate libretro core) and the Baldosa guest in one process. Feed them identical input per logic tick and diff masked WRAM after each tick. Print the first diverging tick, address and writer. This is standard practice in SNES/N64 recomp and decomp work (snesrev's verify mode; decomp "diff" tooling). It turns each course into a single command instead of a bespoke multi-PR investigation.
- **R3 — Run all 45 courses as a batch as soon as R1 and #1608 have landed.** The "do not automate 45 courses before one passes" rule in WORK-QUEUE is backwards for systemic causes. A single timing-model bug (DRAM refresh, RF-016 SPC700 clock at 0.164% fast) affects every course, and a 45-course run would have exposed it in one pass. The frontier cross-check already compared 10,400 random 2P trajectories with **0** mid-race divergences. That is strong evidence that the simulation is right and the remaining work is timing, not gameplay.
- **R4 — Fix the clocks upstream, not only in local patches.** The DRAM refresh error and the SPC700 rate exist in `baldosa/snesrecomp` and in the legacy `cd5875c` core. Open upstream issues or PRs, as normal open-source dependency hygiene. This shrinks the local patch stack and lets the Baldosa author review the fix.
- **R5 — Retire the legacy core on a date.** #1608 notes that the portable smoke ZIP and the shared Modern acceptance build still use legacy `cd5875c`, while Baldosa is the "leading" backend. Two execution cores means two timing behaviours, two evidence populations and duplicated QA. Pick a cut-over date, move every acceptance build to Baldosa and keep legacy only as a tagged rollback artifact.

---

## 3. The unit of work: receipts, re-validation and PR-per-thought

### 3.1 Observations

- About 115 merged PRs per day, many of them evidence-only. Titles of the form "preserve … negative receipt", "independently classify …", "independently qualify exact Windows six-artifact PR-head cohort" and "independently validate exact Windows journey executable binding receipt" describe **verification of verification**. One agent produces a receipt, and a second agent produces a PR that re-validates it. Neither changes the product.
- Every negative result is written up as a doc, a SHA-bound JSON, a validator and a test. `analysis/data` has 128 files and `analysis/` holds 441.
- Ledger `next_action` fields are multi-hundred-character narratives full of run IDs and SHA-256 prefixes. They are append-only log entries stored in a status field.
- WORK-QUEUE.md says "Reconciled 2026-10-11", but about 800 PRs merged after that. The live board is stale under its own rules, because no single reconciliation can keep pace with 115 PRs per day.

### 3.2 Why it is slow

Each artifact carries fixed costs: CI fan-out, merge-conflict exposure on shared docs and ledger, review, and the context it adds for the next agent. Fine-grained evidence PRs also bury the few decision-changing results, such as #1608, among hundreds of receipts.

### 3.3 Recommendations

- **R6 — PRs carry code or decisions; experiments go in a lab notebook.** Keep one append-only notebook per lane, for example a GitHub issue per lane or an `analysis/notebooks/<lane>.jsonl`, for bounded experiments and negatives. Promote an entry to a PR only when it changes code, a test, an accepted fact (Research Ledger) or a gate. Target: fewer than 20 merged PRs per day, each meaningful.
- **R7 — Move independent QA to release-candidate cadence, not per-PR cadence.** QA re-validates a **nominated candidate**, for example weekly. It does not re-qualify each feature PR's artifacts. Whatever a QA agent checks repeatedly should become an assertion in the product's own CI job, executed once.
- **R8 — Turn ledger `next_action` back into a short field (≤ 200 characters).** Move narrative into the lab notebook. Generate any human-readable status page from the ledger JSON instead of maintaining prose copies.
- **R9 — Use outcome metrics, not activity metrics.** Report weekly on four numbers: (a) Modern destinations working natively (3/5 today), (b) courses passing under R1 (0/45), (c) gates with a witness on a nominated candidate (0/12), and (d) open P0 player-visible defects. If PR count rises while (a)–(d) stand still, that is an alarm, not progress.

---

## 4. No human playable build: the missing feedback loop

- There are no releases or tags, and the ledger candidate is `null`. QA-04 (physical Windows), QA-06 (audio), QA-09 (UX), QA-10 (soak) and physical 4K are all L5 and all `unverified`.
- The only human product review on record, the 2026-10-10 recruitment-footage art veto, immediately overturned a long-standing "approved" status. Human contact with the product produces high-value information quickly, and the project gets very little of it.
- Scripted SDL routes are being certified in more and more detail ("semantic pad scripts are not physical devices") while no physical pad has been used for acceptance.

**Recommendations**

- **R10 — Publish a nightly or per-merge ROM-free playtest ZIP as a GitHub (pre-)release.** The ROM-free deterministic ZIP path already exists (#1609/#1611). This is standard practice for source ports and recomp projects (nightly builds of Ship of Harkinian, Zelda64Recomp and similar). The nominated candidate for the ledger then simply becomes "the release tagged X".
- **R11 — Hold a weekly 60-minute owner playtest with a structured form.** Cover controller, audio, every Modern destination, one 2P race, quit/relaunch, 16:9 and 4K display. Each session yields L5 evidence for several gates at once. It is far cheaper than any CI campaign, and it surfaces "this feels wrong" defects that receipts cannot detect.
- **R12 — Make "player-visible" the next product milestone.** Bind Practice and Options to the existing Modern models before any further evidence hardening of Play/Records. A 5/5-destination playable build is worth more than another independent re-qualification of the 3/5 already working.

---

## 5. Context, documentation and status sprawl

| Measure | Value |
|---|---:|
| `AGENTS.md`, described as a "compact router" | **27.7 KB, 47 numbered rules** plus several unnumbered rule blocks |
| Markdown files under `docs/` | 325 (132 top-level date-stamped; 144 `QA*`) |
| Files restating "0/45" | **78** (180 occurrences), against rule 4 ("a mutable fact should have one owner") |
| `docs/RESEARCH-LEDGER.md` | 286 KB |
| `prod_diary/` conversation transcripts | 94 files |
| Tests that assert document or workflow text | ≥ 37 unit-test files; `test_ci_trigger_policy.py` alone is 793 lines |

Every new agent pays this context cost before doing useful work. Every rule added after an incident adds a permanent reading tax. The existing rules already say all this (rules 4, 14 and 39), so the gap is enforcement, not policy.

**Recommendations**

- **R13 — Enforce hard size budgets in `check_repo_hygiene.py`.** For example: AGENTS.md ≤ 8 KB, WORK-QUEUE.md ≤ 6 KB, the top-of-file status block of any authority ≤ 1 KB. Make the check fail, not advise.
- **R14 — Give mutable status a single owner, mechanically.** Fail hygiene when status tokens such as `/45` counts or gate states appear outside the ledger and a generated status page. Docs link to the ledger instead of restating it.
- **R15 — Consolidate AGENTS.md.** Collapse rules 11–12, 20–24, 41–46 and the CI paragraphs into a pointer to `CI-WORKFLOW-BEST-PRACTICES.md`. Collapse rules 28–37 (evidence economics) into one paragraph and a pointer. Most of the 47 rules are lessons from specific incidents. They belong in owning docs, not in mandatory context.
- **R16 — Stop asserting prose in tests.** Tests that grep docs or workflow YAML for phrases make documentation edits fail CI and encourage text that is written to satisfy tests. Keep schema and validator tests for machine-readable files. Remove phrase assertions on Markdown.
- **R17 — Archive by moving.** Move date-stamped docs older than 72 hours that are not linked from WORK-QUEUE or PROJECT-PLAN into `docs/archive/` with a generated index. Git history already preserves them.

---

## 6. CI and research apparatus

- There are **148 workflow files**: 106 dispatch-only, about 31 PR-triggered, 1 scheduled.
- Closed or deferred experiments are still present as separate workflows:
  - six `widescreen-vs-plus{16,24,32,40,48}-capacity`/`vs-capacity` siblings, against rule 37;
  - eight `switch-*` workflows for a platform the plan explicitly defers;
  - many `historical-*`, `audio-*` and `course-*` probes.
- 213 of 300 sampled workflow starts were tooling-unit or repository-hygiene ([CI acceleration record](CI-ACCELERATION-EXECUTION-20261014.md)). The repository has no merge queue (`merge_group` is unused). Only 5 workflows use any build cache.

**Recommendations**

- **R18 — Delete closed research workflows; keep one parameterised research runner.** Git history is the archive. A small number of generic dispatchers (native build + script, original-vs-native lockstep, Windows journey) cover nearly all experiment shapes.
- **R19 — Batch heavy validation instead of running it per push.** At 100+ merges per day, a GitHub merge queue would batch validation and remove the "green on stale base" and re-run churn that dominates the CI notes. Check plan availability first: merge queues on private repositories need an organisation plan that supports them. If none is available, get the same effect with a nightly or per-candidate heavy stage. Either way, run heavy Windows journeys in the merge-group or nightly stage, not on every agent push.
- **R20 — Cache compilation.** Use ccache/sccache via `actions/cache` for the Baldosa guest and Modern host on Windows and Linux, or reuse a nightly prebuilt guest object archive keyed by pinned upstream SHA and toolchain. Most PRs do not change the generated guest.
- **R21 — Path-filter tooling-unit tests by changed package.** For example, use `pytest --testmon` or a module→test map. A docs-only PR should not run 3,000 tests.

---

## 7. Architecture and code-health hotspots

- `native/product/uniracers_modern_host.cpp` is **10,939 lines** and has been touched by 30 commits since 10-08. WORK-QUEUE explicitly warns lanes not to edit it concurrently. A god file is a serialisation point for a multi-agent team. **R22:** split it along the existing Modern domains (root/router, profiles, play session, records, options, multiplayer) behind the existing C ABI, as a mechanical no-behaviour-change refactor guarded by the current native tests. Do this before Practice and Options are bound.
- `native/presentation/racer_hd_presenter.hpp` is 3,035 lines, almost all in a header. The procedural racer art in it has been visually vetoed. Avoid further investment until R24.
- The Baldosa adapter is spread across about 20 `baldosa_native_*.hpp` headers, each a narrow seam added by one PR. Consolidate them after the cut-over (R5).

---

## 8. Scope discipline

PROJECT-PLAN defers ports, online play and archaeology, yet the following work exists and is still growing: P2P research labs (R0/R2, dated 10-11), Switch S0–S2 contracts plus eight workflows, a desktop post-race video specification, a self-sustaining P2P networking charter, and a "definitive technical reference" declared a **coequal** deliverable.

- **R23 — Enforce WIP limits.** Allow at most three active lanes (product, graphics, gameplay timing) and reject new docs or workflows whose lane is deferred. Make the technical reference a **by-product** of the gameplay-oracle work (R1–R3), not a coequal programme with its own budget.
- **R24 — Use a human artist for racer HD art.** The owner vetoed agent-generated procedural art. The original sprites were pre-rendered from 3D models, and the reconstruction brief already identifies a 3D model/rig as the target. The established route is to commission a 3D modeller, using the reference contact sheet the brief calls for, and render all poses at 4× from the rig with an automated registration check. Agents should build the render-and-register pipeline, not the likeness.

---

## 9. Practices from comparable projects not yet used, or under-used

| Practice | Where it is standard | Use here |
|---|---|---|
| In-process lockstep RAM verification against an emulator | snesrev `zelda3`/`sm`/`smw`; N64Recomp-family debugging | R2: the backbone of QA-01 |
| Accuracy-tier reference cores and hardware test ROMs to decide timing | Emulator development (bsnes/ares/Mesen2; peterlemon, undisbeliever and blargg test suites) | R1: the timing envelope; settle Snes9x/bsnes disagreements |
| Nightly downloadable builds and player bug reports | Ship of Harkinian, Zelda64Recomp, sm64 ports | R10–R11 |
| Upstreaming fixes to the recomp framework | All healthy recomp forks | R4 |
| Merge queue and compile caching | Any high-merge-rate monorepo | R19–R20 |
| Single source of truth plus generated status | Docs-as-code practice | R8, R14 |
| Commissioned art pipeline from 3D source | HD remasters of pre-rendered-sprite games | R24 |
| TAS/bot movies as regression inputs across all courses | Decomp/recomp CI (TAS playback suites) | R3: the project already holds SMV/bot archives |

---

## 10. Suggested order (about two weeks)

1. **Day 0–1 (owner decisions):** approve the R1 equivalence relation; set the legacy-core retirement date (R5); approve the PR/notebook policy (R6–R7) and the WIP limits (R23).
2. **Days 1–4:**
   - Land the #1608 correction in the shipping Baldosa build and investigate RF-016 (SPC clock).
   - Build the R2 lockstep harness.
   - Publish the first nightly ZIP (R10).
   - Split `uniracers_modern_host.cpp` (R22).
3. **Days 4–8:**
   - Run the 45-course batch (R3) and file upstream issues (R4).
   - Bind Practice and Options (R12).
   - Hold the first owner playtest (R11).
   - Delete closed workflows and add the merge queue (R18–R19).
4. **Days 8–14:**
   - Nominate the first ledger candidate (a tagged release).
   - Run QA against that candidate only (R7).
   - Enforce the context budget (R13–R15).

**Stop signals:** after R1–R3, if more than about 10 courses still fail on gameplay-authoritative state, gameplay fidelity is the real blocker and deserves the lanes. If they pass, the project is much closer to an alpha than 0/45 suggests, and product and polish should take over.

## 11. Caveats

- PR categorisation is by title keyword and is approximate.
- Line counts include generated and imported data in `analysis/` and `reference/`, so the product share is indicative, not exact.
- This review did not run CI or the game. It did not re-derive any gameplay claim; it relies on the owning documents and on #1608's own measurements.
- Some recommendations (R1, R5, R23, R24) are owner decisions. This report proposes them and does not adopt them.
