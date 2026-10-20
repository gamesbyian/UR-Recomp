# UR-Recomp recovery-vault intake and integration disposition (2026-10-20 UTC)

## Scope and immutable intake

Drive folder: `UR-Recomp Agent Recovery Vault` (folder ID `1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn`). A full folder listing with `top_k=1000` returned **340 top-level files**, **162,121,824 listed bytes**, and no child folders at this checkpoint. File types: 113 JSON, 77 ZIP, 73 patch/diff, 48 Markdown, 27 Python, 2 plain text. Two filenames occur twice, so **Drive file IDs**, not filenames, are the unique keys. See [the snapshot TSV](UR-VAULT-INVENTORY-20261020.tsv). This snapshot does not inventory files inside ZIPs or later additions; it is *not* a sign-off for all 340 files.

## Verified integration performed from this intake

- The Agent 3 H23 recovered two-line CI patch `20261020T2328Z-agent3-pr2060-native-windows-export-workflow-fix.patch` was independently matched against the actual `recovery/h18-records-latest-main-20261020` workflow at blob `9beae331c48e9b602d95d3e5d92ddb01d83bc53d`. **Commit `ee55e82bf79e5a5fd1d867d414cc0947763088bf`** on [PR #2060](https://github.com/gamesbyian/UR-Recomp/pull/2060) moves the earned-run output outside its immutable journey root and updates the artifact upload path. Readback blob `5adccdde03d3cb9a2791a37d44001462673bd086` contains both new paths and zero occurrences of the two old nested paths. No release gate granted; exact-head Windows CI was in progress when last checked.

## Independently inspected latest lane archives

Raw ZIP bytes were fetched and checked with Python `zipfile.testzip()`; all five had no duplicate member names and no CRC failure. All five bundles contained exhaustive SHA256 member manifests (Agent 3's was named `H23-MANIFEST.json`); actual member census, sizes and hashes were independently compared:

| Latest lane archive | Members | Declared payloads | Independent verdict |
| --- | ---: | ---: | --- |
| Agent 1 H23, `20261020T23-agent1-five-line-recovery.zip` | 95 | 94 | Exact declared census and member SHA256 matches |
| Agent 2 H20, `20261020T2007Z-agent2-h20-five-line-recovery.zip` | 31 | 30 | Exact declared census and member SHA256 matches |
| Agent 3 H23 v2, `20261020T2328Z-agent3-h23-five-line-recovery-v2.zip` | 29 | 28 | Exact `H23-MANIFEST.json` census and member SHA256 matches |
| Agent 4 H22, `20261020T223840Z-agent4-h22-five-line-recovery.zip` | 72 | 71 | Exact declared census and member SHA256 matches |
| Agent 5 H22, `20261020T2255Z-agent5-h22-five-line-recovery.zip` | 41 | 40 | Exact declared census and member SHA256 matches |

A valid preservation archive is not a shipping-code approval. In particular, Agent 2 H19's earlier archive has a *known inaccurate member manifest* (66 claimed payloads vs 35 actual; corrected external inventory exists); do not rely on that original manifest or overwrite provenance.

## Pending reconciliation decisions (source authority and tests first)

1. **PR #2060 / Modern Windows Records:** exact-head Windows CI and new exporter tests; conservative Win32 DOS-device whitespace, `CONIN$`/`CONOUT$`, surrogate and UTF-16-unit path rules still require review. The old Agent 5 H22 composite targets historical blob `98eccb71...` and **must not** be stacked onto the current exporter. Agent 3 H23/Agent 1 H23 recovery candidates also require new exact-head qualification; previous exporter/source publications encountered explicit platform safety denials. Never bypass or reframe denied writes.
2. **QA08 and QA06:** chronology, brightness high bit, all-matte/unique source coverage corrections exist in the latest H22/H23 bundles. Reconcile each against current QA sources and existing draft #1996; none proves genuine original/native PPU pixel consumption, physical 4K or artwork sign-off.
3. **CPU/QA01:** genuine RF081 sample-local WRAM/SRAM comparisons and nine-frame NMI sequence research remain evidence-only. The first causal instruction read and 45 complete-equivalent USA events are not established. Do not silently upgrade sampled results to release acceptance.
4. **P2P and Records/live video:** recover independent checkpoint/rollback audits, clock identity, presented-frame and device/PCM continuity tests as narrow pilots. SQLite does not provide an independently protected monotonic anchor; no complete peer networking or MP4 tap/encoder is evidenced.
5. **QA04, archive and knowledge tools:** source/test work and Windows path predicates need narrow review against canonical helpers. A committed source-only strict-vault branch `agent1/h22-strict-vault-manifest-20261020` still lacks denied test publication; do not merge it as-is.
6. **Previously denied and orphaned GitHub work:** [#2039](https://github.com/gamesbyian/UR-Recomp/issues/2039) tracks two separately committed source/test branches with denied PR creation; [#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711) tracks 99 historical PR-less refs. Their content requires semantic overlap checks rather than bulk cherry-picking. Latest hourly recovery attempts repeatedly recorded explicit safety denials; preserve the exact record.

## Safety, retention and closure

- **No Drive files have been deleted.** The vault is a recovery source and audit trail. File deletion requires matching exact content hashes to a reviewed accepted commit or a verified retained superseding archive, no unique evidence, current owner consent where applicable, and an independently recorded deletion decision. Superseded source patches may still contain valuable failure evidence.
- No ROM/binary evidence, source-bound captures, large dumps or potentially unlicensed assets were copied wholesale into the public repository.
- Preserve producer/independent QA separation, source identity, branch/PR head and workflow IDs. No 1/45 USA, 0/12 Windows, network, physical-device or art acceptance is self-awarded by this audit.
- Every row marked `not-verified-for-integration` in the TSV requires individual content disposition; **the TSV is an intake ledger, not evidence that every artifact has been reconciled**.
