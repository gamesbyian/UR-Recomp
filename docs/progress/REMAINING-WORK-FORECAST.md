# Remaining work uncertainty: first-prior forecast

**Status: 2026-10-26, hypothetical relative-work estimates, not a ship-date forecast.** This supplements the immutable 135-criterion Windows-beta v2 completion measure.

The [relative-work prior](remaining-work-prior-v1.json) covers every currently unfinished criterion (85 at the reviewed source 82fd7d2a), with small/moderate/large/hard/unknown/physical/event effort ranges. The model also counts **42 provisionally completed but not independently reviewed criteria** as separate bounded-audit work, with deliberately small [0.25, 1, 3] relative-unit ranges per review. This cannot award another completion point and does not stand in for physical release sign-off. Its unit is one ordinal small bounded engineering delivery, **not an agent hour, PR, calendar day, or percentage point**. The script expands the stable IDs from the v2 inventory and treats shared parity, raster, racer art and release-package prerequisites as four one-time tasks. Marginal event checks are modeled conditional on shared parity, so 45 events do not repeat the same underlying correction 45 times.

Reproduce from repo root with Python 3 standard library:

- python3 tools/remaining_work_forecast.py --format markdown
- python3 tools/remaining_work_forecast.py --format json
- python3 tools/remaining_work_forecast.py --reviewed-head FULL_40_CHARACTER_REVIEWED_SOURCE_SHA
- python3 -m unittest discover -s tests -p test_remaining_work_forecast.py

P10, median and P90 are deliberately **wide expert-prior scenarios**, not statistically calibrated confidence levels. New causes can exceed P90. External physical reviews, human art approval, hardware availability and 4K device checks are counted as unresolved dependencies, **not estimated waiting times**.

[Twenty independently observed recent PR cycles](pr-cycle-observations-20261026.json) range from 0.01 to 21.42 open-to-merge hours (median ~0.72 hours). This is a deliberately selected convenience sample, not task labor time: it excludes pre-PR engineering and includes CI/review wait. It **cannot** calibrate work units into delivery dates. No date forecast should be displayed until agent-active time, blocking, rework, first acceptance and source-dependent velocity are measured for multiple comparable closures.

## Updating after a real outcome

1. Independently qualify a complete criterion in the *existing* v2 inventory against exact source, binary and executable evidence. The model then removes its marginal remaining work, without inventing a new product score.
2. If a real discovery changes the effort *without completing the criterion*, add one current range adjustment to [adjustments](remaining-work-adjustments.json), with the item/shared-task ID, new three-point estimates, a precise reason and GitHub evidence URL. Git history retains the previous estimate. Unverified time spent earns nothing.
3. In every future update decompose changes into **earned completed work**, **re-estimated outstanding work** and **scope corrections**. Never label a reduction in an estimate as verified engineering completion.
4. Release gates and all 45 USA original/native events remain under independent authority; an effort estimate cannot award them.

An independently resolved shared blocker may also be recorded under the adjustments file's completed_shared array, with its stable shared-task ID, evidence URL, independent reviewer and reason. It removes that once-only cost even while dependent acceptance criteria remain open, without changing formal completion or release counters.

## Priorities for calibration

Measure active agent-session work where receipts permit it, and separately record assignment-to-acceptance elapsed time, CI/review waiting, rework and blocked human/physical time. Calibrate by task family, not PR count. Only then derive throughput distributions, dependency-aware P50/P80 dates and a work-weighted completion baseline. Until then use the relative-work ranking to prioritize a first complete event, actual player-controller routes, full Unicode persistence and remastered racer art, instead of starting new general-purpose infrastructure projects.
