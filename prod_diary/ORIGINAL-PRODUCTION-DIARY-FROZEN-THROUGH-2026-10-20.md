# Original production diary: complete pre-rebuild compilation

**Frozen editorial baseline:** October 20, 2026. This is a byte-for-byte (at section level) concatenation of the ten standard pre-rebuild diary files. Their original paths remain in the repository unchanged. This compilation is kept for historical comparison, **not** ongoing updates. The contemporaneous reconstructed conversation files and Cajun edition remain separate and untouched.


---

## Archived source 1: [PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md)

# UR-Recomp Production Diary

**Period:** 2026-09-28 through 2026-10-04  
**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`

This is the narrative production diary for the first intensive UR-Recomp excavation sprint. It is synthesized from the project conversation transcripts in `prod_diary/`, merged and superseded pull-request descriptions, the research/plan documents those conversations produced, and the repository state that survived reconciliation.

It is deliberately written as an engineering journal rather than a complete changelog. Pull requests remain the authority for exact diffs and CI evidence. The diary records what the project was trying to learn, what changed the working model, which dead ends were useful, and why the next work became the next work.

---

## 2026-09-28 — From “could this be remade?” to an instrumented excavation project

UR-Recomp began with a deceptively simple question: whether *Uniracers* would make a good modern remake project. The answer rapidly stopped being about copying a 1994 game in Godot and became a much more interesting proposition: use modern reverse-engineering tools and AI coding agents to excavate the original program deeply enough that a new implementation can be tested against the old one rather than merely tuned until it “feels close.”

That distinction became foundational. The visible game is compact: riderless unicycles, small course tilesets, race and stunt modes, a comparatively modest UI. The behavioral problem is not compact. Acceleration, jumping, rotation, landing validation, boost economy, collision, camera behavior, CPU racers, course geometry, tricks and timing all interact. A conventional remake could reproduce the broad design while missing the machinery that makes the game recognizable. UR-Recomp instead adopted a forensic reconstruction model: extract evidence, build deterministic experiments, infer semantics, and only then reproduce or deliberately modify behavior.

### Repository bootstrap

The repository was created as `gamesbyian/UR-Recomp`. The first useful milestone was not a rendering mock-up but a reproducible technical substrate:

- the USA retail ROM was fingerprinted and characterized as a 2 MiB LoROM with 8 KiB SRAM and no coprocessor;
- early SNESRecomp analysis and native bring-up work reached a verified title screen;
- the project began recording symbols, research evidence and open questions rather than leaving discoveries in chat;
- the RNC compression family was identified as a major content boundary, with the eventual corpus containing 45 valid Method-1 streams.

The emerging rule was simple: if an observation could matter later, it should have a durable repository home and provenance.

### Building a reference corpus

PR #2 established the first external reference corpus. This was the point where “research” became a repository feature rather than an ad hoc browsing activity. Public documentation, historical reverse-engineering notes, emulator implementation evidence, cheats, graphics references and provenance metadata were catalogued. Material with unclear redistribution rights was indexed and summarized rather than copied wholesale.

PR #3 then reconciled repository hygiene and the research toolchain, while PR #4 added a synthesized knowledge layer under `docs/knowledge/`. That knowledge layer was intentionally secondary to evidence. Agents could use it to orient quickly, but the research ledger, symbol tables, generated analysis and pinned external sources remained the authority.

This distinction mattered immediately. The project was going to have many AI agents touching the same subject from different directions. A compact synthesis layer saves context; a provenance-first evidence layer prevents the synthesis from quietly turning guesses into facts.

### The first deterministic oracle

PR #5 was the first major shift from archaeology to experimental science. A controller-only route from clean boot to the first one-player race was recovered and replayed through both the native SNESRecomp build and a pinned Snes9x-based reference path.

The route passed through the expected frontend states and reached active race state without poking game state. That gave the project something far more valuable than screenshots: the same input program could be run against two implementations while recording complete WRAM checkpoints.

The first full comparison looked alarming at first. Early frontend checkpoints differed by hundreds of bytes, and the settled race entry still differed at seven bytes. Instead of treating byte inequality as proof of broken simulation, PR #6 reduced those seven bytes to causes:

- four bytes in page `$01xx` were stale stack history;
- the remaining bytes were free-running timing/phase counters;
- none represented an unexplained persistent gameplay-state divergence.

That produced an early methodological lesson that kept resurfacing later: **whole-machine equality is often too strict to be a semantic oracle.** The project needed event-relative, meaning-aware comparisons, not a fetish for every byte matching at the same host frame.

### Moving from race entry to race behavior

PR #7 extended the deterministic harness into race behavior. Straight-line acceleration was tested first because it was a low-confounder probe. Recovered X position and signed X speed fields matched between native and Snes9x at event-relative checkpoints. Then came jump experiments.

The first B-button pulse appeared to correlate with an airborne state, but closer comparison showed the changing field belonged to the other racer. A matched no-B control demonstrated that the short pulse had not launched player 1 at all. The failed experiment was retained as negative evidence, and the fixture was changed to a sustained B hold matching the behavior of the recovered historical bot. That finally produced a causal player-1 jump, again matching across engines.

This was an important tone-setter for the project. An attractive interpretation was discarded because the control contradicted it. The negative result improved the model instead of being papered over.

### Archaeology broadens, but with boundaries

In parallel, the project began collecting the historical ecosystem around *Uniracers*: old bots, TAS material, reverse-engineering notes, press materials, SNES development tools, emulator quirks and developer references.

A recurring concern was whether external tools were trustworthy enough to become infrastructure. PR #8 started auditing imported and pinned tooling rather than treating it as a black box. PR #10 formalized “research before reinvention” as an agent rule: after a few materially different local attempts fail, broaden the search to analogous work in emulator, ROM-hacking, decompilation, TAS and console-development communities before building another custom instrument.

The project also adopted an important naming discipline. “Widescreen” and “HD” were features, not names for the project itself. UR-Recomp was becoming a reconstruction and modernization platform whose core obligation was exact behavior. Presentation changes would sit on top of that.

### End-of-day state

By the end of September 28, UR-Recomp had crossed the line from speculative hobby project to reproducible research environment. It had:

- a native executable reaching real game states;
- a reference emulator path;
- deterministic input fixtures;
- full-WRAM comparison;
- a provenance-first reference corpus;
- a growing symbol and knowledge system;
- a toolchain that was being audited instead of blindly trusted;
- a clear project thesis: recover behavior well enough that fidelity can be mechanically tested.

The next problem was scaling that methodology without letting the repository become dependent on a sprawling collection of network-fetched tools and fragile CI experiments.

---

## 2026-09-29 — Turning the tool shelf into a research system

The second day was less glamorous and arguably more important: the project began making its tools reproducible, headless and eventually self-contained.

### Auditing third-party code

The third-party tooling audit, eventually reconciled through PR #12, treated imported code and external tools as evidence-bearing dependencies rather than conveniences. Several classes of issue surfaced:

- build recipes that assumed interactive GUI environments;
- scripts using unsafe or unnecessarily opaque shell invocation;
- historical code containing duplicate keys or type-width assumptions;
- emulator implementations whose *Uniracers*-specific hacks made them poor independent corroborators for certain hardware questions.

That last point was especially significant. Snes9x was invaluable as a behavioral oracle, but it explicitly contained special handling for *Uniracers*. Therefore, agreement with Snes9x around the notorious active-display OAM behavior could not count as independent hardware validation. The project began distinguishing “useful reference behavior” from “independent architectural corroboration.”

PR #13 then optimized the toolchain around the way agents actually use it: headless CI, command-line and library surfaces, pinned revisions, and no default building of heavyweight GUI targets that were irrelevant to automated experiments.

### Building an offline island

The user pushed for an unusually strong constraint: core research should remain usable even if external services disappear. PR #15 elevated repository islandization to Priority 0. PR #21 made the contract executable, with a `third_party/` boundary, machine-readable migration/provenance metadata and an offline bootstrap mode that fails closed instead of silently going to the network.

PR #23 landed the first real vendored tranche, `mesen-for-ai`. This turned “self-contained someday” into a concrete migration path.

The island effort had two motives. One was ordinary reproducibility. The more interesting one was agency: if the source for the tools is in the project, agents can inspect, patch and specialize them instead of routing around upstream limitations.

### UI and presentation references become first-class research surfaces

PR #11 mapped frontend UI states and navigation into an evidence-labelled state graph and reverse lookup. This served both automation and future presentation work.

PR #14, later reconciled as #18, added the HD visual-reference pipeline. Importantly, it did not declare an upscaler authoritative. Native ROM/framebuffer evidence remained the ground truth. Modern scalers, shaders and bsnes-hd were positioned as comparative visual workbenches: useful for reconstructing how source art might plausibly look at higher resolution, but never substitutes for semantic evidence.

### Course structure and runtime data paths

The course-format lane also matured. Work following PR #9 corrected an easy-to-make instrumentation error: an interpreter bridge scope entry had initially been treated as the exact store instruction. Static source alignment showed otherwise. That correction reinforced another project habit: trace labels describe what the instrumentation actually measures, not what the investigator wishes they measured.

The course work continued to connect the 45 RNC streams to decoded course structures, cursor paths and runtime materialization. This would later become crucial to Widescreen, because widening the camera safely requires knowing which world data is authoritative, which data is streamed for presentation, and where those two concerns diverge.

### CI becomes part of the experimental apparatus

The growing number of one-off probes exposed a workflow problem. A successful experiment could still fail at persistence because `analysis/generated/` matched a broad ignore rule. PR #22 fixed the repository rules and harvested the evidence that had already been computed.

This episode accelerated a larger shift: CI was no longer just “tests that protect code.” It was a laboratory scheduler. That meant its triggers, artifacts and persistence semantics needed the same rigor as the code under test.

### End-of-day state

September 29 left the project with a far more disciplined operating environment:

- research tools had explicit trust/provenance posture;
- headless operation was preferred and documented;
- offline/islandization had become an executable program rather than aspiration;
- frontend states and visual-reference generation had durable models;
- course/runtime investigation was producing evidence that would later constrain Widescreen safely;
- CI failures were increasingly classified as experimental-infrastructure problems rather than generic red/green status.

The remaining archaeology was now rich enough to begin mining historical artifacts for semantics rather than just collecting them.

---

## 2026-09-30 — Historical bots become executable documentation

By September 30 the project had accumulated enough old material that the question changed from “can this be found?” to “what can this tell us mechanically?”

### Acquisition closes into triage

The archive hunt continued through PRs in the 70s and 90s, but the process became more selective. Old development tools, emulator notes, TAS recordings, bot scripts and reverse-engineering files were preserved when they could answer concrete questions.

A major recovery was the historical Uniracers bot/TAS material associated with Dessyreqt, USJO and Nitrodon. PR #93 preserved a nine-file Nitrodon archive with hashes and provenance; PR #94 mined it into a structured semantic index.

This produced corrections, not just confirmations. Historical labels were compared against current runtime evidence and some were reinterpreted:

- tabletop state behaved as duration/progress rather than a simple accumulated count;
- stunt counter widths and twist semantics were refined;
- shared working slots were separated from stable per-player fields;
- useful routine seeds were identified for stunt finalization, vertical acceleration, controller decode and HUD/message handling;
- an exact base-5 stunt-combination index into a 625-byte table was recovered.

The important part was the reconciliation rule: historical annotations remained historical unless corroborated. The archive could accelerate investigation without becoming scripture.

### USJO as a semantic oracle

PR #80 turned recovered USJO v8 into a validation matrix rather than a bag of memory addresses. Three fields were runtime-confirmed, several others received strong static support, and the bot’s reward/control model was extracted into generated artifacts.

PR #81 followed with runtime probes. Native and Snes9x agreed on sampled recovered fields during rotation experiments. Some interventions were deliberately negative: an X-button probe produced no sampled gameplay difference under that timing. Instead of concluding “X does nothing,” the project recorded the narrower result and noted that the historical bot used state-dependent timing, so the next experiment needed to reproduce cadence rather than just press the same button.

That pattern recurred in tabletop work. Transient fields could be missed by sparse checkpoints, so the project added transition extraction and event-relative comparators. Eventually, a causal 0→1→2→3→4→0 tabletop sequence was retained and reconciled.

### Exact historical replay is harder than expected

The project repeatedly attempted to replay historical TAS/bot inputs exactly. The 2008 WIP material desynchronized under the modern reference path before reaching the expected race, demonstrating that “same ROM + same nominal inputs” does not guarantee the same outcome when emulator timing assumptions differ.

That was useful evidence. Historical recordings were reclassified according to what kind of oracle they could serve. Some were excellent sources of controller policy and RAM semantics even when they could not be treated as frame-exact regression inputs.

### Audio archaeology and side lanes

A separate audio lane showed how the project could make progress without disturbing the active gameplay-fidelity line. PR #83 reconciled the CPU-side audio record pool, tied unreachable song records to preserved unused-song SPC captures, and mechanically correlated package blocks against known SPC snapshots.

This was not on the critical path to a remaster, but it demonstrated the value of the evidence architecture: a specialized archaeology lane could operate safely in parallel, produce compact generated facts, and merge without contaminating gameplay conclusions.

### CI hygiene becomes necessary for velocity

With many agents and many experimental workflows, GitHub Actions began doing too much work. PRs #96–#99 progressively narrowed triggers, added per-ref cancellation, isolated tool-specific dependencies and converted one-shot research workflows to manual dispatch where appropriate.

The principle became explicit: exploratory workflows should remain available without behaving like permanent regression gates. Genuine regressions should run on PRs and main; one-off archaeology should not wake up every time a planning document changes.

### Comparative archaeology is planned

PR #100 promoted the four-ROM corpus into a comparative code-analysis program. The USA retail, Europe retail, PAL prototype and legacy beta were no longer just sources for occasional byte diffs. They became a structured way to discover stable semantic islands and to distinguish relocations, inserted regional code, data and analyzer disagreements.

This decision would dominate the next phase.

### End-of-day state

By the end of September 30, UR-Recomp had something unusual for a reverse-engineering project this young:

- historical automation had been converted into runtime-testable semantic hypotheses;
- old RAM maps were being corrected by current evidence;
- multiple independent research lanes could run without trampling each other;
- CI had been reshaped around the difference between experiments and regressions;
- the four-ROM corpus was poised to become a semantic multiplier.

The project was ready to move from individual clues to systematic structural recovery.

---

## 2026-10-01 — From isolated facts to a semantic map of the game

October 1 was the high-volume excavation day. The repository accumulated a large number of structural, behavioral and planning PRs. The raw count is less important than the transition they represent: the project stopped asking only “what does this address do?” and began recovering coherent subsystems.

### AI-assisted reverse-engineering becomes explicit methodology

PR #119 codified the working method in `docs/AI-ASSISTED-REVERSE-ENGINEERING.md`. The document collected practices the project had already discovered empirically:

- deterministic fixtures before interpretation;
- cheapest discriminators first;
- code/data coverage;
- perturbation and controlled mutation;
- context packets for agents;
- mechanical oracles wherever possible;
- explicit dead-end recording;
- escalation to emulator/test-ROM/hardware evidence when software references are ambiguous.

The goal was not to make agents “smart enough” to reverse-engineer unaided. It was to shape the environment so that agent mistakes become cheap, visible and correctable.

### Comparative ROM recovery scales up

The multi-ROM program began identifying bounded structural islands with accepted call edges and clean semantic boundaries. Across many PRs, routines in course materialization, race control, geometry, camera, rendering and message handling were recovered and compared across the four preserved ROMs.

The strongest pattern was structural conservation with regional relocation. USA retail and the legacy beta were often byte-identical. PAL prototype and Europe builds frequently shifted routines while preserving opcode roles. Where a regional build grew internally, the analysis stopped forcing a single constant offset and instead recorded local shift profiles and edit scripts.

That detail matters because it marks a maturation in the comparative method. A simplistic “Europe = USA + N bytes” model works until it doesn’t; the repository learned to preserve the shape of disagreement rather than normalize it away.

The structural census grew rapidly, but by the end of the day that growth was itself becoming a risk. It is easy to optimize the number of recovered bytes instead of the ability to answer project questions.

### Multiplayer fidelity exposes small but meaningful drift

A multiplayer lane found a concrete native/Snes9x divergence in racer state, with small differences in position and velocity. Rather than dismissing them as noise, the project isolated multiplayer HUD, viewpoint, camera and culling work into separate lanes.

This produced a useful organizational pattern: multiple agents could inspect adjacent subsystems if each lane had explicit ownership boundaries. “Safe separate line of work” became a recurring operational request, and PR reconciliation routines were developed to rescue useful orphan branches without forcing stale histories onto main.

### Course representation becomes presentation-sufficient

The course-format work moved beyond “we can decompress it.” By the end of the period, the project understood enough of Dragster’s spatial contract to support presentation reasoning:

- raw dimensions resolve to a 1024 × 16 grid of 64-unit coarse sectors;
- the representative world domain is 65,536 × 1,024 world units;
- a 16,384-entry u16 table maps coarse sectors to fine records;
- fine records resolve 64×64 sectors into 16×16 world cells;
- runtime materialization, sector-neighborhood gathering and surface sampling were connected.

This was deliberately called **presentation-complete**, not editor-complete. The project did not need every authoring semantic decoded before it could reason safely about what the renderer should expose outside the classic viewport.

That distinction saved time. It separated “what must be known to widen presentation” from the much larger task “what must be known to build a full course editor.”

### Graphics provenance reaches exact round trip

The racer presentation lane reached a similarly useful sufficiency threshold. Exact asset streams, frame identifiers, race-init OBJ graphics resources and palette provenance were tied together. Original 4bpp data could be extracted and reconstructed byte-for-byte.

This meant future HD work could be anchored to semantic frame identity rather than screenshots alone. The project now had a bridge from gameplay state to the exact original graphics data used to present that state.

### Save/load persistence is proven; progression is not

PR #188 proved real game-authored SRAM persistence. A reset-anchored bot run changed checksum-protected SRAM, emitted a valid 8 KiB save, and that save reloaded in a fresh reference process byte-for-byte with its checksum intact.

But extending the fixture did not produce medal or tier mutation. PR #191 retained the negative medal/chord experiments and explicitly refused to call the progression-changing acceptance item complete.

This is a good example of the project’s evidence discipline. “Save/load works” and “winning progression survives save/load” are adjacent but different claims. The first was closed. The second remained open.

### The plan is deliberately re-prioritized

By PR #183 the structural census had become large enough that the project paused to ask whether more structural islands were still the best use of effort.

The answer was: only when they unlock a concrete semantic capability.

The new `docs/SEMANTIC-SUFFICIENCY.md` introduced a more useful model:

1. **observe** the relevant state;
2. **explain** the causal mechanism;
3. **modify safely** without changing unrelated behavior;
4. **validate** against a trustworthy oracle.

This reframed the next priorities around renderer-facing causal closure, gameplay-object activation, finite fidelity matrices and small Widescreen discriminators. Structural recovery received an admission/stop rule so byte-count growth could not become an end in itself.

This planning pivot is probably the most important project-management event of the sprint.

---

## 2026-10-02 — Widescreen stops being a vague feature and becomes a causal experiment

The next phase began with a deliberately tiny question: what happens if the host presentation is widened by only eight pixels?

That sounds trivial. It exposed exactly the sort of hidden coupling the project had been preparing to diagnose.

### First: establish the presentation contract around the classic viewport

PR #184 completed the representative Dragster spatial/resource contract needed for Widescreen work. PR #189 then reconciled the object activation timeline.

The key result was that presentation and gameplay activation are not the same boundary. The finish/checker presentation appears before the later collision/contact-derived behavior transition. Therefore a wider renderer must be allowed to reveal presentation earlier **without** widening the gameplay activation domain.

That rule is crucial. A naive Widescreen implementation that simply makes “visible” objects active sooner could alter races.

### Tiny-margin Widescreen produces a red flag

PR #190 added a staged 0/+8/+16/+24 margin probe. The harness worked, but +8 failed the initial authoritative-state equality gate against the 4:3 control.

At first glance this looked like the nightmare result: adding eight pixels changed simulation.

The project did not accept that interpretation without classification.

PR #202 updated the plan so the immediate task was specifically to distinguish:

1. checkpoint/capture misalignment;
2. harness bookkeeping;
3. host-presentation timing perturbation that leaves meaningful simulation intact;
4. genuine simulation dependency on presentation width.

### The “simulation divergence” collapses into cadence

PR #204 closed that classification.

The +8 run was already three guest frames ahead during the frontend, before the race began. That same offset persisted through race entry and the retained Dragster checkpoints. When compared event-relatively, durable race state matched: position, velocity, camera, checkpoint/gate state and laps. The progression transition occurred at the same semantic event.

A transient field differed briefly and then reconverged without affecting trajectory or progression.

The original whole-WRAM equality rule had therefore been too strict. The widening changed host cadence, not meaningful retained-race simulation.

This result echoed the seven-byte race-entry investigation from the first day. The project had now encountered the same methodological trap in two very different contexts: comparing machines at the same nominal frame can manufacture “divergence” out of timing residue.

### Then a real rendering failure appears

Once the harness was fixed, PR #205 found the first actual +8 presentation regression.

It was wonderfully small: two pixels at classic x=255 during a specific object-tail checkpoint.

The causal narrowing was strong:

- guest OAM was byte-identical at onset;
- BG-only and OBJ-only output each matched at the onset checkpoint while the composite differed;
- the first OBJ-only divergence appeared later;
- the first OAM divergence appeared later still, too late to cause the onset;
- SNES sprite-limit accounting was ruled out;
- the runner’s pinned-window expansion was ruled out.

That moved the bug from “Widescreen breaks something” to a very specific host-renderer composition/edge-semantics question.

PR #206 then recorded another valuable negative result. A layer-mask experiment seemed like an obvious causal discriminator, but disabling layers changed guest cadence enough to invalidate the comparison. The instrument perturbed the phenomenon it was measuring. The project retained that as negative instrumentation evidence and moved to a bounded host-only trace that left the full renderer path intact.

This is the kind of failure a production diary should preserve. The discarded test was not wasted effort; it established that layer masking was not causally clean enough for this timing-sensitive seam.

### Closing the camera-to-VRAM scrolling chain

In parallel, the renderer-facing preparation/streaming lane finally identified the active Dragster scrolling transport.

PR #192 had preserved compact update-list structures at `$0DCD/$0DCF`, but the runtime fixture observed those counts remaining zero. The tempting interpretation would have been that the fixture was bad. Instead, later work showed the compact lists were simply not the active scrolling path in this scene.

PR #203, reconciled through #208, closed the actual chain:

- camera state updates;
- camera/window helper computes entering-edge coordinates;
- entering columns are materialized into a `$03xx` DMA descriptor family;
- NMI consumes those descriptors;
- the horizontal presentation behaves as a 32-column VRAM ring.

Other plausible live paths were classified and excluded rather than forced into the story: one was HUD/message tilemap emission, another racer-presentation graphics preparation.

This is exactly the kind of causal closure the semantic-sufficiency plan was demanding. Widescreen work now has a concrete route from camera movement to streamed presentation data rather than a collection of adjacent addresses.

### Consolidation and inference audit

PR #207 performed a broad evidence consolidation and two-pass inference audit. This was not just documentation cleanup. Once facts from RNC headers, historical track landmarks, SRAM medal rows, paired racer data and deterministic fixtures were normalized into common datasets, new deductions became possible.

Among the reconciled results:

- canonical RNC stream/name/tour order was corrected;
- Dessyreqt track IDs map cleanly as `stream_index - 1` across all 45 courses;
- historical start/finish landmarks were attached across the full corpus;
- paired header coordinates were strengthened into a paired racer-spawn model;
- cross-course relationships and a stunt-signature pattern became visible;
- normalized progression, course-resource and deterministic-fixture catalogs were added;
- the state schema absorbed regional WRAM clusters and reconciled historical semantics.

This validated the earlier intuition that the project had reached the point where **consolidation itself could generate new knowledge**. Facts that were individually weak became useful when aligned by course, player slot, region and runtime role.

PRs #208 and #209 then updated the canonical plans so future work consumes those normalized query surfaces rather than rediscovering relationships from scattered Markdown.

### Quiet-repo reconciliation becomes routine

Several PRs in the #193–#201 range existed primarily to rescue completed work from stale or orphaned branches and replay it onto current main. This happened often enough to become an operational pattern:

- do not babysit CI unnecessarily;
- do not merge stale branch history merely because useful work exists inside it;
- identify unique files/evidence;
- transplant cleanly onto current main;
- supersede redundant PRs explicitly;
- update canonical plans only after the merged state is known.

That process sounds mundane, but it is essential in a repository where multiple AI agents can produce valid work concurrently faster than a human would normally sequence it.

### End-of-sprint state

At the end of this diary period, UR-Recomp was no longer merely “a recomp that can run *Uniracers*.”

The project had developed:

- deterministic frontend and race fixtures;
- event-relative native/reference semantic comparison;
- confirmed movement/jump state anchors;
- game-authored SRAM round-trip acceptance;
- a large, region-aware structural map of important subsystems;
- historical RAM/bot semantics reconciled against runtime evidence;
- presentation-complete Dragster spatial/resource knowledge;
- exact racer asset extraction and reconstruction;
- a causal camera-to-VRAM scrolling chain;
- an object activation-versus-visibility timeline;
- a Widescreen probe that distinguished cadence from simulation and isolated the first true rendering regression to a two-pixel host composition seam;
- normalized cross-domain datasets capable of supporting inference rather than just storage;
- a semantic-sufficiency framework to decide when reverse engineering is “enough” for the next implementation step.

The project also accumulated several open questions that were now much sharper than when the sprint began:

- close the host composition/OBJ-edge semantics causing the +8 two-pixel regression;
- obtain a genuine game-authored medal-winning progression fixture and prove save/load acceptance for that state;
- continue finite fidelity closure where native/reference behavior still differs, especially multiplayer;
- use the camera/streaming and activation boundaries to design Widescreen changes that expose more presentation without expanding gameplay authority;
- keep converting scattered evidence into queryable normalized data whenever cross-domain inference becomes cheaper than another bespoke runtime probe.

---

## 2026-10-02, late — The first real modernization layers stop being hypothetical

The earlier October 2 work had reduced Widescreen to causal seams and racer HD work to exact semantic assets. During the rest of the day those seams began turning into product code. This was the point where UR-Recomp started to look less like an excavation project preparing for a remake and more like a remake architecture that could already prove some of its hardest ownership boundaries.

### Progression save/load finally closes

The open progression gap from PR #191 did eventually close. PR #213 used a period-correct Snes9x 1.51 rerecording path and a verified historical 100% movie to obtain a genuine game-authored medal mutation rather than poking SRAM or synthesizing an expected save. The acceptance path watched the real medal matrix, waited for legal checksum-valid game state, captured the mutation, reloaded that SRAM in a fresh current reference process, and checked medal/tier/checksum behavior against the machine-readable progression model.

That matters because the persistence claim is now complete in the form the project actually needed: not merely "an 8 KiB SRAM image can round-trip," but "real progression authored by the game can survive the save/load path and still satisfy the recovered progression/checksum rules."

### Racer graphics move from extraction to a replacement system

The racer lane closed several layers in quick succession.

PRs #210, #212, #215 and #216 tightened the relationship between presentation records, packed cells, DMA source words, staging consumers and stable OAM presentation. PR #218 turned that into deterministic transparent raster extraction, and PR #224 closed the primary/companion composition rules strongly enough that exact composed racer images could be reconstructed from canonical ROM data rather than inferred from screenshots.

PR #220 then made the intended graphics product explicit. The project now treats three representation families as first-class modes over shared semantic identity:

- Original SNES art;
- faithful high-resolution Remastered art;
- a more freely modernized Reimagined art family.

The important architectural decision is that those modes share semantic frame identity, placement contracts and gameplay authority. Art can change without inventing a second simulation.

PRs #230, #236, #238, #239, #240 and #241 built the runtime half of that contract. Replacement selection reads authoritative WRAM without writing it; live position, orientation and object size come independently from the PPU/OAM path; and the native host can decide whether a known semantic composition has a replacement while failing closed for unknown or mismatched states.

PR #249 crossed the line that the previous diary had only been preparing for: the native host actually removed one validated stock racer instance from the presented raster and substituted a deterministic high-density replacement in its place. WRAM, VRAM, OAM and CGRAM remained guest-owned and unchanged.

From there the lane stopped being a single-frame demo and became a coverage program. PR #252 added explicit stock-derived pivot/contact anchors. PR #256 registered the synchronized P2 semantic state. PR #259 recovered the split-screen placement model and proved that both racers appear in both viewports through four host-side presentation instances. PRs #261, #263, #264 and #266 added another synchronized state, temporal-coherence checks, a dense semantic animation trace and exact registry-aware adjacency neighborhoods.

That dense trace changed how coverage was chosen. Rather than selecting convenient sparse checkpoints, the project began registering states by observed adjacency. PR #268 added the first repeated adjacent state. PR #271 removed the assumption that one semantic ID maps to one representation and made registration composition-aware. Subsequent work added duplicate-context, predecessor and forward states, then continued backward through companion-context variants. By PRs #281/#282, #285 and #286, same-primary/different-companion states were being measured against canonical ROM geometry before registration, and distinct synchronized contexts remained distinct even when their visible geometry happened to match.

The practical result is modest in screen area but important in architecture: racer HD is now a live, fail-closed, composition-aware replacement pipeline with deterministic geometry, split-screen placement, temporal evidence and growing adjacency-driven coverage.

### Widescreen advances from diagnosis to native materialization

The +8 work also crossed its implementation boundary.

PR #217 finished classifying the earlier presentation-sequence divergence. The widened run sampled a different presentation/frontend phase class at the same semantic event, while authoritative race state remained aligned event-relatively. PR #219 then showed that the stock preparation path already had a useful neighboring strip schedule. PR #226 mapped the generation seam required to make that result survive SNESRecomp regeneration.

PR #228 turned the accepted +8 experiment into a real native hook while preserving stock 4:3 as the untouched control. The implementation reused the stock preparation/helper path rather than building a parallel guest renderer.

The next constraint appeared at +16. PR #257 established the ownership split that the project had been circling around: the first extra column can use the accepted guest +8 path, but further presentation capacity belongs to the host. The accepted +16 experiment proved a second host-owned column against later stock evidence while leaving camera, collision, activation, progression and simulation unchanged. Attempts to manufacture the second column by recursively replaying guest preparation were retained as negative evidence.

PR #280 then rescued the actual course-backed +16 materializer from superseded branches and reconciled its retained liveness evidence into current main. That is a major architectural step. Further widening no longer needs a future-stock oracle as its intended content source; it can be derived from the recovered live course presentation model in host-owned state.

The Widescreen question has therefore changed again. The project is no longer asking whether it can expose eight or sixteen extra logical pixels without changing gameplay. It is now testing how far the host-owned materializer can be generalized, with +24 as the next bounded discriminator and true 16:9 still downstream.

### Restart Race becomes a real modern product feature

The modern-product lane matured just as quickly.

PRs #229 and #231 established host-owned product state and a pause/restart session contract. PR #232 bound Pause to the existing host frame gate. PRs #234, #235 and #237 established an exact race restart anchor, proved deterministic rollback/replay, and made the lifecycle safe across results.

PR #248 then routed Restart Race through the actual modern product command stack rather than a test-only rollback call. PR #253 tightened the critical persistence boundary: Retry restores the race attempt while preserving the *current* 8 KiB SRAM, so retrying after results cannot rewind legitimate progression.

The feature then acquired real player-facing controls. PR #258 added keyboard bindings without synthesizing guest controller input. PR #262 rendered the first host-owned Pause/Retry overlay. Controller navigation followed, and PRs #267 and #269 proved that gamepad-menu and keyboard-hotkey paths converge on the same semantic command policy. PR #273 promoted the whole accepted stack into the ordinary production native host rather than leaving it inside an acceptance harness.

PR #284 added the first ordinary settings behavior on top of that substrate: pause on focus loss. The setting is typed and host-owned, uses the same pause gate, remains inert in Authentic mode, and never borrows racer/save-slot state for product configuration.

This is the first genuinely modern UX surface in the project, and it preserves the core rule established at the beginning: the guest simulation and progression remain authoritative; modern convenience behavior belongs to the host.

### The inference audit catches up with implementation

PR #242 recovered an evidence-tracked scene policy for Widescreen rather than leaving scene assumptions implicit. PR #243 ran a third inference audit across the newly merged progression, racer-native, Widescreen and restart evidence. PR #245 then reconciled the plans after runtime closures, preserving the audit's historical negative findings while recording which issues had subsequently been resolved.

This was another useful test of the project's documentation discipline. An audit finding is not silently erased when implementation closes it. The negative observation remains part of the intellectual history; current disposition is layered on top.

### Platform and display policy become explicit product architecture

Late in the day the project also answered a question that had remained oddly unspecified: what machines is this thing actually intended to run on?

PR #287 made Windows x64 the primary consumer/reference target and recorded additional personal-use targets for macOS, a best-effort High Sierra-compatible legacy Mac build, Web, Switch homebrew and PlayStation 5. The Switch lane is explicitly based on public homebrew tooling and preserved reference examples, with no proprietary SDK material or platform secrets entering the repository. None of these targets get their own simulation fork.

PR #288 separated output resolution, internal render scale and presentation refresh/FPS from the authoritative game cadence. High-refresh output may repeat or interpolate presentation frames, but it cannot accelerate the SNES-derived simulation.

PR #291 then resolved the broader display-geometry policy. Authentic 4:3, raw square pixels and Remastered/Reimagined output are treated as different presentation transforms rather than one hard-coded width. Pixel aspect, overscan, logical view width, filtering, graphics representation, output resolution and presentation cadence are independent axes. Widescreen margins are derived from logical display policy instead of being baked into a single source-width assumption.

That separation should save the project from a common remaster trap: using one convenient renderer setting to smuggle several unrelated design decisions into the same knob.

### Late-day state

By the end of the local October 2 session, several things that had been architectural sketches in the earlier diary were now real:

- game-authored progression save/load acceptance was closed;
- the +8 Widescreen path was a regeneration-safe native hook;
- +16 had a host-owned, course-backed materialization architecture;
- racer HD had performed real native draw-frame substitution and expanded into composition-aware, split-screen, adjacency-driven coverage;
- Pause, Resume and Retry were production native-host features with keyboard/controller UI paths and SRAM-safe lifecycle behavior;
- the first host-owned gameplay-adjacent setting was live;
- platform targets, resolution/FPS policy and display geometry were explicit parts of the product contract.

The center of gravity has moved again. Excavation is still active, but increasingly in service of bounded implementation questions. The project is now proving that modernization can be layered around the original game without quietly taking authority away from it.

---

## Engineering notes from the sprint

Several practices emerged strongly enough to preserve as production rules.

### Negative results are project assets

A short B pulse that failed to jump, an X intervention that failed to change sampled stunt state, a medal chord that failed to mutate SRAM, compact update lists that stayed zero, and a layer-mask experiment that perturbed cadence all narrowed the search space. They belong in the evidence system, not in the trash.

### Compare semantics, not incidental machine residue

Stale stack bytes, phase counters and host cadence can defeat byte-for-byte or frame-for-frame comparisons while meaningful game state remains identical. Exact equality remains appropriate where the data itself is the contract, such as asset round trips or SRAM persistence. Gameplay fidelity often needs event-relative semantic invariants instead.

### Instrumentation has side effects

A debugging mode, render mask, trace hook or timing change can alter the behavior being measured. Every discriminator needs a perturbation model. “More instrumentation” is not automatically “better evidence.”

### Recover only as much structure as the next decision needs

The comparative structural census was extremely productive, but the semantic-sufficiency pivot prevented it from becoming an infinite decompilation project. Structural recovery earns priority when it unlocks observation, explanation, safe modification or validation.

### Historical sources are accelerants, not authorities

Bots, notes and old RAM maps often contain excellent information and occasional mistakes. Their best use is to propose cheap hypotheses that current fixtures can test.

### Consolidation is an inference tool

Once course data, progression data, regional correspondences, historical landmarks and runtime fixtures are normalized into compatible schemas, relationships emerge that are difficult to see in prose. Data-model work is part of reverse engineering.

### The repository itself is the lab notebook

Conversations generate hypotheses, but durable evidence must land in the repository. PR descriptions explain experimental intent and outcome; generated data preserves machine results; plans state what remains; `prod_diary/` preserves the human-scale narrative that connects them.

---

## Production status at 2026-10-02

The core risk has changed.

At project inception, the major uncertainty was whether enough of *Uniracers* could be recovered from the compiled SNES ROM to support a faithful modern implementation. The first sprint strongly suggests that the answer is yes. The logic is discoverable, the data structures are tractable, historical material is unusually useful, and modern agents can operate a fairly sophisticated deterministic reverse-engineering loop when the repository supplies good oracles and evidence discipline.

The harder remaining problem is deciding where exact reproduction ends and intentional modernization begins.

That is a much better problem to have.

Late-session work strengthened that conclusion. The project now has working examples of the intended layered architecture: authoritative guest simulation underneath host-owned Widescreen materialization, semantic HD substitution, modern session controls and display policy. The remaining difficulty is increasingly one of coverage, composition and productization rather than proving that the separation itself is possible.

---

## 2026-10-03 — The architecture starts behaving like a product

October 3 was the day several long-running research lanes stopped being separate demonstrations and began fitting together as parts of one modern game.

The previous day had already proved the central ownership model: authoritative SNES-derived simulation underneath host-owned presentation and convenience systems. October 3 tested whether that model could survive ordinary product concerns: graphics settings, output geometry, menu structure, real authored art, additional platforms, and CI that had grown large enough to become an engineering problem of its own.

### Widescreen capacity stops being the hard part

The Widescreen lane began the day with host materialization already accepted beyond the original +8 guest lane. PR #283 generalized that materializer through +64 while keeping the same architectural split: +8 remained the single guest-owned secondary descriptor path, while every deeper presentation column lived in host-owned state and came from the recovered live course/resource model.

That changed the question from whether the game could prepare enough scenery to what the widened picture should actually be.

PRs #300–#302 made the display decision mechanical rather than aesthetic. The project gained exact-rational derivation for target margins, then built a review surface over canonical 256×224 captures. Official-manual screenshots were measured as title-specific historical evidence rather than relying only on emulator convention.

Two conclusions followed. Raw 8:7 pixels were not a good model of the intended historical display shape; the evidence supported the 4:3 family and therefore 7:6 horizontal correction for a 256-wide SNES image. Separately, the tempting centered 216-line crop was rejected as logical geometry because canonical menu, transition and race frames contained real authored information in the eight lines it would remove.

The resulting Authentic logical transform became full-height 256×224 at 7:6 PAR. A true 16:9 field therefore requires 42⅔ source pixels of extra width on each side. The practical symmetric integer viewport became 342×224, +43 pixels per side, backed by +48 pixels of strip capacity.

PR #309 then pushed the provider to +72, proving that ordinary-race preparation capacity had ceased to be the blocker. Subsequent work bound the accepted policy into the live host: the provider and viewport could now turn recovered extra world data into an actual wider output while fixed scenes remained conservative.

By PR #336, scene-aware output composition was explicit. Ordinary 1P and ordinary 2P race scenes could request the widened 342×224 view; title, frontend, pre-race and results surfaces failed closed to centered 256×224 unless independently justified.

The architecture was no longer stretch-the-SNES-image. It was a scene-classified, host-owned composition system with a defined display transform, a separate logical-view axis, and stock 4:3 preserved as a regression mode.

### VS proves that split screen is genuinely different

The remaining multiplayer case refused to be hand-waved into the ordinary path.

PR #340 showed that widening the host canvas in VS did not invoke the ordinary-race preparation hook. Importantly, racer state, race progress and tracked camera/view state still matched stock. The failure was in presentation preparation, not gameplay semantics.

PR #342 then found the separate split-screen schedulers. P1 and P2 each used their own horizontal preparation regions, each scheduling an 8-word strip, before rejoining the shared descriptor builder and NMI transport.

That meant VS did not need a second rendering system. It needed a separate producer feeding the already-understood transport.

PR #345 proved the first +8 adjacent strip independently for both viewports. PRs #349, #354 and #359 then walked the same live-course model through +16, +24 and +32 without inventing new guest descriptor lanes. The proof kept the same discipline used elsewhere: exact calibration against accepted +8 events, protected state equality, and no earlier gameplay activation.

The split-screen lane was still incomplete at the end of the day, but it had moved from unknown special case to the same host-owned materialization idea with a different stock preparation seam.

### Racer HD stops being a technical demo and starts becoming art direction

The Racer HD lane crossed a similarly important threshold.

PR #293 closed a continuous fully registered temporal window from frames 1205–1220. That gave the project a stopping rule: no more generic adjacency archaeology just because another neighboring state could be found.

PR #297 converted that closed semantic window into an approval dossier. Each observed representation could now be reviewed with canonical ROM-derived pixels, exact composition guards, verified pivot/contact anchors and real temporal neighbors. This turned the pipeline from a reverse-engineering instrument into an art-production instrument.

PRs #298, #299 and #303 then answered the first visual-language questions. Developer history indicated that the tiny original sprites had been rendered down from much more detailed 3D source artwork. The faithful Remastered target therefore reconstructs coherent high-resolution geometry rather than preserving SNES pixel stair-stepping as if it were intended shape language.

The accepted first-family baseline became smooth source-model-like geometry, object-local baked lighting, preserved dark silhouette/value hierarchy, dark rubber tire, dark saddle material, glossy colored frame metal, bright neutral hardware, no invented cast shadow, restrained highlights, and micro-detail only when it survives gameplay motion and split-screen scale.

The key discipline was that none of those art decisions could alter semantic pose, stock envelope, pivot, contact point or guest-authored cadence.

The first actual authored Remastered candidate failed its initial motion review for exactly the right reason: although plausible in isolation, its mass drifted too far from the stock silhouette in motion. The next tuning pass restored the stock envelope and contact anchor while keeping the higher-resolution material language.

From there the lane became a sequence rather than a specimen. Adjacent P1 poses were authored or safely reused, and the workflow learned an important distinction: exact semantic registrations do not imply unique art assets. When two guarded states produced byte-identical stock rasters, they retained separate semantic guards but shared one authored asset.

P2 followed through PRs #343, #346, #348, #352 and #353. PR #355 finally promoted the whole 1205–1220 P1/P2 strip into a temporal-coherence gate. Static stock edges had to stay static in the authored sequence; dynamic edges had to remain dynamic; stock contact deltas had to be preserved; and the magnitude of changed pixels had to remain within a measured band.

At that point the first family was no longer just replaceable. It was reviewable as motion.

### True high-density presentation becomes real

The next renderer step separated guest geometry from host presentation density. Guest state still described the same 256×224 world and the same 64×64 racer object. Remastered presentation could operate on a host-owned 1024×896 surface, retaining actual sub-logical-pixel detail rather than using high-resolution art as an expensive nearest-neighbor source.

This produced a clean three-layer model: guest simulation and semantic animation selection; logical presentation geometry and placement; and host presentation density.

The first shipping-art review was deliberately unsparing. All ten unique visual poses in the closed strip were technically valid, but their saddles, wheel/hardware treatment and internal structure still looked too schematic at true density. The project had reached the point where remaining problems were recognizable art problems rather than reverse-engineering ambiguity.

### The modern pause menu becomes a small frontend of its own

The modern-product lane expanded quickly. Focus Pause became a selectable menu item, a Controls panel was added, Run Data became a read-only host view, and confirmed Exit/Quit actions were separated from guest state.

Display configuration then arrived one axis at a time: desktop display mode, VSync, presentation FPS, output resolution, and later internal render scale.

Presentation FPS was especially important because it made a long-standing timing policy executable. A 120 Hz presentation setting produced multiple host presents across the same authoritative guest timeline. Native acceptance proved that higher presentation cadence was re-presentation, not faster physics, AI, RNG or timers.

Output Resolution received the same layered treatment. Monitor capabilities, user-facing resolution choices, persistence, application policy and stale-monitor recovery were developed as separate contracts before being exposed together. Windowed and Borderless modes remained resolution-inert; explicit mode application belonged only to true exclusive Fullscreen.

The host-state schema reached v6, but the project deliberately stopped treating every new setting as a reason to churn the schema version. Later reconciliation made v6 additive: a small required administrative core plus known optional fields with typed defaults, while unknown, malformed or duplicated fields still fail closed.

### Frontend modernization gets policy before redesign

The original UI was classified feature by feature into presentation artifacts, gameplay mechanics and administrative/hardware-era systems. The resulting policy preserves recognizable presentation and mechanics by default while allowing save-slot bureaucracy, destructive controller chords, repeated administration and other cartridge-era constraints to be redesigned deliberately.

This was a useful brake on a common remake failure mode: replacing a distinctive old frontend with a generic settings shell simply because modern UI code is easier to write.

### Platform targets become engineering constraints, not wish lists

Windows x64 remained the primary consumer/reference package. Modern macOS, WebAssembly/browser, Switch homebrew, a best-effort High Sierra path and a personal-use PS5 host were all framed as host implementations around the same authoritative game core.

Switch reconnaissance stayed within public devkitPro/libnx/SDL2 tooling. The Web plan centered on Emscripten/WebAssembly with browser-specific persistence, audio, input and fullscreen behavior kept outside simulation. Console targets remained explicitly non-commercial and prohibited proprietary SDK material from entering the repository.

The immediate benefit was not that five ports suddenly existed. It was architectural pressure: new product seams now had to avoid gratuitous desktop-only assumptions when a similarly small portable interface was available.

### CI becomes a performance problem

By late October 3, the test laboratory itself had become expensive. Native build/boot smoke and UI evidence were taking long enough that they were explicitly called out as a bottleneck.

The response was not to weaken tests. The workflow was split into a fast build/boot gate and a separate heavier UI-evidence lane. Independent capture cases were sharded while expensive shared compilation stayed shared.

This distinction became the template for later optimization: parallelize independent runtime cases, not the expensive build that every case needs.

---

## 2026-10-04 — Reconciliation day: finish the seams, rescue the branches, tame the CI

October 4 began with many of the right things existing in the repository, but not all of them existing together on current main.

This was the predictable cost of parallel agent velocity. Widescreen graduation, additive host-state work, Internal Render Scale, Racer HD refinements, platform experiments and CI fixes had advanced on partially overlapping branches. The work of the day was both technical and operational: reconcile accepted ideas without regressing one another, repair the workflows exposed by those merges, and keep pushing the remaining product seams while the repository was already open.

### SDL3 becomes the canonical desktop backend

One early architectural cleanup settled a question that had surfaced in agent commentary: the project was still using host SDL2 in places even though the pinned framework’s modern path was SDL3.

PR #380 made SDL3 the canonical desktop backend for Windows x64, modern macOS and Linux CI. SDL2 remained only where it served a genuine compatibility/platform purpose, such as the reference emulator, Switch homebrew or the legacy High Sierra lane.

The project vendored the exact SDL3 source release matching the framework pin so native builds remained offline and reproducible. Workflows that had silently relied on network fetches were converted to explicit repository-owned staging.

A new Windows x64 smoke build then proved the intended consumer target could compile and boot through the same modernized framework. ClangCL was used because the framework’s alignment attributes were not accepted cleanly by the default MSVC path.

### The historical replay workflow finally gets its missing runtime

The SDL3 sweep exposed an embarrassing but useful fact: one historical native replay workflow had effectively never succeeded. Across roughly 115 runs, its Lua client kept trying to connect to a bridge that the generated desktop host never started.

PR #402 wired the existing Lua bridge into the host lifecycle. The first reconciliation still patched the wrong framework checkout: the project generator materialized its own pinned SNESRecomp tree, so changing an outer checkout did not affect the code actually compiled.

PR #407 corrected that final ownership mistake by applying and verifying the Lua bridge patch against the generated project’s framework checkout.

The lesson was broader than Lua. In a generated-code project, the repository containing a patch is not enough. The build must prove that the exact materialized dependency being compiled actually received it.

### Widescreen reaches product graduation

The ordinary-race Widescreen lane had already solved capacity, geometry and scene policy separately. October 4 was about making them one real user-facing path.

The accepted +48 ordinary-race materializer, scene-aware presenter and persisted Modern Options VIEW setting were reconciled into the ordinary product-generation path. Original remained the conservative default. Authentic mode remained inert. A diagnostic environment selector was retained for deterministic tests, but user-facing behavior no longer depended on it.

The result is the first end-to-end Widescreen product path: persisted user choice, scene classification, live course-backed extra strips, dynamic native-wide presentation where supported, fixed scenes remaining stock-centered, output composition using the accepted 342×224 full-height 7:6 geometry, and unchanged authoritative simulation.

VS continued independently. The accepted capacity advanced through +40 and then the final +48 probe. This was the last important backing-width question for universal race coverage, not a reopening of display geometry or ordinary-race architecture.

### Internal Render Scale joins the stable settings envelope

Host-state reconciliation produced another architectural improvement.

Instead of creating schema v7 merely because Widescreen and Internal Render Scale arrived after Output Resolution, v6 was made explicitly additive. Old versions retained strict historical codecs. Current v6 required its small administrative core and allowed recognized optional settings to appear together in any combination, with typed defaults for missing known fields.

Internal Render Scale then entered that same envelope as 1×/2×/3×/4×, defaulting to 4× for the modern HD path.

On the Racer HD side, presentation density became runtime-variable while the authored 4× source remained authoritative. Lower densities center-sampled from the same source; 4× mapped bit-for-bit to the authored pixels. Guest geometry, semantic selection and OAM placement did not change.

This joined two earlier principles cleanly: host settings should evolve without guest-state pollution, and presentation resolution should remain independent of simulation and logical geometry.

### Racer HD enters real refinement rather than coverage expansion

By October 4 the first motion strip was semantically saturated, temporally gated and presented at true density. The next work was therefore exactly what the plan had been trying to reach: improve the art rather than excavate more state.

Mismatch maps showed that different poses failed for different reasons. For P2 0542/0543, the weak area was missing internal structure, so refinement added restrained frame bracing and hub-centered spoke detail while preserving stock outer bounds and contact anchors.

For P1 057D/057E, extra structure made things worse. Their dominant error was excessive authored saddle mass, so the successful refinement was subtractive: shift and narrow the saddle rather than add detail. The 057F and P2 0541 transition poses received the same evidence-driven saddle reshaping.

This is the desired production loop. The toolchain can now ask where an authored high-resolution pose disagrees with the mechanically recovered stock pose and support a local visual decision without reopening semantic identity, animation timing or renderer ownership.

Technical acceptance and artistic approval remained separate. The refined bytes still required review before any shipping-art claim.

### Modern product settings become coherent rather than additive clutter

Display Mode, VSync, Presentation FPS and Output Resolution all became durably persisted, with Output Resolution tied to the real active-monitor catalog and applied only in exclusive Fullscreen. Unsupported or stale saved modes fail safely back to effective Native behavior rather than leaving the host in a broken state.

Internal Render Scale was persisted before the UI bridge was considered ready. This policy/persistence-first, UI-when-ownership-is-concrete pattern had now been used often enough to become a project habit.

Exit to Frontend also matured through its own lifecycle acceptance, separate from Quit Desktop. Controller navigation was rescued from an orphaned branch in PR #411 and reconciled against the semantic host-navigation vocabulary so keyboard and controller did not become two menu systems.

### CI reconciliation reveals the cost of fast parallel work

The repository then hit a wall of red runs.

Some failures were real regressions from stacked reconciliation. Others were stale assumptions in workflows, bad paths, missing reference-only SDL2 dependencies, or patch-registration mistakes.

One especially destructive issue was a malformed dynamic-Widescreen framework patch plus a stale registered SHA-256. Because so many native workflows stage the same framework patch set, one corrupt diff could make the entire CI surface look catastrophically broken. PRs #399–#401 repaired the hunk metadata and canonical digest.

The response broadened into a systematic workflow audit.

PR #406 removed redundant push-to-main triggers from pure validation workflows. PR #408 added automatic guardrails requiring path-scoped main pushes and concurrency. PR #410 extended that rule to pull-request workflows too.

The resulting policy became: validate changes on PR; do not automatically run the same expensive validation again merely because that PR merged to main; retain PR+main behavior only for workflows that genuinely write or preserve historical evidence on main; path-scope every automatic workflow; and define concurrency so stale runs cancel.

Runtime-heavy workflows were then attacked with the same shared-build/sharded-run idea used on October 3. PR #409 parallelized Widescreen depth and liveness probes against one compiled executable. PR #410 did the same for independent Exit-to-Frontend and rotation cases.

The goal was no longer merely green CI. It was fast enough CI that agents could keep using it as a laboratory without spending most of their time waiting for the laboratory to reboot.

### Branch rescue becomes part of ordinary operations

The user repeatedly asked for abandoned or un-PR’d work to be checked rather than assuming the PR list represented the real state of the project.

That instinct was justified. Several useful lanes existed only on recent branches after sessions stalled. The day included explicit rescue/rebase/reconciliation work for Widescreen product graduation, Racer HD refinement, Internal Render Scale and controller navigation.

By the end of the reconciliation sweep, open PRs were back to zero.

This operational pattern is now mature enough to state plainly: in an AI-agent repository, branch archaeology is part of source-control hygiene. No open PR does not necessarily mean no unfinished work, and an old branch does not necessarily mean merge it. The useful question is whether a recent branch contains unique accepted work that main still lacks.

### The project diary itself becomes part of the evidence system

The conversation archive was also brought current.

Earlier project chats had already been captured as transcript-style notes rather than falsely reconstructed verbatim logs. October 2–4 had outpaced that archive, so twenty-five additional conversation summaries were added to prod_diary, covering Widescreen, Racer HD, modern-product settings, platform/display policy, CI reconciliation and the latest agent-planning work.

This matters because PR descriptions answer what changed, while conversations often preserve why that became the next thing to try. The production diary exists to connect those two scales.

---

## Production status at 2026-10-04

The project is now in an unusual middle state: the difficult architectural questions are much closer to solved than the visible game is to finished.

A rough whole-project estimate at this point is about 52% complete, but that single number hides a very uneven distribution.

The reverse-engineering and architecture foundation is on the order of 80% mature for the needs of the planned product. Stock-native execution, deterministic fixtures, semantic fidelity tooling, progression persistence, course presentation data, camera/streaming boundaries and the first presentation family all have working decision-quality evidence.

Widescreen is roughly 85% complete as an architecture and first product feature. Ordinary 1P/2P now have an end-to-end user-selectable path with accepted geometry and host-owned course materialization. VS is the remaining major race-coverage seam, with its separate preparation path recovered and capacity progressively validated toward the same +48 backing target.

HD Presentation is perhaps 30% complete as a finished visual product, despite the underlying presentation architecture being much further along. The first racer family has exact semantic selection, true-density host rendering, reusable pose equivalence, temporal gating and a real refinement pipeline. What remains is large in content terms: final shipping-quality racer art, broader racer animation families when needed, track/background presentation, UI/fonts/effects, and eventually coherent Remastered/Reimagined treatment across a full route.

The modern product layer is also around 30–35% complete. Pause/Resume/Retry, Controls, Run Data, Exit/Quit actions and a meaningful stack of persisted display settings are real. Still open are the larger product systems: independent profiles, autosave/resumable progression, racer identity/customization, local run records and replay, personal-best/previous-run ghosts, timing/splits/deltas, practice/free play, fast navigation, accessibility, local multiplayer flow, localization readiness and deliberate frontend/progression redesign.

Platform work is deliberately asymmetric. Windows x64 has a real native smoke path and is the reference consumer target. macOS, Web, Switch homebrew and PS5 remain host-feasibility and productization work rather than separate game implementations.

Custom courses/editor work remains downstream. The course model is already strong enough to support Widescreen presentation and future neutral modeling, but editor-complete semantics and authoring UX are not launch-ready work yet.

The biggest shift since September 28 is therefore not percentage complete. It is risk composition.

At the start, the central risk was epistemic: perhaps the compiled SNES game would not yield enough structure to preserve its behavior faithfully.

By October 4, that risk has fallen dramatically.

The dominant remaining risks are production risks: make enough high-quality art; finish enough modern UX; extend proven architecture across all meaningful game states; package it across desired hosts; and keep the evidence and CI machinery fast enough that parallel development remains an advantage rather than becoming its own bottleneck.

Those are large jobs, but they are ordinary engineering and content-production jobs.

UR-Recomp has crossed from can this game be recovered into how much of the recovered machine can be turned into a polished modern product without losing the thing that was worth recovering?

---

## Archived source 2: [PRODUCTION-DIARY-2026-10-05.md](PRODUCTION-DIARY-2026-10-05.md)

# UR-Recomp Production Diary — 2026-10-05

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation of:** `PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md`

This daily continuation is synthesized from October 5 project conversations and the PRs that survived reconciliation. As before, PRs remain the authority for exact diffs and CI evidence; the diary records why the work moved where it did.

---

## October 5 — The project turns decisively into a Windows product

The first week ended with most architectural risk already burned down. October 5 therefore looked different from the preceding excavation sprint. The central question was no longer whether the game could be reconstructed faithfully. It was how quickly the proven substrate could be converted into a coherent Windows x64 product without letting parallel agents rebuild the same systems twice.

### Planning gets compressed around product decisions

PR #483 was the hinge. The project plan and work queue were rewritten around the current Windows consumer path rather than the historical fidelity → Widescreen → HD ladder. Old completed archaeology and stale “future work” claims were removed from active planning surfaces. Several questions that already had enough evidence were reclassified as product-policy choices and actually decided.

That produced a clearer Modern frontend policy: Play / Practice / Multiplayer / Records / Options; simultaneous local multiplayer setup; canonical racers without invented personalities; selectable Bronze/Silver/Gold challenge tiers; resumable tours; a unified Records browser; modern text entry; and deferred advanced cosmetics/photo/replay-editor/mod work.

PRs #482 and #484 were then reconciled down to the non-duplicated pieces that still mattered: a shared PPM validator and hardened Internal Render Scale acceptance. PR #485 repaired a test whose assumptions had become stale after the policy cleanup. PR #486 turned the day's CI failures into explicit agent guidance rather than another pile of local fixes.

### Three product lanes immediately become real features

The next agent batch produced three of the most obviously player-facing features yet.

PR #487 added a profile-safe Modern Continue Tour path. It preserves authoritative profile/SRAM ownership while restoring the transient tour state that stock rider selection normally clears. The acceptance story is fresh-process and fail-closed: valid resumable state reaches stock TRACK_SELECT with the expected tour row restored; stale or mismatched state does not.

PR #488 added authoritative live timing, PB comparison, signed deltas and split presentation, while also advancing the first unified Records surface. It reused completed-run records rather than creating a second timing database.

PR #489 removed repeated menu traversal with Rematch, Repeat Practice and Recent Course shortcuts. These routes reuse existing stock/Quick Practice/Restart machinery and are explicitly progression-safe. A speculative Next Event shortcut was left out until its semantics are equally well proven.

The pattern is becoming consistent: expose a modern shortcut or surface, but route it into the same authoritative game machinery instead of cloning game rules in the host.

### Product breadth expands around the same ownership rule

Earlier October 5 work had already added first-run help and authoritative Quick Practice (PR #466 plus the later 45-course routing probe), giving ordinary users a compact way to learn controls and enter real stock-initialized practice without contaminating progression, records or ghosts.

Packaging also crossed an important threshold. PR #493 established a validated Windows x64 portable ZIP/folder package that boots correctly from an unrelated working directory. PR #504 later rescued the startup-diagnostics contract. The next packaging lane is therefore lifecycle work, not “make a ZIP”: mutable user data needs a clean durable home outside immutable package contents, and diagnostics/settings/profile/run persistence must continue to work after ordinary consumer relocation and relaunch.

Local multiplayer took a similar contract-first route. Separate conversations established deterministic P1/P2 assignment, duplicate rejection, reconnect/reassignment rules, launch eligibility and stock 2P authority. The useful pieces were rescued into PR #503.

Controls rebinding followed the same pattern. PR #498 landed the framework-authoritative rebind model. A later product-integration pass opened PR #512 to wire that model through the visible Modern Controls surface using SNESRecomp's actual keybind/save authority.

### Modern progression moves from policy to stock-authoritative implementation

Challenge tiers were deliberately treated as a Modern policy layer around the stock generator rather than a replacement progression engine.

PR #491 locked the Bronze/Silver/Gold policy. PRs #492, #496, #499 and #501 progressively identified and wrapped the real stock challenge-generation/writer/award seams. PR #502 then rescued the selected-tour challenge-completion lifecycle into main.

This is the same architectural discipline seen elsewhere in the project: host-side product logic may choose, present and persist policy, but canonical gameplay state transitions should remain the guest's job whenever the stock game already owns them.

### Uniracers / Unirally becomes a presentation feature instead of a second game

A new conversation asked whether typing `NTSC` or `PAL` on the title screen could switch between Uniracers and Unirally presentation. The idea expanded into a secret controller-accessible switch with persistent regional preference where platform storage allows it.

PR #500 added the regional presentation substrate. PR #508 documented a stock-style animated transition, preferring the game's own horizontal title movement vocabulary and keeping the effect presentation-only rather than rebooting or retiming the guest.

The scope remains intentionally narrow: preserve one authoritative simulation and switch the player-visible regional presentation where the retail versions actually differ.

### Racer HD work changes its selection rule

The first Racer HD family is no longer being expanded by sprite adjacency or generic archaeology. The new instruction is empirical: measure Original↔HD fallback frequency during representative ordinary play, rank unsupported states by actual player-visible burden and implement the highest-value missing presentation family first.

This is a meaningful maturation of the HD pipeline. Semantic selection, equivalence, temporal coherence, review packets and shipping-readiness machinery now exist. The question is no longer “what sprite comes next?” but “what missing state is the player actually seeing most often?”

At the moment this diary was first captured, that measured-coverage lane had only just started and had not yet produced a new PR.

**Retrospective, October 6:** the selection rule worked. The lane produced a sequence of bounded, review-gated additions chosen by observed fallback burden rather than ROM adjacency, moving the broader ordinary-play census from 118/5282 HD selections (2.23%) to 653/5282 (12.36%) by the 01B9 slice. The useful process result was not merely the extra art. Once the agent was given a quantitative work-selection oracle, it stopped spending context on deciding what looked promising and could iterate through measure → author → review → hash-bind → remeasure with comparatively little supervision.

### CI briefly becomes the product's biggest scalability bug

The day's ugliest symptom was 108 active or queued Actions runs from only a few agents.

The first pass fixed trigger overfire and reconciled useful stranded work. PR #505 stopped planning/deferred-platform changes from waking expensive validation. PR #506 fixed a stale framework patch digest that could poison many native workflows at once.

The user then explicitly asked for an aggressive second pass: not merely “are these workflows coded correctly?” but “do they still deserve to exist automatically?”

PRs #507, #509 and #510 pruned or manualized completed research, deferred Switch work, closed Widescreen probes, archaeology/reference jobs and other obsolete automatic workflows. Native UI acceptance was collapsed around shared build work where possible. The repository stopped treating every historical experiment as a permanent regression service.

PR #511 made that cleanup durable by updating agent and CI/operations/hygiene guidance with creation, trigger, maintenance and retirement rules.

This is an important production lesson. In an agent-heavy repository, CI is a shared compute product. A workflow can be perfectly implemented and still be wrong to run automatically.

### End-of-day state

By late October 5, the repository had no meaningful orphaned work left from the CI reconciliation sweep, and current `main` had reached `74040131...` after PR #511. PR #512 then opened for full player-facing Controls rebinding.

### Overnight follow-through and a warning from the next day

Several October 5 “next lanes” became merged product work within hours. Resume/Restart Tour moved from policy into a player-facing confirmed flow; the regional secret gained its first exact retail Unirally title consumer; local multiplayer gained an independent source-aware join overlay; portable state moved into a durable per-user root; and Racer HD began climbing its measured fallback ranking.

That velocity came with a sharp caveat. The repository had become capable of generating changes faster than its integration machinery could cheaply validate them. Session stalls were survivable because agents had been told to commit often, update owning docs and leave bounded branches that another session could rescue. CI stalls were more dangerous because shared framework patches, generated snapshots and broad workflow assertions turned otherwise independent work into hidden coupling. The October 6 cascade would make this the next major engineering problem.

The project has crossed another boundary. The major remaining Windows work is now recognizable consumer-product work:

- finish the visible Controls rebind lifecycle;
- turn portable packaging into a durable user-data/update lifecycle;
- continue Racer HD by measured fallback burden rather than archaeology;
- keep filling the Modern root/progression/multiplayer/records surfaces using stock-authoritative state transitions;
- continue pruning CI whenever a completed research lane tries to fossilize into a permanent tax.

The most striking change after one week is that the repo no longer needs a single serial “critical path.” The hard-won semantics are strong enough that multiple product leaves can proceed in parallel, provided each agent respects ownership boundaries and the CI machinery remains small enough to let that parallelism breathe.


---

## Archived source 3: [PRODUCTION-DIARY-2026-10-06.md](PRODUCTION-DIARY-2026-10-06.md)

# UR-Recomp Production Diary — 2026-10-06

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation of:** `PRODUCTION-DIARY-2026-10-05.md`

October 6 was the day the project's extraordinary parallel throughput finally outran some of the infrastructure built to contain it.

The useful work did not stop. Windows x64 continued to gain real product behavior: Resume/Restart Tour became a complete player flow, the regional Uniracers/Unirally preference gained an exact retail title consumer, local multiplayer gained an independent join surface, portable state became upgrade-safe, startup diagnostics closed into a release-facing contract, Racer HD coverage expanded by measured burden, and presentation-density policy was bounded for Modern overlays.

But most of the human attention went somewhere less glamorous: GitHub Actions.

## Product lanes kept landing

Several October 5 lanes crossed from plan to product overnight.

The unfinished-tour work is now a coherent Modern flow rather than a hidden persistence trick. Resume and Restart both travel through stock menus; only Resume may restore the narrow validated continuation; Restart waits until stock itself proves it performed the historical wipe before retiring host continuation state. The implementation is transactional around host profile and SRAM publication and fails closed on context changes or route failure.

Regional presentation also became visible. The Europe setting can present the exact verified Unirally title raster on the admitted idle-title surface while NorthAmerica remains the live canonical Uniracers raster. Authentic mode and guest machine state remain untouched. The animated stock-style transition is still open, which is the correct outcome: the evidence supports the title substitution, not yet the flourish around it.

Local multiplayer moved from a deterministic assignment model to an actual source-aware join overlay. The framework still owns device-to-seat assignment and the stock game still owns rider selection. The host surface only decides whether two valid sources have joined. A later parity failure showed why these narrow authority descriptions matter: controllerless deterministic routes were accidentally entering the new overlay until the runtime gate was tightened to require a real connected source.

The Windows package stopped behaving like a clever ZIP and started behaving like a durable consumer application. Mutable config, bindings, saves, profiles, run data and related state now have a per-user home outside the package. Legacy package-local state migrates transactionally and idempotently, destination state wins, and host-state publication is atomic. Startup failures now have stable release-facing codes and a bounded log rather than depending on a developer watching stderr.

## Racer HD finds a scalable rhythm

The measured-fallback rule introduced on October 5 paid off immediately.

Instead of browsing adjacent ROM registrations and deciding what looked like the next animation family, the tooling ranked unsupported states by actual player-visible fallback burden. The agent then worked through bounded P1 contexts one at a time, retaining stock raster evidence, temporal witnesses, authored geometry, review artifacts and hash-bound approval.

By the `01B9` slice, broader ordinary-play coverage had moved from 118/5282 HD selections to 653/5282. Measured coverage rose from 2.23% to 12.36%, removing 535 baseline Original fallback frames.

The deeper win is procedural. Art expansion is one of the easiest places for an autonomous agent to wander because almost every neighboring asset can be argued to be useful. Giving the agent a machine-generated priority queue turns taste-adjacent work into a reproducible optimization loop. It also gives later agents an exact place to resume after a stalled session.

## The CI repair loop

The day's dominant story was a chain of red workflows that repeatedly appeared to be fixed and then revealed another failure.

Some defects were tiny: malformed patch hunk counts, stale SHA-256 registrations, shell continuation mistakes, CRLF-versus-LF comparison, second-run migration fixtures retaining read-only state. Others were architectural: workflows encoded assumptions about exact hook shapes; a new multiplayer UI changed deterministic presentation routes; Native UI evidence rebuilt essentially the same candidate multiple times; aggregate validators ran after prerequisites had already failed; expensive product journeys lived inside a nominal smoke gate; historical specialist workflows still carried broad triggers.

The frustrating property of these bugs was their cost function. Most took minutes to understand and seconds to patch, but the answer often arrived only after another long remote run. An AI agent's ability to produce a quick local fix is actively unhelpful when the dominant latency is ten or fifteen minutes of CI and each run exposes only the next hidden assumption.

The successful move was to stop treating the latest red as the unit of work.

PR #563 audited and hardened the CI architecture itself. Native build/boot smoke was refocused into a bounded fast gate with an approximately four-minute target and an eight-minute timeout. Long product journeys went back to focused owner workflows. Native UI evidence now builds one candidate and fans that exact artifact across five capture shards instead of compiling five copies. Aggregate validation is gated on successful prerequisites. Structured diagnostics replace order-sensitive log greps. Specialist workflows have narrower triggers and toolchains. Evidence writers that mutate retained reports are serialized. Mechanical tests now reject several of the fragility patterns that caused the day's failures.

The result matters more than whether one particular run is green. The repository now has fewer ways to convert an unrelated product change into fifteen minutes of opaque integration roulette.

## A note on agent coordination

The project passed roughly 471 nominal agent-hours during its first week, based on PR open-to-close intervals plus a small per-PR allowance. That number is not a meaningful measure of human labor, but it describes the shape of the project accurately: enormous parallel machine effort compressed into a few days of wall-clock time.

The repository architecture is what makes that remotely useful.

The good parts of the AI-driven process are clearest when work can be turned into independent evidence-rich leaves: one exact regional raster consumer, one progression policy seam, one measured Racer pose, one package migration rule. Agents are very effective at exhausting those bounded problems, especially when acceptance can be run mechanically.

The weak parts appear in shared implicit infrastructure. Framework patches, generated snapshots, manifests, workflow contracts and broad host integration seams can couple agents that never touch the same source file. Prompting agents to “avoid overlap” helps, but it cannot solve invisible coupling. The durable answer is to make those shared contracts explicit, cheap to validate and narrow enough that failures identify their owner.

Session stalls supplied a related lesson. They were annoying rather than catastrophic because agents had been committing frequently and leaving durable docs/branches. Work that exists only inside one conversational context is fragile. Work that is committed in small, semantically named increments can be rescued by another agent with very little ceremony.

## End-of-day state

By the end of October 6, UR-Recomp was more obviously a modern Windows product than it had been twenty-four hours earlier, but the larger advance was operational.

The project now has a clearer separation between fast integration confidence and slow specialist acceptance; host-owned product policy and guest-owned game behavior; measured player-visible priorities and open-ended archaeology; recoverable repository state and ephemeral agent context.

That separation is likely to matter as much to the remaining remaster work as any rendering or reverse-engineering breakthrough. The project has already shown that AI can generate changes at startling speed. October 6 was the day the repository learned that the harder problem is making those changes compose.


---

## Archived source 4: [PRODUCTION-DIARY-2026-10-08.md](PRODUCTION-DIARY-2026-10-08.md)

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


---

## Archived source 5: [PRODUCTION-DIARY-2026-10-09.md](PRODUCTION-DIARY-2026-10-09.md)

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


---

## Archived source 6: [PRODUCTION-DIARY-2026-10-10.md](PRODUCTION-DIARY-2026-10-10.md)

# UR-Recomp Production Diary — October 10, 2026

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation:** `PRODUCTION-DIARY-2026-10-09.md`  
**Evidence cutoff:** October 10, evening Calgary time. Project conversations are reconstructed and labeled separately. GitHub commit/PR history grounds integration claims.

There was a strange kind of electricity in the project on October 10. Eleven days ago this had been an attempt to remake a beloved SNES unicycle game. Now there were other people in other countries independently carving into the same machinery, a newly encountered MIT-licensed source reconstruction, a serious modern Windows product emerging from Baldosa, authentic widescreen capture, and an uncomfortable question about who would be remembered as having made the definitive new Uniracers.

The user did not hide the feeling: “I know it's petty and emotional, but I don't want Baldosa's thing to be the ‘new version of Uniracers’ after the 11 days of work we've done.” The desired outcome was a 4K widescreen version people would find distinctly more appealing. That is a genuine competitive impulse. But the same conversation insisted that the project become the definitive evidence-backed technical reference: “every question is answered, every recreation is faithful AND evidence-backed.” The ambition is simultaneously to make the best game *and* to leave the best explanation of how the original worked.

## Three lanes, one product

Three new autonomous agents received exclusive mandates: actual Baldosa Windows product integration; gorgeous and faithful 4K/widescreen graphics; and complete-event original/native gameplay QA. An additional lane was assigned recruitment footage, and another the malmazuke research intake. The user's repeated “keep working, go as far as you can” reflected a preference for sustained autonomous work. Reports of stalled sessions were operational recovery instructions, not impatience or criticism. There were enormous nominal agent-hours available, yet useful progress was only what persisted into current main, verified artifacts and completed player journeys.

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

The last few days have held delight, competitiveness and a nearly archival instinct for completeness. The user wants to *win* on presentation, without faking fidelity; wants outside collaborators, without surrendering product direction; wants to accelerate, without pretending every green Actions job is an independent playable beta; and wants nothing significant about the original game to remain a mystery.

There is something revealing in the demand for a definitive repo. It is not enough that the modern executable feels right. A hypothetical reader should be able to follow every decision to a source byte, emulator trace, test and carefully bounded conclusion. This makes the work slower in places, but it also turns an eleven-day burst of parallel agents into an accumulating body of knowledge rather than an opaque pile of code.

The useful lesson for future reconstruction projects sits naturally inside this story: enthusiasm can create momentum, rivalry can clarify standards, and parallel automation can create startling throughput. But sustainable quality comes from explicit ownership, evidence that survives expired CI artifacts, release gates that refuse overclaiming, and an understanding of when a beautiful demo is still only a demo.

At the close of this diary window, UR-Recomp had crossed important visual, media and product-integration thresholds. It was becoming recognizable as the desired 4K remaster while simultaneously sharpening the technical reference beneath it. The polished beta remained ahead. The difference from earlier days was that more of the claim could now be shown moving.

## Sources and boundaries

Conversation archive: `PROJECT-CONVERSATIONS-2026-10-10-RECONSTRUCTED.md`. Recent merged-main evidence referenced here includes #1189–#1202, #1208–#1218, #1221, #1228–#1249, #1253–#1282 as specifically named above. The PR ledger is high-volume and concurrent; a PR mentioned for technical context does not imply its full release gate is closed. Temporary one-shot workflow PRs marked NEVER MERGE are not treated as product merges.


---

## Archived source 7: [PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md](PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md)

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


---

## Archived source 8: [PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md)

# UR-Recomp Production Diary: October 14–17, 2026

**Continuation:** [October 11–13](PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md). **Evidence cutoff:** 2026-10-17 evening in Calgary (some source PR merges appear on GitHub as October 18 UTC). This is the standard narrative diary, separate from the [reconstructed project conversation collection](PROJECT-CONVERSATIONS-2026-10-14-TO-2026-10-17-RECONSTRUCTED.md). It differentiates the user's intentions, agents' implementation, original/native experimental results, CI checks, and independently accepted release gates.

## October 14–15: An actual Windows candidate, not a declaration of beta

The project shifted from a succession of hopeful alphas toward a source-identified product somebody could finally be asked to operate. The user reiterated an unusual preference: to direct a faithful, polished Uniracers remake through agents without personally playing each interim alpha. Their benchmark was ambitious but specific: 4K widescreen, original-feeling menus and HUD, authentic unchanged gameplay and controller-first Windows operation. A clean, portable Windows build had to justify its own identity, not merely compile.

Modern #1648 had already integrated Play, local joined Multiplayer, Records, persistent Options and Practice into the existing native product, backed by thirteen scripted Windows journeys. On October 15, [#1667](https://github.com/gamesbyian/UR-Recomp/pull/1667) nominated an immutable source/ROM-free ZIP pair for owner playtesting: source `11501a15dea38fa912335cfc63103ce3a7208001` and ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`. Subsequent changes to main could not retroactively upgrade that candidate. The release ledger still had zero of twelve accepted gates and the original-course census zero of forty-five complete USA events.

The planning conversations also turned outward. The user asked whether malmazuke's Unirally reconstruction and morluto's REA project offered useful methods or code. Cross-project archaeology was useful only when source identity and regional distinctions were respected. External PAL facts became conditional hypotheses for the USA guest, not permission to import new gameplay timing or a second game engine.

## October 16: Finding the correct clock edge and making saves survivable

Original/native gameplay work narrowed a subtle, real timing split. The research sequence RF-029 through RF-034 tested and often rejected plausible CPU-to-SPC timing treatments rather than accepting visually neat explanations. [RF-034 / #1741](https://github.com/gamesbyian/UR-Recomp/pull/1741) showed that the first CPU $2140=$CC publication straddled the actual SPC opcode-78 execution boundary differently in original and native. That is a causal observation, not proof that a global cycle offset should be changed. Zoo result +5163, next Bowl +267 and eleven matching earned SRAM images were strong bounded positives; full-event acceptance remained zero.

Meanwhile the Windows save system exposed a more concrete P0: a genuine raw guest SRAM write could be durable while the typed metadata describing it was not. Draft [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) constructed a write-ahead intent and explicit R/T/S/Q operator recovery choices with exact profile isolation and fail-closed unknown states. Independent [#1743](https://github.com/gamesbyian/UR-Recomp/pull/1743) established real Windows F0/F2/F3/B crash-cut and multi-profile evidence on one precisely identified tested executable. These do not certify actual power loss, complete disk failure, all human-operated recovery, or merged-source durability.

The October 16–17 integration [#1744](https://github.com/gamesbyian/UR-Recomp/pull/1744) repaired an important identity seam: the Windows bridge now stages RF-015 and RF-017 rather than building the older timing source, with regenerated bank/clock-charge validation. It integrated the exact-composite cold original/native Zoo record proof. After correcting an exact unit-test marker and an overlong active queue, the final integration passed Windows x64 and 13 scripted journeys, tooling units and hygiene. Two superseded research PRs were closed with provenance; the shipping milestone was real integration, not an accepted complete USA race.

## October 17: Four focused agents and the refusal to hide red tests

At the user's request, work was divided into four non-overlapping lanes: gameplay/CPU/APU; Modern Windows product and crash recovery; source-faithful raster/4K presentation; and independent candidate-bound QA/hygiene. Each lane was told to reuse existing experiments, keep original/native and release evidence separate, and spend hosted Actions runs only on questions that could change an implementation or acceptance decision. The user repeatedly requested autonomous continuation and recovery after stalled sessions; such messages are operational instructions, not evidence of negative feelings.

The sound investigation reached [RF-037 / #1756](https://github.com/gamesbyian/UR-Recomp/pull/1756): all 45,645 compared original CPU port2/3 payload values matched a native prefix, with three same-SPC-age ordering ambiguities, but sampled WRAM still disagreed. [RF-038 / #1775](https://github.com/gamesbyian/UR-Recomp/pull/1775) isolated a single +156-master-clock writer interval among 36,448 adjacent pairs. [RF-039–041](https://github.com/gamesbyian/UR-Recomp/pull/1791) discriminated actual SPC receiver/queue ordering; the [RF-042 negative / #1799](https://github.com/gamesbyian/UR-Recomp/pull/1799) showed an equal-age queue intervention worsened the 78-checkpoint comparison from 51 exact to 46. [RF-043–046](https://github.com/gamesbyian/UR-Recomp/pull/1814) traced early Zoo stack discrepancies toward NMI pre/post phase, but did not prove that the native phase was correct or the differing bytes ignorable. More receipts do not constitute event admission.

Graphics took a similarly evidence-first route. Selected genuinely moving original 1P/2P Windows raster frames matched exactly, but finish/result greyscale phase and medal-region OBJ/color differences persisted. [#1779](https://github.com/gamesbyian/UR-Recomp/pull/1779) guarded authentic 342×224/7:6 full-UHD presentation and centered fixed 4:3 fallback without a 216-line crop. [#1815](https://github.com/gamesbyian/UR-Recomp/pull/1815) retained a source-pinned 65-frame exact moving-1P result, while held graphics drafts kept pre-math brightness and HDMA/V0 changes out of unqualified shipping. Historical procedural four-times racer art remained unapproved for likeness.

Independent QA tightened genuine Windows source, package and disk-error checks through [#1777](https://github.com/gamesbyian/UR-Recomp/pull/1777) and later P0 fault studies, including a disposable full-NTFS VHDX substrate. The latest Modern head `9b861367` had green units, hygiene and execution seam, but [Windows bridge run 39091080467](https://github.com/gamesbyian/UR-Recomp/actions/runs/39091080467) was red: an ENOSPC condition was raised during the full-volume fixture's setup before the specifically required postraw typed-publication witness could be proven. The correct response was not to waive it. The October 17 cleanup recorded this failure on [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713), preserved failing artifacts, closed an explicitly research-only stacked graphics PR #1809 and kept the historical orphan-ref census [#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711) intact rather than deleting unseen work.

The user then requested the next dispatch be prepared from contemporary outside findings. Malmazuke's [league tours #81](https://github.com/malmazuke/unirally-reconstruction/pull/81) and [podium audio #82](https://github.com/malmazuke/unirally-reconstruction/pull/82) had merged on October 16 and 17; their PAL controller, league-score and sound-cue semantics supplied bounded reuse leads. A small [UR intake #1816](https://github.com/gamesbyian/UR-Recomp/pull/1816) was prepared separately for exact-head CI, without asserting USA equivalence.

## Editorial and evidence note

This diary is a reconstruction from project conversation context and GitHub PRs, not a verbatim exchange. Agent instructions such as “keep going as far as you can” or “session stalled” are not proof that the requested outcome occurred, and must not be interpreted as frustration. An Actions test can certify its stated scope without validating physical two-controller/audio/display experience; a pixel-perfect bounded frame subset is not a complete game; matching SRAM at sampled endpoints is not complete frame-by-frame parity. At this cutoff, **0/12 independent release gates and 0/45 complete USA events** were accepted. No product release was declared.


---

## Archived source 9: [PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md](PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md)

# UR-Recomp Production Diary: October 18–19, 2026

**Continuation:** [October 14–17](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md). **Evidence cutoff:** October 19, 2026 (PR descriptions inspected during this entry's preparation). The separate [reconstructed conversation collection](PROJECT-CONVERSATIONS-2026-10-18-TO-2026-10-19-RECONSTRUCTED.md) records what the user asked; this standard narrative distinguishes prompts from experiments, QA adjudications, proposed changes and settled release results. PRs cited below may still be open, draft, superseded or blocked: follow their actual states rather than reading a diary paragraph as a merge receipt.

## October 18: The question changed from “where are the bytes?” to “who actually read them?”

The project was already rich in Zoo/Bowl candidate evidence, after several days of reproducing original and native run boundaries, SRAM results and precise frame samples. The user pushed four parallel lines forward: original/native USA event coverage, independent QA-01/07 adjudication, authentic source-visible raster graphics and Windows harness repair. The original/native acceptance instruction was unusually strict: determine precisely why **zero of forty-five** complete USA events qualified, correct *acceptance-side* defects independently, and never confer a pass by relaxing the definition. Agents were told to read the latest queue and owner evidence before working, preventing one lane from accidentally claiming another lane's unsolved problem.

Another conversation asked what the research factories would usefully discriminate next. Instead of requesting enormous numbers of runs for their own sake, the user instructed the agent to consume the authentic producer experiments already performed and capture a **real executed read with an opcode PC**, its original-side counterpart and raw-memory frame. This was the practical hinge in the search for first causal divergence: observing stored bytes or coincident frame labels alone does not identify the executed instruction that consumed the difference.

Operationally, the user kept asking agents to work ahead, inspect PRs, and resume after session stalls. The tone was supportive and autonomy-forward, and the stall messages meant that the agent's session needed recovery. The prompt history establishes sustained direction and overlapping scientific lanes; PRs and CI artifacts, not the number of requests to continue, establish actual technical progress.

## October 19: A qualified negative is more valuable than a convenient success

The native CPU/interrupt investigation established narrower boundaries. [#1971](https://github.com/gamesbyian/UR-Recomp/pull/1971) reopened genuine RF054/RF073 evidence and counted forty-five first byte observations from **twenty-nine distinct native helpers** *after* handler return. These cannot be reclassified as compiled RTI reading the saved guest PC or PB: that would attribute a consumed return address to instructions that did not consume it. [#1974](https://github.com/gamesbyian/UR-Recomp/pull/1974) pinned upstream source semantics: the compiled RTI path reads P, skips saved PC/PB and returns through the host scheduler, whereas the interpreted RTI path actually loads PC/PB. A fidelity risk exists **conditionally** if the stacked return address is rewritten or scheduler continuation disagrees, but the available source contract did not prove that Uniracers exercised either condition.

Independent [#1977](https://github.com/gamesbyian/UR-Recomp/pull/1977) then cross-checked two authentic, hash-bound archives. Nine native NMI brackets had status read `01ED=26`; four same-host-label original/native stored PC lows differed. The vital restraint was refusing to turn those different saved bytes into a claimed **executed** wrong return target. The next discriminating producer requires a frozen authentic original/native case, original getter first-reads and the native interrupted opcode/scheduler continuation/first fetched PC under the correct source contracts. Ownership remained with the native RF074 experiment, not independent QA.

The test apparatus faced its own deceptive failures. [#1973](https://github.com/gamesbyian/UR-Recomp/pull/1973) made a strictly defined allowance for a **single** valid flat or nested `qa01-case/` evidence root after a real Actions artifact-layout mismatch had wrongly reported missing evidence. This repaired transport, not emulation. [#1975](https://github.com/gamesbyian/UR-Recomp/pull/1975), a deliberately disposable wrapper-on/off native control, failed the mandatory generated-source-diff qualification **before** replay, so it provided no runtime conclusion about the wrapper. In [#1976](https://github.com/gamesbyian/UR-Recomp/pull/1976), the unchanged strict logger comparator still failed because the native host's terminal wall-clock video seconds differed despite equal simulation/presentation totals. A separately qualified host-only normalization could compare the remaining genuine guest logs, but could not silently rewrite the old comparator as green or extend a logger A/B result to wrapper A/B or original/native fidelity. These were examples of preserving a negative result while explaining its scope.

The graphics lane produced an equally precise unresolved measurement. [#1978](https://github.com/gamesbyian/UR-Recomp/pull/1978) checked thirteen genuine 256×224 original/native guest frames at the authentic 112-field cadence. Within those frames it identified **359,013 RGB5-mismatched pixels**, including **318,775** pixels in four specific grayscale-cycle transitions; that class constituted **35.8%** of mismatches over the larger 263-frame comparison. The measurement isolated a major raster symptom, but by itself neither identified PPU ingest/beam root cause nor authorized shifting rendered fields to make screenshots appear similar.

Documentation had become an engineering dependency, too. [#1972](https://github.com/gamesbyian/UR-Recomp/pull/1972) restored growth headroom under a strict active-work-queue length test without overwriting the RF074 owner's newly merged priorities. [#1979](https://github.com/gamesbyian/UR-Recomp/pull/1979) recorded an October 19 QA safe-stop navigation point including exact research PR ownership, failed archive/run constraints and explicit HOLD. These guardrails prevented a passing documentation workflow, a source-only finding or a temporarily green proof from being mistaken for the game's release verdict.

## What remained unresolved

At the evidence cutoff, the PR descriptions still explicitly reported **0/45 complete original/native USA events** and **0/12 Windows release QA gates** independently accepted. A strict first complete event needs comparable genuine original/native execution and all required evidence; a release needs candidate-bound tests beyond individual raster, CPU, SRAM, UI or Windows CI positives. Pending PRs and disposable experiments must be adjudicated by their exact source hashes, checks and dispositions before inclusion in current truth.

The user repeatedly asked the agents to continue eagerly, independently and thoroughly, while also making safe stopping points after interrupted sessions. The engineering narrative of these two days is therefore an accumulation of *qualified distinctions*: source state versus executed behavior, diagnostic logging versus wrapper substitution, artifact transport versus gameplay, and frame-difference histograms versus causal graphics repair. Those distinctions are genuine progress even where they cannot yet move a headline acceptance counter.

## Editorial and evidence note

This entry uses paraphrased project conversation instructions and dated PR descriptions, not fabricated dialogue or inaccessible full transcripts. PR evidence is cited as an engineering reference; its description is not a substitute for checking CI artifacts or merge status. The active [work queue](../docs/WORK-QUEUE.md), [independent QA authority](../docs/QA-BOUNDED-RELEASE-CAMPAIGN.md) and [release ledger](../docs/RELEASE-QUALITY-LEDGER.json) remain the current sources of truth. The user's “session stalled” reports are workflow recovery directions, never evidence of frustration.


---

## Archived source 10: [PRODUCTION-DIARY-2026-10-20.md](PRODUCTION-DIARY-2026-10-20.md)

# UR-Recomp Production Diary: October 20, 2026

**Continuation:** [October 18–19](PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md). **Conversation source:** [October 20 reconstruction](PROJECT-CONVERSATIONS-2026-10-20-RECONSTRUCTED.md), archived first in commit `cd26e7b93ef38bccf248d21c498386a057ec138c`. **Evidence window:** October 20 and early October 21 UTC corresponding to the October 20 evening in Calgary. GitHub commit/PR descriptions and issue evidence are contemporary pointers, not independent proof of all CI or physical acceptance. This is a chronological narrative, not a live dispatch board.

## October 20: Ten moving lines of work need ten persistent identities

The project had accumulated a second kind of complexity alongside its gameplay and rendering investigations: multiple independently dispatched agents, ten hourly work positions, interrupted publication, and a recovery Vault containing work that GitHub alone could not account for. The user wanted recurring task prompts to refer to the current *position on a mutable list*, rather than freeze an objective into each task. Just as important, changing the assignment at position five should not erase the history of work done there previously. The operational response introduced stable objective identities and journal continuity separate from scheduling positions. [#2085](https://github.com/gamesbyian/UR-Recomp/pull/2085) documents dynamic slot dispatch and a Drive recovery preflight; [#2091](https://github.com/gamesbyian/UR-Recomp/pull/2091) assigns stable work IDs across board rotations; [#2092](https://github.com/gamesbyian/UR-Recomp/pull/2092) links ten verified Drive journals and reconciles legacy aliases. This was progress in *coordination infrastructure*, not an increase in game-completion percentage.

The Drive Vault was not intended to replace GitHub as the ordinary record of source changes. [#2095](https://github.com/gamesbyian/UR-Recomp/pull/2095) directs manually dispatched agent handoffs to GitHub, preserving Drive for genuine publication failures. [#2097](https://github.com/gamesbyian/UR-Recomp/pull/2097) distinguishes retriable technical failures from explicit publication denials, avoiding duplicate submissions, and [#2100](https://github.com/gamesbyian/UR-Recomp/pull/2100) records a bounded GitHub-first retry and lossless fallback. The Vault reconciliation ran deeper than a folder count: the recovery evidence ledger reports **393 Drive file IDs** and **87 ZIP archives** under a content-integrity census, with unique members still requiring explicit disposition. [Issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) explicitly retains incomplete recovery work, avoiding premature deletion of any original archive.

## The Modern frontend becomes visible product work

At the same time, the user directed separate owners to make the Modern in-game frontend feel genuinely finished. The title work covers faithful logo art, 16:9 presentation and controller-first root entry; destination work covers Play, Practice, Multiplayer, Records and Options, including profiles and submenus; the animated unicycle hero must use source-verifiable original imagery, controlled idle/selection/transition timing, and reduced-motion behavior. The briefs explicitly prohibit substituting a trailer, altering Authentic mode or changing guest simulation to improve appearance.

The artifact history contains meaningful narrow results rather than a blanket design approval. [#2096](https://github.com/gamesbyian/UR-Recomp/pull/2096) records original clip inventory and **private** ROM-derived source-raster review plates, with tests preventing copyrighted stock review art from accidentally entering the public worktree. That is valuable input for the motion owner, but does not establish final hero animation approval. An independently recovered Modern layout change restores overflow-safe text dimensions and boundary tests. [Issue #2079](https://github.com/gamesbyian/UR-Recomp/issues/2079) documents a concrete remaining gap: controller-first title input and original title image evidence exist, but Modern idle must still hand off to a *genuine original attract/demo cycle*, consuming wake input so it never selects a hidden destination. The original's source-pinned title/menu and demo timings are known; their integrated Modern handoff is not yet proven. Full native screenshot acceptance, visual approval, 4:3 fallback and reduced motion still require the relevant owner evidence.

## Fidelity work measures the seam instead of disguising it

The original/native race program remained focused on discriminating *executed* behavior from nearby observations. Several source-bound RF081 diagnostics recovered NMI frame gaps, sampled-memory differences, selected opcode-PC candidates and wake-PC/stack evidence. [#2099](https://github.com/gamesbyian/UR-Recomp/pull/2099) adds rejection paths for repinned wake PC or stack drift. These are necessary defenses against misidentifying evidence; they are not a causal CPU fix or a complete USA event result. Likewise, recovered original Dragster traces provide bounded comparative witnesses without assuming that the native execution already matches.

Graphics work retained the distinction between original-source frame truth and a polished-looking screenshot. The late QA08 investigation still carries mismatched source epochs and draft/HOLD restrictions. [Issue #2037](https://github.com/gamesbyian/UR-Recomp/issues/2037) documents independent concerns about a final-stage label impersonation and a read-by-path archive race in research consumers. The issue does **not** claim to prove incorrect physical output by itself. Held graphics proposals must not be promoted based on visually attractive but source-incomparable results.

## Recovery must not turn provenance into an acceptance shortcut

The same caution applied to recovering old Windows QA and saved Records work. [#2089](https://github.com/gamesbyian/UR-Recomp/pull/2089) recovered six bounded exporter and Windows CI changes from superseded #2060 onto current main; [#2094](https://github.com/gamesbyian/UR-Recomp/pull/2094) recorded the source-exact merger and supersession. Separate [issue #2076](https://github.com/gamesbyian/UR-Recomp/issues/2076) identifies a QA04 attachment path check/read race requiring a proper Windows handle-bound solution; [issue #2075](https://github.com/gamesbyian/UR-Recomp/issues/2075) records nonportable Windows ZIP-member names accepted by a provenance verifier. Neither is evidence of an actual compromised release, and neither should be erased by superficial green synthetic tests. The QA08 archive-admission and CI-source classifier recovery [#2066](https://github.com/gamesbyian/UR-Recomp/pull/2066) likewise must not grant release credit to historical mismatches.

The continuing [#2039 recovery hold](https://github.com/gamesbyian/UR-Recomp/issues/2039) names two unpublished evidence-design branches and explicit platform publication denials. This matters operationally: a denied write is not permission to relabel the same material as safe, and a Drive copy is not a merged PR. The user requested broad reconciliation and safe PR closure, but the safe procedure requires exact current-main comparison, proof of unique missing work, and retention of unresolved archives.

## Editorial verdict and next gate

The day's accomplishments were organizational continuity, genuine recovery and provenance checks, product-facing Modern UI scaffolding, and narrower source-exact CPU/graphics evidence. They were not sufficient to award full source-faithful original/native event completion, a visually approved Modern frontend, or physical Windows shipping acceptance. The previous diary reported **0/45** independently accepted complete USA events and **0/12** Windows gates; nothing independently verified in this diary establishes a changed count. Check the live [work queue](../docs/WORK-QUEUE.md), [release ledger](../docs/RELEASE-QUALITY-LEDGER.json) and the exact active PRs before treating either number as current.

The user continued to demand both velocity and rigor: independent agents should keep finding useful work when CI is waiting, but a source-bound negative must stay negative. The engineering story here is a shift toward traceable ownership and recoverable evidence while the difficult last-mile fidelity and presentation gates remain open.
