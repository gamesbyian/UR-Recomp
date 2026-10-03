# UR-Recomp Production Diary

**Period:** 2026-09-28 through 2026-10-02  
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
