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

### Shared native candidate across focused workflows

Several focused automatic workflows still independently build materially the
same Linux native candidate. Native UI was the clearest duplication and has
been corrected first.

A later optimization should measure whether a reusable workflow or trusted
build-candidate artifact can safely serve Profile Panel, Ghost Target, Modern
Onboarding, Completed Run Replay and similar gates. Do not centralize merely to
reduce YAML: the shared producer must preserve each consumer's required patch,
instrumentation and source inputs, and artifact transfer must be cheaper than
the build it replaces.

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
