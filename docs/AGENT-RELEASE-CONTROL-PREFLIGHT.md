# Agent release/integration preflight

This is an opt-in read-only view, not a second assignment queue, release
authority, automatic PR merger, CI dispatcher or ROM distribution workflow.

Run from an authenticated checkout with read-only GitHub access:

    python3 tools/agent_release_control.py --live --lane release-qa --gate QA-04 \
        --json-out /tmp/agent-control.json --markdown-out /tmp/agent-control.md

The script requires an authenticated gh CLI. It collects fresh main and up
to 25 open PRs, each exact-head status, file names and GitHub mergeability,
a bounded recently closed sample, and rechecks main and each PR head.
No guest logs, binaries, ROMs or player files are fetched. Incomplete file
or PR listings are explicitly labelled unknown. Changed-path overlap
is a collision hint, NOT a Git merge conflict. Passing observed checks do
not prove that branch-protection-required checks are satisfied. Only the
hourly board and independent Agent 5 authorize shared integration work.

For a saved offline GitHub snapshot, use --snapshot PATH instead of --live.
For optional exact-main diagnostic receipt reuse, pass --receipt-db PATH.
That database is built by tools/index_ci_receipts.py. Its source-bound
unit/fanout rows are producer receipts, never independent release proof;
missing rows do not establish that no historic evidence exists. The
underlying index has no artifact expiration authority. Check original
Actions artifacts before assuming downloads remain available.

For measured CI cost, add --ci-runtime-report PATH using the JSON from
tools/report_ci_runtime.py (the existing manual ci-runtime-report.yml).
Missing job timing makes runner seconds a lower bound. Partial run samples
cannot support whole-week cost or speedup claims. Recently merged PR
turnaround is likewise a sample, NOT useful engineering closure.

For an actual independently nominated candidate, the existing manual
windows-acceptance-fanout-pilot.yml can run a shared build and its 13
original hosted Windows journeys at an explicitly checked source. That
workflow does not constitute a full private shipping ZIP, original/native
USA-event parity, or QA-04 physical controller/audio/display testing.
The source and full private inner ZIP must be separately qualified by the
release owner; no auto-dispatch or acceptance is performed here.

Run source-only regression checks:

    python3 -m unittest tests.unit.test_agent_release_control -v

The result is deliberately advisory: re-read the live hourly board and
owning PR, identify the smallest missing witness, run only a decision-
changing test, and route fixes to their specialist and Agent 5.
