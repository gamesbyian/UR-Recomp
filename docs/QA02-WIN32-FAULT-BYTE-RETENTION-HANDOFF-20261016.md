# QA-02: urgent retention handoff for six original Windows fault byte witnesses

**2026-10-16 | Independent exact-source evidence maintenance, not new gameplay or release acceptance.**

## Verified October 16 update

The October 30 **evidence-loss risk is mitigated** by independently verified 90-day GitHub retention through January 14, 2027 (artifact `12069939434`), plus an owner-controlled private backup. The original source artifact expiration times below remain true for those *original* wrappers. This was archival, not a repaired Windows candidate; QA and event gates remain unchanged. See the completed retention details below.

The sole nominated Windows source and ROM-free package remain `11501a15dea38fa912335cfc63103ce3a7208001` / SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` (original executable SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`). The original candidate ZIP and source-bound *initial* nine QA wrappers have separate verified 90-day GitHub Actions retention until January 2027: [the established retention audit](QA-EXACT-MAIN-RETAINED-WINDOWS-BYTE-AUDIT-20261015.md).

**Original preservation gap (now closed):** Six additional exact-original-Windows crash, conflict and storage-fault byte witnesses collected *after* those prior retention jobs were due to expire **October 30, 2026**. They are essential matched before/after inputs for the Modern persistence P0 [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) repair and future independent QA. The preexisting 90-day artifacts do not contain these later six ZIPs.

The complete exact original run/ID/expiry/outer ZIP SHA256 table is [the retention-handoff machine receipt](../analysis/evidence/qa02-win32-fault-wrapper-retention-handoff-20261016.json). Each was independently downloaded again October 16, whole-ZIP SHA256 checked against the original hosted GitHub digest, every member CRC checked, and original bytes left unmodified. Six ZIPs: **12 + 12 + 11 + 29 + 24 + 33 = 121** original entries, all synthetic disposable QA guest/profile evidence, no full private USA ROM or tested executable in these small ZIPs.

| Source run | Artifact ID | Relevant decision | Existing expiry (UTC) |
| --- | --- | --- | --- |
| [38848852832](https://github.com/gamesbyian/UR-Recomp/actions/runs/38848852832) | `12024617002` | Actual post-raw-write/pre-typed `_Exit(86)`, 28 raw bytes change, next-process refusal | Oct 30 04:11 |
| [38856720047](https://github.com/gamesbyian/UR-Recomp/actions/runs/38856720047) | `12027761297` | Directory ACL preflight denial, does not reach real raw write | Oct 30 05:41 |
| [38861260577](https://github.com/gamesbyian/UR-Recomp/actions/runs/38861260577) | `12029890032` | File-only ACL denial **ineffective**, original game nevertheless commits raw+typed | Oct 30 06:31 |
| [38867691561](https://github.com/gamesbyian/UR-Recomp/actions/runs/38867691561) | `12031753976` | Original game A versus independent Modern writer B selected-profile conflict | Oct 30 07:36 |
| [38870134987](https://github.com/gamesbyian/UR-Recomp/actions/runs/38870134987) | `12033107568` | Two concurrently running genuine game processes, stale A refusal and B cold boot | Oct 30 07:58 |
| [38872238234](https://github.com/gamesbyian/UR-Recomp/actions/runs/38872238234) | `12034140741` | Selected B post-raw crash blocks existing canonical switch to otherwise intact A | Oct 30 08:16 |

These are *not six passing release tests*. The original two ACL experiments include explicit negative/ineffective interventions. The crash itself remains a **reproduced P0**. A successful Windows reproducer CI step must never be counted as a passing user recovery.

## Completed independent backup and verified GitHub archival

Independent QA also created one small **77,814-byte, seven-entry evidence archive** in the active conversation, SHA256 `4c681c87e3f66208882b054554f6768c8df1654035d9f242dcb0725685213308`. It nests the six **unchanged** GitHub Actions source ZIP bytes and a standalone machine-readable provenance manifest. This is a separate fallback copy, **not** a file committed to GitHub and **not** an extension of GitHub Actions artifact retention. The user can download the conversation artifact directly and save it outside expiring Actions storage.

**Completed GitHub Actions archival (2026-10-16):** [PR #1712](https://github.com/gamesbyian/UR-Recomp/pull/1712) merged a narrowly scoped one-shot workflow. [Run 38956731834](https://github.com/gamesbyian/UR-Recomp/actions/runs/38956731834) uploaded 90-day original-wrapper artifact **12069939434**, expiring **2027-01-14T19:41:11Z**. The independently re-downloaded *new Actions envelope* SHA256 is `f35055a086dff30bb82982b3d4ef12476f06b0553f5f2eb84318f92e08754622` (77,097 bytes). It contains the **six byte-identical original ZIP wrappers** plus an archival receipt. Independent audit matched all six complete original ZIP SHA256s from the table, compared each inner wrapper byte-for-byte against original downloads, and CRC-checked the 121 original members. No new Windows build or original-ROM upload occurred. The artifact's new outer digest must never be confused with the original six SHA256 values.

A second new 78,904-byte independent backup (SHA256 `b47d407aadbcae029e7875b64c621fa297fd900af1d465d4682979d9022ae588`) is privately held by the owner and independently read back. The original 77,814-byte conversation backup remains a separate historical backup; neither is committed to GitHub. Private owner storage identifiers are intentionally excluded from this public authority.

**Next actionable work:** independently accept the product owner's eventual #1214 fix using [the exact source/ZIP negative baseline and new-candidate acceptance matrix](QA02-NEXT-EXACT-WIN32-RECOVERY-INDEPENDENT-ACCEPTANCE-20261016.md). GitHub preservation has been verified; it does not constitute a data-recovery pass.

**Current release truth:** QA-02 `in_progress`, QA-12 `unverified`, **0/12** accepted full QA gates, **0/45** complete original-USA events, physical Windows still unverified, one historic candidate still `not_assessed`, P0 #1214 unresolved. Three-project reuse preflight: existing UR original Windows source verifier and Actions retention design; Baldosa original guest/typed storage behavior established by retained original evidence; Malmazuke advisory only. No external clone or duplicated release engineer implementation.
