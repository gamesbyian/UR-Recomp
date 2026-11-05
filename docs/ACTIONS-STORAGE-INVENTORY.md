# Account-wide GitHub Actions artifact storage inventory

Use the **read-only** `tools/actions_storage_inventory.py` utility to rank retained
artifact bytes across `gamesbyian` repositories. This complements the
**source-bound, single-run** `tools/artifact_retention_preflight.py`;
the two tools answer different questions.

Requirements: Python 3.10+ and a GitHub CLI (`gh`) session with permission to
read Actions artifacts in the target repositories. Authenticate with
`gh auth login` outside the script. No token values or contents are printed.
The script never invokes deletion and never downloads artifact bytes.

```shell
python3 tools/actions_storage_inventory.py --owner gamesbyian --json-out storage.json
python3 tools/actions_storage_inventory.py --repo gamesbyian/Chunks --repo gamesbyian/Glimpse
python3 -m unittest tests.unit.test_actions_storage_inventory
```

The report is a **complete-or-error** inventory. It rejects truncated or
inconsistent pagination rather than presenting a partial scan as a storage
total. GitHub's `size_in_bytes` is a metadata-based *compressed size estimate*,
not a measurement of the account's **accrued billing GB-hours**; current storage
and previously accrued usage are different quantities.

When reviewing large artifact families, first identify exact run/source,
artifact consumers, release dependencies and irreplaceable original/Windows
research evidence. Retain qualified evidence in a durable versioned store
with digests and provenance **before** making a deletion recommendation.
A recent successful build does not automatically replace the evidence of a
different input or failed native state. Existing `artifact_retention_preflight.py`
performs source-specific checks; this account report does not.

GitHub's artifact deletions are **irreversible**. This utility deliberately
does not have a `--delete` switch, does not need Actions write permission, and
must not silently promote candidates into automatic cleanup. For new upload
steps use explicit `retention-days` appropriate to evidence importance
rather than relying on the public-repository default of 90 days.

Ref: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts
