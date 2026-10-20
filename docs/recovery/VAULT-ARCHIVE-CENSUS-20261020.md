# UR-Recomp Recovery Vault: independent ZIP preservation census (2026-10-20)

This is a **static, source-independent preservation check**, supplementary to the [340-item vault intake](VAULT-RECONCILIATION-20261020.md). It is not code acceptance, exact-platform QA or permission to delete archives.

The Drive snapshot contained **77 ZIP records**. An independent local read of **75 distinct ZIP filenames** was completed. One historical ZIP filename (`20261020T110232Z-agent1-h10-five-line-recovery.zip`) occurs under two different Drive IDs and cannot be treated as one verified Drive record merely because an automatic local mount reused the filename. The remaining record-level difference remains unqualified; do not report 77/77. No source bytes were extracted into GitHub.

## ZIP-level audit

| Property | Observed among 75 local archives |
| --- | ---: |
| ZIP member occurrences | 3,238 |
| Archives with ZIP CRC failures | 0 |
| Archives with duplicate internal member names | 0 |
| Archives with absolute or parent-traversal member paths | 0 |
| Archives with Unix symlink members | 0 |
| Archives with a recognized full SHA-256 manifest and no unlisted members | 45 |
| Archives with a recognized SHA-256 manifest that did not cover every ZIP member | 9 |
| Archives without a recognized complete-member manifest under the audited schema names | 21 |
| Declared member hashes or byte lengths mismatched among audited manifests | 0 |
| Manifest declarations referring to nonexistent members | 0 |

Several H09–H22 archives use `MANIFEST-Hxx.json`, `Hxx-MANIFEST.json`, `PATCH-MANIFEST.json` or nested manifest conventions. The 21/9 split above uses a deliberately conservative detector: a patch-only manifest is not accepted as a complete archive inventory, and an absent recognized manifest does **not** mean the ZIP is corrupt. For example, Agent 5 H20 declares its patch payloads but does not include `HANDOFF.md` in its top-level member inventory. Agent 2 H19 has a historically known inaccurate full manifest; its independent corrected member census takes precedence for that specific artifact. Preserve both the original and the correction.

## Independent RF081 evidence control

From the SHA-256-pinned genuine original/native archive `df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37` nested within the latest H23 recovery: 44 matched WRAM binary pairs of 131,072 bytes, 44 matched SRAM pairs of 8,192 bytes, no unmatched pair members. **17 of 44 WRAM pairs differ, with 82 differing-byte occurrences total; all 44 SRAM pairs match exactly.** Of those WRAM differences, 15 are scene snapshots, each limited to offsets 493–496 (`0x01ED–0x01F0`); two result-stage snapshots differ at more offsets. These observations say nothing about equivalence between sparse snapshots or the first causally consumed CPU divergence. No USA event or Windows QA gate is awarded.

## Retention and next actions

1. Identify and independently hash both Drive IDs sharing the historical H10 ZIP filename before classifying either as redundant. Check exact cross-references before even considering deletion.
2. For every archive with a partial, alternate or missing member inventory, retain the raw original; normalize its actual-member SHA list in a separate, verifiable receipt rather than rewriting it.
3. Merge only narrow current-main source/test deltas after licensing/provenance review, duplicate/semantic overlap screening and exact-head CI. Never stack old PR #2060 exporter composites or the older QA08 composites on a newer head.
4. Do not retry or work around explicit historical platform safety denials for source/file/PR publication. Keep those candidates on the original GitHub branches and in Drive for legitimate later review.

**Deletion verdict: NONE.** All Drive originals stay intact until each item has independent, recorded retention/integration coverage.
