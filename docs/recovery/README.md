# UR-Recomp recovery entrypoint

**Purpose:** reconcile the Google Drive [Agent Recovery Vault](https://drive.google.com/drive/folders/1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn) with current GitHub `main` without losing unique source, negative evidence, rejected publication history or owner/physical acceptance obligations.

## Inventory (append-only, by exact Drive ID)

- [Initial 340-ID census](UR-VAULT-INVENTORY-20261020.tsv) and [baseline decisions](VAULT-RECONCILIATION-20261020.md)
- [H23 14-ID supplement](UR-VAULT-DELTA-H23-20261020.tsv) and [H23 evidence](VAULT-H23-ADDENDUM-20261020.md)
- [H24/H25 25-ID supplement](UR-VAULT-DELTA-H24-H25-20261021.tsv) and [archive/test adjudication](VAULT-H24-H25-RECONCILIATION-20261021.md)
- [Late H25 14-ID supplement](UR-VAULT-DELTA-H25-20261021.tsv), [87-ZIP 3,740-member content census](VAULT-87-ZIP-CONTENT-CENSUS-20261021.md)
- [Six new folder IDs and required recursive traversal](VAULT-RECURSIVE-LAYOUT-20261021.md). At that checkpoint the 393 files remained in root and the new folders were empty; **do not use root-only listing as a permanent total**.

These are checkpoint inventories, not a static live count. File moves preserve the Drive ID. The two historical same-name H10 ZIPs have different Drive IDs even though separately verified byte-identical. Never use filename or folder placement as an integration/delete verdict.

## Integrated by exact source or bounded semantics

- [#2089](https://github.com/gamesbyian/UR-Recomp/pull/2089) **MERGED** at `a3ae40508915889ff22ba728f0243d4a40d6959b`: fresh-main six-file Windows Records exporter/CI recovery, successful exact-head unit/hygiene/native Windows checks, and 6/6 source blobs equal to the former [#2060](https://github.com/gamesbyian/UR-Recomp/pull/2060), now **CLOSED UNMERGED** as superseded. H25 staging-race/name hardening held; no physical Windows gate.
- [#2071](https://github.com/gamesbyian/UR-Recomp/pull/2071) OBJ-depth evidence-only verifier and controls, **merged**.
- [#2072](https://github.com/gamesbyian/UR-Recomp/pull/2072) overflow-safe Modern text layout and tests, **merged**.
- [#2073](https://github.com/gamesbyian/UR-Recomp/pull/2073) original Dragster result witness and tests, **merged**; [#2074](https://github.com/gamesbyian/UR-Recomp/pull/2074) ties it to marshal authority without same-input parity, **merged**.
- [#2078](https://github.com/gamesbyian/UR-Recomp/pull/2078) RF081 sparse WRAM/SRAM census, **merged**; [#2081](https://github.com/gamesbyian/UR-Recomp/pull/2081) nine-frame NMI sequence-gap analyzer and [#2082](https://github.com/gamesbyian/UR-Recomp/pull/2082) selected-PC candidate census, **merged**, each with source-exact archived Git blobs and ROM-free regression tests.
- [#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711) owns individual historic PR-less ref dispositions, including byte-identical code, semantically superior current implementations, recovered tests and intentional holds. **Do not bulk cherry-pick or delete historical refs.**

## Active holds and release boundaries

- [#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075) ZIP portability verifier Win32 aliases/Unicode;
  [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076) QA04 validated-path/reopened-file TOCTOU.
- [#1996](https://github.com/gamesbyian/UR-Recomp/pull/1996) QA08 chromatic/source-PPU provenance remains draft/HOLD, with an earlier explicit source-publication safety denial. Do not retry denied writes or stack old composites.
- H24/H25 P2P signed SQLite trust, UHD raster-comparison, presented-frame/audio and CI merge-epoch source proposals remain **research-only** unless an independently authorized owner publishes narrow current-head source plus tests.
- No complete original/native USA events, physical Windows acceptance, release gate or art likeness approval was granted by this archive audit. Do not infer it from a synthetic test or folder named `Integrated`.

## Every artifact needs a disposition

For each exact Drive ID and useful inner member, record one of: **source-exact integrated (commit+blob+tests), semantically superseded (evidence), preserved research/negative finding, source publication denied (do not bypass), physically pending, or unreviewed**. A complete SHA member manifest proves preservation, not current-source integration. Never delete until a separate per-ID review shows zero unique dependencies and identifies authoritative retained copies. If an item has not received that review, **keep it**.

This is a living index for future recovery passes. When the vault changes, first traverse the root and all nested folders, then add a new immutable ID delta rather than overwriting historic snapshots.

## Current GitHub-first recovery practice

Follow the [publication runbook](GITHUB-FIRST-PUBLICATION-RUNBOOK.md). An invocation-level safety-check block is not proof that source code is permanently invalid. Preserve original errors and artifacts; do not repeatedly resubmit a blocked operation to evade the check. Future runs independently re-evaluate current GitHub state and permissible publication options. Ordinary transport/API failures get bounded fresh-HEAD retries. Successful GitHub work does not need Drive status mirrors.

**RF081 H26:** [#2099](https://github.com/gamesbyian/UR-Recomp/pull/2099) merged at `8a38454f3edd1a493101258d6f9e42f9f17c1afd` after unit and hygiene success. Original wake-PC and stack coherence guard/tests came from Agent 1 H26 Vault archive ID `1kULfQIJSV-YJ1lwWBPJAnH6iLtzt5W9d`. Remaining H26 P2P, QA04, QA08 and UHD proposals are not integrated by that PR; no QA gate or physical credit.


## Latest H27 Vault source and issue crosswalk (2026-10-21 UTC)

- **[#2110](https://github.com/gamesbyian/UR-Recomp/pull/2110) MERGED**, squash `5cdbbc57dc991d77df10c1a2ecabab2772c8063c`: source-bound **QA01 nonmonotonic sparse-transition bounds**, with exhaustive ROM-free endpoint regression tests and green exact-head unit/hygiene. Archived 41 genuine WRAM-pair fixture independently passed 6/6 normal and 6/6 optimized earlier. QA01 original source ZIP Drive ID `1DHRV4082CWJ7YLxicGR20CINyWwFEc8N` SHA-256 `f902f821a1e89d11c660343c91ba0be0035ab805b6b832677bcea41b134af8a6` verified 7/7 members and moved Incoming to Integrated **as a bounded source/test recovery**, while private sampled WRAM research and USA event acceptance remain separate.
- **[#2109](https://github.com/gamesbyian/UR-Recomp/pull/2109) MERGED**, squash `2c6a6ef6b7b42d9416cb9e3070565e042fb807bd`: corrected historical #2060 open/closed misstatement in the work-ID continuity register, catalogued H27 unresolved candidates. #2060 is CLOSED UNMERGED after #2089 source recovery.
- **[#2111](https://github.com/gamesbyian/UR-Recomp/issues/2111) OPEN**: distinct H27 P2P signed-invite/finish replay-token commit research. Drive ZIP `1cW_qjnxY8mfclORRfSCIHkQbenhZ4XcO` verified 7/7, local loopback tests independently 4/4 normal + 4/4 optimized; underlying source-publication tool check blocked and source is not in main. No WAN/NAT or trusted rollback claim. Earlier #2022 owns a separate revocation-sequence barrier.
- **[#2103](https://github.com/gamesbyian/UR-Recomp/issues/2103) OPEN**: Records Windows colon/ADS namespace sibling negative; Win32 source/hardware review still needed. H25 exporter publication race remains an independent research hold.
- **H27 Knowledge source holds**: Agent 3 source-epoch classifier Incoming ZIP `1p99v0BHznh173DpXFDwj0Yr8Q1ZmBTsX` authenticated 14/14 with 8/8 normal and optimized; Agent 4 malformed-lane guard ZIP `1_RScoARFTHjfttOY87v9PKBepXmE8tK8` authenticated 9/9 and eight isolated guard fixtures. Both exact source writes safety-blocked and remain unpublished; their unique Inbox pointers stay until authorized disposition. These are distinct from merged #2104's duplicate capability-matrix ID guard.
- **H27 QA08/PPU source hold**: Agent 5 temporal original-anchor census ZIP `1wW_zP28K8OWA--3UMLX4Yc2_VuIVOgSq`, SHA `25b0c7c00380d43f1e6f7edcac5163614ecf0a1841fff09cf37e8e2049065be0`, independently verified 12/12 members and 6/6 normal + 6/6 optimized ROM-free tests. A source `create_file` safety check blocked the exact research proposal; Inbox pointer remains. Its 11 original-only frames and phase transitions are **not** native final-pixel/effective-CGRAM parity; #1996 remains draft/HOLD.

The historical Agent 2 H27 five-work-ID pointer `1ya49XDmwKyRkpj9aX1Q3EmmAAFPbcl3B` moved from Integration Inbox to Evidence after its individual topics were either merged (#2102/#2104/#2110) or received durable issues (#2103/#2111). **No files deleted.** The [member-level reconciliation issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) remains open for older and nested archives; counts of stored digests must never be equated with actionable or unmerged implementations.

## Historical GitHub write-failure triage (2026-10-21)

Do not equate all historical failures with permanent policy decisions. The [coordination protocol](../AGENT-COORDINATION.md) now requires the **original error response** and classifies each unresolved operation as technical-retryable, source-conflict, explicit-safety-denial, unknown or already resolved in main. Ordinary transient failures warrant bounded attempts using fresh HEADs. Explicit safety denials remain restricted and must not be repeated via alternate publication routes. If the original response was not independently retrieved, retain UNKNOWN rather than trusting a handoff label.

- [#2039](https://github.com/gamesbyian/UR-Recomp/issues/2039): **RECOVERED EXACT**, despite historical write-denial reports and divergent branch ancestry. QA04 candidate verdict historical head `2a0ffd7fd75a272f762ae54fb8429fb65db3a87f` matches current `main` source/test Git blobs (`7a47167c003c71454894f8c3ca4cb0151f80f112` / `b9a7460da8f031d080fe815d379bca6e1fc64084`); [#2046](https://github.com/gamesbyian/UR-Recomp/pull/2046) was merged. P2P independent monotonic anchor historical head `c3c0d8c7aba27ed579f1c47ea395421750dc0891` likewise matches current source/test blobs (`48ca0e21c372166ab4f3386225f43c67a7c70edd` / `3fd34595e37dbb9e3f2443ae6ea30d726a6f525c`). Both source/test pairs were freshly rechecked; do not reapply. These proofs show code integration, **not** physical QA04 acceptance or trusted P2P anti-rollback.
- [#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075): strict vault ZIP Win32 portability source publication previously reported safety-denied. The original raw error has not been recovered here; bug still open. No source repost.
- [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076): QA04 TOCTOU source publication previously reported safety-denied; original raw error not recovered here. POSIX proof does not qualify Windows fix. No source repost.
- [#1996](https://github.com/gamesbyian/UR-Recomp/pull/1996): QA08 draft/HOLD and historical reported source denial, independent original/native final-pixel proof absent. Preserve hold.
- QA09 read-only admission source was **later recovered through merged [#2066](https://github.com/gamesbyian/UR-Recomp/pull/2066)**, squash `15b7cb7b22ac78c862bab98193dc904de22cba41`; do not retry its original failed publication.
- Windows Records exporter [#2060](https://github.com/gamesbyian/UR-Recomp/pull/2060) is **already recovered** by [#2089](https://github.com/gamesbyian/UR-Recomp/pull/2089), six exact files and green fresh-head checks, squash `a3ae40508915889ff22ba728f0243d4a40d6959b`; #2060 was closed as superseded.

This is an initial *index* of historical failure families, not a complete audit of all Vault members and not evidence that every original error was transient or a policy denial. Prioritize original raw responses and current-main semantic comparisons in subsequent runs; retain all archival data.
