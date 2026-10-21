# Recovery Vault folder layout and recursive reconciliation (2026-10-21)

**Source:** connected Google Drive folder `1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn`. This is a layout checkpoint, not a source/code acceptance signoff.

At the first independent listing after the 393-ID checkpoint, the root contained **399 direct children: 393 files plus 6 newly created folders**. Every new folder was independently listed with `top_k=1000` and returned **zero direct children** at the checked instant. Therefore no file was missing from the 393-file ID ledger because of these directories at this checkpoint.

| Folder | Exact Google Drive folder ID | Direct children at checkpoint | Required disposition |
| --- | --- | ---: | --- |
| 00 Integration Inbox | `1iq2MP6yzsMK6f-0VIhIUL43IfIL6GT3o` | 0 | Incoming candidate, **not** integrated merely by placement |
| 01 Work Journals | `1QvlB3V-aa8so0HPx_1dTcV8jL9TeD3kr` | 0 | Preserve progress, failures, head/blob and source identities |
| 02 Incoming | `1cdovDqle9IRYKX2lCt513mtWge75HywX` | 0 | Must traverse for unreviewed new arrivals |
| 03 Evidence Library | `1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2` | 0 | Preserve source/QA evidence; hashes do not grant release credit |
| 04 Integrated | `1deqU6Z6IdeudIVvfCmXggW8gV3JRGqsU` | 0 | Verify GitHub blob/commit and test receipts, never trust folder name alone |
| 05 Superseded and Rejected | `1XuTGwAE7zsMhw20mvSPm3WYX94PiNxhY` | 0 | Preserve rejected proposals and negative findings; never republish via evasion |

## No-loss recursive procedure

1. List the root and **all** discovered child folders, including newly created nested folders. Track each file by immutable Drive ID and the parent folder path(s), not basename alone; the historical H10 ZIP has two different IDs with matching bytes.
2. Compare the resulting recursive file-ID set with [the initial 340](UR-VAULT-INVENTORY-20261020.tsv), [H23 14](UR-VAULT-DELTA-H23-20261020.tsv), [H24/H25 25](UR-VAULT-DELTA-H24-H25-20261021.tsv) and [late H25 14](UR-VAULT-DELTA-H25-20261021.tsv) exact-ID intake snapshots. Files moved between folders stay the **same Drive ID**; a root-only drop is not evidence of deletion.
3. Distinguish **preserved**, **source-exact integrated**, **semantic superseded**, **intentional hold**, **physical acceptance pending**, and **not yet audited**. Keep full member-level provenance, including duplicates and failed/rejected approaches. Do not infer disposition from names such as `Integrated`.
4. Only consider deleting an artifact after a per-ID reviewed integration/retention proof: matching authoritative GitHub blob+commit or fully hash-verified retained source archive, no unique negative evidence or citation dependency, no outstanding audit hold or explicit safety rejection needing preservation. Until then, **retain**.
5. For new ZIPs, screen filenames without extraction, verify archive integrity, compare complete manifest member names/lengths/SHA-256 when available, and explicitly label partial manifest/recursion gaps. Historical safety denials are not transient errors; do not route around them.

The [87-ZIP census](VAULT-87-ZIP-CONTENT-CENSUS-20261021.md) covers 3,740 observed member occurrences across the root ZIP corpus *before* the folder move-in operation. It does not claim that 3,740 members were individually merged, and it must be refreshed if any existing ZIP is moved into or replaced inside a subfolder. No Drive files or branches were removed by this layout audit.
