# CI Hardening Audit and Remediation

Status: active hardening program, 2026-10-06.

This document records the repository-wide audit that followed the October 6 CI
failure cascade. It distinguishes mechanical CI defects that can be prevented
centrally from semantic acceptance contracts that require deliberate product
decisions.

## Scope

The audit covered all workflows under `.github/workflows/`. The repository
currently has a large retained workflow library, but most entries are manual
research/evidence instruments. The operational risk is concentrated in the
automatic merge and shipping surface.

The failure classes examined were:

- stale harness assumptions presented as product regressions;
- exact diagnostic text or field-order coupling;
- absolute-frame coupling where frame identity is not itself the invariant;
- nested-shell and line-continuation quoting hazards;
- cursor-count UI navigation;
- serial mega-workflows and duplicated native builds;
- aggregate jobs that create secondary failures after an upstream failure;
- overly broad trigger paths;
- specialist workflows following the global toolchain registry;
- unbounded jobs;
- evidence writers racing or cancelling one another;
- insufficient failure context.

## Implemented in the current hardening branch

### Fast native smoke

The generic native smoke gate is intentionally limited to build identity,
boot/frame sanity, deterministic race entry, cheap profile/host sanity, output
capability, one shipping Widescreen composition proof and display-geometry
review.

Long product journeys are owned by focused gates. The target is roughly four
minutes, with sustained growth past five minutes treated as a design regression
and an eight-minute hard timeout.

### Native UI evidence: one build, many captures

Native UI evidence now has one `build-ui-candidate` producer. The five capture
shards consume an archived copy of that exact candidate rather than independently
staging and compiling five equivalent binaries.

This is both a runtime optimization and an evidence-integrity improvement:
every shard now observes the same compiled candidate.

The aggregate job runs only after a successful build and successful capture
matrix. Failed capture jobs already upload their own diagnostics, so aggregate
semantic validators do not manufacture secondary "missing evidence" failures.

### Structured diagnostic assertions

`tools/ci_log_assert.py` provides order-independent assertions for append-only
key/value diagnostic events. New or reordered diagnostic fields must not break a
consumer that only owns a subset of fields.

The smoke and Native UI host-state checks use this helper rather than treating a
whole log line as an ordered string contract.

### Trigger and dependency boundaries

Automatic specialist workflows should name the toolchain entries they consume.
They must not watch `tools/toolchain.json` or
`tools/toolchain-entries/**`.

Ghost Target and Profile Panel now name their SNESRecomp, SDL3 and global
entries. Completed Run Replay no longer follows the aggregate registry. Final
Windows smoke no longer follows the aggregate registry and no longer retriggers
on its own workflow YAML after merge.

ROM Baseline no longer depends on a recursive `snesrecomp` submodule checkout.
It stages the repository-owned pinned SNESRecomp source through the same offline
bootstrap path as the rest of the product.

Pure header-only product models with Python compile/run wrappers must also trigger the tooling suite when the model header or native driver changes, not only when `tests/unit/**` happens to change in the same PR. The current narrow trigger set names the local-multiplayer setup, Modern root, semantic text catalog and readable-text layout contracts plus their native test drivers individually. Do not replace this with a broad `native/product/**` watch; add another exact path only when a concrete pure-model wrapper exists.

### Writer safety and timeouts

Evidence workflows that commit and push generated reports serialize with
`cancel-in-progress: false`. The audited writers were corrected accordingly.

Automatic jobs have explicit job-level timeouts. The imported-reference audit
and ROM baseline were brought under this rule. Relevant manual evidence writers
were also given bounds while being corrected.

### Machine-enforced CI policy

`tests/unit/test_ci_trigger_policy.py` now guards the following classes:

- automatic jobs without job-level timeouts;
- Git-writing workflows that can cancel one another;
- automatic specialists that watch the global toolchain registry;
- automatic workflows that watch every toolchain entry;
- final-main workflows that self-trigger on their own YAML;
- comments inserted after a backslash-continued shell line;
- host-state log assertions that depend on multiple ordered fields;
- Native UI evidence regrowing multiple native builds;
- Native UI aggregate validation regrowing unconditional cascade behavior;
- the existing trigger, concurrency, manual-research and fast-smoke boundaries.

These tests are intended to make CI architecture failures cheap. A policy
violation should fail in the tooling suite before an emulator or compiler run is
needed to discover it.

## Wall-clock performance policy

The October 7 wall-clock audit adds a second CI objective alongside correctness:
active development must not spend runner time proving superseded intermediate
commits.

The expensive automatic PR gates are draft-aware. They listen for
`ready_for_review`, but their first job skips while the PR is draft. Agents
working on a CI-heavy branch should therefore keep the PR draft while iterating,
batch coherent edits into logical pushes, and mark it ready only when the head
is worth running through the native fleet. Cheap tooling and hygiene remain
active during draft work so workflow-policy and syntax mistakes still fail
quickly.

Recurring Linux native gates use the Ubuntu runner's supplied CMake/Ninja rather
than downloading duplicate copies. SDL3 remains the canonical source/backend;
SDL2 development packages must not creep back into SDL3 gates. Native UI capture
shards install only the runtime tools they need after downloading the single
producer-built candidate.

The runtime report now records queue, job, dependency, build and execution
timings rather than only whole-workflow duration. Use those measurements before
adding caches or restructuring jobs. In particular, compiler caching is not an
automatic win once draft gating suppresses most intermediate native builds.

Modern Onboarding's independent fresh-process acceptance cases own distinct
work/output roots and may run concurrently against the same read-only candidate.
Native smoke's bounded boot and deterministic race-entry routes may disable
per-frame delay because their semantic output was proven unchanged under
unpaced execution. Presentation-sensitive routes should not inherit Turbo or
presentation skipping merely for speed.

### Bounded Stunt UI entry versus exploratory result

The Stunt `ui-stunt-result-route.script` documents a known non-terminating
idle-input case: the event timer expires without advancing to the proposed
0x18 result menu. The automatic Native UI suite previously spent roughly
98–162 seconds running that probe to status 3, retaining only its three
successful entry captures. This was not a demonstrated result-screen
acceptance, and treated research uncertainty as an automatic CI long pole.

The automatic suite now runs `ui-stunt-entry-route.script`, preserving the
original track-selection, Now Playing and entered-race commands and requiring
all three dumps plus a successful scripted exit. The long-running idle-result
experiment remains intact as a **manual research fixture**. This does not
claim the Stunt result screen has been recovered; it makes the existing
automatic evidence precise and prevents recurring time spent on a currently
unfulfilled exploration. The prefix-equivalence unit test prevents drift.

### Automatic UI capture is bounded by evidenced states

Recent green Native UI runs still ran two exploratory scripts past their
actual achieved evidence. The historical ending shortcut captures splash
`009F=84` but stalls trying to reach `009F=5B` (roughly 39–67 s).
The Circuit result probe captures track entry and all sixty driving
checkpoints but stalls trying to reach `009F=BC` (roughly 91 s total).
The failed state transitions were never demonstrated product acceptance.

Automatic Native UI now uses exact command prefixes of those fixtures:
`ui-splash-capture.script` exits immediately after the successful splash
dump, while `ui-circuit-drive-capture.script` exits after the existing
Circuit terminal driving dump. The automatic gates **require** successful
exit and the same evidence dumps, making loss of those proven captures
a real regression. Historical `ui-ending-shortcut.script` and
`ui-circuit-result-route.script` stay untouched as manual research
experiments; the classifier no longer runs automatic heavyweight builds
when only those manual probes change. The prefix contracts are unit-tested.

To rebalance these now-shorter shards without increasing six-job matrix
concurrency, `ui-main-branches` moves from core to profiles using its
unchanged script and independent `ui-branch-dumps` root. The atlas,
transition comparisons and aggregate reset-separated-capture checks
continue to see the same immutable artifact roots.

The original ending shortcut and Circuit-result hypotheses remain open.
Observed wall-clock benefit must be reported only after green native runs;
historical timings are *not* a prediction of stable future performance.

### Two-core replay reference capture overlap

Measured full-router replay acceptance spent about 82 seconds in its
initial `Capture completed Dragster run` step: the unpaced reference
finished after roughly 25 seconds, then the paced control ran for
roughly another 55 seconds. The two captures have independent record/log
targets, separate config/user-data roots and fresh emulator processes.
Only their final strict `.urrun` comparison depends on both outcomes.

The shared Modern replay workflow now starts the two captures concurrently
on distinct Xvfb displays, **at most two emulator processes on its two-core
runner**. Both statuses and logs are collected before any further work.
Any failed or absent capture fails the job, and the original
`UR_RUN_REPLAY_COMPARE PASS` plus ghost/replay follow-ons remain intact.
This reduces serialized waiting without introducing another Actions job
or treating unpaced equivalence as a weaker oracle.

The change is a measured hypothesis until a green CI replay job proves the
two-process arrangement is deterministic and the actual wall-clock impact
is compared against run 37755129420. If CPU competition or display
contention eliminates the saving, revert the overlap rather than weaken
the reference comparison.

### Circuit capture acceleration: controlled evidence, not a blind turbo switch

The native UI `ui-circuit-drive-capture.script` must exercise 60 seconds
of scripted race frames and historically took about 71 seconds of hosted
runner time. The first unpaced comparison in
[run 37766987356](https://github.com/gamesbyian/UR-Recomp/actions/runs/37766987356)
found 64 file differences because the preexisting paced baseline reused
the executable-owned user-data root after a different race while the
unpaced run started from a pristine root. Its early menu checkpoints were
already 3–5 simulation frames apart. It did **not** establish a pacing
regression.

The follow-up controlled diagnostic in
[run 37776055765](https://github.com/gamesbyian/UR-Recomp/actions/runs/37776055765)
ran two instances of the **same** Circuit script against the **same**
executable/ROM, starting from independent freshly initialized user-data
roots. One had `DisableFrameDelay=0`, the other
`DisableFrameDelay=1`. Their eleven capture checkpoints were at the
same script frames (track selected 736, Now Playing 802, race entered
1075, terminal 4260). The paced run took about 71 seconds; the unpaced
run 28 seconds. The final CI assertion itself errored due to a
three-argument/two-target unpacking defect, but its uploaded
`native-ui-capture-results-a` artifact
([archive 11550625072](https://github.com/gamesbyian/UR-Recomp/actions/runs/37776055765/artifacts/11550625072))
contained the complete controls. Independent read-only SHA-256
comparison of those retained captures found **121/121 byte-identical
files**, including the full framebuffer, WRAM, SRAM, VRAM, OAM, PPU
metadata, registers, DMA and palette dumps. The original mixed-state
paced baseline differed from the pristine paced control in 64 files.
Thus the earlier drift was explained by initial persistent state rather
than the pacing setting.

The required automatic Circuit route now uses an **isolated, initialized
user-data root** with `DisableFrameDelay=1` and retains its original
script, all eleven dump labels, the same artifact directory, and a
required zero exit. This makes the compared initial state reproducible
rather than dependent on which other capture happened earlier in the
shard. The full Native UI aggregate/atlas/finish-time contracts must
still pass on the optimized configuration; the one-off paired diagnostic
is not retained in permanent automatic CI.

### Combined-shard validation after Circuit acceleration

PR #891's native candidate (run 37778037908) proved the pristine-root
Circuit route finished in approximately 28 seconds and preserved the
full Native UI aggregate. PR #894's green branch run 37828086895
validated moving Modern settings persistence into Results-A, but its
branch originated **before** #891 and thus ran a paced Circuit route
(~71 seconds). These two successful PR-head validations are not by
themselves evidence of the merged, simultaneous execution policy.

For the combined main-derived check, the required Circuit capture now
verifies its own native host log announces
`config dir anchored: $SNESRECOMP_USER_DATA_DIR` after executing
the unchanged route, as well as the exact isolated config file's
`DisableFrameDelay = 1` setting. It emits
`UR_CIRCUIT_ISOLATED_CONFIG_ROOT PASS` only after the guest and
config root match. The full six-shard aggregate continues as the
merge gate. This avoids silently falling back to the executable-owned
config or treating a merged workflow as measured merely because its
two constituent PRs separately passed.

## Remaining semantic debt

### Racer native presentation exact-frame contracts

`racer-native-presentation-acceptance.yml` contains many assertions tied to
absolute global frame numbers and exact temporal windows. Some of these may be
true timing invariants; others may only identify a convenient observation in a
deterministic trace.

Do not mechanically relax them.

The future repair should classify every frame assertion as one of:

1. **timing invariant** — the exact frame is product behavior and remains exact;
2. **ordered transition invariant** — assert event order/delta instead of an
   absolute frame;
3. **evidence anchor** — discover or select a qualifying event and capture it
   without binding the contract to unrelated earlier timing.

A useful end state is a structured presentation trace validator that consumes
events and relative relationships rather than dozens of independent
`grep -F "... frame=N ..."` statements.

The first non-authoritative shadow seam now exists in
`tools/check_racer_presentation_trace.py`. It parses the existing
`UR_RACER_PRESENTATION_TRACE/OBS` and `UR_RACER_HD_DRAW PASS` records and,
for every complete four-instance draw transition it observes, verifies the
frame-independent slot/semantic relationship: top 98 / bottom 97 must carry
the traced P1 primary and top 99 / bottom 96 the traced P2 primary. The
automatic Racer presentation workflow runs this validator with
`continue-on-error: true` and retains its JSON report. No absolute-frame
assertion has been removed or relaxed. Promote this seam to authority only
after retained runs demonstrate that the relationship is stable and the
remaining frame assertions have been classified deliberately.

### Cursor-count UI automation

Profile Panel and the Modern settings acceptance still drive SDL windows with
`xdotool` and menu-relative Up/Down counts. This makes menu insertion a hidden
test API change.

Do not replace these checks with weaker coverage. The future repair should add a
semantic host/test seam that can target named menu actions or rows while still
exercising the real presentation and persistence path. Until that seam exists,
cursor-driven tests should remain focused, heavily diagnosed and outside the
generic smoke gate.

### Shared native candidate and bounded acceptance fan-out

The heavyweight Modern Linux gates now use a classifier-driven router rather
than paying blindly for duplicate producers. Shared Modern, Modern Onboarding
and Native UI keep independent consumer graphs and suite-specific path
manifests, but the router owns automatic PR selection. Artifact forensics on a
completed three-gate PR proved that all three producers emitted the same native
executable and the same patched main.c, game_rtl.c and CMakeLists.txt, so they
are one semantic build seam rather than merely similar YAML.

Build sharing is adaptive rather than unconditional. When all three heavyweight
suites are selected, one canonical producer builds and uploads the immutable
candidate and each reusable suite bridges that artifact into its existing
consumer contract. When only one or two suites are selected, the canonical
producer is skipped and the selected suites keep their standalone builds in
parallel. The two-suite #835 pilot proved the reusable-workflow artifact handoff
but was roughly 40 seconds slower in wall-clock than two parallel producers.
The full three-suite proof, run 37751358382, passed all 27 jobs in 433 seconds
versus 518 seconds for the comparable standalone cohort. Producer runner time
fell from 569 to 214 seconds, a 62.4% reduction, while the slowest producer path
to consumer fan-out fell from 256 to 194 seconds. This keeps the runner-minute
and dependency-pressure win without serializing narrower PRs.

Fan-out is deliberately bounded. A two-core runner should normally execute no
more than two CPU-bound emulator processes at once. Pacing-heavy cases may
temporarily tolerate more local concurrency, but once frame delay is removed
they should move into a small matrix of chunky shards rather than oversubscribe
one runner. Prefer roughly three to five useful consumer shards over one job per
test case so repository-level Actions concurrency is spent on wall-clock
reduction rather than scheduler overhead.

Candidate sharing must be semantic, not merely YAML deduplication. Before a
consumer joins the shared producer it must prove that its setup-project flags,
SNESRecomp patches, Modern host patch, SDL backend, generated sources and
instrumentation requirements match the producer. A gate requiring a genuinely
different binary remains a separate producer.

Until repeated package installation has been removed, install-heavy jobs need
enough timeout headroom to survive transient mirror stalls. Timeout tightening
follows measured execution time and must not turn dependency-service latency
into routine false-red CI.

## Wall-clock operating policy

Measured CI runtime is now treated as an architecture constraint, not a cosmetic
workflow concern.

For expensive pull-request gates:

- keep the PR in draft while a workstream is still producing commits;
- push one coherent logical change rather than one file at a time;
- expensive native gates must skip draft PRs and include
  `ready_for_review` in their pull-request event types so the full evidence
  fleet runs when the change is actually presented for review;
- cheap policy/unit/hygiene checks may continue to run on drafts so structural
  mistakes are caught before the expensive gates are released;
- do not add a fixed debounce sleep. Draft deferral and narrow path triggers are
  the debounce mechanism;
- do not treat cancelled superseded runs as signal.

Dependency setup is also part of the runtime budget. GitHub-hosted Ubuntu
already supplies CMake and Ninja; automatic native gates must not repeatedly
download them, and SDL2 development packages must not be pulled into canonical
SDL3 builds. Runtime-only artifact consumers should install runtime tools only,
not compiler/development stacks.

Acceptance pacing may be removed only where it is explicitly proven not to
change the evidence contract. `DisableFrameDelay = 1` is preferred for
deterministic script-driven CI because it removes host waiting without the
presentation-skipping behavior of Turbo. Keep wall-clock-driven `xdotool`
journeys paced. Promote additional unpaced routes one bounded gate at a time,
with byte/state evidence or an equivalently strong semantic comparison.

Independent acceptances may share one compiled candidate and run concurrently
when they own separate mutable state, dump, log and display roots. Do not
parallelize cases merely because their YAML steps are adjacent.

The runtime report must retain enough timing detail to distinguish queueing,
dependency setup, compilation, acceptance execution and cancelled wall time.
Optimization decisions should be based on those components rather than whole-run
duration alone.

## Operating rules

When a CI job turns red:

1. identify the first failing invariant, not merely the final red job;
2. classify it as product/runtime, harness/contract, orchestration, toolchain or
   evidence failure before editing product code;
3. inspect adjacent assertions and assumptions before rerunning;
4. preserve complete diagnostics for the failed class in one run;
5. do not make a product behavior change solely to satisfy a broken harness;
6. do not babysit superseded Actions runs.

When adding a workflow or acceptance:

1. state the invariant in one sentence;
2. choose the narrowest trigger inputs that can change that invariant;
3. prefer structured state/evidence over raw log-string shape;
4. prefer event/relationship assertions over incidental absolute timing;
5. reuse an existing native candidate when provenance and cost justify it;
6. give every external/native job a hard timeout;
7. ensure failure output names the violated invariant and preserves bounded
   evidence;
8. add a policy test when the rule is repository-wide rather than local.

## Completion criterion

This hardening program is complete when mechanical CI architecture mistakes are
caught by fast tooling tests, expensive gates run only for inputs that can
change their invariant, native candidates are not rebuilt redundantly without a
measured reason, and the remaining exact-frame/UI-navigation contracts are
either explicitly semantic or replaced by semantic harnesses without reducing
coverage.
