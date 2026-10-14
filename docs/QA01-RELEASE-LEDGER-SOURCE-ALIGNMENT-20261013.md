# Independent QA-01 release-ledger/source-census consistency check (2026-10-13)

**Purpose:** make it impossible to claim a complete Windows-original USA course-event census by editing only aggregate release-ledger counts. This is an independent **source reconciliation** guard, not a new gameplay oracle.

## Authority and rule

The release ledger at `docs/RELEASE-QUALITY-LEDGER.json` summarizes a separate original/native source register at `analysis/data/course-event-runtime-evidence.json`, whose canonical 45-course catalog is `analysis/data/course-corpus.json`. The existing `tools/audit_original_course_event_coverage.py` implements the independently maintained population, event kinds, original-vs-native source metadata checks and per-course status classification.

The QA-12 ledger validator now **reuses that exact existing census builder** and checks that all these ledger fields equal the source register on every validation, even if someone preserves the 45-case/90-case arithmetic:

- `complete_event_passes`: actual `usa-retail` `passed` rows from the independent register
- `partial`: actual `usa-retail` `partial` rows
- `unverified`: remaining USA rows, including any `blocked` or `failed` source investigation that has not produced a release-accepted pass
- `regional_comparison_complete`: `passed` rows for Europe retail and PAL prototype
- `regional_comparison_unverified`: their remaining rows (comparative partials do **not** cause USA release failure)

The previous structural checks still require 45 USA, 90 comparison and 135 total course/build identities. When QA-01 is declared `passed`, the source register must also identify the **same exact nominated release source commit for every accepted USA course**, in addition to the existing L4 report/ZIP requirements.

Missing, invalid or stale original-event input now fails the ledger validation rather than silently trusting whatever summary is typed by an operator. No source evidence, ROM, original/native reference, course comparator, gameplay implementation or release status is changed by this work.

## Current real disposition

At this audit the source register has 4 USA partial rows (Dragster, Zoom Zoo, Bowl, Jumpover), zero USA accepted complete events and 41 unverified; 90/90 comparative cases are unverified. The current ledger matches those counts. **QA-01 remains 0/45, no release candidate is nominated, and no L4/L5 release gate is promoted.**

A synthetic unit fixture that supplies future 45 source-bound results is only a validator contract exercise. It does **not** produce an independent original/native result, prove the source records truthful, authenticate a reviewer, exercise a Windows executable, or remove physical device acceptance. Full playthroughs and independent source comparator results remain prerequisites for *creating* any `passed` source observation.

## Why this matters to Windows release QA

The 15-frame adaptive frontier and other native fingerprint campaigns may discover candidate control states, split visibility or air-state seeds, but their native-only outputs cannot make a new course `passed` in the source register; a ledger-only count change is now explicitly rejected. Likewise, a genuine Baldosa 1P/2P result-to-Records publication is product evidence, not proof of parity against independently executed original Snes9x/MesenCE events. Comparatives to PAL are informational and do not raise the 45-case Windows-USA threshold.

Contract command: `python3 -m unittest tests.unit.test_release_quality_ledger`. Existing tooling-unit-tests CI is sufficient for this QA-only validator change.
