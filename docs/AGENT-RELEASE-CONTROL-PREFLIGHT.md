# Agent release/integration preflight

This is an opt-in read-only view, not a second assignment queue, release
authority, automatic PR merger, CI dispatcher or ROM distribution workflow.

Run from an authenticated checkout with read-only GitHub access:

    python3 tools/agent_release_control.py --live --lane release-qa --gate QA-04 \
        --json-out /tmp/agent-control.json --markdown-out /tmp/agent-control.md

The script reuses the canonical read-only Python GitHub API reader in
`tools/ops_live_status.py`, using `GH_TOKEN` or `GITHUB_TOKEN`
for authenticated access. No separate gh CLI is required. It collects fresh main and up
to 25 open PRs, each exact-head status, file names and GitHub mergeability,
a bounded recently closed sample, then rechecks the entire selected PR\nhead/draft/base census and main before reporting. A mid-scan PR update\nrefuses the report; no stale green head is presented as current.
No guest logs, binaries, ROMs or player files are fetched. Incomplete file
or PR listings are explicitly labelled unknown. Changed-path overlap
is a collision hint, NOT a Git merge conflict. Passing observed checks do
not prove that branch-protection-required checks are satisfied. Only the
hourly board and independent Agent 5 authorize shared integration work.

For reproducible offline review, add `--snapshot-out /private/observation.json`
to a **live** command. It records the exact GitHub main SHA, observed PR
heads and checks, population completeness and closed-PR sample without
credentials or raw artifacts, and refuses to overwrite an existing snapshot.
Then use `--snapshot /private/observation.json` instead of `--live`.
**Both modes require the same clean local Git checkout at the recorded main
commit** before reading the release ledger. To replay an older snapshot,
check out its exact original source commit first; never join a historical
GitHub census to a newer ledger. The repository identifier must also match.
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

Alternatively, after this tool merges onto main, run the **existing** manual
Agent control and recovery contract GitHub Actions workflow with
`live_preflight=true`. The new manual-only step renders the read-only
report into the GitHub Actions Job Summary using the runner's read-only
GitHub token. Ordinary PR/push validations never execute the live scan;
that step has no rights to edit branches, Actions or release ledgers.
A workflow-dispatch run cannot prove current-main agreement if main moves;
the command detects and fails on that exact-source mismatch.

For release progress across two exact-source checkouts, supply
`--previous-brief /private/earlier-release-brief.json`, produced from
the separately checked old checkout with `tools/release_evidence_brief.py
--source-sha EXACT_OLD_COMMIT --json-out FILE`. The combined preflight
uses the existing fail-closed `tools/release_evidence_delta.py` schema to
report whether ledger bytes and tracked gate metadata changed and how many
statuses say passed before/after. This is a change in **recorded metadata**,
not independently reauthenticated evidence or an acceptance award. It is
displayed *separately* from merged PR count, so agent throughput cannot be
confused with product or QA completion. A baseline without an exact checked
source is rejected.


## Connect existing artifact metadata to the live agent preflight

For **one exact main or currently open PR head**, use the already merged
retention inspector and pass its JSON to the live agent preflight:

    python3 tools/artifact_retention_preflight.py --live-run-id RUN_ID \
      --expected-sha EXACT_MAIN_OR_OPEN_PR_HEAD --json-out /tmp/retention.json
    python3 tools/agent_release_control.py --live --lane ci \
      --artifact-availability /tmp/retention.json

The join refuses mismatched/missing source identities, foreign schemas,
release-credit claims, and a source absent from the current main/open-PR
census. It reports per-artifact next actions rather than a generic list:
byte-inspect qualifying original artifacts, urgently request authorized
rights-safe preservation, refresh aged metadata, or investigate a failed
producer/partial listing. Metadata older than 60 minutes is stale, even
when the historical API reported an available artifact. Check the original
GitHub run and repository when consuming saved JSON because a source SHA
alone does not authenticate repository custody.

A matching, fresh, complete metadata entry **only** indicates that the
original artifact may be available for independent download, digest
verification and executable/inner-ZIP provenance inspection. It does
not establish that bytes have been inspected, that GitHub still serves
them, that the workflow head equals a packaged PE, or that any gameplay,
hardware or release QA gate passed. This remains a read-only route with no
automatic CI dispatch or private ROM/player/SRAM upload.


## Optional original-byte Windows artifact qualification

When the original public `windows-native-smoke` Actions ZIP is already
downloaded, preflight joins three separate identities without conflating them:

    python3 tools/artifact_retention_preflight.py --live-run-id RUN_ID \
      --expected-sha EXACT_GITHUB_RUN_HEAD --json-out /tmp/retention.json
    python3 tools/agent_release_control.py --live --lane ci \
      --artifact-availability /tmp/retention.json \
      --romfree-archive /private/retrieved-windows-native-smoke.zip

This invokes the existing independent ROM-free auditor directly. It checks
canonical ZIP structure, **every retained member's CRC**, AMD64 PE, executable
digest, original public binding and manifest, and the private full ZIP digest
**claim**. The actual downloaded outer SHA256 and byte length must match
exactly one artifact in the saved original GitHub run metadata; missing,
duplicated or inconsistent metadata is rejected.

The report keeps the GitHub run-head SHA, separately claimed original
build-checkout commit, staged PE hash and private ZIP digest claim distinct.
A synthetic PR merge build can differ from its run head. Such a PE cannot be
reused as exact PR-head/main bytes by assertion; the report directs source
review. A verified downloaded archive may exist even after its availability
metadata grows stale, so byte inspection and API availability are reported
separately.

The private playable ZIP is **not** inspected, downloaded or authenticated.
This remains zero independent release, original/native, hardware or gameplay
acceptance. Do not inspect/publish ROM, save-state, player or restricted
test data through this route.
