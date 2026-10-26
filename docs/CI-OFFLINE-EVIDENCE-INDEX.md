# Offline CI evidence lookup pilot

This opt-in SQLite index helps future agents find previously ingested producer
receipts by **exact 40-character source commit**, without mirroring logs,
profile data, ROM, SRAM or private input paths. It accepts exactly the
`UR-CI-UNIT-RESULT/1` and `ur-win32-acceptance-fanout-aggregate/2`
machine receipts. Everything is **local, explicit-input, offline, read-only
toward the source receipts**, with bounded size and a whitelist of indexed
fields. Digests are content identifiers, not provenance signatures.

Example:

```sh
python3 tools/index_ci_receipts.py ingest --db /private/ci-index.sqlite3 /private/receipts/*.json
python3 tools/index_ci_receipts.py query --db /private/ci-index.sqlite3 --source-sha FULL40CHARCOMMIT
```

The index stores only schema, SHA256 of original receipt bytes, source SHA,
bounded result category, expected/observed population, failed/missing counts,
and fixed zero release-gate credit. Any unknown schema, malformed identity,
fabricated physical acceptance or attempted release promotion refuses import.
All inputs are validated before creating the index for a batch; duplicates are
idempotent. Source receipts may include private or additional fields but
**none are saved in the SQLite database**. Treat that database as a local
derived lookup, not an archived attestation.

Next optional extension: source-qualified, privacy-reviewed adapters for
other existing evidence types, only when real repeated lookup justifies one.
No automatic crawling, GHA dispatch, release-gate mutation, or unbounded JSON
document storage. The authority remains the source archive and
`docs/RELEASE-QUALITY-LEDGER.json`.
