# UR-Recomp Production Diary — October 7–8, 2026

**Repository:** `gamesbyian/UR-Recomp`  
**Continuation:** `PRODUCTION-DIARY-2026-10-06.md`  
**Evidence cutoff:** October 8, approximately 14:40 Calgary time. PR and commit claims below distinguish integrated changes from outstanding work.

October 7 carried forward the process reform that October 6 had forced. By October 8, the dominant organizing principle was explicit lane ownership. Multiple agents were tasked with narrow technical fronts, told to refresh `main` before beginning, check recent branches for collisions, preserve ROM/reference evidence, commit in small increments, and keep moving when GitHub Actions was busy. Session stalls and repeated “go on” prompts remained part of the operating environment. The useful lesson was continuity through durable repository state, not an assumption that a conversational instruction itself delivered code.

## Windows distribution approaches a real handoff

The recent Windows sequence converted packaging from an exercise in generating a ZIP into independently checkable consumer behavior. PR #909 made the standalone verifier reject mutable legacy mod state, including hidden content and manipulated manifests. PR #919 recorded byte-audited ZIP and hosted Windows boot evidence. PR #921 repaired diagnostics in install and user-data paths containing CMD metacharacters; PR #922 extended the clean-machine procedure to cover special-character extraction roots. PR #926 pinned the canonical USA retail ROM identity inside the independent portable verifier so a newly signed, internally consistent wrong-ROM archive could not pass. PR #933 added a stock-PowerShell AMD64 PE32+ executable check.

Those are material advances, but hosted Windows evidence and portable-package verification are not equivalent to an independent Windows 10/11 consumer-PC signoff. That last-mile gap remains worth describing plainly.

## Course archaeology becomes more spatial and less speculative

PR #910 strengthened decoded course materialization boundaries and compared effective world-space surfaces across regions, avoiding false differences from record numbering. PR #920 connected checkpoint resource candidates to ROM-derived world cells and observed C000 slots. PR #923 introduced strict read-only header-pair/WRAM-player assignment discriminators. PR #925 triangulated a known Dragster finish event against exact ROM-derived cells without claiming to know the touched Y/contact footprint. PR #930 demanded complete decoded course-payload identity before treating a header assignment as authoritative. PR #928 exposed USA/PAL world-unit header-coordinate differences: the Switcher header A.Y candidate moves by −64 world units, but the live racer binding remains unproven.

The pattern is important: every new bridge from static bytes to dynamic gameplay includes a test for what the evidence **does not** yet prove. That discipline prevents an attractive coordinate coincidence from becoming invented gameplay authority.

## Replay, records and tournament surfaces

PR #914 rejected controller-input frame-offset overflow in completed-run replay. The contemporaneous #932 proposal addressed cross-process staged-input collisions and late changes to a selected `.urrun`, but its PR description is evidence of proposed branch work, not by itself proof of mainline integration.

On the visible product side, merged PR #907 supplied a player-facing local-tournament panel on confirmed stock two-player selection, with setup, fixtures, standings and receipt-bound history demonstrated in its native acceptance. The follow-on #931 proposed Records access from the Modern main menu and improved tournament hint positioning on the stock rider grid. The interface and persistence responsibilities remain separated from replay simulation.

## CI stops measuring avoidable delay as progress

PR #911 delivered byte-proven unpaced Records acceptance and rebalanced a native UI shard; PR #912 excluded unfinished jobs from reported completed-run wall-time averages. PR #917 recorded six-shard timings. Another in-flight line, #929, proposed byte-verified isolated unpaced Rename captures after earlier branch work fell behind main. These changes build on the October 6 architectural correction: shared proof and fast feedback matter more than repeatedly launching redundant long jobs. Performance claims must remain tied to the exact measured run and acceptance coverage.

## Cosmetics enter the roadmap, not the shipped binary

The user considered lightweight accessories, scarves, auras and wakes for customizable unicycles, plus a golden honorary crown for names containing `halamantariel`, `dessyreqt` or `nitrodon`. Merged PR #924 documented a host-owned, post-baseline cosmetic layer, derived crown eligibility, split-screen and OAM priority rules, fallback behavior, and replay-safe presentation separation. It intentionally avoided changing canonical game state. The distinction is healthy: a compelling feature can be specified without covertly becoming a release blocker.

## The integration lesson

The volume of narrowly scoped PRs is now high enough that “what landed?” and “what is only under review?” must be treated as separate questions. The user explicitly requested repeated integration audits and no idle CI babysitting. Each lane has to leave clear provenance, testable artifacts, and a current-main merge story. A stalled agent with a coherent PR is recoverable. A vivid conversation with no surviving artifact is not.

As of this cutoff, substantial Windows, course, replay safety, local tournament, CI and cosmetic-plan changes have landed; other follow-ons remain proposals until integrated and validated. This entry intentionally uses numbered PRs as its audit trail rather than treating an agent prompt as a delivery receipt.

## Source notes
Merged PRs/commits visible in recent history: #907, #909, #910, #911, #912, #914, #917, #919, #920, #921, #922, #923, #924, #925, #926, #928, #930, #933. PR descriptions inspected but not asserted merged: #929, #931, #932. Conversation summaries: `PROJECT-CONVERSATIONS-2026-10-07-TO-2026-10-08-RECONSTRUCTED.md`.
