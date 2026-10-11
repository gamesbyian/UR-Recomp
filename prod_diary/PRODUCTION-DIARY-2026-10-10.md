# UR-Recomp Production Diary — October 10, 2026

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation:** `PRODUCTION-DIARY-2026-10-09.md`  
**Evidence cutoff:** October 10, evening Calgary time. Project conversations are reconstructed and labeled separately. GitHub commit/PR history grounds integration claims.

There was a strange kind of electricity in the project on October 10. Eleven days ago this had been an attempt to remake a beloved SNES unicycle game. Now there were other people in other countries independently carving into the same machinery, a newly encountered MIT-licensed source reconstruction, a serious modern Windows product emerging from Baldosa, authentic widescreen capture, and an uncomfortable question about who would be remembered as having made the definitive new Uniracers.

The user did not hide the feeling: “I know it's petty and emotional, but I don't want Baldosa's thing to be the ‘new version of Uniracers’ after the 11 days of work we've done.” The desired outcome was a 4K widescreen version people would find distinctly more appealing. That is a genuine competitive impulse. But the same conversation insisted that the project become the definitive evidence-backed technical reference: “every question is answered, every recreation is faithful AND evidence-backed.” The ambition is simultaneously to make the best game *and* to leave the best explanation of how the original worked.

## Three lanes, one product

Three new autonomous agents received exclusive mandates: actual Baldosa Windows product integration; gorgeous and faithful 4K/widescreen graphics; and complete-event original/native gameplay QA. An additional lane was assigned recruitment footage, and another the malmazuke research intake. The user's repeated “keep working, go as far as you can” and reports of stalled sessions had an edge of impatience. There were enormous nominal agent-hours available, yet useful progress was only what persisted into current main, verified artifacts and completed player journeys.

The target became a polished Windows beta in roughly seven days, while the user explicitly said nine days would be acceptable if they produced a better game. That sentence carried unusual strategic weight: speed remained desirable, but arbitrary schedule pressure was not permitted to erode authenticity, persistence integrity or player experience.

The planning changes made this visible. Merged #1201 adopted the definitive technical-reference charter, #1202 set a quality-first Windows beta campaign with separate lanes, and #1239 constrained the active work queue so the agent coordination document itself did not become an obstacle.

## The game starts looking like a game

Merged Baldosa Modern work brought real player-facing joins between once-disjoint subsystems. The native pause surface (#1194), paused Quit Desktop and shutdown checkpoint (#1208), re-opened named-profile SRAM (#1212), safer selector lease around SRAM publication (#1216), and held-menu-edge coalescing (#1213) addressed ordinary use rather than research prototypes. Source-confirmed settled results (#1229), course/controller fields (#1238), strict record admission (#1249), read-only native Records (#1230), and a guarded one-player Race publisher (#1253) formed a credible path from race to durable record. #1258 fixed truncated hundredths in the narrow Records modal.

These merges matter because the project's most vulnerable distinction has been between a working backend and a coherent Windows application. The progress is real; it does not authorize claiming all routes, packages, consumer environments or two-player record journeys have passed beta acceptance. The diary must never turn a green unit test into a fictional happy customer.

## Widescreen stops being a promise

October 10 brought unusually tangible graphical evidence. #1191 and #1189 addressed the genuine fixed native Original viewport and 4K matte; #1210 verified the source HUD and P1/P2 center; #1221 independently proved post-GO 3840×2160 split racing with original central parity. #1231 captured actual post-countdown one-player widescreen motion and measured missing authored poses. #1228 and #1245 guarded real 4× pixels within eligible original source footprints.

Some findings were stubborn negatives, and therefore valuable. #1218 measured hundreds of guarded 2P Remastered occlusion rejects, not a secretly complete HD implementation. Later #1255 showed the apparent frequent missing 0A4B racer art was dominated by a held/nonracer or offscreen condition; authentic motion mostly cycled through 08D5, 0895 and 0855. Original PPU source-isolation experiments #1264 and #1271 revealed alpha-empty bottom slots despite unicycles visible in the upper image, making further top-slot source ownership checks necessary. It is much better to discover an incorrect candidate sprite now than to paint and ship a beautiful phantom.

The visual standard is deliberately demanding: 4K resolution alone is easy to advertise; accurate source movement, framing, OAM ownership, readable split-screen and correct replacement phase are harder to demonstrate.

## The footage finally moves

The recruitment-video work crossed an important conceptual boundary. Earlier teaser footage had been sampled-frame presentation. Merged #1236 recorded genuine continuous Baldosa two-player Original widescreen play, #1241 assembled a gameplay-led trailer and vertical edit, and #1246 recorded actual title and menu navigation. Their provenance is as important as their aesthetic appeal. The user had said of the earlier AI-generated clips, “The videos are astonishing,” while immediately recognizing that future recruitment needs real several-second gameplay, not merely animation-like sampled frames. That challenge now has an evidence-backed partial answer.

A trailer is not acceptance coverage, but it is a different kind of evidence: the first thing a prospective contributor or curious player can understand without reading the repository. The user is interested in collaborators principally as additional agent-hours, not as a new creative committee. A genuine moving demonstration is therefore a recruiting instrument and a test of whether the product identity is legible.

## Mark Feaver, malmazuke, and the odd coincidence

Discovering `malmazuke/unirally-reconstruction` changed the mood. The user forked the repository, drafted and sent an introduction to Mark Feaver, and asked how best to exploit the independent research even if he never replies. The purpose was straightforward: two teams apparently “bake two similar cakes”; it would be wasteful to duplicate every investigation. In repository terminology the contributor is to be named `malmazuke`.

Merged #1277 preserved a commit-pinned, MIT-licensed research/source slice, native PAL symbols and constrained PAL/USA leads; #1281 triaged specific PAL mechanics and ambiguity. This is research intake, not permission to silently replace USA runtime semantics with PAL observations. The work illustrates the project's intended character: use outside evidence eagerly, but show its provenance and preserve the uncertainty boundary.

The user also wondered why three independent Uniracers projects appeared in separate countries within about ten days, and whether MVG's recompilation coverage might explain the timing. The coincidence was exciting, faintly threatening and intellectually irresistible. The diary cannot settle causation by coincidence alone.

## Fidelity remains the sober counterweight

The original/native QA lane continued down to instruction-level details. Switcher result-boundary investigations (#1190, #1235, #1250, #1263, #1268, #1274) pushed apparent state mismatch into the distinctions between NMI hardware stack effects, PHA opcode writers and exact accumulator/stack state. That is extraordinary depth for a game most players will judge by how a wheel lands. Yet the release discipline must stay honest: mechanistic understanding of a Switcher trace is not 45/45 complete-event acceptance, nor should narrow exact-state coincidences eclipse whether the game can be finished.

This tension explains the scale of the undertaking. One group is trying to publish race results into a real profile while another is trying to identify which exact original interrupt wrote a stack byte. Both jobs belong to the same project, but they have different definitions of “done.”

## The emotional center of the project

The last few days have held delight, irritation, competitiveness and a nearly archival instinct for completeness. The user wants to *win* on presentation, without faking fidelity; wants outside collaborators, without surrendering product direction; wants to accelerate, without pretending every green Actions job is an independent playable beta; and wants nothing significant about the original game to remain a mystery.

There is something revealing in the demand for a definitive repo. It is not enough that the modern executable feels right. A hypothetical reader should be able to follow every decision to a source byte, emulator trace, test and carefully bounded conclusion. This makes the work slower in places, but it also turns an eleven-day burst of parallel agents into an accumulating body of knowledge rather than an opaque pile of code.

The useful lesson for future reconstruction projects sits naturally inside this story: enthusiasm can create momentum, rivalry can clarify standards, and parallel automation can create startling throughput. But sustainable quality comes from explicit ownership, evidence that survives expired CI artifacts, release gates that refuse overclaiming, and an understanding of when a beautiful demo is still only a demo.

At the close of this diary window, UR-Recomp had crossed important visual, media and product-integration thresholds. It was becoming recognizable as the desired 4K remaster while simultaneously sharpening the technical reference beneath it. The polished beta remained ahead. The difference from earlier days was that more of the claim could now be shown moving.

## Sources and boundaries

Conversation archive: `PROJECT-CONVERSATIONS-2026-10-10-RECONSTRUCTED.md`. Recent merged-main evidence referenced here includes #1189–#1202, #1208–#1218, #1221, #1228–#1249, #1253–#1282 as specifically named above. The PR ledger is high-volume and concurrent; a PR mentioned for technical context does not imply its full release gate is closed. Temporary one-shot workflow PRs marked NEVER MERGE are not treated as product merges.
