# QA-02: urgent retention handoff for six original Windows fault byte witnesses

**2026-10-16 | Independent exact-source evidence maintenance, not new gameplay or release acceptance.**

The sole nominated Windows source and ROM-free package remain `11501a15dea38fa912335cfc63103ce3a7208001` / SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` (original executable SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`). The original candidate ZIP and source-bound *initial* nine QA wrappers have separate verified 90-day GitHub Actions retention until January 2027: [the established retention audit](QA-EXACT-MAIN-RETAINED-WINDOWS-BYTE-AUDIT-20261015.md).

**New gap:** Six additional exact-original-Windows crash, conflict and storage-fault byte witnesses collected *after* those prior retention jobs each currently expire **October 30, 2026**. They are essential matched before/after inputs for the Modern persistence P0 [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) repair and future independent QA. The preexisting 90-day artifacts do not contain these later six ZIPs.

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

## Completed independent backup and remaining GitHub action

Independent QA also created one small **77,814-byte, seven-entry evidence archive** in the active conversation, SHA256 `4c681c87e3f66208882b054554f6768c8df1654035d9f242dcb0725685213308`. It nests the six **unchanged** GitHub Actions source ZIP bytes and a standalone machine-readable provenance manifest. This is a separate fallback copy, **not** a file committed to GitHub and **not** an extension of GitHub Actions artifact retention. The user can download the conversation artifact directly and save it outside expiring Actions storage.

**Integration/release engineering next action:** using the preexisting [one-shot original-owner retention workflow](../.github/workflows/retain-nominated-owner-playtest.yml) as the implementation pattern, make one narrowly scoped, read-only **90-day Actions retention** of these six exact original ZIP wrappers before expiry. Reuse the exact six artifact IDs plus SHA256 hashes in the machine receipt, download via GitHub internal authenticated Actions artifact endpoint; verify each entire old wrapper **before** reupload; reject any missing/extra file, archive extraction, changed hash, private-ROM upload or substituted new Windows build. The *new Actions envelope* will have a different outer digest; never silently relabel it as an old original wrapper. Preserve a short explicit `release_gate_credit=0` attestation, and independently download/verify the new retained artifact when complete.

Only **after verified GitHub retention** should QA update the evidence status as hosted preserved. This document and machine receipt are a **handoff**; they do not claim retention occurred on GitHub. No automated hourly/PR CI reruns or another native Windows AOT build are justified.

**Current release truth:** QA-02 `in_progress`, QA-12 `unverified`, **0/12** accepted full QA gates, **0/45** complete original-USA events, physical Windows still unverified, one historic candidate still `not_assessed`, P0 #1214 unresolved. Three-project reuse preflight: existing UR original Windows source verifier and Actions retention design; Baldosa original guest/typed storage behavior established by retained original evidence; Malmazuke advisory only. No external clone or duplicated release engineer implementation.
