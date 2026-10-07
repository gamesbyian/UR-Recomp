# Expert Playtest Protocol

Status: Windows x64 release-readiness contract.

This protocol turns expert/community playtesting into reproducible evidence without treating player testimony as simulation authority. It complements deterministic fixtures and the lead list in `PLAYTESTER-INTEREST-LEADS.md`.

## Purpose

The release-readiness pass should include, where practical:

- at least one current/high-skill Uniracers player;
- at least one PAL/Unirally-experienced player;
- at least one collision/glitch-oriented player;
- multiplayer familiarity when validating local multiplayer/rematch/records work.

A single tester may satisfy more than one category. The goal is coverage of expertise, not a headcount target.

## Privacy and provenance

The retained machine-readable report is about **the build and finding**, not the person.

Do not store tester names, handles, email addresses, private messages, IP addresses, controller serials, account IDs, or other personal/contact data in a playtest report. The public lead list remains the provenance surface for publicly identified prospective testers. Outreach/contact records, if they ever exist, are not part of the game-evidence corpus.

Each report must bind to:

- exact source/build revision;
- SHA-256 of the tested distribution artifact;
- region, execution mode, logical view and graphics mode;
- broad tester-experience class;
- one bounded finding.

The canonical example is `analysis/data/playtest-report-example.json`. Validate a report with:

```bash
python tools/validate_playtest_report.py path/to/report.json
```

## One finding per report

Keep each report to one claim. A tester session that finds three unrelated issues produces three reports. This makes triage and fixture promotion independently decidable.

Required finding fields describe:

- **area**: the owning product/fidelity surface;
- **summary**: one compact claim;
- **reproducibility**: always / often / sometimes / once / not reproduced;
- **severity**: observation / minor / major / release-blocker;
- **steps**: the shortest reproducible route the tester can describe;
- **expected**: what the tester expected and why;
- **observed**: what differed;
- **comparison_source**: none, memory, original hardware, emulator, video, or timed run.

Optional frame/input/reference anchors may narrow the investigation. They are clues, not promoted invariants.

## Triage

Classify a valid report before changing code.

1. **Product/presentation issue.** If the finding concerns layout, navigation, explanation, persistence UX, rematch flow, controller presentation, or another host-owned product choice, reproduce it in the current Windows build and add the cheapest deterministic product test that would have caught it.
2. **Possible fidelity issue.** If the finding concerns handling, collision, timing, stunts, camera behavior coupled to gameplay, AI, RNG, or progression semantics, reproduce it against the canonical original/reference route before changing behavior. Player testimony selects where to measure; it does not authorize the fix.
3. **Expected/intentional difference.** If the difference is a documented Modern product decision or presentation-only effect, improve explanatory copy or the test protocol if useful. Do not convert it into a fidelity bug.
4. **Not reproducible.** Preserve the report only while there is a concrete next discriminator. Do not accumulate unbounded anecdotal backlog.

## Promotion into deterministic evidence

A playtest finding is closed only when one of these dispositions is recorded:

- **fixture-promoted**: a deterministic regression fixture reproduces the issue and owns the acceptance criterion;
- **product-test-promoted**: a pure/native product contract test reproduces the issue;
- **documented-intent**: the observation matches a deliberate product policy;
- **reference-variance**: comparison-source behavior is understood and does not establish a canonical difference;
- **not-reproduced**: bounded investigation failed to reproduce and there is no justified next discriminator;
- **deferred**: a named missing seam/evidence source blocks resolution.

For simulation-affecting findings, the durable fixture belongs in `tests/fixtures.json` or an already-established title-specific acceptance harness. Do not create a parallel replay format merely because the observation came from a human session.

## Release-readiness focus

Ask expert testers to spend most of their time on places ordinary smoke tests under-sample:

- handling under high-skill lines;
- jump/landing/boost and stunt timing;
- loops, transitions, wall/ceiling adhesion and known fall-through/glitch locations;
- camera/scroll behavior under optimal or unusual routes;
- widened track-reading without altered activation/collision;
- PAL/Unirally presentation and timing expectations;
- local multiplayer setup, rematch and track rotation;
- persistence, resume/restart and package-refresh behavior;
- records/timing presentation under repeated attempts.

Do not ask testers to perform broad unscripted QA when a narrow question is known. Give them the build identity and the smallest route that exercises the uncertainty.

## Stop condition

The external pass is sufficient for a release candidate when the planned expertise classes have been represented, every major/release-blocker report has a recorded disposition, and no unresolved report implies an unmeasured change to authoritative simulation.

More hours of play are not automatically more evidence.
