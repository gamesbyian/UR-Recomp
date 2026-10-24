# October 24 Vault semantic reconciliation: review and handoff

> **Live reconciliation after main advanced to `468e46ecd0845afecabe8986a7c4c4eb2dab7768`:** PR [#2479](https://github.com/gamesbyian/UR-Recomp/pull/2479) has merged the read-only, SHA-keyed [`vault-member-dispositions.json`](vault-member-dispositions.json) consumer. Earlier references below to an *unbuilt* reviewed-queue consumer are historical. Agent 2's [H27 qualification](https://github.com/gamesbyian/UR-Recomp/issues/2088#issuecomment-6380789495) has already dispositioned the **H27 CPU `1fog_2M...` as research-only and H27 P2P rollback as behaviorally superseded** by current source/tests. Do **not** reassign them as new engineering work. Its [scoped H26 follow-up](https://github.com/gamesbyian/UR-Recomp/issues/2088#issuecomment-6380836754) also finds exact QA07 eligibility, evolved byte witness, superseded QA06 opacity test, and a nonshipping source-clock pilot. Agent 1 owns the canonical per-member dispositions; Agent 3 verifies merge/provenance before credit.

**Revised unclosed Agent 2 semantic-review packages:** (1) *unsampled* H26 nested source leaves after #2458/#2459 and Agent 2's scoped follow-up; (2) Incoming `1fXw7f5CkgsmkO_YBeXqR1aVZ2ngfAFxt` unsigned-ACK/cross-invite tests, unless owner #2088 has since qualified those exact tests; and (3) Evidence `10zJs9NMaHWxFXBDyLFAAaKDOpLDenl00` H28 Records archived proposal. None is yet a confirmed novel implementation. The formerly listed H27 CPU/P2P rows in the historic work-group matrix are **resolved evidence leads**, not active Agent 2 tasks.

**Authority and scope.** Read `AGENTS.md`, the current work queue, hourly agent board, recovery runbook/publication contract, issue #2088, issue #2468, and recent main/PRs before interpreting this historical snapshot. The machine-readable ledger is [VAULT-SEMANTIC-REGISTER-20261024.json](VAULT-SEMANTIC-REGISTER-20261024.json), one row per exact surviving direct-child Drive ID. This report does **not** approve any ROM, source-publication hold, title artwork, Windows hardware gate, or historical safety-denied operation.

## Verified census and transport

On observed main `153d3141bf10313613545e7a8c4db8a023fca9e1`, authenticated Google Drive reports **224 surviving direct children**: Inbox 25, Incoming 45, Evidence 66 (including one nested backup folder), Integrated 51, Journals 37 and Superseded/Rejected 0. The runner's independent Evidence enumeration is **71** and must not replace the authenticated direct-child figure. Owner-retired 387 historical files are intentionally excluded.

Production manual intake [run #40068102434](https://github.com/gamesbyian/UR-Recomp/actions/runs/40068102434) succeeded with durable separate artifacts: Incoming `12550460740` and Evidence `12549589792`. Checkpoints now retain **15/45 Incoming** and **14/71 runner-enumerated Evidence**, leaving **30** and **57** to scan. These are audit queue counts, **not** counts of missing modules. The H26 Evidence archive `142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ`, SHA-256 `601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00`, was read and outer-manifest verified earlier; the full recursive analyzer exceeded its 128 MiB expansion guard. Its 14-day cooldown ends around **November 7, 2026, 05:33 UTC**. Use bounded nested audits, not repeated full expansion.

## Inbox: all 25 have an explicit outcome

| Semantic disposition | Pointers | Engineering inference |
| --- | ---: | --- |
| Exact source and test on current main | 2 | P2P authenticated finish ledger and UHD title prompt verifier |
| Merged or current-main semantically equivalent | 9 | Focus, controller lifecycle, Windows package/profile, Records scans, P2P anchor, ghost, QA01 and other targeted guards |
| Later-main supersession / duplicate deliverable | 10 | Practice/Options subset, Unicode, Records Results, Local Runs shared inspector, Win32 sibling, ROM uploads, controller/Results research |
| Existing UHD title/integration ownership and publication/technical review hold | 3 | No independent new PRs; work belongs with drafts #2043/#2149 |
| Historical PPU cross-epoch evidence only | 1 | Retain source hash methodology and #1996 HOLD; no QA08 acceptance |

**Important resolved semantic false positives:**

* Local Runs source `1B6qmg2uacrkudkKtZp1VcEc8unKWAECy` changed direct `.urrun` symlink admission, but current `CompletedRunBrowser::refresh` already uses shared `inspect_completed_run_record_artifacts()` with a native test for both linked entries and linked roots (merged #2364). Do not replay that old patch.
* Portable sibling ZIP `19AofFm0zVjhmZaayHvZ4Jk1Y0BVCBPTm` proposes `_portable_run_namespace_entries()`. Current `tools/export_baldosa_earned_1p_run.py` implements that helper with Unicode NFC, device names and casefold collision checks. Its exact source transform is superseded. **Issue #2103 remains open for real Windows/NTFS ADS qualification**, which an archive comparison cannot satisfy.
* Results feedback `1JhHl6ZWRVWtiPQI6Sp_PaTw5HDAxR8at` is present in source-width 256/342 strip geometry, and the current root presenter passes `width`. No new UI candidate is warranted.
* Staged first-party P2P `tools/p2p/authenticated_finish_ledger.py` plus its test are **exact Git blobs on main** (`82042f0f...`, `b28ad923...`), regardless of the old safety-denied GitHub publication incident.
* Original `UR-WIN-RESILIENCE` document `16COCzeUjMh604R-3aPowacYM8nomQlUabIqyQ2ku57s`: six last-amendment texts exact main and one atomic-replace implementation later evolved. No stale preimage overwrite.

## Integrated folder: independent integrity and crosswalk

All **51** archived direct entries were downloaded from authenticated Drive; the **50 ZIPs passed CRC inspection** and their **291 ZIP members** have SHA-256 and Git blob fingerprints in the independent binary audit. The remaining item is an 8,500-byte DOCX. The machine ledger includes **all 51 exact Drive IDs and whole-file SHA-256 digests**, plus relevant PR/issue or exact-main comparison references. A `main` path or merged PR receipt, rather than the folder label, determines implementation status. Examples:

* P2P finish ledger `1KHoNBxtQd9XU3AAeeRQQVdiEkaHhWtyQ` is exact on main and merged in #2354.
* Native title prompt `1sk4W9TBmANhiAZk06HypoDiz7T0EbQOk` is exact on main and merged #2397.
* PPU temporal census `1wW_zP28K8OWA--3UMLX4Yc2_VuIVOgSq` source and test are exact on main; the research is **not** a QA08 release gate.
* QA08 cross-epoch CRC source/test `1eBRIAdDsdMitm6R71fecb81Zu_UNtu2t` are exact on main; #1996 remains held.
* Knowledge duplicate-ID `11x4qXDt8swIg52188tLpkkLHloauPyhf` is an older standalone test/tool; current `tools/select_three_project_reuse.py` already fails closed on duplicate capability IDs.
* First-error audio `1BaqZ7GNAeis64RmZWcyp_LsBVjSRI5nC`: sticky `incomplete_reason` and terminal regression already appear in `tools/live_capture_research/clock_bound_audio_span.py` and `tests/unit/test_live_capture_audio_interval_h25.py`.
* Historic title/SDL mapping `1Ubhzi-jExEWHcHcouxxaE4xqFjioKAnQ`: source verifier and test already exist on main; original/native scene fidelity, art and signed-off visual acceptance remain **separate** from tool existence. Do not count the archive as a release integration gate.

The crosswalk is a **triage index**, not a statement that 291 members were individually proven byte-identical to current main. Rows labeled semantic successor or technical hold explicitly require targeted member-to-main comparison if an agent needs stronger exactness evidence.

## Distinct review deliverables and owners

| Work group | Exact source IDs, SHA where verified | Owner / priority | Narrow next action and stopping rule |
| --- | --- | --- | --- |
| **A. H26 nested source-distinct review** | Evidence `142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ`, SHA `601d6131…be00`; Incoming `1kULfQIJSV-YJ1lwWBPJAnH6iLtzt5W9d`, SHA `57067026…f983e` | **Agent 2 / P2** | Reuse scoped walk in #2445 and historical member fingerprints. Around 140 nested source-like leaves lack exact current-main blobs; many are archival harnesses. #2458 LAN policy and #2459 QA06 full-frame audit already merged. Inspect plausible source-distinct behavior, including SQLite checkpoint anchor and Windows validation, only if existing issue/PR fails to cover it. Do not create 140 tickets. |
| **B. H27 CPU first-divergence member review** | Incoming `1fog_2M1xOs7gi9fJ8N8jSKGbVnJQkqoJ`, SHA `e7f7ef0ea847b8842094a4e39b05299b9b507a24c40f1c48a600c0e49278fd04` | **Agent 2 / P2** | Inspect the two source-like members and current RF081 producer/test semantics. A missing Git blob is not a missing causal NMI witness; if already present, close receipt, otherwise send narrow source plus before/after negative to Agent 3. No event acceptance. |
| **C. H27/H26 P2P source-distinct controls** | Incoming `1JXYRrbE89whUjvLaTrRPCG4iBzcxTGii`, SHA `d476a0993d69fea73d0443ef47f5acb140b660c03ece1122a81d56feb504c328`; `1fXw7f5CkgsmkO_YBeXqR1aVZ2ngfAFxt`, SHA `458bef7a8782bbc5055f82546a77193cc21c630dc13d36d4692c8cf98abbf5f2` | **Agent 2 / P2** | Reconcile archived unsigned ACK / replay cases against merged #2354, #2367, #2371 and #2458. Classify original test coverage per leaf before any recovery PR; do not claim production decentralized P2P proof from synthetic cases. |
| **D. UHD original title and SDL witness** | Integrated `1Ubhzi-jExEWHcHcouxxaE4xqFjioKAnQ`, SHA `8a59f35d778169b7df5e725d0cf4a1d74c3266552b91236002ff08f95e13b21a`; related `1j8T18Xaw4xKnIfcgdwlH6AHFyLo0M8IO` and `1t6q8W3kd8X40YT2Jj-eI4d2N1B5PPpxd` | **Agent 3 / P2** | Coordinate existing draft #2043/#2149, source-pinned captures, independent technical/art review and recorded GitHub publication hold. These form one source-to-SDL deliverable; do not fork a parallel implementation. |
| **E. Windows physical ADS and exact package** | Integrated `19AofFm0zVjhmZaayHvZ4Jk1Y0BVCBPTm`, SHA `6c1148f8f0806348489590ed652897cad92fb02543b41ffe52ea954a1c6eb0d7`; source on main | **Agent 3 + independent Windows QA / P2** | Close archival source receipt without duplicating `_portable_run_namespace_entries()`. Leave issue #2103 and physical NTFS/ADS and Windows QA gates open until their real tests run on a nominated exact package. |
| **F. Historical Options rollback source** | Google Doc `1_3tsAlIptW03MNeT9z1QIhztyZwfEFO2rqEAt06V32c`; the single Drive revision contained a BOM but no recoverable source text | **Agent 2 / P3, evidence/authorization hold** | If the currently observable Options rollback defect persists, derive a new source-native regression separately. Do not treat a vanished draft as a byte-recoverable archive or replay denied writes. |

**Assignments (superseded by the live reconciliation above):** A, B and C were originally proposed as three candidate-review packages. Agent 2 subsequently closed the selected H27 CPU/P2P candidates as research or already represented; remaining Agent 2 reviews are the unsampled H26 leaves, unsigned-ACK tests, and H28 Records evidence. **Zero confirmed novel product-source gaps** at this checkpoint. D, E and the crosswalk/disposition bookkeeping belong to Agent 3. F is a conditional engineering investigation with unavailable original bytes, not a promised source restoration. No new PRs are justified merely by checkpoint review-lead counts. Issue #2468's read-only queue-to-review consumer landed in #2479 and must remain review-gated; it never publishes source automatically.

## Handoff protocol

Agent 2 consumes `items[].drive_id`, SHA-256, work-ID, existing PRs and this narrowed review matrix; for any genuine missing test or behavior, report intended GitHub path, exact archived member SHA-256, source preimage, failing current-main negative and corresponding proposed fix **without touching Agent 3's branches**. Agent 3 reconciles merges, owner holds, issue #2088 comments, and register dispositions; never infer integration from a folder move. Original Vault files and historical incidents remain intact. No hourly-agent board, simulation source, release acceptance ledger or other agent branch was changed.

**Acceptance truth:** 0/45 independently accepted complete USA events and 0/12 physical Windows release gates, pending independent evidence under `docs/RELEASE-QUALITY-LEDGER.json`.
