# UR-Recomp Recovery Vault: complete mounted-ZIP integrity census and H25 holds

**Checkpoint:** 2026-10-21 01:50 UTC. [The 14-ID intake](UR-VAULT-DELTA-H25-20261021.tsv) supplements the [340-file baseline](UR-VAULT-INVENTORY-20261020.tsv), [H23 14-ID delta](UR-VAULT-DELTA-H23-20261020.tsv), and [H24/H25 25-ID delta](UR-VAULT-DELTA-H24-H25-20261021.tsv). Exactly **393 distinct top-level Drive IDs** were listed at this checkpoint (340 + 14 + 25 + 14). This does not count ZIP members as Drive records, and it is not a continuously updated value. Preserve all originals.

## Full mounted ZIP inspection

The Drive folder had **88 ZIP records across 87 different names**, because `20261020T110232Z-agent1-h10-five-line-recovery.zip` has two Drive IDs. Both IDs were previously independently fetched and yielded identical 6,127,510-byte, SHA-256 `586e6c9055623e60c98de2bf5c9d8b6c48c1df2be8a56e0da4e1e669c08aa0e5` files. This does not automatically authorize deleting either historical ID.

All **87 distinct locally available ZIP filenames** (191,014,224 aggregate bytes) were examined via Python `ZipFile.testzip()`, member name census and compressed member reads without extraction. The scan observed:

| Preservation property | Result |
| --- | ---: |
| Distinct archive filenames read | 87 |
| ZIP member occurrences (including archive manifests and nested ZIPs as opaque members) | 3,740 |
| Distinct member-name strings across archives | 2,593 |
| Distinct member SHA-256 digests across archives | 2,163 |
| Digests seen in just one archive-member occurrence | 1,509 |
| Digests appearing two or more times | 654 |
| ZIP CRC failures | 0 |
| Archives with duplicate internal member names | 0 |
| Archive members with absolute/drive-prefixed/parent-traversal paths | 0 |
| Archive members marked as Unix symlinks | 0 |
| ZIPs that could not be opened/read | 0 |

**Cautions:** A SHA-256 seen once is only unique **within the inspected ZIP member corpus**, not proof that GitHub or a standalone Drive file lacks its content. ZIP CRC and absence of unsafe names prove byte-level preservation, not that arbitrary source inside has passed tests, licensing, policy, or same-epoch release QA. Nested archives counted as members were **not automatically recursively source-certified** here. Earlier H19 full-manifest exceptions and partial/alternate manifests remain explicit. No archive was extracted to a shipping repository.

The most recent Agent 5 H25 recovery `20261021T0150Z-agent5-h25-five-line-recovery.zip` (Drive ID `1rFARJznFkWQpOl-mNSPEi5Ix-4d2Yb76`, outer SHA-256 prefix `e11d61a18184`) additionally has 30 ZIP entries; every one of its 29 declared `MANIFEST.json` payloads matches the exact member name, byte length and SHA-256. Its recovered QA08 cumulative patch and additive UHD/P2P/CI pilots remain **unpublished** following recorded explicit safety denials for comparable source changes. Preserve them for permitted, source-specific reconciliation. Its QA08 12-model chromatic probe is a proposed experiment, not observed native effective PPU chromatic parity.

## Content-addressed integration performed

- [#2081](https://github.com/gamesbyian/UR-Recomp/pull/2081) merged the nine-frame RF081 NMI source-local sequence-gap audit; current `main` source Git blob `bbd0240abacb250717acd23b7dabb06f14f027f9` matches the exact Agent 1 H25 recovered source. Six repo-safe tests were added. Independent archived 12-test normal/optimized runs used the genuine SHA-256-pinned RF081 archive.
- [#2082](https://github.com/gamesbyian/UR-Recomp/pull/2082) merged the selected-PC candidate census; current `main` source Git blob `9e0f084860691abdac464f55688438dba4b16e41` matches the Agent 1 H23 archived source. Six repo-safe tests were added and the original six-test suite passed locally against the genuine archive. Four differing / five matching selected PC **labels** do not establish same-instruction-phase parity or first causal divergence.
- Earlier [#2078](https://github.com/gamesbyian/UR-Recomp/pull/2078) merged separate RF081 WRAM/SRAM sparse snapshot tools; its 82 differing WRAM bytes and zero differing SRAM bytes are diagnostic, not continuous event proof.
- Prior [#2071](https://github.com/gamesbyian/UR-Recomp/pull/2071), [#2072](https://github.com/gamesbyian/UR-Recomp/pull/2072), [#2073](https://github.com/gamesbyian/UR-Recomp/pull/2073) and [#2074](https://github.com/gamesbyian/UR-Recomp/pull/2074) integrated bounded OBJ evidence tooling, integer-overflow safety and original Dragster source/cross-reference. See [historical orphan reconciliation issue #1711](https://github.com/gamesbyian/UR-Recomp/issues/1711).

## Intentionally held rather than stranded

- **PR #2060 Windows Records:** later Agent 3 H25 recovered an exact-head source-staging mutation race. DOS-device / C1 / DEL filename controls and fresh same-merge-base CI still need source-owner verification. Historical hosted green runs do not qualify new patches or physical NTFS. No blind PR merge.
- **QA04 attachment provenance:** [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076) holds a checked-path-to-reopened-file race; a POSIX file-descriptor experiment is not equivalent to a Windows reparse-safe handle implementation.
- **Vault verifier filenames:** [#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075) holds independently reproduced Win32-unsafe member alias controls; historical similar source writes were explicitly denied.
- **QA08 graphics:** [draft #1996](https://github.com/gamesbyian/UR-Recomp/pull/1996) remains held. Genuine samples are grayscale with four distinct colours; proposed chromatic tests do not replace an original/native effective-CGRAM and consumption witness. Do not publish overlapping historical patches atop one another or award art approval.
- **P2P, UHD, presented media and CI pilots:** preserve the complete H24/H25 manifests, patches, tests, logs and failure evidence. SQLite rollback-safe external trust, real P2P, host capture/MP4, physical 4K and native Windows acceptance remain unproven.
- **Historical GitHub branches:** [#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711) identifies byte-identical, semantically superseded and unreviewed PR-less refs. The recovered source and negative tests are individually adjudicated; a branch ahead/behind count does not prove missed content.

## No-loss retention rule

**Deletion disposition: zero files eligible.** Each Drive ID and each unique or superseded member must have a recorded mapping to a reviewed GitHub commit, a hash-verified retained evidence copy, or an explicit intentional hold with rationale. A newer recovery ZIP, a matching filename, a duplicated byte hash or a successful unit test alone is insufficient to close that mapping. Previously denied source publications are retained without retrying or disguising the denied action. Preserve raw evidence and negative results even after the relevant code lands, unless an independently verified retention policy explicitly covers them.

This is a **preservation census, not 3,740 completed semantic merge decisions**. Further per-member content disposition and eventual human/physical source verification remain needed; no 1/45 original/native USA or 0/12 Windows release-gate numbers are upgraded here.
