# Independent audit of actual Windows smoke artifacts

Use tools/audit_windows_romfree_smoke_artifacts.py on the **original**
downloaded GitHub Actions ZIP artifact or artifacts. This consumer is
separate from Agent 1's producer in PR #2601; it never rebuilds the
executable or stages a new copy of private package data.

    python3 tools/audit_windows_romfree_smoke_artifacts.py \
      /private/downloaded-smoke-A.zip /private/downloaded-smoke-B.zip \
      --json-out /tmp/windows-audit.json \
      --markdown-out /tmp/windows-audit.md

Optionally provide --expected-source with a separately checked exact
40-character checkout SHA, and --expected-private-zip with an independently
approved 64-character inner private ZIP SHA-256. Absent pins report unknown,
never match. A sidecar in the public artifact is merely a producer's private
ZIP hash claim. The tool CANNOT inspect or authenticate the private full
portable package, the original ROM, a physical machine, player storage or
original/native parity.

The tool independently hashes the **actual staged executable bytes**,
original package manifest retained in the public archive, binding.json,
and source/checksum claims. It verifies MZ AMD64 PE32+, exact sizes and
canonical paths, rejects ROM-named files and unsafe ZIP paths, and detects
raw SRAM snapshots by count **without emitting their raw bytes**.
Saved-game bytes already in the existing smoke artifact require a separate
publication/rights review, even when the new staging subdirectory is
ROM-free. Never label the entire smoke artifact as containing no player
state on the strength of the binding's staged-subdirectory flag.

Multiple artifacts are compared without splicing identities. Distinct
executable hashes are **distinct build candidates**, even if a normalized
offline comparison finds that only COFF timestamp bytes differ. Distinct
private ZIP SHA claims are distinct candidate packages. Only one
independently nominated exact private ZIP/PE/source can feed the release
ledger at a time, and qualified L4/L5 original/native/hardware witnesses
must still be independently checked. No gate is promoted by this auditor.

Run the ROM-free negative tests locally or in existing tooling CI:

    python3 -m unittest tests.unit.test_audit_windows_romfree_smoke_artifacts -v
