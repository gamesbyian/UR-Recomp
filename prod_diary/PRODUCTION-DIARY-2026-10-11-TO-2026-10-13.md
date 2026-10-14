# UR-Recomp Production Diary — October 11–13, 2026

**Project:** UR-Recomp  
**Continuation:** `PRODUCTION-DIARY-2026-10-10.md`  
**Evidence cutoff:** October 13, 2026, circa 22:29 Calgary time (04:29 UTC October 14). This account uses available reconstructed conversation context and recent merged-main commit history; it distinguishes execution, research observations, implementation and final release acceptance.

## October 11–12: The laboratory wants a scheduler

After the intense rush toward a playable Windows beta, the user asked a rather different question: if there are ten thousand things left to test, why not test them systematically instead of paying an agent to choose one hypothesis at a time? The resulting long-running experiment factories were conceived as cumulative, resumable evidence producers, not a pile of one-off workflow buttons. The user wanted all the useful campaigns, clear continuation semantics, and a way to know whether repeating a completed run could reveal something genuinely new.

The economic question was just as sharp. The GitHub account allows 20 concurrent Actions runners. Three or four independent agents can usually work profitably without saturating that pool, whereas a broad factory can occupy much of it. The user asked for a hybrid: let implementation agents keep shipping while reserving long campaigns for hypotheses whose verification cannot be reduced to cheap local tests. Rather than celebrate raw case counts, the goal became exact evidence and decision-relevant yield. The user challenged the use of “estimates” when the real prize was an original/native gameplay proof.

By October 13 the repository had moved toward a more mature experimental infrastructure. Merged #1444 established admission control, yield/stopping rules, resumable series and evidence-retention policy; #1470 introduced a guarded turbo frontier experiment; #1475 stopped rotating automatically onto lanes unable to change the next decision; #1476 recorded measured frontier savings of roughly 36–40 percent and recalibrated costs. #1445 reduced CI expense with balanced unit shards and compilation caching without removing acceptance gates. These are tools for directing finite runner-hours toward meaningful new information, not engines that magically turn research fingerprints into event correctness.

The conversations also broadened the eventual product beyond the imminent beta. The user outlined a decentralized PC/macOS P2P multiplayer ideal: no permanent central servers or proprietary account system, and a shareable code or link for direct intentional rendezvous when discovery fails. This remains architecture research, not a shipping feature.

## October 13: Four separate agents, one increasingly real game

The user maintained four strictly separate development authorities: Modern Windows/Baldosa product integration; original/native gameplay and strict event-oracle research; faithful PPU/OAM and widescreen/HD graphics; and independent adversarial release QA. The instructions named their conflicting PRs and explicitly forbade crossing into one another's files or claiming release evidence from synthetic probes. “Go on, as far as you can” recurred, along with session-stall recovery requests. Session-stall reports were operational requests to recover and resume work, not evidence of fatigue, criticism or impatience. The project was no longer lacking tasks. It needed clean ownership, useful stopping criteria and a trustworthy integration ledger.

### Windows gains real first-player and paired-result journeys

The strongest product advance was moving from independently demonstrated components toward actual hosted Windows journeys. Merged #1416 and #1425 exercised real native played 1P and joined 2P result flows, paired `.urrun`/`.urmatch` publication and fresh-process Records. Independent QA #1431, #1432, #1435 and #1438 tightened provenance, source-result linkage and canonical saved-record identity rather than accepting any vaguely similar output. The proof remains scoped to its exact candidate and environment.

A cold anonymous player's path then advanced. #1439 added first-run stock racer creation and safe next-process activation, #1442/#1463 supplied narrow real launcher restart behavior, and #1451 demonstrated the first created racer earning an actual native 1P result and reopening Records. #1459 addressed interrupted selector publication, #1478 admitted a non-default first racer, and #1485 established safe second-racer profile admission without switching the active P1 identity. The subsequent controller-driven P2 journey was still in follow-on work (#1490 at this cutoff). #1480 updated the candidate README to reflect new actual capabilities without overpromising.

The user-facing achievement is significant: somebody can finally encounter more than a technology demo. But the ledger rightly preserves unresolved controller-only routes, exact 2P onboarding, fault injection and independent physical Windows verification. #1489 tightened exact source-frame and pair-directory evidence, while #1483 checked real saved `.urrun` bytes rather than trusting a producer's summary.

### Fidelity evidence grows narrower and more exact

Original/native QA produced a telling mixture of detailed progress and stubborn non-acceptance. Zoo result investigations (#1450, #1460, #1472, #1486) exposed precise SRAM restore and result-text timing and authenticated large guest-memory snapshots. Earlier Switcher NMI/stack discrepancies were pursued at executed source-PC and register level. Dual-air seed 50036056, rotation arm, frame 2580, received paired original/native evidence handling (#1410, #1428, #1464, #1488); raw air-register coincidence was not accepted as an authentic physics result.

The published census retained **zero fully strict-accepted complete USA original/native events** in the relevant snapshots, despite several valuable partials and genuine original-only completion traces. This is an almost uncomfortable contrast with product progress: a played Windows result can work while the independent reconstruction researcher still refuses to certify matching every source transition. Both facts deserve to coexist.

### Graphics go back to the machine that drew the pixels

The source-faithful graphics lane no longer treated a sprite name or plausible on-screen box as sufficient proof. #1405/#1408 corrected interpretations of original OAM shadow and $1599 visibility. #1433, #1453, #1461 and #1474 interrogated real two-player PPU BG3/OBJ composition, fixed colors and HDMA COLDATA source bytes; #1481 added executed original Snes9x writer observations. #1458 preserved a hash-authenticated original 12-pose racer atlas for future faithful art, while #1468 retained actual source shade classes. Scanline behavior, top/bottom source ownership and the difference between CPU journal state and live rendered color remained important boundaries.

The user demanded authentic 256×224 geometry with 7:6 pixel aspect and real host-owned wider world, while explicitly withholding aesthetic approval from the existing procedural HD racer. The artwork needed recognizable multiple poses from period and source references, not a speculative declaration of shipping likeness. This restraint is an unusually valuable design decision amid all the enthusiasm for impressive 4K output.

### Independent QA refuses to get swept along

The independent release lane became a brake by design. It separated actual hosted Windows runs, synthetic acceptance harnesses, archived source fingerprints and physical end-user hardware. #1454/#1455/#1462 demanded candidate-bound, independently readable first-racer proof, while #1479 updated readiness only after merged earned Records evidence; #1467/#1489 further tightened native 2P pair naming, directory and host-frame traceability. QA-09/12 still retained physical-machine, consumer input and recovery gaps. No amount of useful archaeology can close a packaged Windows signoff by inference.

## A changing emotional climate

The previous days carried rivalry, wonder and a desire to be remembered for a superior remaster. These three days felt more operational and more relentless. The user repeatedly pressed agents onward, challenged factory estimates, confronted runner exhaustion and demanded that research campaigns discover something exact. The ambition remained huge, but the questions grew more adult: where should scarce compute go, what would count as a genuine result, what can a new process really recover, and who is allowed to say the build is ready?

One of the project's most interesting contradictions is now visible. The executable is steadily turning into a game a person can play, while the archaeology is becoming stricter about how little is fully certified. That is not necessarily a failure of either effort. It is what happens when product engineering and historical reconstruction are measured honestly and separately.

The next stretch should preserve this distinction. Move the player all the way through onboarding, authentic 1P/2P play, Records, replay and fresh boot. Keep the physical Windows evidence gap open until someone really runs it. Use automated factories to answer high-value questions with reproducible source witnesses, and rest lanes whose next thousand cases would merely decorate a chart.

## Sources and chronology notes

Conversation archives: `PROJECT-CONVERSATIONS-2026-10-11-TO-2026-10-12-RECONSTRUCTED.md` and `PROJECT-CONVERSATIONS-2026-10-13-RECONSTRUCTED.md`; neither claims to be a verbatim export. Mainline commit subjects and PR descriptions inspected through October 13 local time include #1405–#1490 as selectively referenced above. A numbered PR used as a research context reference is not by itself proof of final independent acceptance. Claims about later completions are excluded from this historical cutoff.
