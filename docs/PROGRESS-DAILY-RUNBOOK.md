# Progress reporting: repeatable daily handoff

The [fixed 100-point Windows-beta inventory](PROGRESS-INVENTORY.json) is unchanged. Scoring tiers are coarse, so the companion evidence-velocity report records reviewed and merged product advances between score transitions. **Do not equate counts of PRs, changes, lines or tests with percentage completion.**

## Reproduce a report

After reviewing latest `main`, identify its full 40-character source SHA. Append a single `docs/PROGRESS-CHANGELOG.json` interval with that exact `source_commit`, date, source-linked unique evidence changes, `engineering_maturity_before` and `engineering_maturity_after` (both from the frozen inventory), and formal event/gate deltas from authoritative sources.

```sh
python3 tools/progress_calculator.py --format markdown
python3 tools/check_progress_freshness.py --reviewed-head FULL_REVIEWED_SHA
python3 tools/progress_report.py --reviewed-head FULL_REVIEWED_SHA --format markdown
python3 -m unittest discover -s tests -p 'test_progress*.py'
```

If there was **no** verified engineering change, an interval may explicitly record an empty set, but do not claim a fresh review without inspecting the source and ledger. If the latest reviewed SHA does not match the requested SHA, report fails instead of recycling yesterday's numbers. A report records 0.00 percentage-point movement whenever the fixed criteria have not advanced, alongside the independently grounded work actually integrated.

## Reporting ownership

The integration/release-operations lane should update the changelog as part of its existing normal handoff, using independent QA outcomes for gate and event counts. No new scheduled agents or repeating Actions are required. Research archives, pending PRs and unmerged branches count as pending, not engineering changes to `main`. A newer commit after the last review makes the report *dated*, rather than retroactively false.

Initial reproducible comparison as of the independently reviewed October 23 source `1bc0f100228c0601357397ca1a6cd4c829934120`: **48.50% maturity, 0.00 percentage-point change, ten source-linked merged advances, 0/12 accepted QA gates and 0/45 accepted events.**

## Future resolution of coarse milestone scoring

Design an independent `windows-beta-v2` inventory with finer criterion boundaries, one-time denominator freeze, and no retrospective recasting of v1 scores. Report v1 and v2 side-by-side during migration; only replace the headline on an explicitly dated switchover. Do not add points to v1 for nearby fixes that cannot satisfy the existing threshold.

The output of `tools/progress_report.py` is the standard handoff format for each request for progress. Statuses represent documented evidence, not automatic CI green or PR-merge equivalence.
