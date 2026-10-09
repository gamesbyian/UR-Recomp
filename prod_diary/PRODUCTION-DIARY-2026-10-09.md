# UR-Recomp Production Diary — October 9, 2026

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation:** `PRODUCTION-DIARY-2026-10-08.md`  
**Evidence cutoff:** October 9, 2026, circa 11:12 Calgary time. This entry uses inspected mainline commit history and PR descriptions. The conversation capture is reconstructed, not verbatim.

October 9 became the day an immense QA checklist started turning into narrower, falsifiable release claims. The user noticed that fixing everything identified by the audit could consume almost as many nominal agent-hours as the project had already accumulated. The response was to audit the audit: separate product features still missing from actual reproduced defects, make work cross-productive, assign exclusive owner lanes, and spend acceptance effort on finished journeys rather than an ever-widening set of isolated probes.

## Durable multiplayer, or it has not shipped

Persistence and tournament correctness provided some of the clearest tangible results. Merged #1018 and #1019 addressed aborted registration reruns and failed profile SRAM switching; #1027 and #1030 recovered pristine profiles in orphan/postpublication crash situations. #1032 strengthened receipt durability, #1033 and #1035 forced artifact bytes to stable storage before run/match or ghost publication, and #1038/#1041 protected immutable tournament archives including migration. #1042 fenced receipt credit to the actual persisted launch attempt. #1044 protected newer-version ghost sidecars against downgrade overwrites.

A more dangerous process race appeared in #1050: two game windows could both possess legitimate-looking tokens, yet one could supersede the other's unfinished fixture. It is possible to prevent an incorrect receipt while still ruining a legitimate player attempt. Merged #1052 added a live, crash-released nonblocking OS fixture lease; a second process must receive Busy rather than silently steal the event. Merged #1054 then exercised real three-leg two-player and three-plus-participant tournaments through independent processes, including fixture selection, receipts, standings and history. That moves confidence from serialized store unit tests toward the actual multiplayer product journey.

There are still live transaction edges. Merged #1057 changed profile activation to commit the selector only after target framework SRAM publication, addressing a kill window the earlier compensating rollback could not survive. PR #1058 investigates distinguishing receipt storage outage from invalid evidence while preserving exact live fixture ownership. Its proposal is not treated as merged. The release ledger continues to retain Windows fault/recovery qualification and other P0 gates, even after native process tests pass.

## Authentic gameplay: the denominator matters

The user repeatedly insisted on complete original/native event results: non-Dragster Race, multi-lap Circuit and scored 45-second Stunt, across the 45 USA courses. Earlier test code could mistake motion drift for checkpoint semantics, compare reward outputs while overlooking differing trajectories, or omit one player's gate and lap state. Merged #1031, #1047 and #1049 improved those discriminators rather than asserting an unearned gameplay repair.

Original Snes9x Zoom Zoo archaeology became denser through #1023–#1026, #1036 and #1039, including course-cell proximity, archived input identity, entry and lap events, and scene-aligned contact samples. This work keeps original X displacement, stopwatch onset and other observed state separate. Merged #1059 tightened completed-result detection by rejecting transient scratch/menu bytes and requiring stable actual result-screen states. The original archived events are valuable, but they cannot substitute for matching settled native results. The scoped course census described in PR #1055 remains **0/45 complete original/native acceptance, 4/45 partial, 41/45 unverified**, rather than transforming source-only completions into passes. The frame-2903 Dragster interpretation remains unresolved absent instruction-time evidence.

## Moving HD has to survive motion

Merged #1022 admitted actual native one-player and versus moving-scene samples; #1028 preserved their evidence and remaining blockers. #1029 repaired isolated PPU OBJ export, and #1034 added exact-state OBJ/capture-removal evidence. #1040 addressed source-absent phantom HD racer cases and measured visibility over real moving scenes. PR #1045 proposed a stricter per-racer original-source footprint test to prevent one source sprite from authorizing an unrelated second HD racer; its status must be checked independently of nearby merged work.

The larger change is the standard of proof: a replacement asset may be correct in isolation while animation flickers, source pixels disappear, priority breaks or split-screen gains phantom objects. Coverage means measuring the real moving raster, not counting registered sprites.

## Modern root and audio still need the player's test

The user launched a specific QA-05/09 lane for issue #890, where Return confirming Restart could leak a guest Start input and leave race audio silent, and issue #1053, implementing the Modern five-destination root (Play, Practice, Multiplayer, Records, Options) with Racer/Profiles access. PR #1056 contains proposed implementation and a guest-input release barrier. At this cutoff it is a PR under review, not accepted mainline behavior. Controller-only cold-launch-to-quit proof, proper focus and held-button release remain essential before that route is called finished.

Merged #1051 removed an unnecessarily expensive downstream Windows audio acceptance trigger after every smoke build while retaining targeted audio validation and explicit release dispatch. Faster proof is worthwhile only while its qualifying evidence remains intact.

## New research and collaboration branch

The user also forked a separate Uniracers repository and asked for comparison with UR-Recomp, transferable technical work, a provenance trail and a way to contact its developer, Ema. This is recorded as research direction, not as evidence that source code was imported or the developer contacted. An eventual transfer should explain which semantics, tools or assets were adopted and what they displace in the existing project plan.

## What this day changed

October 6 was about making parallel development composable. October 9 was about making release claims accountable. The project's strongest progress now comes from small real-world counterexamples that expose false success: a stolen but formally uncredited tournament race, a crash halfway through SRAM/selector publication, a result-screen detection triggered by transient low-WRAM scratch state, an HD rider with no source sprite, or a Restart input leaking through the host/guest boundary.

A disciplined audit need not expand forever. The output that matters is a bounded path from reproduced player failure to fixed code, fresh-process evidence, and a release gate that says exactly what was tested. These merged improvements reduce risk, but the remaining unsupported full-course completions, Windows fault qualification and controller-only Modern journey must remain visible rather than being buried by the number of commits.

## Evidence index

Merged changes inspected in mainline history include #1018, #1019, #1022, #1027, #1029, #1030–#1044 (selected subject-specific PRs), #1046–#1052, #1054, #1057 and #1059. Contemporary PRs reviewed without asserting integration: #1045, #1055, #1056 and #1058. Conversation context: `PROJECT-CONVERSATIONS-2026-10-09-RECONSTRUCTED.md`. Exact statuses should be rechecked at any later cutoff.
