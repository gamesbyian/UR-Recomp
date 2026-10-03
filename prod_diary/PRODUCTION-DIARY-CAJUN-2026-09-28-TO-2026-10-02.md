# UR-Recomp Production Diary, Bayou Edition

**Period:** 2026-09-28 through 2026-10-02  
**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`

Pull up dat chair, cher. Dis here be de same production story what got wrote down proper in de regular diary, only dis time it come crawlin’ out de cypress water with mud on its boots, a pot bubblin’ on de fire, an’ enough back-porch grammar to make a compiler start wonderin’ whether semicolons got souls.

Technical facts ain’t changin’. PRs, generated evidence, tests, traces, symbols, an’ repository artifacts still de law of de land. Dis copy just tellin’ de tale de way a swamp-dweller might tell it: what got dragged out de reeds, what bit somebody, what looked like a gator but was only a log, an’ what looked like a log till it opened its mouth.

---

## 2026-09-28 — One little remake idea wander into de swamp an’ come back carryin’ a laboratory

Whole thing start innocent enough.

Would *Uniracers* make a good game to remake?

Mais, dat question ain’t stay innocent long.

Regular remake, you know how dat go. Put de thing in Godot, get dat wheel rollin’, tune de jump till it feel right, make de graphics nice an’ shiny, call everybody to supper.

UR-Recomp go wanderin’ off de other way entirely.

Visible game look small. One riderless unicycle. Little courses. Racing. Stunts. Menus. Ain’t exactly *Final Fantasy VI* with seventeen opera houses an’ a moon fulla paperwork.

But underneath? Cher, dat little unicycle ain’t got no business carryin’ dat much machinery.

Physics. Landin’ rules. Stunt state. Boost economy. Camera behavior. CPU racers. Collision. Course geometry. Timin’. Whole mess packed in dere tighter’n crawfish in a trap.

So de project make a choice early:

Don’t imitate de game from outside.

Dig down in it.

Pull out evidence. Build deterministic experiments. Make two implementations eat de same inputs. Learn what de state actually mean. Then rebuild from what can be proved.

Dat right dere be de first big bend in de bayou.

### Repo bootstrap: build de camp before huntin’ monsters

Repository get made as `gamesbyian/UR-Recomp`.

First useful milestone ain’t some fancy mock-up. It a field station.

USA retail ROM get fingerprinted. Two MiB LoROM. Eight KiB SRAM. No coprocessor. SNESRecomp work get far enough to show a real title screen. Symbols start gettin’ written down. Research evidence stop livin’ only in chat where it liable to drift off downstream.

RNC compression turn out to be one of de big doors in de whole game. Eventually, project count 45 valid Method-1 streams.

A rule settle in fast:

> If dat observation might matter later, put it somewhere somebody can find it again.

Sound obvious till you got six agents, three emulators, forty generated reports, an’ one suspicious byte at `$0FE9` all yellin’ different things before coffee.

### PR #2: build de pantry before cookin’ de gumbo

PR #2 make de first proper external reference corpus.

Historical reverse-engineerin’ notes, emulator evidence, graphics references, public material, cheats, provenance. All dat quit bein’ browser-tab fog an’ become repository knowledge.

Anything with muddy redistribution rights get indexed or summarized instead of tossed wholesale in de pot.

PR #3 clean up repo hygiene an’ research tooling.

PR #4 add a synthesized knowledge layer under `docs/knowledge/`.

But project make one important distinction:

Knowledge layer be for orientation.

Evidence layer be de authority.

Agents can read de short version to get dey bearings. But when somebody wanna make a serious claim, dey gotta walk back to de source water: research ledger, symbols, generated analysis, pinned references, runtime evidence.

Else Monday somebody write “probably,” Tuesday somebody paraphrase it, an’ by Thursday three agents swear it carved on stone tablets.

### PR #5: now dis thing actin’ like science

PR #5 where de whole operation quit just diggin’ bones an’ started performin’ experiments.

Recovered a controller-only route from clean boot into de first one-player race.

Run same route through:

- native SNESRecomp;
- pinned Snes9x reference.

Ain’t pokin’ no game state.

Ain’t draggin’ de program by its suspenders.

Just controller input an’ whatever truth come spillin’ out.

Now both implementations can walk through de same frontend states, enter de same race, an’ dump full WRAM at known checkpoints.

Dat changed de game.

Screenshots tell you two things look alike.

Deterministic replay tell you whether dey thinkin’ alike underneath.

First full comparison look ugly.

Hundreds of bytes differ up front.

Seven still differ at settled race entry.

Easy conclusion: native busted.

Actual conclusion after PR #6?

Nah, cher.

Four of dem seven bytes was stale stack mud in page `$01xx`.

Other three was timing an’ phase counters tickin’ a little outta step.

No unexplained persistent gameplay divergence.

An’ dere come one of de project’s biggest lessons:

> Whole-machine equality can holler wolf when all you got is swamp grass movin’.

Sometimes exact bytes matter. Asset round trip? You bet. SRAM persistence? Absolutely.

Gameplay? Better ask whether de same semantic event produce de same meaningful state.

Don’t go worshippin’ every changed byte just ’cause it changed.

### PR #7: make dat wheel actually move

Once race entry trustworthy, project start pokin’ behavior.

First straight-line acceleration.

Low-confounder probe.

Hold Right.

Sample X position.

Sample signed X speed.

Native an’ Snes9x match.

Then come jumpin’.

First B-button poke look mighty promising. One air-state-looking byte start dancin’, so a fella coulda slapped a label on it an’ gone home happy.

But nah.

Closer comparison show dat changin’ field belong to de other racer.

So project run de same timing with no B.

Other racer still jumpin’.

Into de evidence pot dat theory go, lid an’ all.

Short pulse get preserved as negative evidence.

Fixture change to a sustained B hold based on recovered historical bot behavior.

Dat finally launch player 1 proper.

Native an’ reference match again.

From here on, project got itself a rhythm:

1. see somethin’ interesting;
2. distrust it;
3. build de cheapest experiment likely to embarrass it;
4. keep it only if it survive.

Good reverse-engineerin’ oughta be a little rude to its own ideas.

### Old sheds, dead websites, an’ tools with snakes in de cooler

Meanwhile archaeology spread out.

Old bots. TAS files. Emulator notes. reverse-engineerin’ scraps. SNES dev tools. Press material. Dead links. Strange corners of de web where filenames go to die alone.

PR #8 start auditin’ imported tooling instead of trustin’ whatever somebody uploaded in 2009.

PR #10 formalize “research before reinvention.”

If two or three genuinely different local approaches ain’t shrinkin’ uncertainty, stop buildin’ fancier homemade contraptions.

Go see how emulator authors, ROM hackers, TAS folks, decompilers, an’ consoledev people solved related problems.

Another naming rule get nailed down:

“Widescreen” be a feature.

“HD” be a feature.

Neither one be de whole project.

UR-Recomp about faithful reconstruction an’ deliberate modernization.

Widescreen just one pot on de stove.

### End of September 28

By sundown, project got:

- native executable reachin’ real states;
- trusted reference path;
- deterministic input;
- full-WRAM comparison;
- provenance-first research corpus;
- symbols an’ knowledge docs;
- audited toolin’;
- a proper experimental method.

Started de day askin’ whether *Uniracers* be fun to remake.

Ended it buildin’ a forensic lab around a SNES ROM.

Dat escalated quick.

---

## 2026-09-29 — Get dem tools up on dry land before de flood come

Second day less flashy.

Also mighty important.

You can do brilliant archaeology with fragile tools right up till de tool vanish, de dependency move, CI image change, or some GUI decide it need a display server at three in de mornin’.

UR-Recomp start fixin’ dat before it become a proper mess.

### Third-party tools get frisked at de dock

Tooling audit, later reconciled through PR #12, treat every imported script an’ external tool like a stranger walkin’ into camp carryin’ a locked cooler.

Might have beer in dere.

Might have snakes.

Audit turn up:

- build recipes expectin’ GUI environments;
- shell invocation doin’ more magic than necessary;
- historical code with duplicate keys an’ width assumptions;
- emulator implementations useful for behavior but poor as independent witnesses at certain hardware seams.

Snes9x be de big example.

Snes9x mighty useful.

But it explicitly carry special handlin’ for *Uniracers*.

So if native an’ Snes9x agree around active-display OAM behavior, dat ain’t independent proof of hardware truth.

Could just mean both routes got de same practical patch.

Project start distinguishin’:

- useful behavioral oracle;
- independent architectural corroboration.

Dat distinction save trouble later.

PR #13 make toolchain more headless, more CI-friendly, less interested in drawin’ windows nobody watchin’.

Agents usually don’t need a pretty GUI.

Dey need one deterministic trace an’ a JSON file.

### Build an island before de bridge wash out

Then come de offline-island obsession.

User want core research usable even if external services disappear.

Not “we pinned a version.”

Not “we got a lockfile.”

Actually self-contained where practical.

PR #15 make islandization Priority 0.

PR #21 turn it into executable policy:

- `third_party/` boundary;
- machine-readable provenance;
- explicit migration states;
- validation;
- offline mode what fail closed instead of sneakin’ off to de network.

PR #23 bring in first real vendored component: `mesen-for-ai`.

Reason one be reproducibility.

Reason two be power.

If source live in de repo, agents can inspect it, patch it, specialize it.

Ain’t gotta dance around upstream behavior like somebody tryin’ not to wake a gator.

### UI, HD references, an’ de seduction of pretty wrong answers

PR #11 map frontend states into an evidence-labelled navigation model.

Useful for automation.

Useful later for rebuilding UI.

HD visual-reference work, from PR #14 an’ reconciled as #18, get same disciplined treatment.

Modern scalers, shaders, bsnes-hd?

Useful.

Authoritative?

Nah.

ROM data, framebuffer evidence, extracted assets, known semantics remain de source water.

A very pretty wrong answer still wrong.

You can put all de CRT glow on it you want.

### Course work start showin’ its bones

Course-format lane keep diggin’.

One useful correction come when an interpreter bridge scope entry got treated like exact store location.

Static source alignment say otherwise.

Project learn another rule:

> Name de instrument by what it actually measure.

If you know you entered a scope, call it a scope.

Don’t name it `definitely_the_store_that_proves_everything` just ’cause dat make de report feel confident.

Course work keep connectin’ RNC streams, decoded structures, cursor paths, runtime materialization.

At de time it just look like course archaeology.

Later, dat work become one of de big reasons Widescreen could be investigated without accidentally rewritin’ gameplay.

### GitHub Actions turn into lab machinery

More experiments mean more workflow weirdness.

One batch compute useful evidence, then fail to persist it because `analysis/generated/` got swallowed by a broad ignore rule.

PR #22 fix dat.

Harvest de already-computed evidence.

An’ from dere, role of Actions get clearer.

CI ain’t just tests no more.

It a research scheduler.

A laboratory need clean labels, sample storage, reproducible instruments.

Same thing here.

### End of September 29

By end of day:

- tools got trust categories;
- headless operation preferred;
- offline-island work real;
- UI states got durable map;
- visual-reference work got proper hierarchy;
- course structures gettin’ useful;
- experiment persistence treated as correctness.

Now project got enough old evidence collected to start askin’ whether them historical bots know things de current code don’t.

---

## 2026-09-30 — Them old bot scripts start talkin’

September 30 where de museum pieces start givin’ testimony.

Findin’ an old RAM map one thing.

Provin’ what it mean now another.

Project start closin’ dat gap.

### Nitrodon, Dessyreqt, USJO, an’ de old toolbox

PR #93 preserve nine Nitrodon files with provenance.

PR #94 mine ’em.

Archive don’t just confirm ideas.

It correct some.

Project refine:

- tabletop state as duration/progress instead of simple count;
- stunt counter widths;
- twist an’ Z-flip semantics;
- shared working slots versus stable player fields;
- useful routine seeds;
- exact base-5 stunt-combination index into a 625-byte table.

Coulda copied historical labels straight into modern symbols.

Didn’t.

Historical label remain historical till corroborated.

Dat rule matter.

Somebody’s 2014 note can be brilliant.

Can also be half-right in a way what waste three days if you treat it like scripture.

### USJO v8 become a testable model

PR #80 turn recovered USJO v8 into a validation matrix.

Some fields become runtime-confirmed.

Some get strong static support.

Reward ladders, control model, stunt behavior get extracted into generated artifacts.

PR #81 poke dem semantics at runtime.

Native an’ Snes9x match on sampled recovered fields.

One X-button intervention produce no sampled difference.

Project don’t write “X does nothin’.”

Project write de narrower truth:

Under dis state an’ dis timing, X produce no observed change.

Historical bot use state-dependent timing.

So next experiment gotta reproduce dat cadence.

Ugly sentence.

Good science.

### Historical replay get cantankerous

Attempts to replay old TAS/bot input exactly run into emulator timing trouble.

2008 WIP desync before expected race under modern reference route.

Ain’t useless.

It tell project what kind of evidence de old file is.

Maybe not a frame-perfect modern oracle.

Still useful for:

- controller policy;
- RAM semantics;
- intended transitions;
- historical timing assumptions.

Now future agents know how to use it without askin’ a crawfish trap to catch ducks.

### Audio lane fishin’ another canal

PR #83 work audio while gameplay fidelity happen elsewhere.

CPU-side record pool get reconciled.

Unreachable song records tied to preserved unused-song SPC captures.

Package blocks mechanically correlated with known snapshots.

Not de critical path.

Still good research.

Separate lane.

Compact evidence.

No tramplin’ on race work.

### CI finally learn some manners

Too many workflows wakin’ up for nonsense.

PRs #96–#99 tighten triggers, add cancellation, split one-shot research from permanent regression.

New rules:

- real regression? Run on PR an’ main;
- expensive archaeology? Manual;
- superseded run? Kill it;
- docs-only change? Don’t wake a twenty-minute emulator build unless dat doc actually drives somethin’.

Machine time stop gettin’ burned like wet firewood.

### Four ROMs become one big comparative instrument

PR #100 promote four preserved ROMs into a proper comparative corpus.

USA retail.

Europe retail.

PAL prototype.

Legacy beta.

Now differences ain’t occasional curiosities.

Dey become a systematic way to identify:

- stable functions;
- relocations;
- code/data boundaries;
- regional growth;
- analyzer disagreements;
- conserved semantics.

Dis setup about to pay off heavy.

### End of September 30

By now UR-Recomp got:

- old bot semantics gettin’ tested;
- historical recordings classified by real usefulness;
- parallel lanes runnin’ safely;
- CI tuned for research;
- four ROMs ready to act like geological cores through de same buried machine.

Tomorrow de digging get serious.

---

## 2026-10-01 — Dig enough holes an’ eventually you find de plumbing

October 1 be wild.

PR numbers multiply like mosquitoes after rain.

Structural islands.

Race-control routines.

Course helpers.

Renderer paths.

Multiplayer clues.

Whole repo start lookin’ like somebody dumped a tackle box on de floor.

But underneath all dat activity, one real transition happen:

Project stop askin’ only:

> What dis address do?

Start askin’:

> What subsystem dis belong to, how it behave, an’ what can we safely do with dat knowledge?

### Method get written down

PR #119 codify de AI-assisted reverse-engineerin’ method.

By now de project already know:

- deterministic fixture before interpretation;
- cheap discriminator before giant trace;
- perturbation before speculation;
- mechanical oracle whenever possible;
- preserve dead ends;
- use external research deliberately;
- escalate to emulator/test-ROM/hardware evidence when needed.

Goal never be “AI stare at assembly till magic happen.”

Goal be buildin’ a lab where bad guesses die young.

### Structural islands start linin’ up

Comparative-ROM program recover bounded executable regions in:

- course materialization;
- geometry;
- race control;
- race-loop support;
- camera math;
- message/state bridges;
- rendering;
- tile preparation.

USA retail an’ beta often byte-identical.

PAL prototype an’ Europe frequently relocate same logic.

Sometimes regional build grow inside de routine.

When dat happen, project stop forcin’ one constant offset across everything.

Record local shifts.

Record edit scripts.

Keep de messy history messy.

Ain’t no prize for makin’ de data prettier than de cartridge.

### Multiplayer give de project a splinter

Multiplayer lane find small native/reference drift in racer state.

Tiny differences in position an’ velocity.

Could dismiss ’em.

Didn’t.

Instead split work into separate lanes:

- HUD;
- viewpoint;
- camera;
- culling;
- geometry;
- fidelity state.

Dat lead to one practical operating habit:

Before startin’ new work, see what de other agents touchin’.

Then pick another trail.

A swamp fulla brilliant hunters still no good if dey all shootin’ at de same duck.

### Course format become “enough” before it become “complete”

Dis one be important.

Project recover enough Dragster spatial structure to support presentation reasoning without finishin’ de whole authoring model.

Key structure:

- 1024 × 16 coarse sectors;
- 64-unit sector size;
- 65,536 × 1,024 world domain;
- 16,384-entry coarse-sector-to-fine-record table;
- fine 4×4 cell structures;
- runtime materialization;
- neighborhood gathering;
- surface sampling.

Call it **presentation-complete**.

Not editor-complete.

Two different finish lines.

Dis save project from spendin’ forever decode-everythin’ before touching Widescreen.

You don’t need to know how every plank in de dock was milled before you can tell whether de dock reach de boat.

### Racer graphics get a clean chain of custody

Presentation lane reach same kind of sufficiency.

Persistent racer presentation IDs tied to exact table entries.

Exact ROM streams identified.

Race-init OBJ resources identified.

Original SNES 4bpp data extract an’ reconstruct byte-for-byte.

Palette provenance tied in.

Now “dat racer frame” mean both:

- de semantic state;
- de exact original asset.

Way stronger than eyeballin’ a screenshot an’ sayin’ “close enough.”

### Save/load works. Winnin’ still need proof.

PR #188 prove real game-authored SRAM round trip.

Game write SRAM.

Checksum valid.

8 KiB image reload in fresh reference process.

Bytes survive exact.

Good.

But run ain’t produce medal or tier mutation.

So medal-winning progression acceptance stay open.

PR #191 preserve negative chord/search results.

Dat evidence discipline right dere.

“SRAM persistence works” proven.

“Meaningful progression survives save/load” not yet.

Don’t make one fact wear another fact’s hat.

### PR #183: quit countin’ holes, ask whether any of ’em reach water

Structural census growin’ fast.

Dat productive.

Also dangerous.

Easy to start thinkin’ “more recovered bytes” equal “more progress.”

PR #183 change de planning spine around **semantic sufficiency**.

New questions:

1. Can we observe de relevant state?
2. Can we explain de mechanism?
3. Can we modify it safely?
4. Can we validate de result?

If yes, maybe stop diggin’.

Build de bridge.

You can always come back later if somebody need de exact shape of a beam.

Dat move probably save de project from becomin’ one magnificent endless decomp swamp.

---

## 2026-10-02 — Eight extra pixels walk in an’ start a family argument

Now come de Widescreen story.

Project ask one tiny question:

What happen if de presentation get eight pixels wider?

Eight.

Not eighty.

Eight.

Eight little pixels come sidlin’ in from de edge like dey ain’t fixin’ to bother nobody, an’ next thing you know de whole renderer got family troubles.

### First, learn what lives past de old screen edge

PR #184 finish representative Dragster spatial/resource contract.

PR #189 nail down object activation timeline.

An’ here come de important rule:

Presentation visibility an’ gameplay activation ain’t de same boundary.

Finish/checker presentation can show up before later collision/contact behavior activate.

Therefore:

> Wider renderer can reveal more world, but it must not make gameplay become authoritative sooner.

Dat de contract.

If Widescreen make offscreen objects “alive” earlier just because dey visible now, race logic can change.

Now Widescreen got a real engineering rule instead of “show more picture.”

### PR #190: +8 go red

First tiny-margin harness capture:

- 0;
- +8;
- +16;
- +24.

+8 fail initial authoritative-state equality gate.

Well, now.

Look like eight pixels done changed simulation.

Could be true.

Could also be bad alignment.

Could be harness bookkeeping.

Could be host cadence.

So project classify before panic.

Next question become:

1. checkpoint alignment?
2. bookkeeping?
3. presentation timing perturbation?
4. real simulation dependency?

### PR #204: scary divergence turn out to be clocks wearin’ costumes

+8 already three guest frames ahead in de frontend.

Before race start.

Dat -3 offset persist all de way through retained checkpoints.

Line de runs up by semantic event instead of nominal frame, an’ durable race state match:

- position;
- velocity;
- camera;
- checkpoint/gate state;
- laps;
- progression transition.

One transient field wiggle, then come back.

No meaningful trajectory change.

So whole-WRAM gate was hollerin’ at shadows.

Widening changed host cadence.

Didn’t meaningfully change retained race simulation.

Same lesson from day one come paddlin’ back:

> Same frame number ain’t always same moment.

### PR #205: now dey find de real critter

Once cadence noise come out de comparison, actual presentation regression show itself.

Two pixels.

Right dere at classic x=255.

Two raggedy little pixels causin’ more commotion than a raccoon in a bait shed.

Project narrow it down:

- guest OAM still identical at onset;
- BG-only still match;
- OBJ-only still match;
- composite don’t;
- OBJ-only divergence come later;
- OAM divergence later still;
- SNES sprite-limit accounting ruled out;
- pinned-window expansion ruled out.

Now de bug got a proper name:

Host renderer composition / OBJ edge semantics at classic viewport boundary.

Dat what good reverse-engineerin’ look like.

Start with “Widescreen broke somethin’.”

Keep cuttin’ away possibilities till all you got left one muddy footprint.

### PR #206: measuring stick bend in de hand

Next obvious test: layer-mask matrix.

Turn off layers, isolate source.

Except changin’ layer mask change guest cadence.

Now de instrument alterin’ de thing it supposed to measure.

So dat matrix can’t support causal claims.

Project keep it anyway.

Negative instrumentation evidence.

Then switch to a bounded host-only trace what leave normal render path intact.

Dis one deserve paintin’ on de porch wall:

> Debugger can lie by changin’ de world it lookin’ at.

Ain’t malicious.

Just mechanical.

### Meanwhile, camera-to-VRAM chain finally close

PR #192 found compact update-list structures at `$0DCD/$0DCF`.

Runtime samples show dem stayin’ zero.

Coulda blamed fixture.

Didn’t.

Later work show dem structures real, just not de active Dragster scrolling transport.

PR #203, later reconciled through #208, find de real path:

1. camera state update;
2. camera/window helper derive entering-edge coordinates;
3. entering columns build into `$03xx` DMA descriptor family;
4. NMI consume descriptors;
5. horizontal presentation run as a 32-column VRAM ring.

Two tempting live paths get excluded:

- one HUD/message tilemap path;
- one racer-presentation graphics-prep path.

Dat be causal closure.

Not “some camera-ish code near some DMA-ish code.”

A chain.

Camera move.

Edge computed.

Column built.

Descriptor queued.

NMI send it.

VRAM change.

Now Widescreen work got plumbing diagram instead of folklore.

### PR #207: label dem jars

By now de repo got facts scattered across:

- course headers;
- track names;
- landmarks;
- SRAM progression;
- racer state;
- regional correspondence;
- deterministic fixtures;
- historical notes.

PR #207 consolidate dem into normalized queryable datasets an’ run a two-pass inference audit.

An’ here’s de pretty part:

Organizin’ de facts create new facts.

Results include:

- corrected canonical RNC stream/name/tour order;
- `dessyreqt_track_id = stream_index - 1` across all 45 courses;
- historical start/finish landmarks attached across corpus;
- paired header coordinates strengthened into racer-spawn model;
- cross-course relationships become visible;
- progression/course-resource/fixture catalogs normalized;
- state schema enriched with regional an’ historical semantics.

Plain bayou translation:

Project stop keepin’ every ingredient in a separate paper sack.

Put ’em in jars.

Label de jars.

Then suddenly recipes start showin’ up.

PRs #208 an’ #209 update canonical plans so future agents use dat query layer instead of crawlin’ through twenty markdown files with a lantern.

### Quiet-repo cleanup turn into a proper craft

PRs around #193–#201 mostly rescue useful completed work from stale or orphan branches.

Pattern become:

- identify what genuinely unique;
- replay onto current main;
- leave stale history behind;
- supersede redundant PRs;
- merge evidence, not confusion.

Dis be mundane.

Also essential.

A repo fulla parallel agents can produce useful work faster than branch history can stay civilized.

Without cleanup, pretty soon every line got three cousins an’ nobody remember who own de boat.

---

## What dis first sprint teach

By end of October 2, UR-Recomp don’t look like “somebody makin’ a Uniracers remake” no more.

It look like a reverse-engineerin’ platform what happen to have *Uniracers* sittin’ in de middle.

Project now got:

- deterministic frontend an’ race fixtures;
- event-relative native/reference comparison;
- confirmed movement an’ jump semantics;
- game-authored SRAM round-trip acceptance;
- large comparative structural map;
- reconciled historical bot/RAM semantics;
- presentation-complete course model;
- exact racer asset round trips;
- camera-to-VRAM scrolling chain;
- activation-vs-visibility contract;
- Widescreen diagnostics strong enough to separate cadence from simulation;
- real two-pixel host renderer bug narrowed down tight;
- normalized data capable of inference;
- semantic-sufficiency model for knowin’ when to stop diggin’.

An’ de questions get better too.

Project no longer ask:

> Can dis game be understood deep enough?

Now it ask:

- Why dem two pixels at x=255 compose different?
- How we get a real medal-changing fixture?
- Which multiplayer differences actually matter?
- How we show more world without wakin’ up more gameplay?
- Which consolidated dataset can answer de next question cheaper than another trace?

Dat be fine questions.

Fine questions mean de swamp mapped.

Ain’t drained.

Wouldn’t wanna drain it anyhow.

Dat where all de interestin’ critters live.

---

## 2026-10-02, late — De modernization layers quit bein’ sketches an’ start bein’ product

Earlier October 2 work had Widescreen boiled down to causal seams an’ Racer HD boiled down to exact semantic assets. Rest of de day, dem seams start turnin’ into real product code. Dis where UR-Recomp start lookin’ less like an excavation camp gettin’ ready to build a remake, an’ more like a remake architecture already provin’ some of its hardest ownership rules.

### Progression save/load finally close proper

Dat progression hole left open by PR #191 finally shut.

PR #213 use a period-correct Snes9x 1.51 rerecordin’ path plus de verified historical 100% movie to get a real game-authored medal mutation. No pokin’ SRAM. No makin’ up de save we hoped de game would write.

Acceptance watch de real medal matrix, wait for legal checksum-valid game state, catch de mutation, reload dat SRAM in a fresh current reference process, then check medal, tier an’ checksum behavior against de machine-readable progression model.

So persistence claim got de form we actually needed now:

Not just “8 KiB SRAM can go out an’ come back.”

Real progression authored by de game can survive save/load an’ still obey de recovered rules.

### Racer graphics go from extraction table to replacement machine

Racer lane close a whole stack of layers fast.

PRs #210, #212, #215 an’ #216 tighten up how presentation records, packed cells, DMA source words, staging consumers an’ stable OAM presentation fit together. PR #218 turn dat into deterministic transparent raster extraction. PR #224 close primary/companion composition strong enough dat exact composed racer images come straight outta canonical ROM evidence instead of somebody eyeballin’ screenshots.

PR #220 also make de graphics product choice explicit. Three first-class representation families now sit on de same semantic identity:

- Original SNES art;
- faithful high-resolution Remastered art;
- more freely modernized Reimagined art.

Key rule ain’t “pick one art style forever.”

Key rule be all three share semantic frame identity, placement contract an’ gameplay authority. Change de paint. Don’t invent another engine under it.

PRs #230, #236, #238, #239, #240 an’ #241 build de runtime side. Replacement selector read authoritative WRAM but don’t write it. Live position, orientation an’ object size come separate from de PPU/OAM path. Native host can recognize one exact composition an’ fail closed on anything unknown or mismatched.

Then PR #249 cross de line we been walkin’ toward: native host actually remove one validated stock racer from de *presented* raster an’ draw a deterministic high-density replacement in its place.

WRAM untouched.

VRAM untouched.

OAM untouched.

CGRAM untouched.

Dat replacement belong to de host picture, not de guest machine.

After dat, one frame ain’t enough.

PR #252 add explicit stock-derived pivot an’ contact anchors. PR #256 add synchronized P2 semantic coverage. PR #259 recover de split-screen placement model an’ prove both racers appear in both viewports, four host-side instances total. PRs #261, #263, #264 an’ #266 add another synchronized state, temporal-coherence checks, dense semantic animation trace, an’ exact registry-aware neighborhoods.

Dat dense trace change how we choose coverage.

No more pickin’ a pretty checkpoint just ’cause it easy.

Start registerin’ what de animation actually visit.

PR #268 add de first repeated adjacent state. PR #271 kill de old assumption dat one semantic ID always mean one visual registration, makin’ lookup composition-aware. Then come duplicate-context, predecessor an’ forward states, followed by more backward adjacency. By PRs #281/#282, #285 an’ #286, same-primary/different-companion states get measured against canonical ROM geometry before dey earn a registration. If two contexts look geometrically identical, dey can still stay distinct identities if de synchronized composition say dey distinct.

Screen area still small.

Architecture ain’t.

Racer HD now a live, fail-closed, composition-aware replacement pipeline with deterministic geometry, split-screen placement, temporal evidence an’ coverage growin’ from real adjacency.

### Widescreen move from diagnosis into native materialization

+8 work cross its line too.

PR #217 finish classifying dat earlier presentation-sequence divergence. Wider run sample a different presentation/frontend phase class at de same semantic event, while meaningful race state still line up event-relative.

PR #219 show stock preparation already got a useful neighboring strip schedule. PR #226 map de generation seam needed so de result survive SNESRecomp regeneration.

PR #228 turn accepted +8 experiment into a real native hook.

Stock 4:3 stay untouched control.

Hook reuse de stock preparation/helper path instead of growin’ a second guest renderer off de side.

At +16, next wall show itself.

PR #257 establish de ownership split: first extra column can ride de accepted guest +8 lane. Further presentation capacity belong to de host. Accepted +16 proof get a second host-owned column matched against later stock evidence while camera, collision, activation, progression an’ simulation stay put. Attempts to fake dat second column by recursively replayin’ guest preparation get saved as negative evidence instead of buried.

PR #280 then rescue de actual course-backed +16 materializer from superseded branches an’ reconcile its liveness evidence onto current main.

Dat be a real architecture change.

Further widening ain’t supposed to depend on peekin’ at future stock frames forever. Host can derive what it need from de recovered live course presentation model.

So de Widescreen question move again.

Ain’t “can eight extra pixels survive?”

Ain’t even “can sixteen?”

Now it “how far can dis host-owned materializer generalize cleanly?” +24 be de next bounded discriminator. Real 16:9 still farther down de bayou.

### Restart Race become a real modern product feature

Modern-product lane grow teeth just as fast.

PRs #229 an’ #231 establish host-owned product state an’ pause/restart session contract. PR #232 bind Pause to de existing host frame gate. PRs #234, #235 an’ #237 establish exact race restart anchor, prove deterministic rollback/replay, an’ make lifecycle safe across results.

PR #248 route Restart Race through de actual modern product command stack instead of a test-only rollback shortcut.

PR #253 close de dangerous persistence edge: Retry restore de race attempt while preservin’ de *current* 8 KiB SRAM. So hit Retry after results an’ it cannot quietly rewind legitimate progression.

Then de feature get hands an’ buttons.

PR #258 add keyboard bindings without synthesizin’ guest controller bits. PR #262 draw de first host-owned Pause/Retry overlay. Controller navigation follow. PRs #267 an’ #269 prove gamepad-menu an’ keyboard-hotkey paths end up at de same semantic command policy. PR #273 promote de accepted stack into de ordinary production native host instead of leavin’ it trapped in an acceptance harness.

PR #284 add de first ordinary setting on top: pause on focus loss.

Typed.

Host-owned.

Uses de same pause gate.

Authentic mode ignore it.

Never steal racer or save-slot memory to hold product configuration.

Dis be de first genuinely modern UX surface in de project, an’ it keep de old rule intact: guest simulation an’ progression got authority; modern convenience belong to de host.

### Inference audit catch up with all dis movin’

PR #242 recover an evidence-tracked scene policy for Widescreen instead of lettin’ scene assumptions float around in people’s heads.

PR #243 run a third inference audit across fresh progression, racer-native, Widescreen an’ restart evidence.

PR #245 reconcile de plans after runtime closures while preservin’ de audit’s old negative findings an’ addin’ current dispositions on top.

Dat matter.

When later work solve a problem, project don’t rewrite history pretendin’ de problem never existed.

Old observation stay.

New answer get stacked above it.

### Platform an’ display policy finally get names

Late in de day we answer a question dat somehow stayed fuzzy while reverse-engineerin’ half de machine:

What boxes dis thing actually supposed to run on?

PR #287 make Windows x64 de primary consumer/reference target. Also record personal-use targets for macOS, best-effort High Sierra-compatible legacy Mac, Web, Switch homebrew an’ PlayStation 5.

Switch lane stick to public homebrew tooling an’ preserved public examples. No proprietary SDK stash. No keys. No platform secrets. An’ none of dem platforms get their own simulation fork.

PR #288 split output resolution, internal render scale an’ presentation refresh/FPS away from authoritative game cadence. High-refresh host can repeat or interpolate pictures if needed. It don’t get to make de SNES-derived simulation run faster just ’cause de monitor got ambition.

PR #291 settle de bigger display-geometry policy.

Authentic 4:3, literal raw square pixels, an’ Remastered/Reimagined output be separate presentation transforms.

Pixel aspect, overscan, logical view width, filtering, graphics representation, output resolution an’ presentation cadence all stay separate axes.

Widescreen margin come from logical display policy, not one magic hard-coded source width.

Dat should save us from a classic remaster stew where one renderer checkbox secretly decide five unrelated things.

### Late-day state

By end of local October 2, a pile of stuff what used to be architecture sketches be real:

- game-authored progression save/load acceptance closed;
- +8 Widescreen be a regeneration-safe native hook;
- +16 got host-owned, course-backed materialization;
- Racer HD performed real native draw-frame substitution an’ grew into composition-aware, split-screen, adjacency-driven coverage;
- Pause, Resume an’ Retry live in de production native host with keyboard/controller UI paths an’ SRAM-safe lifecycle;
- first host-owned gameplay-adjacent setting be live;
- platform targets, resolution/FPS policy an’ display geometry be explicit product contracts.

Center of gravity move again.

Still excavatin’, sure.

But more an’ more, every shovel go in de dirt because some bounded implementation question ask for it.

Project now provin’ modernization can wrap around de original game without quietly stealin’ authority from it.

---

## Bayou engineering rules

A few lessons deserve paintin’ right on de side of de pirogue.

### Negative result still feed somebody

Short B pulse ain’t jump?

Good.

Now you know.

X press ain’t change sampled stunt state?

Good.

Problem narrower.

Medal chord ain’t mutate SRAM?

Good.

Quit wastin’ bait on dat hole.

Compact update list stay zero?

Good.

Wrong transport.

Layer mask change cadence?

Excellent.

Instrument dirty.

Proper experiment either confirm somethin’ or kill somethin’.

Both progress.

### Don’t go worshippin’ every byte just ’cause it changed

Some bytes gameplay.

Some clocks.

Some stack leftovers.

Some machine scratchin’ itself.

First ask what dat byte mean.

Second ask whether it mean anything at all.

Exact equality where exact bytes be de contract.

Semantic/event-relative equality where game behavior be de contract.

Don’t chase every swamp bubble thinkin’ it a catfish.

### Instrument can scare de wildlife

Trace hooks, layer masks, debug servers, alternate render modes?

All can perturb timing.

Always ask what de measuring tool itself change.

Sometimes best probe be de one what barely touch nothin’.

### Stop diggin’ when you got enough for de next bridge

Comparative structural work powerful.

Could go forever.

Semantic sufficiency put a gate on it:

- can observe?
- can explain?
- can modify safely?
- can validate?

If yes, maybe build de bridge.

Count tree rings later.

### Old notes be leads, not gospel

Historical bot authors know plenty.

Dey also work with old emulators, incomplete models, shortcuts, an’ practical hacks.

Use old work to aim experiments.

Don’t confuse “somebody wrote dis in 2014” with “de hardware swore to it in court.”

### Organizin’ data can make new knowledge fall out

Once course order, SRAM rows, header fields, landmarks an’ fixtures line up in compatible structures, relationships appear what prose been hidin’.

Sometimes de next reverse-engineerin’ tool ain’t another emulator.

Sometimes it a better table.

### Repo be de camp ledger

Chats where ideas happen.

PRs where claims get argued.

Generated data where machines testify.

Plans say what still open.

`prod_diary/` remember why anybody cared.

Dat division worth keepin’.

---

## Production status at 2026-10-02

At de start, biggest question be whether a compiled 1994 SNES ROM still got enough recoverable truth inside it to support a deeply faithful modern implementation.

After dis first sprint?

Look mighty encouraging.

Logic recoverable.

Data tractable.

Historical material rich.

Runtime instrumentable.

Agents can work in parallel without settin’ de dock completely on fire, long as lanes stay separate an’ evidence discipline stay strict.

Biggest question changed.

Now project gotta decide where exact reproduction stop an’ deliberate modernization begin.

An’ cher, dat be a much nicer alligator to wrestle.

Late-session work make dat conclusion stronger. Project now got working examples of de layered architecture we been aiming at: authoritative guest simulation underneath host-owned Widescreen materialization, semantic HD substitution, modern session controls an’ display policy. What remain look more an’ more like coverage, composition an’ productization work, not a fight to prove de separation can exist at all.
