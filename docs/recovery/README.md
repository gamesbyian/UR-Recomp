# UR-Recomp recovery entrypoint

**Continuous intake:** [Recurring Vault Intake](RECURRING-VAULT-INTAKE.md) describes the six-hour GitHub Actions metadata-and-checkpoint route. A successful direct binary download was verified by [run 40022473433](https://github.com/gamesbyian/UR-Recomp/actions/runs/40022473433). These do not certify public source publication or engineering integration.

**Purpose:** reconcile the Google Drive [Agent Recovery Vault](https://drive.google.com/drive/folders/1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn) with current GitHub `main` without losing unique source, negative evidence, rejected publication history or owner/physical acceptance obligations.

**New transport route (2026-10-23):** [Direct Vault Intake](DIRECT-VAULT-INTAKE.md) and [Recovery Agent Handoff](RECOVERY-AGENT-DIRECT-INTAKE-HANDOFF.md) replace conversational base64 relay for accessible archives. Successful [inventory run 40020834318](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318) listed **45 Incoming direct files / 0 errors**, without downloading archive bytes; first real ZIP transfer is pending validation. [PR #2435](https://github.com/gamesbyian/UR-Recomp/pull/2435) merged the working gdown 6.4.2 and PR inventory trigger. No release or integration credit from enumeration. Historical checkpoints below are unchanged.

## Vault reconciliation checkpoint (2026-10-23, supersedes the counts below)

Direct-child counts: **20 Inbox, 38 Incoming, 66 Evidence Library, 51 Integrated, 0 Superseded**. A full pass over the Inbox pointers, small Incoming items and the first-candidate list found almost every previously "held" source already on `main`; check `main` and the cited PR before re-deriving any of these.

- Newly merged: #2397 (`prompt_only_motion` in `tools/verify_title_plate_artifact.py`, Drive `1sk4W9TBmANhiAZk06HypoDiz7T0EbQOk`) and #2425 (QA04 attachment hashing through one opened handle, mitigating #2076).
- Already integrated (byte-identical blobs or the same code): QA01 evidence-ref guard #2340; dual-disconnect mask #2342; quit-confirm footer; Records save-strip #2341; Unicode runner and profile-ancestor reparse guard #2345; stale-Up results focus #2384; Practice identity/restore/two-repeat #2357/#2356/#2362; package symlink and mods-root guards #2347/#2350; authenticated finish ledger #2354; P2P uint64 anchor #2349 and revocation barrier #2367 (closes #2022); Windows smoke upload/same-run tournament #2352/#2361/#2366 (closed #2185 and #2307 are superseded); source-epoch checker #2381; QA08 patches #2376/#2378/#2379/#2382; SDL log tokens #2250.
- Superseded: #2198 same-key seat swap repro by #2330; 856px cross-resolution witness by `tools/verify_cross_resolution.py` (#2285).
- Newly merged after the first checkpoint: #2430 (P2P loopback handshake research module `tools/p2p/direct_loopback_handshake.py`, source blob `167d2e7b` verified from Drive `1fXw7f5CkgsmkO_YBeXqR1aVZ2ngfAFxt`; two of its archived test members were re-expressed, not byte-copied).
- Still unintegrated: the H26 `h26_five_line_decisions.py` harness (needs evidence ZIPs and `references/agent*` modules that are not in the repo; its manifest/shift/publication-window ideas overlap `tools/strict_vault_manifest.py` and the source-pinned QA06 audits) and the 2 MB to 28 MB H25/H26/H27 bundles, which were not re-opened. The Drive connector returns base64 only, so archives above roughly 8 KB are unreliable to transcribe by hand; per-ZIP-member CRC checks make chunked transcription workable.
- Open for native Windows proof: #2076 and #2103. No release gate or physical acceptance changed.

## Live integration intake crosswalk (2026-10-21, independently checked)

The latest six-folder direct listing found **3 Integration Inbox pointers, 33 Incoming files, 35 Evidence Library files, 29 Work Journals, 3 Integrated receipts and 0 Superseded**. These are point-in-time direct-child counts, not an archive-member inventory or release proof; retain all source archives and the historical checkpoints above.

The three Inbox pointers represent **two distinct outstanding deliverables**, not three independent integration jobs:

- Original-title/source-to-SDL geometry evidence: pointer `1BRdWTbWMyI6toXGtRCos_jbw2nRPEs06`, extended by original-demo/cross-aspect pointer `1559xj-XZwwaCFM50etdOGRJnrcbSblGE`. Both belong to the same visual evidence candidate. Source-owner reconciliation with draft [#2149](https://github.com/gamesbyian/UR-Recomp/pull/2149) and original-title owner [#2043](https://github.com/gamesbyian/UR-Recomp/pull/2043) remains necessary; no physical/art/source-parity signoff follows from the evidence.
- Windows smoke ZIP distribution safeguard: pointer `1CJh91PEzzexmDYvESfcKND-d1G0W74YB`. Requires authorized independent review of ROM-containing artifact publication, current workflow source, and retention of already-uploaded artifacts. The pointer is an unpublished candidate, not a merged fix.

This crosswalk supersedes **only** prior claims that the Inbox is still empty. It does not change candidate owners, qualifying source SHAs, historical recovery receipts, or the release ledger. Verify live GitHub heads and exact candidate archives before integration; avoid duplicate ZIPs or separate PRs for an extension of the same work ID.

## Subsequent H29 routing checkpoint (2026-10-21 UTC)

An independent Drive metadata/readback sweep moved **16 surviving administrative files** from `02 Incoming`: 13 preflight/result/manifest receipts to `03 Evidence Library`, three historic continuations/handoffs to `01 Work Journals`. Post-move direct-child counts: **0 Inbox, 29 Incoming, 34 Evidence, 25 Journals, 3 Integrated, 0 Superseded**. File IDs were preserved; no source archive, source patch, candidate manifest or held source write was deleted/integrated. Full 16-ID routing receipt and limits: [H29 metadata routing](VAULT-H29-ADMINISTRATIVE-ROUTING-20261021.md).

The Evidence Library also contains a nested **six-file historical-main Git backup** (five transfer ZIPs and a manifest ZIP). Its creation-time manifest said independent Drive verification was pending. This pickup **subsequently downloaded and independently verified all five ZIP CRCs, per-part SHA-256 values, the reconstructed 408,610,900-byte bundle SHA-256, Git bundle completeness, and a fresh bare-repository restore/fsck**: recovered main `7e9a1be4016b7a094c93603e2bad116a7ebf6ba7`, 8,118 commits. The original manifest is unchanged. Newer main commits and non-main GitHub state remain outside the backup scope; keep the backup restricted. Exact commands, hashes and limits appear in the [H29 receipt](VAULT-H29-ADMINISTRATIVE-ROUTING-20261021.md).

## Verified live folder-routing checkpoint (2026-10-21 UTC)

A fresh direct listing of all six Vault folders, with readback after routing the latest blocked P2P pointer, observed **0 Integration Inbox items**, **45 Incoming files**, **20 Evidence Library files**, **3 Integrated files**, **22 Work Journal files** and **0 Superseded files**; the root held only those six folders. These are moment-in-time **direct-child counts, not permanent inventory totals or member-level classifications**. No files were deleted, and no unpublished code was marked integrated.

**Owner-confirmed intentional legacy cleanup (2026-10-21):** The owner explicitly confirmed that the **387 historical Vault files absent from the new six-folder layout were deleted intentionally**. Their previous appearance in the four immutable censuses (393 historical Drive IDs, 6 of which overlapped the then-current 90 directly listed file IDs) is **archive history, not an unresolved data-loss incident or a restoration/investigation queue**. Prior exact-ID metadata/cached-content lookups are observations only; they do not override the owner's intentional retention decision. **Do not restore, reupload, search out, or create new recovery tasks for those 387 retired files.** Preserve the historical TSV inventory and old read-only analysis as chronology.

The active Vault consists of the **surviving organized files**, plus any future explicitly submitted Inbox candidates. [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) continues per-member reconciliation **only for surviving accessible source archives with unique unresolved content**; do not count owner-retired files as backlog or require a second deletion audit. An empty Inbox does not resolve genuine surviving unpublished packages, but it does mean no current pickup awaiting intake.

The Inbox's latest pointer, `1Gbf2qssNICNivuiind4mMvC6rPUYv7yN` (`UR-P2P-01-R4-SEQ-BARRIER-20261021`), was moved unchanged to **Evidence Library**, verified by destination-ID readback. Its original source ZIP remains in **Incoming** under `1YWo79CU1ybzl_EgQX5CBIsvRHhceLnKz`; the pointer reports archive SHA-256 `4a88b4bed0a709da651052b8e061ddb5f44e3aceb9c66f848a3742d20d4b65d5`, **now independently rehashed and its 9/9 manifest payloads verified** in the [H26/H27/R4 archive checkpoint](VAULT-H26-H27-R4-VERIFICATION-20261021.md). The pointer documents a source-publication safety denial, so there is no automated source retry. [Issue #2022](https://github.com/gamesbyian/UR-Recomp/issues/2022) owns independent, authorized review of the bounded *offline* signed-contact sequence barrier. The checked source `tools/p2p/peer_island_directory_v0.py` remains byte-identical to its `agent1/ur-p2p-01-r4-sequence-barrier-20261021` branch at blob `0af96bcd35ce410b1bda67888b4d6539d0210832`, i.e. **no barrier implementation was merged by creating or routing this pointer**. This is separate from authenticated-finish [#2111](https://github.com/gamesbyian/UR-Recomp/issues/2111).

Six earlier historic/manual pickup items were already moved unchanged into Evidence. Five older `*-inbox-pointer.json` entries for H27/H28 still have source ZIPs preserved in Incoming and their named GitHub owners [#1996](https://github.com/gamesbyian/UR-Recomp/pull/1996), [#2103](https://github.com/gamesbyian/UR-Recomp/issues/2103) and [#2118](https://github.com/gamesbyian/UR-Recomp/issues/2118). The historical pickup guide moved too; it is not a current prompt. A zero Inbox means **no new independently publishable pickup currently validated**, not that those issues or all 45 Incoming items are resolved. [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) still owns per-member reconciliation of **surviving** archives; never delete their unique content without review. The 387 owner-retired legacy files are excluded.

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

For each **surviving** exact Drive ID and useful inner member, record one of: **source-exact integrated (commit+blob+tests), semantically superseded (evidence), preserved research/negative finding, source publication denied (do not bypass), physically pending, or unreviewed**. A complete SHA member manifest proves preservation, not current-source integration. Never delete until a separate per-ID review shows zero unique dependencies and identifies authoritative retained copies. If an item has not received that review, **keep it**.

This is a living index for future recovery passes. When the vault changes, first traverse the active six-folder Vault layout and add a new immutable ID delta rather than overwriting historic snapshots. Do not seek or restore the owner's intentionally deleted 387 legacy files.

## Current GitHub-first recovery practice

Follow the [publication runbook](GITHUB-FIRST-PUBLICATION-RUNBOOK.md). An invocation-level safety-check block is not proof that source code is permanently invalid. Preserve original errors and artifacts; do not repeatedly resubmit a blocked operation to evade the check. Future runs independently re-evaluate current GitHub state and permissible publication options. Ordinary transport/API failures get bounded fresh-HEAD retries. Successful GitHub work does not need Drive status mirrors.

**RF081 H26:** [#2099](https://github.com/gamesbyian/UR-Recomp/pull/2099) merged at `8a38454f3edd1a493101258d6f9e42f9f17c1afd` after unit and hygiene success. Original wake-PC and stack coherence guard/tests came from Agent 1 H26 Vault archive ID `1kULfQIJSV-YJ1lwWBPJAnH6iLtzt5W9d`. Remaining H26 P2P, QA04, QA08 and UHD proposals are not integrated by that PR; no QA gate or physical credit.


## Latest H27 Vault source and issue crosswalk (2026-10-21 UTC)

- **[#2110](https://github.com/gamesbyian/UR-Recomp/pull/2110) MERGED**, squash `5cdbbc57dc991d77df10c1a2ecabab2772c8063c`: source-bound **QA01 nonmonotonic sparse-transition bounds**, with exhaustive ROM-free endpoint regression tests and green exact-head unit/hygiene. Archived 41 genuine WRAM-pair fixture independently passed 6/6 normal and 6/6 optimized earlier. QA01 original source ZIP Drive ID `1DHRV4082CWJ7YLxicGR20CINyWwFEc8N` SHA-256 `f902f821a1e89d11c660343c91ba0be0035ab805b6b832677bcea41b134af8a6` verified 7/7 members and moved Incoming to Integrated **as a bounded source/test recovery**, while private sampled WRAM research and USA event acceptance remain separate.
- **[#2109](https://github.com/gamesbyian/UR-Recomp/pull/2109) MERGED**, squash `2c6a6ef6b7b42d9416cb9e3070565e042fb807bd`: corrected historical #2060 open/closed misstatement in the work-ID continuity register, catalogued H27 unresolved candidates. #2060 is CLOSED UNMERGED after #2089 source recovery.
- **[#2111](https://github.com/gamesbyian/UR-Recomp/issues/2111) OPEN**: distinct H27 P2P signed-invite/finish replay-token commit research. Drive ZIP `1cW_qjnxY8mfclORRfSCIHkQbenhZ4XcO` verified 7/7, local loopback tests independently 4/4 normal + 4/4 optimized; underlying source-publication tool check blocked and source is not in main. No WAN/NAT or trusted rollback claim. Earlier #2022 owns a separate revocation-sequence barrier.
- **[#2103](https://github.com/gamesbyian/UR-Recomp/issues/2103) OPEN**: Records Windows colon/ADS namespace sibling negative; Win32 source/hardware review still needed. H25 exporter publication race remains an independent research hold.
- **H27 Knowledge source holds**: Agent 3 source-epoch classifier Incoming ZIP `1p99v0BHznh173DpXFDwj0Yr8Q1ZmBTsX` authenticated 14/14 with 8/8 normal and optimized; Agent 4 malformed-lane guard ZIP `1_RScoARFTHjfttOY87v9PKBepXmE8tK8` authenticated 9/9 and eight isolated guard fixtures. Both exact source writes safety-blocked and remain unpublished; their formerly active Inbox pointers are now preserved in Evidence; the source patches remain held pending authorized disposition. These are distinct from merged #2104's duplicate capability-matrix ID guard.
- **H27 QA08/PPU source hold**: Agent 5 temporal original-anchor census ZIP `1wW_zP28K8OWA--3UMLX4Yc2_VuIVOgSq`, SHA `25b0c7c00380d43f1e6f7edcac5163614ecf0a1841fff09cf37e8e2049065be0`, independently verified 12/12 members and 6/6 normal + 6/6 optimized ROM-free tests. A source `create_file` safety check blocked the exact research proposal; historical Inbox pointer is now in Evidence. Its 11 original-only frames and phase transitions are **not** native final-pixel/effective-CGRAM parity; #1996 remains draft/HOLD.

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

## H27/H28 actionable publication dispositions (2026-10-21)

Treat this as a pickup index. Source/agent errors and evidence are preserved under the exact Drive IDs; a linked issue is not a source integration.

| Candidate | GitHub disposition | Drive evidence and outstanding qualification |
| --- | --- | --- |
| H27 QA01 RF081 sparse transition bounds | **Merged [#2110](https://github.com/gamesbyian/UR-Recomp/pull/2110)** at `5cdbbc57dc991d77df10c1a2ecabab2772c8063c`; green unit/hygiene | Original authenticated archive `1DHRV4082CWJ7YLxicGR20CINyWwFEc8N` moved to Integrated; 7/7 manifest entries verified, no USA event credit |
| H27 Knowledge reuse matrix duplicate IDs | **Merged [#2104](https://github.com/gamesbyian/UR-Recomp/pull/2104)** at `2321f3f4b6286204be43bb2502dce6573378fc2c` | Archive `11x4qXDt8swIg52188tLpkkLHloauPyhf` in Integrated; further malformed lane inputs are separate |
| H27 Knowledge source epoch and malformed lanes | **Open [#2118](https://github.com/gamesbyian/UR-Recomp/issues/2118)**, not published | Incoming archives `1p99v0BHznh173DpXFDwj0Yr8Q1ZmBTsX` (14/14) and `1_RScoARFTHjfttOY87v9PKBepXmE8tK8` (9/9), exact historical safety-check receipts, current review needed |
| H27 QA08 temporal PPU census | **Draft [#1996](https://github.com/gamesbyian/UR-Recomp/pull/1996)** remains HOLD; source publication blocked, research comment added | Incoming `1wW_zP28K8OWA--3UMLX4Yc2_VuIVOgSq` (12/12); sampled source temporal phases do not prove effective-CGRAM final pixels |
| H28 QA07 Unicode-surrogate test | **Open [#2116](https://github.com/gamesbyian/UR-Recomp/issues/2116)**; committed branch not qualified | Incoming `10zJs9NMaHWxFXBDyLFAAaKDOpLDenl00` (6/6); wrong double-escaped test literal, PR/correction attempts tool-blocked; do not merge broken branch |
| H28 UHD numeric type receipt | **Owner comment on [#2113](https://github.com/gamesbyian/UR-Recomp/pull/2113)**; not published | Incoming `1XxdajwxMpiD8Xvdqr4yFTAAXeb9LXKB8` (7/7); old Inbox pointer retired into Evidence, current SDL source/owner tests required |
| H27 P2P signed invite finish/replay | **Open [#2111](https://github.com/gamesbyian/UR-Recomp/issues/2111)**; no source published | Incoming `1cW_qjnxY8mfclORRfSCIHkQbenhZ4XcO` (7/7); only loopback tests, no restart/anti-rollback/WAN proof |
| H27/H28 Records namespace/producer | **Open [#2103](https://github.com/gamesbyian/UR-Recomp/issues/2103)**; no new source merged | Existing #2089 baseline merged. Win32 colon filename and source-freeze races remain independent platform negatives |

**Queue distinction:** Evidence Library stores resolved/historical pointers and research-only receipts without deleting their sources. Integration Inbox retains genuinely unresolved source-authorized pickup requests. Agents must deduplicate against current PRs and `main` before making a new recovery file. [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) owns ZIP-member reconciliation. No completed source-recovery row automatically changes the 0/45 original/native USA or 0/12 physical Windows release acceptance.
