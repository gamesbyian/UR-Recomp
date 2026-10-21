# Field Guide: Beginning an Agent-Driven Game Remaster

**An evidence-derived companion to the [Uniracers Production Diary](README.md).** This is a retrospective set of practices drawn from one unusual project, not a universal method or a claim that UR-Recomp is already finished. Each pattern points to a documented episode, concrete artifact or unresolved limitation. Read the narrative volumes first if you want to understand *why* these recommendations exist.

## 1. Begin with a player-facing contract

**Observed practice:** Ian specified a modern 4K widescreen product with controller-first menus and features, while demanding original gameplay behavior rather than a newly balanced approximation. That dual condition governed every major subsystem. A proposed shortcut had to preserve the guest game's authority, and a screenshot had to satisfy both art and source identity. [Diary 01–03](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md), [episode 39](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md), [Modern design](../docs/MODERN-FRONTEND-MASTER-DESIGN.md).

**Apply:** Write down in two separate columns what may change (presentation, accessibility, UX, platform infrastructure) and what must not (physics, scoring, original timing, accepted source identity), plus what requires human aesthetic approval. If your goal is an inspired remake rather than a high-fidelity remaster, say so explicitly; do not inadvertently adopt this project's strict release denominator.

**Failure to avoid:** Letting an agent infer “faithful” from appearance alone.

## 2. Reuse existing code, but qualify its origin

**Observed practice:** The project used SNESRecomp, Baldosa native work, malmazuke's reconstruction, and historical third-party scripts. The productive shift was to compare three implementations before starting a fourth, while refusing to treat PAL source facts as automatically authoritative for USA timing. [Diary 37–38](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md), [trusted adoption rules](../docs/TRUSTED-UPSTREAM-ADOPTION.md).

**Apply:** For each lane, inspect existing source, license, version, target region, test coverage, and the smallest reuse candidate. Test against *your actual authoritative binary*. Keep a written verdict: reuse, adapt with validation, bounded pilot, or new implementation.

**Failure to avoid:** Copying a plausible algorithm from a different regional/version source without preserving provenance.

## 3. Preserve an exact research substrate before scaling agents

**Observed practice:** Early ROM fingerprints, deterministic fixtures, symbols and an evidence corpus made otherwise ephemeral agent findings reusable. Later historical replay comparisons exposed misleading host-frame alignment, and source-exact fixtures prevented naive byte equality from becoming a false causal claim. [Diary 02, 05, 08, 10](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md), [research ledger](../docs/RESEARCH-LEDGER.md).

**Apply:** Establish canonical target hashes, independent reference runner, deterministic input fixtures, event definitions, a current source map, ROM/reference privacy rules and a small negative-test suite. Record the experiment question, exact inputs and source revision before presenting an answer.

**Failure to avoid:** Running many clever experiments against objects whose identity or semantic phase cannot be established.

## 4. Give each agent an exclusive lane, but one shared definition of truth

**Observed practice:** Agents owned CPU/APU producer evidence, original/native independent QA, Modern product, graphics and release integration in separate branches. Producer evidence and independent acceptance remained distinct, preventing an attractive trace or successful hosted journey from automatically becoming a release gate. [Diary 44–48](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md), [work queue](../docs/WORK-QUEUE.md).

**Apply:** Appoint a single writer for mutable queue and release ledgers; label which agents produce candidates, independently review them and integrate them. Specify cross-lane interfaces and source boundaries, not merely a list of files each agent may edit. Require fresh-main/PR review before implementation.

**Failure to avoid:** Two agents independently granting the same gate or modifying the same evolving authority.

## 5. Separate a scheduled worker from the identity of its job

**Observed practice:** Ten scheduled positions followed a mutable list, creating a continuity problem when assignments moved. The director questioned how workers would remember what they had been doing and suggested per-lane logs. Stable objective IDs and journals emerged in response. [Diary 67–68](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md), [#2085](https://github.com/gamesbyian/UR-Recomp/pull/2085), [#2091](https://github.com/gamesbyian/UR-Recomp/pull/2091).

**Apply:** Use separate fields for **schedule slot**, **stable objective ID**, **current owning agent**, **branch/PR/source SHA**, **last accepted evidence**, **open blocker** and **next bounded action**. Keep job continuity independent of the latest chat session.

**Limit:** For two or three agents, an issue and dedicated branch may suffice. Don't reproduce an elaborate Vault unless publishing/recovery problems demand it.

## 6. Keep GitHub first, and know exactly what a recovery archive means

**Observed practice:** Some useful work lived outside GitHub after interrupted or denied publication, and recovery census found hundreds of files and archives. That proved preservation could succeed while integration remained unresolved. The program moved to bounded GitHub-first attempts and exceptional Drive fallback. [Diary 60, 68, 70](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md), [recovery runbook](../docs/recovery/GITHUB-FIRST-PUBLICATION-RUNBOOK.md), [recovery issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).

**Apply:** Treat a recovery item as **unreviewed source/evidence**, with original digest and its provenance. Check exact contents against latest main for true missing behavior and tests, then merge through normal review. Preserve unresolved originals; never claim that an archive count equals integrated feature count.

**Failure to avoid:** Copying entire stale branches into main or turning the fallback archive into a second uncontrolled source of truth.

## 7. Optimize for useful answers, not runner occupancy

**Observed practice:** A few agents generated 108 active/queued CI runs; later 10,000-case research factories competed for an account-wide 20-runner pool. The eventual strategy introduced trigger controls, stopping criteria, resumable campaigns and decision-relevant yields. [Diary 24–27](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md), [40–41](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md).

**Apply:** Before large experiments, require a hypothesis, decision it affects, cheapest discriminator, expected cost and stop rule. Make CI selective; let agents work on independent useful tasks while checks run. Track runner-hours and unresolved decisions, not merely PR count or executed cases.

**Failure to avoid:** Treating expensive activity as a proxy for product completion.

## 8. Make the QA denominator explicit before congratulating yourself

**Observed practice:** The project simultaneously demonstrated real native Windows player paths, matching source frames and several saved-run proofs while still reporting **0/45** strict complete original/native USA events and **0/12** accepted physical Windows gates at the October 20 historical cutoff. [Diary 52–54, 61–66, 71](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md), [release ledger](../docs/RELEASE-QUALITY-LEDGER.json).

**Apply:** Define complete player journeys, required original/native traces, source-identified artifacts and physical acceptance *before* measuring passes. Label partial, held, source-only, synthetic, hosted and independently accepted. Never replace a strict result with a more flattering numerator.

**Failure to avoid:** Lowering the acceptance criterion because a genuinely useful subsystem remains below the release threshold.

## 9. Keep code quality, original fidelity and artistic approval separate

**Observed practice:** 4× procedural racer sprites could have technically valid pose mappings while failing the director's likeness standard. Authentic 1P frames could match while results/greyscale phases diverged, and host-widened world could function while a title-to-original-attract handoff remained unfinished. [Diary 17, 48, 53, 63, 69](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md), [character authority](../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md).

**Apply:** Keep separate acceptance matrices for compilation/tests, original CPU/PPU behavior, user interaction, visual likeness, final output and release readiness. Give a named human creative authority final say on art without permitting subjective preference to override measured emulation fidelity.

**Failure to avoid:** Using “the screenshot looks right” to certify guest correctness or “the shader test is green” to certify the art.

## 10. Write your own history while the work is happening

**Observed practice:** The original diary was written in multi-day batches, then rebuilt into episodes because decisions and director-agent interactions had been submerged in PR summaries. The archive contained incomplete or reconstructed conversations; a chronicler can recover much, but cannot reconstruct invisible talk honestly. [Editorial guide](PRODUCTION-DIARY-EDITORIAL-GUIDE.md).

**Apply:** Capture multiple meaningful events per active day, with dates, original quotes when available, a short causal story, evidence links, rejected alternatives, exact implementation disposition, and later corrections. Treat the human director's questions and ideas as a first-class event type. Keep first-person narrator synthesis separate from purported firsthand observation.

**Failure to avoid:** Waiting until the project ends, then narrating every outcome as obvious in retrospect.

## A minimal starter template

You can start without a ten-agent board or a research Vault:

1. One product contract, one source/rights inventory, one canonical target binary and runnable original reference.
2. One repository with `AGENTS.md`, a live priority queue, an evidence ledger and strict branch/PR convention.
3. Two or three exclusive lanes: native/source fidelity; product UI/packaging; independent validation.
4. One end-to-end test from clean startup to meaningful gameplay and durable result.
5. Daily observations from the director's questions, agent findings, verified changes and failures.
6. A weekly retrospective measuring critical-path progress, expensive dead ends, integration overhead and changing assumptions.

Scale agent concurrency only after knowing what each new worker will own, how its output is reviewed and where it will publish progress. The strongest lesson from UR-Recomp is not that more agents automatically create more software. It's that **delegation, verification, integration and memory all require deliberate engineering**.

*Evidence classification:* This guide describes documented patterns, but it has not experimentally compared UR-Recomp with an identical human-only project. Assertions about speedups or superiority to conventional workflows remain unproven unless future measurement establishes them.
