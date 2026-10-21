# Daily mobile operations snapshot

The existing [Live operations snapshot](https://github.com/gamesbyian/UR-Recomp/actions/workflows/ops-live-snapshot.yml)
runs **once per day** at 14:30 UTC (07:30 in Alberta's winter MST, 08:30
in summer MDT). You may still use GitHub's **Run workflow** at any time.
No sixth ChatGPT agent, separate subscription, GitHub write token, repository
commit or email notification is added.

The scheduled job is the existing five-minute-capped, read-only GitHub API
report, with a bounded seven-day artifact lifetime. It preserves the exact
observed SHA and refuses to conflate the latest 100 Actions runs with a
24-hour census or billable runner minutes.

The recorded [Drive main-history backup](main-history-custody.json) is an
independently verified **historical** recovery point. The snapshot marks it
stale relative to observed main whenever the SHAs differ. Drive's *current*
file contents, scheduled-agent activity, physical Windows tests, original
game acceptance and art approval remain **unknown** unless actually
verified by their distinct authorities.

Scheduled GitHub Actions are best-effort and may be delayed or not run
during GitHub outages/inactivity. The dashboard's observation timestamp is
therefore authoritative for freshness. A missing recent snapshot is a
missing observation, **not** evidence that the five agents stopped working.

This workflow exists to reduce phone effort and report operations health.
If it becomes redundant with a verified existing daily agent summary, retire
the new `schedule` trigger rather than doubling instrumentation.
