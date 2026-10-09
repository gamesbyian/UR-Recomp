# Bounded, cross-productive release QA campaign

Status: planning and resource policy, 2026-10-08. Applies to QA-01..QA-12. This document **does not waive** the release criteria in `ADVERSARIAL-QA-AND-RELEASE-READINESS.md`, promote any ledger gate, or assert that unexecuted journeys pass. It sets a cost-controlled **first campaign** and an explicit decision point, not an unconditional promise of release readiness.

## Objective and budget

Optimize for **player-visible correctness per productive agent-hour**, rather than number of tests, fixtures, archaeological facts, or PRs. Initial capacity planning target: **300 aggregate productive agent-hours**, with checkpoints at 100 and 200 hours. This is a *planning hypothesis*, not time tracking or a claim that release can be completed for that amount. Review the last 100 hours' reproduced defects, severity, coverage gained, duplicate work, and remaining blockers at every checkpoint. Do not silently authorize further work when the evidence has weak yield.

Suggested initial allocations (total 300; reallocate by evidence at checkpoints):
- 100h course and expert original/native event fidelity (QA-01 + QA-07).
- 55h storage, tournament and replay integrated journeys (QA-02 + QA-03 + QA-11).
- 55h moving-scene graphics, visual UX and controller/input review (QA-05 + QA-08 + QA-09).
- 35h audio, physical Windows candidate and session longevity (QA-04 + QA-06 + QA-10).
- 25h independent QA oracle, candidate/repro/coverage instrumentation (QA-12, supports all).
- 30h contingency for **reproduced P0/P1 defects only**; unused contingency returns to the pool.

Counts are agent effort, not elapsed-clock estimates. Hardware players, shipping design/art work, unpredictable new ROM archaeology, and large new animation families may exceed this allocation; expose them explicitly rather than disguising them as existing QA fixes.

## One campaign, multiple gates: shared witness matrix

A test run has one immutable manifest: candidate commit; ROM edition/hash; ZIP/checksum; fixture/script; OS/GPU/controllers/audio/display; profile/root and initial state; frame-aligned source/native observations; outcomes; artifact/recovery inventory; logs/screenshots; reproducibility; unsupported/blocked exclusions. Record **one authoritative run ID** and link that evidence from every gate it actually exercises. Do not duplicate a costly packaged journey merely to satisfy separately owned QA rows.

| Shared campaign | Journey(s) | Gates that may reuse evidence | One coherent execution |
| --- | --- | --- | --- |
| A. Authentic course/event completion | J-09, J-15 | QA-01, QA-07, QA-11 where replay exercised, QA-12 | Original and native from valid start to settled result; frame-relative checkpoints, laps, timer, score, event class, finish; run replay on selected completed cases |
| B. Stateful multiplayer tournament | J-03..J-08, J-14 | QA-02, QA-03, QA-05, QA-11, QA-12 | Two pads/profiles; held modal input, seat swap, leg 2/3 and three entrants; clean restart; duplicate/kill at selected commit boundaries; Records and replay reconciliation |
| C. Moving-scene product capture | J-13, J-16, J-19 | QA-05, QA-08, QA-09, QA-12 | Existing 1P/2P/VS scripts at Original/Remastered, 4:3/16:9; source-OBJ visibility, priority, framewise HD availability/fallback, camera, split seam, UI/readability |
| D. Physical packaged user session | J-01, J-02, J-10, J-17..J-20 | QA-02, QA-04, QA-05, QA-06, QA-09, QA-10, QA-12 | Clean portable ZIP; uncoached controller journey, save/reload, music/SFX, focus/suspend/replug, multi-hour use, actionable errors, different machines |
| E. Fault-recovery matrix | J-02, J-07, J-08 | QA-02, QA-03, QA-11, QA-12 | Representative interruption points chosen from a **transaction graph**; intact prior record, no phantom credit and deterministic recovery are shared invariants |

Evidence reuse is conditional: one run may cover multiple gates, but no gate is passed until **its own distinct stop condition and required source independence** are satisfied. Physical hardware cannot be inferred from CI. An art fallback cannot count as HD coverage. Do not equate a source-model consistency test with a second independent oracle.

## Course coverage without 45 bespoke investigations

Keep the **45-USA primary course denominator** and the separate **90 regional-comparative cases** in the ledger. Do not lower it or report partial cases as complete. First build a data-driven completion runner and compact per-course manifest using existing ROM/course corpus, bot and emulator assets. Group courses by **race/stunt/event type, lap/checkpoint topology and geometry**. Complete one *end-to-end* original/native comparison per family before expanding the same harness to all 45 USA courses. The runner must record genuinely unsupported routes instead of manufacturing completion. Only divergent or unusually high-risk courses get full per-course instruction-time archaeology.

A course counts complete only from legitimate entry to settled authoritative result, including checkpoint/lap/finish or scoring/timer as applicable. Keep scene-relative physics and expert stress seeds as **targeted counterexamples**, not 45 independent TAS research projects. Frame-2903 contact remains disputed until instruction-time evidence; do not overwrite observation with hypothesis.

If an event family cannot execute, log its exact blocker and an owner, then continue other families. Prioritize **breadth of event classes** before polishing a sixth Dragster-like fixture. For PAL, establish targeted differential discriminators first; the 90 comparisons remain unverified unless actually run.

## Admission and stopping rules

A new task must state (a) a plausible player-visible or data-integrity failure, (b) a named existing oracle or lowest-cost new oracle, (c) an observable stop condition, (d) the smallest independent test sample, and (e) which *shared campaign* collects evidence. No speculative framework, new format, research apparatus, UI system, or broad ROM archaeology without a discriminating case and owner-approved expected gain.

Prioritize: **reproduced critical defect > blocked core journey > high-information evidence gap > cosmetic refinement > speculation**. Source-confirmed races are legitimate defects even if the UI manifestation has not yet been observed; retain that classification. Cap exploratory spikes at **6 agent-hours per hypothesis** before documenting result, closing it, or escalating with evidence. Cap a family-validation investigation at **12 agent-hours** without a new counterexample, reusable runner, or event completion. Never force a failed investigation into a fake pass.

**Do not reopen accepted archaeology** solely to improve confidence. Reopen when an independent original/native divergence, player-visible artifact, security/data-loss defect, or genuinely missing product behaviour shows the accepted abstraction insufficient. Do not rebuild fixture harnesses when existing ones can be adapted. Do not add tests that assert only the test fixture's own predictions.

**Graphics**: first correct source/foreground priority and false riders. Choose coherent high-frequency animation families by measured moving sequence fallback and transition reduction. Stable Original and Upscaled are legitimate first-release options; wider Remastered coverage is feature scope, not a reason to indefinitely block an honest non-Remastered beta. Never enable visibly incoherent HD merely to increase a coverage percentage.

**Audio/UX**: test representative full user sessions first; fix audible/reproducible flaws, dead ends, controller failures and illegible text. Avoid making every possible skin, obscure host setup, accessibility preference or optional cosmetic feature an unconditional first-beta gate. Preserve known limitation statements.

**Persistence**: prioritize consistency invariants through a minimal transaction-graph fault set covering precommit, committed-but-unpaired and postcommit states plus concurrency. Don't multiply every fault point by every mode/OS without a failure demonstrating the need. Any ambiguous duplicate credit or old-data destruction remains a hard blocker.

## Release decision and escalation

- **Private playtest**: documented exact candidate, reproducible core 1P and 2P starts/results, known limitations, basic recovery and no known P0 corruption. May explicitly ship Original/Upscaled while HD remains experimental.
- **External beta**: QA programme's existing P0 and representative P1 criteria remain authoritative; a documented waiver may narrow *optional* feature exposure, not excuse loss of valid saves or false results.
- **Release candidate/public release**: preserve the stricter gate ledger and human decision. This 300-hour campaign cannot automatically certify it.

At each 100-hour checkpoint, independently answer: new reproduced defects and severity; previously blocked journeys now usable; distinct course families/full completions; moving-scene fallback/false-draw improvements; real packaged systems observed; unclosed P0s; and marginal yield. If the work is dominated by speculative test infrastructure, **stop and rescope**. If major systemic failures emerge, re-estimate publicly with concrete evidence and a fresh budget rather than quietly extending the campaign.

## Work ownership

One QA integrator owns candidate manifests, shared journey selection, witness indexing, and ledger truth. Feature lanes own only their production repairs. The gameplay lane owns A, tournament/persistence lanes co-own B/E, graphics/UI owns C, physical test coordinator owns D. Do not schedule separate expensive runs for each QA number. Keep CI speed improvements and optional Racer Studio/cosmetics out of the QA-critical path except where proven release blockers.

Canonical refs: [ADVERSARIAL-QA-AND-RELEASE-READINESS.md](ADVERSARIAL-QA-AND-RELEASE-READINESS.md), [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md), [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json), [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md), [WORK-QUEUE.md](WORK-QUEUE.md).
