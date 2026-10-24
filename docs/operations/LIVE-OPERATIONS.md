# Live operations snapshot

GitHub's read-only dashboard is a **fresh observation**, not another editable
planning document. It complements [the dispatch contract](../recovery/CONTROL-PLANE.md)
and keeps the release ledger as sole independent QA authority.

**Phone link:** [Live operations snapshot workflow](https://github.com/gamesbyian/UR-Recomp/actions/workflows/ops-live-snapshot.yml).
Open the latest successful run, choose `observe`, then read its **Job Summary**.
To force a fresh observation, use GitHub's **Run workflow** on main. No new account
or scheduled agent is required. The workflow is manual-only and does not write to
any branch or Drive folder.

The dashboard additionally displays the last independently verified
**historical main-history Drive backup** from
[main-history-custody.json](main-history-custody.json), with its saved commit,
date and commit count. It compares that stored source commit with freshly
observed GitHub `main`, without claiming to monitor Drive bytes. Even when
the commits happen to match, the current Drive copy is explicitly marked
UNKNOWN until a new Drive download and integrity test is performed.
The saved metadata is validated by
`tools/validate_history_custody.py` and its contract tests.

**Real cancellation occupancy:** the daily report now also fetches the latest-attempt
GitHub job records for **up to eight cancelled runs** selected from the
existing latest-100-run sample. It sums actual started/completed job intervals,
not the run's wall-clock span; concurrently active jobs contribute separate
runner-seconds. An API error, incomplete job pagination or invalid job record
is **UNKNOWN**, never silently zero. The report shows how many of the selected
runs had complete job censuses, how many others were not sampled, and the
measured totals grouped by workflow. These are measured occupancy intervals
for a small, biased sample, **not** a last-24-hours bill, total workflow cost,
estimated cost saving or proof a cancelled job did useless work.

In a separate bounded 20-cancelled-run inspection on 2026-10-21, the three
most frequently cancelled CI workflows already showed approximately **80
runner-minutes** of aggregate occupied job intervals before cancellation.
This motivated the source-based metric but does not imply all 80 minutes could
have been saved. Before changing production triggers, inspect the source/PR
update cadence, existing concurrency grouping, and downstream required-test
coverage; keep release gates and independent QA intact.

The output contains the exact observed main SHA/branch protection, open PR count
(and whether pagination was exhaustive), draft count, PRs whose last update is
older than 48 hours, a **bounded latest-100-run** Actions sample, the five
assignment definitions, and direct GitHub PR cross-checks for the curated Drive
recovery registry. A PR older than 48 hours is not necessarily stalled.
Cancelled/failed latest runs are not an estimate of billing or the last 24 hours.

**Provenance guard:** release gate status and 0/45-type complete USA-event
counts are read exclusively from the checked-out
`docs/RELEASE-QUALITY-LEDGER.json`. The report compares this checkout's git
commit with the just-observed main branch SHA. If these differ, the QA figures
are explicitly **STALE / UNVERIFIED SOURCE**, not current release acceptance.

**No implied connections:** the workflow has no access to the owner's
Google Drive vault or ChatGPT scheduled-task state. Their presence, agent
run history, recovery completeness and permissions therefore say **UNKNOWN**
until someone actually checks them with the connected tools. The curated
registry is only a partial set of exact Drive IDs. Every source archive
still requires original byte/hash comparison, live PR qualification and
independent QA where applicable.

For a local authenticated read-only report, in a checkout:

```sh
GITHUB_TOKEN=... python3 tools/ops_live_status.py
GITHUB_TOKEN=... python3 tools/ops_live_status.py --format json --output /tmp/ops.json
python3 -m unittest tests.unit.test_ops_live_status
```

The token may be omitted for a limited public-API call, but the unauthenticated
rate cap may return HTTP 403. The tool does not print tokens or modify GitHub.
The workflow uses GitHub's built-in short-lived token with read-only permissions
and retains its machine-readable JSON artifact for seven days.

For recurring publication, **Agent 4** can review the newest exact-head status
in its existing integration slot and link the corresponding run from an
existing GitHub integration issue when useful. Do not introduce a sixth schedule
or open a PR merely to publish unchanged observations. The dashboard's
next upgrade should be a truly connected Drive and scheduler comparison,
not an invented count from a historical inventory.
