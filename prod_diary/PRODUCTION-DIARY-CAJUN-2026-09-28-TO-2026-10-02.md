# UR-Recomp Production Diary, Bayou Edition

**Period:** 2026-09-28 through 2026-10-02  
**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`

Pull up a chair on the porch, cher. This here is the same production story told in the regular diary, only now it has got some cypress knees in the water, a cast-iron pot on the fire, and enough bayou philosophy to make a debugger wonder whether it ought to bring bug spray.

The technical facts remain the same. PRs, generated evidence, tests and repository artifacts are still the authority. This version is for the story of the work: what got hauled out the swamp, what bit back, what looked like a gator and turned out to be a floating log, and which logs turned out to be very definitely gators.

---

## 2026-09-28 — One little remake idea wanders into the swamp and comes back carrying a laboratory

The whole business started innocent enough: would *Uniracers* make a good game to remake?

Mais, that question did not stay innocent for long.

A regular remake would have been the obvious road. Put the thing in Godot, get a wheel rolling around, tune the jumps until they feel right, put some shiny new graphics on top, call it supper.

UR-Recomp went the other direction entirely.

The visible game is small. One riderless unicycle. Little courses. Racing. Stunts. Menus. Not exactly *Final Fantasy VI* with seventeen opera houses and a moon full of accounting.

But underneath? That little unicycle got physics, landing rules, stunt state, boost economy, camera behavior, CPU racers, collision, track geometry, timing and enough tiny interlocking state to fill a bait bucket.

So the project made a decision early: do not imitate the game from the outside. Excavate it from the inside.

The job became:

- extract evidence;
- make deterministic fixtures;
- run the same inputs against different implementations;
- recover semantics instead of guessing;
- keep provenance for every important claim;
- rebuild only after the machinery is understood well enough to test the rebuild.

That was the first big turn in the river.

### The repo gets built like a field station

The repository became `gamesbyian/UR-Recomp`.

Right away the work started looking less like “make a game” and more like “establish a research camp before the mosquitoes carry the scientists away.”

The USA retail ROM was fingerprinted. It was confirmed as a 2 MiB LoROM with 8 KiB SRAM and no coprocessor. SNESRecomp work got a native build to a real title screen. Symbols and observations started getting written down in durable docs instead of being left to evaporate in chat.

The RNC compression work also started opening doors. Eventually the project would account for 45 valid Method-1 streams, and those streams would become one of the main trails through the game’s data.

A rule settled in early and never really left:

> If a discovery might matter later, put it somewhere an agent can find it again.

That sounds obvious until you have six agents, three emulators, forty generated reports and one mysterious byte at `$0FE9` all trying to tell you different stories before breakfast.

### PR #2: build the pantry before cooking the gumbo

PR #2 created the first proper external reference corpus.

Public reverse-engineering notes, emulator evidence, graphics references, historical materials and provenance records stopped being browser tabs and became repository knowledge.

Anything with muddy redistribution rights got indexed and summarized instead of casually copied in. That kept the project useful without turning the reference directory into a legal crawfish trap.

PR #3 reconciled repository hygiene and tooling.

PR #4 added the synthesized knowledge base under `docs/knowledge/`.

And here the project made another smart distinction: the knowledge base was for orientation, not authority.

Agents could read the short version first, but when the question got serious, they had to walk back to the source water: the research ledger, symbols, generated analysis, pinned references and actual runtime evidence.

Because if you let summaries become truth, sooner or later somebody writes down “probably” on Monday and by Thursday three agents are citing it like Moses brought it down the mountain.

### PR #5: the first real oracle

Then the project got itself a proper measuring stick.

PR #5 recovered a controller-only route from clean boot into the first one-player race and ran it through both:

- the native SNESRecomp build;
- a pinned Snes9x reference route.

No state pokes. No cheating the menus. Just inputs.

Now both implementations could be driven through the same frontend states and into the same race, while the project dumped full WRAM at known checkpoints.

That changed everything.

Screenshots tell you what two things look like.

A deterministic replay with state capture tells you whether they are doing the same thing underneath.

At first, the full comparisons looked ugly. Hundreds of differing bytes in frontend states. Seven still different at settled race entry.

Easy conclusion: native is wrong.

Actual conclusion after PR #6: not so fast, cher.

Four of those bytes were stale stack history in page `$01xx`. The remaining three were timing and phase counters running on slightly different cadence.

Meaningful race state was fine.

That taught the project one of its most important lessons:

> Byte-for-byte equality can be a terrible oracle when the bytes include harmless machine residue.

Sometimes you need exact equality. Asset reconstruction? Absolutely. SRAM round trip? You bet.

Gameplay? Often the right question is whether the same semantic event produced the same meaningful state, not whether every timer and dead stack byte happened to match on host frame 1,044.

### PR #7: make the unicycle actually do something

Once race entry was trustworthy, the project started poking behavior.

First came straight-line acceleration. Nice and clean. Right input, staged checkpoints, recovered X position and signed X speed.

Native and Snes9x matched.

Then came jumping, and here the swamp handed over a nice little lesson.

A short B press seemed to correlate with an airborne field.

Could have stopped there and declared victory.

Instead, the paired racer data showed the changing field belonged to the other racer.

So the project ran a matched no-B control.

Result: player 1 had not jumped at all.

That “success” went straight into the bucket marked **NOPE**.

The short pulse became useful negative evidence, the fixture got changed to a sustained B hold based on the recovered historical bot behavior, and *that* produced the real player-1 jump.

Native and reference matched again.

This became the project’s preferred rhythm:

1. see something interesting;
2. distrust the interesting thing;
3. build the cheapest control that could embarrass the hypothesis;
4. keep the hypothesis only if it survives.

A good reverse-engineering project ought to be a little rude to its own ideas.

### Digging through old sheds

Meanwhile, the archaeology spread outward.

Old bots. TAS files. emulator notes. reverse-engineering scraps. SNES development tools. press material. abandoned utilities. strange old corners of the web where filenames go to die.

PR #8 started auditing imported tools rather than assuming anything old and useful was also correct.

PR #10 made “research before reinvention” part of the operating method. If two or three different local approaches fail to reduce uncertainty, stop building fancier homemade contraptions and go see how emulator authors, ROM hackers, TAS people, decompilers and console developers solved related problems.

Also, one naming rule got hammered in early:

“Widescreen” is a feature.

“HD” is a feature.

Neither one is the name of the whole project.

UR-Recomp is about recovering and modernizing the game faithfully. Widescreen is one pot on the stove, not the whole kitchen.

### End of September 28

By bedtime, the project had gone from “maybe remake Uniracers” to:

- native executable;
- trusted reference path;
- deterministic input;
- full WRAM comparison;
- provenance-first research corpus;
- symbol and knowledge systems;
- audited tooling;
- a working scientific method for testing fidelity.

Not bad for day one.

The next problem was making sure all that machinery did not depend on half the internet being awake and cooperative.

---

## 2026-09-29 — Put the tools on dry land before the flood comes

The second day was mostly about infrastructure, which means it looked less dramatic and mattered enormously.

You can do brilliant archaeology with fragile tools right up until the tool disappears, the dependency changes, the CI image updates or a GUI decides it needs a window server at three in the morning.

UR-Recomp started fixing that before it became a crisis.

### Third-party tools get frisked at the door

The tooling audit, eventually reconciled through PR #12, treated every imported script and external tool like a stranger arriving at the fishing camp carrying a locked cooler.

Could be useful.

Could also contain snakes.

The audit found:

- build assumptions tied to GUI environments;
- shell invocation that did more magic than necessary;
- historical scripts with duplicate-key and width assumptions;
- emulator implementations that were useful references but poor independent corroborators in certain hardware seams.

One especially important example was Snes9x.

Snes9x was tremendously useful for behavior comparison, but it explicitly carried special handling for *Uniracers*.

So if native and Snes9x agreed around active-display OAM behavior, that did **not** automatically mean the implementation matched actual hardware. They might simply be sharing the same practical workaround.

That distinction between “good behavioral oracle” and “independent architectural witness” became part of the project’s evidence vocabulary.

PR #13 then made the toolchain more headless and CI-friendly, because agents do not need a gorgeous GUI if what they really want is one deterministic trace and a JSON file.

### Build an island before the bridge washes out

Then came the offline-island push.

The user wanted the core project usable even if external services vanished.

Not “we have a lockfile.”

Not “we pinned a Git hash.”

Actually islanded.

PR #15 made that Priority 0.

PR #21 turned the idea into executable policy:

- a `third_party/` boundary;
- machine-readable provenance;
- explicit migration state;
- validation;
- an offline mode that fails instead of quietly fetching from the network.

PR #23 brought in the first real vendored component: `mesen-for-ai`.

The practical reason was reproducibility.

The more interesting reason was control.

If the tool source lives in the repo, agents can inspect it, patch it and adapt it to the project instead of inventing workarounds around some opaque upstream behavior.

That is a big difference in a project where the tools are part of the experiment.

### UI, HD references and the danger of pretty pictures

PR #11 mapped the frontend states into an evidence-labelled navigation model.

That helped deterministic automation, but it also laid groundwork for future UI recreation.

The HD visual-reference work, brought in through PR #14 and later reconciled as #18, got a similar treatment.

Modern scalers, shaders and bsnes-hd were useful.

But they were reference tools, not truth machines.

The ROM, framebuffer, extracted assets and known semantics remained the authority.

Because a very pretty wrong answer is still wrong, no matter how many CRT bloom filters you put on it.

### Course work starts turning into something you can reason with

The course-format lane kept digging.

One useful correction came when an interpreter bridge scope entry had been treated too literally as the actual store site.

Static source alignment showed it was not.

That led to another quiet rule:

> Name instrumentation according to what it truly measures.

If you know you entered an interpreter scope, call it that.

Do not name it `exact_store_that_proves_my_theory` just because that would make the markdown prettier.

The course data work kept connecting RNC streams, decoded structures, cursor paths and runtime materialization.

At the time it was “course archaeology.”

Later it would become one of the main reasons Widescreen could be approached safely.

### GitHub Actions stops being just CI and starts being lab equipment

The growing experiment count exposed another little swamp hole.

Some successful research jobs computed the right answer and then failed to save it because `analysis/generated/` had been caught by an over-broad ignore rule.

PR #22 fixed that and harvested the evidence.

That was the point where the role of Actions became explicit:

GitHub Actions was not just a test runner.

It was a research scheduler.

A laboratory needs working labels, clean sample storage and reproducible instruments. Same principle here.

### End of September 29

By the end of the day:

- tooling had trust categories;
- headless operation had priority;
- offline operation was becoming real;
- UI states had a durable map;
- visual-reference work had a proper evidence hierarchy;
- course structures were becoming useful for presentation reasoning;
- experiment output persistence got treated as part of correctness.

Now the project had enough historical material to stop merely collecting it and start asking what old bots and reverse-engineering files actually knew.

---

## 2026-09-30 — The old bot scripts start talking

September 30 was when the historical material turned from museum pieces into working evidence.

There is a difference between finding an old RAM map and proving that an address still means what somebody said it meant fifteen years ago.

UR-Recomp started closing that gap.

### Nitrodon, Dessyreqt and the old toolbox

PR #93 preserved nine Nitrodon files with provenance.

PR #94 mined them.

That archive did not merely confirm current ideas. It corrected some.

The project refined:

- tabletop state into duration/progress rather than a simple count;
- stunt counter widths;
- twist/Z-flip semantics;
- shared working fields versus stable player fields;
- routine seeds for stunt finalization, vertical acceleration, controller decode and HUD/message work;
- the exact base-5 stunt-combination index into a 625-byte table.

Now, the project could have simply copied the historical names into the modern symbol table and gone fishing.

It did not.

Historical labels stayed historical until corroborated.

That saved the project from turning one person’s 2014 guess into a 2026 “fact” just because it came in a text file with hexadecimal numbers.

### USJO v8 becomes a testable model

PR #80 transformed USJO v8 from old source into a validation program.

Some fields became runtime-confirmed. Others received strong static support. Reward ladders, control state and stunt behavior got extracted into machine-readable outputs.

PR #81 then poked those semantics at runtime.

Native and Snes9x matched on the sampled fields.

An X-button intervention produced no sampled difference.

The project did not write “X is irrelevant.”

It wrote, in effect:

> Under this particular timing and state, this intervention produced no observed change. The historical bot used state-dependent timing, so go test that instead.

That sort of sentence is ugly and correct, which is usually better than beautiful and wrong.

### Historical replay gets cantankerous

Attempts to replay old TAS and bot inputs exactly ran into emulator-timing differences.

The 2008 WIP material desynchronized under the modern reference route before reaching the expected race.

That might sound like failure.

It was actually classification.

The project learned that some historical artifacts were strong sources of:

- controller policy;
- RAM semantics;
- intended transitions;
- old emulator assumptions.

But not necessarily frame-perfect modern regression oracles.

That is valuable because it tells future agents how to use the evidence without asking it to do a job it cannot do.

### Audio lane goes fishing in a different canal

PR #83 worked on audio without tangling with the active race-fidelity lane.

The CPU-side record pool got reconciled.

Unreachable song records were tied to preserved unused-song SPC captures.

Package blocks were mechanically correlated against known snapshots.

Not the main remaster bottleneck, but a nice demonstration of parallel research done right: separate lane, compact evidence, clear scope, merge cleanly.

### CI learns manners

By now too many Actions workflows were waking up for the wrong reasons.

PRs #96 through #99 tightened triggers, added cancellation and separated true regression jobs from exploratory one-shot research.

The new social contract for CI was:

- real regression? Run on PR and main;
- expensive exploratory experiment? Manual dispatch;
- superseded run? Cancel it;
- docs-only edit? Do not wake a twenty-minute emulator build unless the doc is somehow executable.

That cut noise and made the machine time useful again.

### The four ROMs become one comparative instrument

PR #100 promoted the four preserved ROMs into a proper comparative archaeology corpus.

USA retail.

Europe retail.

PAL prototype.

Legacy beta.

Instead of comparing them only when convenient, the project began using them systematically to discover:

- code/data boundaries;
- stable functions;
- relocations;
- regional growth;
- analyzer disagreements;
- semantic continuity.

This was the beginning of the structural-island era.

### End of September 30

By then UR-Recomp had:

- old bot semantics being tested instead of worshipped;
- historical recordings being classified by actual usefulness;
- parallel research lanes operating safely;
- CI tuned for experimentation;
- four ROMs ready to act like multiple geological cores through the same buried machine.

The project was about to do a lot of digging.

---

## 2026-10-01 — Dig enough holes and eventually you find the plumbing

October 1 was a wild one.

The repo started accumulating structural islands, semantic bridges, course subsystems, renderer paths, multiplayer evidence and enough PR numbers to make a crawfish accountant nervous.

But underneath all that activity was one real transition:

The project moved from isolated addresses to coherent systems.

### The method gets written down

PR #119 codified the AI-assisted reverse-engineering method.

The big ideas were already visible in practice:

- deterministic fixture before interpretation;
- cheap discriminator before giant trace;
- perturbation before speculation;
- mechanical oracle whenever possible;
- dead ends preserved;
- external research used deliberately;
- emulator and hardware evidence escalated when necessary.

The objective was never “let an AI stare at assembly until wisdom happens.”

The objective was to make a laboratory where bad guesses die young.

### Structural islands start lining up

Across a long run of PRs, the comparative-ROM work recovered bounded executable regions in:

- course materialization;
- geometry;
- race control;
- race-loop support;
- camera-related math;
- message/state bridges;
- rendering and tile preparation.

USA retail and the beta were often byte-identical.

PAL prototype and Europe frequently relocated the same logic.

Sometimes a regional version grew internally. When that happened, the analysis stopped pretending the whole region could be explained with one fixed offset.

That was a quiet but important maturity upgrade.

Do not force tidy mathematics onto messy history.

Record the messy history.

### Multiplayer gives the project a splinter

A multiplayer lane exposed small native/reference drift in racer state.

Tiny numbers.

Still real.

The project responded by separating:

- multiplayer HUD work;
- viewpoint/camera evidence;
- culling;
- geometry;
- fidelity state.

That led to a practical habit that showed up in conversation after conversation: before starting new work, check what the other agents are touching and pick a separate lane.

A repo full of clever agents is no help if everybody edits the same five files.

### Course format becomes “enough” before it becomes “complete”

This was one of the best decisions of the sprint.

The project recovered enough Dragster spatial structure to support presentation and Widescreen reasoning without demanding a perfect authoring model first.

The key model included:

- 1024 × 16 coarse sectors;
- 64-unit sector scale;
- a 65,536 × 1,024 world domain;
- a 16,384-entry coarse-sector-to-fine-record table;
- fine 4×4 cell structures;
- runtime materialization;
- neighborhood gathering;
- surface sampling.

That was declared **presentation-complete**.

Not editor-complete.

Different problem.

Different finish line.

Without that distinction the project could have spent weeks decoding every course-authoring edge case before touching Widescreen.

Instead it learned exactly what the next decision required and stopped there.

### Racer graphics get a clean chain of custody

The presentation lane also reached a useful stopping point.

Persistent racer presentation IDs got tied to exact table entries and exact ROM asset streams.

Race-init OBJ resources were identified.

Original SNES 4bpp graphics could be extracted and reconstructed byte-for-byte.

Palette provenance was tied in.

Now “this racer frame” could mean a semantic game state *and* a precise source asset identity.

That is much stronger than saying “this screenshot looks about right.”

### Save/load works. Winning still needs proof.

PR #188 proved a game-authored SRAM round trip.

The game wrote SRAM.

The checksum was valid.

The 8 KiB image reloaded in a fresh reference process.

The bytes survived exactly.

Good.

But the run did not produce medal or tier progression.

So the progression acceptance item stayed open.

PR #191 kept the negative medal/chord experiments instead of pretending the broader problem was solved.

That is evidence hygiene right there:

- “SRAM persistence works” = proven.
- “Meaningful medal progression survives save/load” = still needs a real medal-changing fixture.

Do not make one fact wear another fact’s hat.

### PR #183: stop counting holes and ask whether they reach water

By late in the day the structural census was getting huge.

That was productive, but dangerous.

The repo could easily have turned “number of recovered code bytes” into a vanity metric.

PR #183 changed the project’s planning spine around **semantic sufficiency**.

The new model asked whether the project could:

1. observe the relevant state;
2. explain the causal mechanism;
3. modify it safely;
4. validate the result.

That gave structural recovery a stopping rule.

Recover more code when it unlocks one of those capabilities.

Otherwise, maybe the next best experiment is somewhere else.

That decision probably saved the project from becoming a magnificent decompilation swamp nobody could ever leave.

---

## 2026-10-02 — Eight extra pixels walk in and start a family argument

Now we get to the Widescreen story.

The project asked a tiny question:

What if the presentation gets eight pixels wider?

Eight.

Not eighty.

Eight.

That little margin found exactly the kind of hidden coupling the project had spent four days preparing to investigate.

### First, know what lives beyond the old screen edge

PR #184 finished the representative Dragster spatial/resource contract.

PR #189 nailed down the object activation timeline.

And the important result was this:

Presentation visibility and gameplay activation are not the same thing.

The finish/checker content can enter presentation before the later gameplay/contact behavior activates.

Therefore:

> A wider screen may reveal more of the world, but it must not make gameplay objects become authoritative earlier.

That is the contract.

If a modern renderer accidentally expands the activation domain with the camera, the race itself can change.

Now Widescreen has a real engineering rule instead of just “show more stuff.”

### PR #190: +8 goes red

The first tiny-margin harness captured 0, +8, +16 and +24.

And +8 failed the initial authoritative-state equality check.

Well now.

That looked bad.

Could have meant widening the renderer changed simulation.

Could have meant timing.

Could have meant the harness was comparing the wrong things.

So the project did not scream “Widescreen is broken.”

It classified.

The next question became whether the difference was:

- checkpoint alignment;
- bookkeeping;
- host-presentation cadence;
- actual semantic simulation drift.

### PR #204: the scary divergence turns out to be mostly a clock problem

The +8 run was already three guest frames ahead in the frontend.

Before the race.

That offset persisted.

Once checkpoints were aligned by semantic event rather than nominal frame, meaningful race state matched:

- position;
- velocity;
- camera;
- checkpoint/gate state;
- laps;
- progression transition.

A transient field differed briefly, then reconverged without changing the race trajectory.

So the original equality gate had been too strict.

The widening changed host cadence.

It did not meaningfully alter retained race simulation.

There is that first-day lesson again, wearing a different hat:

> Same nominal frame is not always same semantic moment.

### PR #205: then the project finds the real bug

Once the cadence problem was removed from the comparison, an actual presentation regression appeared.

Two pixels.

At classic x=255.

At one specific object-tail checkpoint.

Now that is a proper bug. Small enough to corner.

The project showed:

- guest OAM still matched at onset;
- BG-only matched;
- OBJ-only matched;
- the combined frame did not;
- OBJ-only diverged later;
- OAM diverged later still;
- sprite-limit accounting was not the cause;
- pinned-window expansion was not the cause.

So the bug moved from “Widescreen does weird stuff” to:

> host renderer composition / OBJ edge semantics at the classic viewport boundary.

That is what good reverse engineering looks like.

Take a vague monster and keep cutting away possibilities until all that is left is one muddy footprint.

### PR #206: the measuring stick bends

The next obvious test was a layer-mask matrix.

Turn layers off, isolate the source.

Except turning layers off changed guest cadence.

The instrumentation perturbed the phenomenon.

So the matrix could not support causal claims.

The project kept the result anyway, as negative instrumentation evidence, and switched to a host-only trace that left the normal render path intact.

That belongs in the diary because it is one of the finest lessons of the sprint:

> A debugger can absolutely lie to you by changing the thing you are debugging.

Not maliciously.

Just mechanically.

### Meanwhile, the camera-to-VRAM chain finally closes

PR #192 had found compact update-list structures at `$0DCD/$0DCF`.

Runtime samples showed them staying at zero.

Maybe bad fixture?

Nope.

Later work showed they were simply not the active scrolling transport for this scene.

PR #203, later reconciled through #208, found the real path:

1. camera state updates;
2. window helper derives entering-edge coordinates;
3. entering columns are built into a `$03xx` DMA descriptor family;
4. NMI consumes the descriptors;
5. horizontal presentation operates as a 32-column VRAM ring.

Two other plausible paths were ruled out:

- one was HUD/message tilemap work;
- one was racer-presentation graphics prep.

That is semantic closure: not just “I found some code near the camera,” but a chain from camera movement to actual presentation data arriving in VRAM.

### PR #207: all them jars on the shelf finally get labels

By now the repo had a great deal of information spread across:

- course headers;
- track names;
- historical landmarks;
- SRAM progression;
- racer state;
- regional correspondence;
- deterministic fixtures;
- old reverse-engineering notes.

PR #207 consolidated those into normalized queryable data and ran a two-pass inference audit.

That produced new knowledge, not just tidier files.

Among the results:

- corrected canonical RNC stream/name/tour order;
- clean `dessyreqt_track_id = stream_index - 1` mapping across all 45 courses;
- historical start/finish landmarks attached across the corpus;
- paired header coordinates strengthened into a racer-spawn model;
- cross-course relationships exposed;
- progression, course-resource and fixture catalogs normalized;
- state schema enriched with regional and historical semantics.

In plain bayou language:

The project stopped keeping every ingredient in a separate paper bag and finally made itself a proper pantry.

And once the jars were labelled, recipes started appearing that nobody could see before.

PRs #208 and #209 then updated the plans so future agents use that consolidated layer instead of wandering back through twenty old markdown files with a lantern.

### Quiet-repo cleanup becomes a craft

A bunch of PRs around #193–#201 were not glamorous research.

They were rescue work.

Completed agent branches had useful evidence but stale history.

So the project developed a clean pattern:

- identify what is genuinely unique;
- replay it onto current main;
- leave obsolete branch history behind;
- supersede redundant PRs explicitly;
- merge the evidence, not the confusion.

This matters when agents work in parallel.

Otherwise the repo turns into a shrimp net full of branches and every one of them has caught the same boot.

---

## What this first sprint taught

By the end of October 2, the project had stopped looking like “somebody trying to remake Uniracers” and started looking like a reverse-engineering platform with a game attached.

It had:

- deterministic frontend and race fixtures;
- event-relative native/reference comparison;
- confirmed movement and jump semantics;
- SRAM round-trip acceptance;
- large comparative structural coverage;
- reconciled historical bot/RAM evidence;
- presentation-complete course knowledge;
- exact racer asset round trips;
- a camera-to-VRAM scrolling chain;
- an activation-versus-visibility contract;
- Widescreen diagnostics strong enough to separate cadence from simulation;
- a real two-pixel renderer bug narrowed to host composition behavior;
- normalized data good enough to support cross-domain inference;
- a semantic-sufficiency model for deciding when “enough reverse engineering” is actually enough.

And the open questions had gotten much better.

The project no longer had to ask:

> Can we understand this game deeply enough?

Now it could ask:

- Why do those two pixels at x=255 compose differently?
- How do we get a real medal-changing fixture?
- Which multiplayer differences remain semantically meaningful?
- How do we expose more world without activating more game?
- Which consolidated datasets can answer the next question cheaper than another trace?

Those are fine questions.

Fine questions mean the swamp is mapped.

Maybe not drained.

Would not want to drain it anyway.

That is where all the interesting critters live.

---

## Bayou engineering rules

A few lessons deserve to be painted right on the side of the pirogue.

### A negative result is still supper

Short B pulse did not jump?

Good. Now you know.

X press did not change sampled stunt state?

Good. Narrower problem.

Medal chord did not mutate SRAM?

Good. Stop pretending that route works.

Compact update list stayed zero?

Good. Wrong transport.

Layer mask changed cadence?

Excellent. Your instrument is dirty.

A proper experiment either confirms something or kills something.

Both are progress.

### Compare meaning, not swamp bubbles

Stack residue, phase counters and host timing can wiggle all day without changing the race.

Use exact equality where exact bytes are the contract.

Use semantic/event-relative equality where gameplay meaning is the contract.

Do not chase every bubble like it is a catfish.

### Instruments can scare the wildlife

Trace hooks, layer masks, debug servers and alternate rendering modes can perturb timing.

Always ask what the measuring tool itself changes.

Sometimes the best probe is the one that touches almost nothing.

### Stop digging when you have enough for the next bridge

The comparative structural work was powerful.

It could also go forever.

Semantic sufficiency put a gate on it:

- can we observe?
- can we explain?
- can we modify safely?
- can we validate?

If yes, maybe build the bridge.

You can always come back and count more tree rings later.

### Old notes are leads, not gospel

Historical bot authors knew a lot.

They also worked with old emulators, incomplete models and practical shortcuts.

Use their work to aim experiments.

Do not confuse “somebody wrote this in 2014” with “the hardware signed an affidavit.”

### Organizing data can create new facts

Once course order, SRAM rows, header fields, landmarks and fixtures were lined up in compatible data structures, relationships appeared that had been invisible in prose.

Sometimes the next reverse-engineering tool is not another emulator.

Sometimes it is a better table.

### The repo is the camp ledger

Chats are where ideas happen.

PRs are where claims get argued.

Generated data is where machines testify.

Plans say what is still open.

`prod_diary/` remembers why anybody cared.

That division of labor is worth keeping.

---

## Production status at 2026-10-02

At the beginning, the great big question was whether a compiled 1994 SNES ROM held enough recoverable truth to support an extremely faithful modern implementation.

After this first sprint, the answer looks mighty encouraging.

The logic is recoverable.

The data is tractable.

The historical material is unusually rich.

The runtime can be instrumented.

The agents can work in parallel without completely setting the dock on fire, provided their lanes stay separate and the repository keeps good evidence discipline.

The biggest question has changed.

Now the project has to decide where exact reproduction ends and deliberate modernization begins.

And cher, that is a much nicer alligator to wrestle.
