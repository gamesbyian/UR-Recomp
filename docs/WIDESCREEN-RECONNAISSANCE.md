# Widescreen reconnaissance contract

Status: Phase F preparation authority. This document defines the research harness and evidence needed before permanent widening changes.

The goal is not to make a pretty wide screenshot quickly. The goal is to discover every place where stock Uniracers equates "outside the classic viewport" with "irrelevant."

## Evidence lookup rule

Before opening or extending a Widescreen investigation, query the normalized evidence surfaces first:

- `analysis/data/fixture-corpus.json` for the semantic/event-relative fixture and known cadence caveats;
- `analysis/data/course-corpus.json` and `course-resource-catalog.json` for world geometry, spawn/resource structure, and conserved course-resource facts;
- `analysis/data/state-schema.json` and `code-semantics.json` for promoted state/function relationships;
- `analysis/data/presentation-assets.json` for recovered presentation identities and frame-format constraints;
- `analysis/generated/inference-audit*.{json,md}` for existing invariants, negative results, and cheapest remaining falsifiers.

Use raw traces, prose notes, or fresh archaeology to answer questions the normalized surfaces do not already settle. If a new Widescreen result establishes a reusable cross-domain fact, feed it back into the appropriate normalized dataset or inference report so the next experiment begins from the new state of knowledge.

## Dependency rule

Do not begin permanent widening until the authentic 4:3 deterministic route is trustworthy enough to detect simulation drift.

Reconnaissance should begin earlier once the renderer-facing state is understood well enough to classify failures. Diagnostic runs may use disposable/non-shipping runtime modifications to expose +8/+16/+24 source-pixel margins, provided every experiment retains an untouched matched 4:3 control and no diagnostic patch is promoted into the shipping path without domain-specific justification and regression coverage.

Use early probes to select reverse-engineering work: stop at the first interpretable failure, identify which horizontal domain owns it, recover only enough additional semantics to explain or safely change that domain, then rerun. Do not require a complete renderer decompilation before the first probe.

## Shared fixture input

Reuse the existing deterministic input grammar already consumed by native/SNES reference tooling.

Do not create a widescreen-specific replay language.

A probe run should identify:

- fixture/script;
- game mode;
- course/scene;
- checkpoint/frame range;
- renderer/runtime revision;
- requested exposure margin or aspect;
- layer/sprite/window policy;
- pixel-aspect and overscan policy.

## Horizontal-domain model

Keep five concepts separate:

| Domain | Question |
| --- | --- |
| simulation / activation | When does the game object exist or become behaviorally active? |
| preparation / streaming | When must presentation data be ready? |
| render / culling | When may an existing object/layer be emitted? |
| camera / composition | What world region is intentionally framed? |
| UI composition | Where do fixed-screen elements belong? |

A widescreen fix should name the domain it changes.

"Increase viewport width" is not sufficient justification for changing simulation/activation.

### Proven representative activation boundary

The deterministic Dragster checkpoint/finish tail provides the first concrete
cross-domain constraint. Its checkpoint/finish resource graphics and
`7E:C000[6..14]` behavior cells are already present before active racing.
Actual finish/checker pixels first enter the framebuffer at guest frame **2789**,
while the checkpoint/finish behavior transition occurs at guest frame **2903**
when collision/contact-derived C000 index 8 selects code `0x14`.

The `$0DCD/$0DCF` camera-filtered update lists are not the gameplay activation
gate. A widened view may expose the finish presentation earlier, but it must not
cause the collision/contact object dispatcher to trigger earlier. Treat this as
a regression invariant for the first +8/+16/+24 probes.

Evidence: `analysis/generated/object-activation-runtime-boundary-2026-10-02.md`.

## Staged exposure sweep

Use the smallest margins first. During early reconnaissance, +8/+16/+24 are the preferred discriminators because they minimize the number of simultaneously violated assumptions. Expand to larger margins only after the earlier failure class is understood.

Initial source-pixel margins:

```
0, 8, 16, 24, 32, 48, 64
```

The harness may add intermediate margins around a detected failure boundary.

For each margin, preserve the matched 4:3 control and capture enough state to classify the first failure.

### Artifact classes

At minimum:

- `bg-stale` — unprepared/stale background data;
- `bg-wrap` — unintended map/tile wrap;
- `world-end` — authored geometry/background ends before viewport;
- `sprite-cull` — sprite disappears at a classic-width boundary;
- `sprite-wrap` — signed/unsigned or coordinate wrap artifact;
- `hidden-object` — object previously staged offscreen becomes visible unexpectedly;
- `late-prepare` — correct object exists but graphics arrive visibly late;
- `window-boundary` — window/color-math/scanline mask ends at classic geometry;
- `offstage-art` — unfinished or placeholder art becomes visible;
- `script-reveal` — cutscene/transition/reveal staging leaks;
- `ui-policy` — fixed-screen layer expands or anchors incorrectly;
- `unknown` — preserved for investigation rather than forced classification.

## Machine-readable output

`tools/widescreen_probe.py` now owns the dependency-free report contract. It reads `analysis/widescreen-policy.yml`, can emit a complete default margin-sweep skeleton, and validates completed reports before evidence is promoted. It is deliberately read-only: emulator/runtime invocation remains a separate concern.

Target report shape:

```json
{
  "schema_version": 1,
  "fixture": "tests/input/...",
  "scene": "one-player-race",
  "aspect_policy": "16:9-par",
  "runs": [
    {
      "margin": 32,
      "first_failure_frame": 1234,
      "class": "sprite-cull",
      "surface": "obj",
      "evidence": ["capture.png", "state.json"]
    }
  ]
}
```

Exact filenames may evolve, but the report must preserve enough provenance to reproduce the observation. The implemented validator additionally requires runtime revision plus checkpoint-range, pixel-aspect, overscan, and layer/sprite/window policy provenance, and requires every default margin including the margin-0 matched 4:3 control. Intermediate margins are allowed for failure-boundary refinement.

Do not commit a giant screenshot corpus by default. Keep compact manifests/results plus selected explanatory captures; use workflow artifacts for bulky transient matrices where appropriate.

## bsnes-hd diagnostic presets

Once deterministic invocation is proven, own a small preset matrix covering:

- stock/raw 4:3;
- widened BG-only;
- each BG layer independently widened;
- sprite `clip`;
- sprite `safe`;
- sprite `unsafe`;
- sprites disabled for layer archaeology;
- default windows;
- window-ignore diagnostic;
- pixel-aspect correction on/off;
- overscan policy variants;
- visible widescreen edge marker.

These are diagnostic presets, not shipping settings.

Record exact bsnes-hd revision and every non-default parameter in each result.

## Aspect policy

16:9 is the first supported widened target, not the engine's internal definition of widescreen.

Represent aspect using viewport bounds/policy rather than magic source widths.

A policy must state:

- target display aspect;
- source pixel-aspect assumption;
- overscan/safe-area behavior;
- derived left/right logical margin;
- any maximum supported margin imposed by the stock renderer.

Preserve named compatibility presets only when they are useful for reproducing prior art or known hardware/display interpretations.

## Scene policy

Initial classes:

- `world-expand`;
- `fixed-4:3`;
- `fixed-center`;
- `edge-anchored-ui`;
- `mixed`;
- `special-scripted`.

Scene policy should be data-driven where practical so title/front-end/cutscene exceptions do not become scattered host-renderer conditionals.

## Information-exposure measurement

For selected hazards/opponents/events record, if recoverable:

```
first_simulated
first_active
first_prepared
first_drawn
first_visible
```

Compare matched 4:3 and 16:9 runs.

Expected default:

- `first_simulated`: unchanged;
- `first_active`: unchanged;
- `first_prepared`: may move earlier if presentation streaming needs slack;
- `first_drawn`: may move earlier;
- `first_visible`: moves earlier by design.

Any simulation/activation change needs an explicit causal justification and independent regression coverage.

## Split-screen matrix

Widescreen reconnaissance is incomplete without:

- one-player;
- two-player;
- Vs.;
- player-1 viewport;
- player-2 viewport;
- authentic sprite-ripping path;
- 4:3 fallback comparison.

The purpose is to determine whether stock-PPU widening remains viable for final split-screen presentation or whether host composition should eventually draw the two logical viewport sprite sets directly.


## Reverse-engineering admission rule

A widescreen failure should create a new semantic-recovery task only when the missing knowledge prevents classification or a safe fix. Prefer the smallest causal chain that answers the failure over broad neighboring-ROM excavation.

For each failure-driven investigation record:

- the first failing margin/frame;
- the observed artifact class;
- the horizontal domain believed to own it;
- the state/routine/resource whose behavior remains unknown;
- the smallest next discriminator;
- the condition under which the investigation stops and the probe is rerun.

Representative checkpoint/finish activation is mechanically separated from presentation and is no longer the default blocker. The representative stock preparation/streaming chain is also mechanically closed: camera demand builds `$03xx` VRAM-strip descriptors and NMI consumes them the same guest frame. The current highest-value unresolved domain is the +8 presentation-state phase seam. Use semantic/event-relative anchors to decide whether a failure belongs to presentation-ID selection, VRAM preparation/content, render/culling, final composition, or UI. Reopen gameplay activation only if a widened probe or a different object family actually changes authoritative simulation.

## Exit condition

Phase F0 is complete when a representative race plus split-screen/Vs. fixture set has:

- reproducible aspect/preset definitions;
- staged margin results;
- classified first failures;
- explicit scene policies;
- horizontal-domain ownership for proposed fixes;
- no unexplained simulation divergence.

Only then should permanent widening hooks graduate from experiments into the shipping path.


## First tiny-margin probe result

The first retained native-host probe ran matched 0 / +8 / +16 / +24
pixel-per-side presentation margins on the deterministic Dragster tail. The
retained workflow artifact from run `36957020940` contains the per-margin
state and framebuffer evidence.

The apparent +8 authoritative-state failure is now classified as a
**host-presentation cadence perturbation plus transient-contact harness false positive**.
This is category 3 from the investigation taxonomy: widening perturbs absolute guest
execution cadence without changing meaningful simulation in the retained race:

- the timing shift is already present at the first frontend milestone: the +8
  run reaches `$009F` readiness at guest frame **443** versus **446** in the 4:3
  control, before the race or widened finish presentation can be causal;
- every retained +8 race-tail script tag remains exactly **3 guest frames earlier**
  than its 4:3 control tag;
- racer position, racer velocity, camera X and checkpoint/finish/lap state are
  identical at every event-relative retained tag;
- the checkpoint/finish progression transition occurs at the same scripted
  event, `object-tail-174`;
- only the diagnostic contact word `$0E95` differs, at
  `object-tail-176/177/178/180`, and it reconverges by the final retained
  sample without changing trajectory or progression;
- whole-WRAM inequality begins earlier in host/global-phase bookkeeping and is
  therefore not a valid equality gate for this presentation experiment.

The probe analyzer now separates durable event-relative race state from the
transient contact diagnostic, reports the absolute guest-frame cadence delta,
and emits its report before applying the CI gate. +8 is considered a valid
matched simulation comparison only when durable trajectory/progression agrees
and the cadence offset is stable; transient contact differences remain visible
in the report rather than being discarded.

The earliest causal divergence is therefore host/frontend cadence, not Dragster
simulation or finish preparation. This closes the +8 simulation-divergence blocker. The next +8 work should
classify the first **presentation** failure or success boundary. Do not widen
beyond the already-captured tiny-margin experiment merely because the harness
gate is repaired, and do not widen gameplay activation bounds.


## +8 first presentation boundary

Follow-up run `36964990868` closes the first true +8 presentation-failure
ownership question without changing guest code or promoting a shipping
Widescreen hook.

Event-relative 0/+8 comparison gives the following boundary:

- the authentic center 256 is pixel-identical through `object-tail-167`;
- `object-tail-168` is the first center regression, only **2 pixels**, both at
  classic x=255;
- guest OAM is byte-identical at that onset and remains identical through
  `object-tail-171`;
- background-only rendering remains matched throughout the sampled window;
- OBJ-only rendering is still matched at `object-tail-168` and first diverges
  at `object-tail-169`;
- the first OAM difference does not appear until `object-tail-172`, where one
  slot differs by one Y pixel, so it cannot cause the earlier failure;
- disabling the SNES 34-sliver sprite limit does not move the first center
  divergence;
- suppressing the host policy that expands 0/255-pinned hardware windows into
  the widened margins also does not move the first center divergence.

Therefore the first +8 failure belongs to the **host renderer**, not simulation,
object activation, course preparation, or the compact preparation/emission
lists. At `object-tail-168`, individually matching BG and OBJ surfaces compose
differently at the classic right edge. One event later, widened OBJ rasterization
also diverges despite still-identical guest OAM.

The product invariant is now sharper: widening may reveal additional pixels
outside the classic viewport, but it must not change the authentic 256-column
center when supplied the same event-relative guest presentation state. Future
renderer work should preserve that center before expanding margins. This result
does not require or justify widening gameplay activation or reopening course
format archaeology.


## Representative camera-strip preparation closure

The reconciled preparation/emission work closes the authentic Dragster scrolling path:

1. `81:A52F` updates camera state from `$04F5/$04F9`;
2. its camera/window logic derives entering-edge coordinates and split counts;
3. `81:A59A -> 81:AB88/ACB1` builds up to eight descriptors in the `$0399..$03E7` family;
4. NMI `80:87E1 -> 82:D197/D19B..D2D0` clears ready flags, programs `$2116/$4302/$4305/$2115`, and triggers DMA through `$420B` to `$2118`.

Run `36966728136` records 681 non-empty build events, 676 non-empty NMI-consume observations and 680 paired build→consume events. Under steady rightward motion, an entering 16-word / 32-byte column is prepared from the settled current-frame camera edge and consumed in that same guest frame. Horizontal destinations form a 32-column VRAM ring and wrap `$0D9F -> $0D80`.

This means the representative stock renderer has **no multi-frame background-prefetch horizon to preserve**. Widescreen preparation work should operate against the known descriptor queue by deliberately scheduling additional/earlier entering strips, after the current presentation-phase divergence is classified. Do not reopen the zero-valued `$0DCD/$0DCF` lists as the primary scrolling transport for this scene.

Evidence: `analysis/generated/camera-dma-preparation-causal-contract-2026-10-02.md`.

## +8 adjacent future-column scheduling acceptance

Run `37066327707` closes the first implementation-facing widened-preparation admission test on the deterministic Dragster fixture.

The accepted diagnostic path deliberately reuses the stock `81:A59E` preparation helper to produce one additional horizontal column, preserves that second staged 32-byte payload in the secondary low-WRAM lane, and lets the existing `81:AB88` descriptor builder plus NMI consumer emit it through slot 3. The stock 4:3 path remains the matched control.

Retained acceptance results:

- **314** future-stock candidates were identified by exact descriptor/payload identity against later stock execution;
- **309** candidates have the expected adjacent horizontal VRAM-column geometry, are consumed by NMI in the same guest frame, and match the exact post-NMI VRAM bytes;
- the longest consecutive accepted interval is **14 frames**;
- camera and protected gameplay state are equal throughout the 932-frame preparation comparison;
- the independent object-liveness guardrail compares **61** common samples with **zero** protected differences;
- control and widened runs first change checkpoint/finish/lap progress at the same semantic sample, `liveness-004`, guest frame **1225**;
- therefore the widened preparation path does **not** activate gameplay earlier.

Two negative discriminators remain useful:

- widening `$052B` from 16 to 32 merely lengthens the existing VMAIN=`$81` vertical transfer and does not supply the adjacent future column;
- simply biasing camera WRAM is invalid because it perturbs or lags authoritative camera state.

The proven +8 seam is consequently **presentation preparation**, not simulation, activation, collision, or final composition. The disposable reference-emulator double-pass remains the causal proof source; it is no longer the implementation target.

Evidence: workflow run `37066327707`; retained artifact `widescreen-strip-scheduling-plus8-acceptance`.

## Native +8 preparation-hook closure and +16/+24 stop

Workflow run `37081391730` closes the smallest regeneration-safe native form of the accepted +8 mechanism. Rather than seeding the isolated preparation helper as a dead AOT island, generation starts from the trusted live race-frame orchestrator at `83:CBCC`; static caller validation confirms executable `83:CD55 -> 81:A52B`, followed by the stock short-call entry `81:A52B -> 81:A52F`. The generated live closure therefore owns the ordinary `81:A597/A59A/A59D/A59E` preparation seam without a parallel renderer protocol.

With `URRECOMP_WS_MARGIN=0`, the hook is inert. At +8 it snapshots CPU plus low WRAM, reuses the generated stock `A59E` helper for a second presentation-only pass, redirects that pass's staging initializer from `$0433` to `$0453`, preserves only the adjacent strip plus the secondary horizontal edge/count lane for `AB88`, and restores the secondary edge/count after descriptor construction. The staged `$0453` payload remains live through the intervening NMI and is restored at the next live `A59A` preparation boundary before another strip is staged; the bounded fixture ends after one final PREP event, so one terminal payload is intentionally pending at process exit.

Retained native acceptance on the deterministic preparation fixture records:

- **678** stock primary reference events;
- **617** +8 preparation events and **616** next-boundary cleanups, with the sole unmatched cleanup explained by fixture termination immediately after the final PREP;
- **74** unique prepared edge values;
- at least **317** exact later-stock payload matches, exceeding the retained PR #219 proof window of 309;
- a longest consecutive exact-match run of **25**, exceeding the retained 14-frame proof window;
- protected gameplay, camera and progression state equal to the margin-0 control;
- all **617/617** same-camera primary→prepared steps advance exactly one position in the low-five-bit 32-column VRAM-ring coordinate. Their full-word transition shapes are **589× `+1`**, **17× `-31`**, and **11× `+33`**, all observed in stock control transitions; the upper bits therefore carry compound resource/segment state rather than changing ring adjacency.

The +16 and +24 probes deliberately do not mutate presentation state. They stop at the first concrete generalization constraint: the stock horizontal preparation surface has one primary lane plus one spare secondary lane. +8 consumes that one spare lane; +16 would require two simultaneous extra columns and +24 three. The native hook therefore **does not** invent extra guest descriptor lanes or special-case additional columns.

This closes the current implementation-facing +8 task and the bounded +16/+24 generalization question. Any wider stock-art design must introduce a larger presentation-capacity seam deliberately, while preserving the now-proven stock 4:3 control and the presentation-only ownership boundary.

Evidence: final native workflow run `37081391730`; PR #228.


## +16 host-capacity replay stop

PR #247 tested whether the accepted one-column guest preparation machinery could
also serve as a host-owned source for the second +16 future column without
inventing guest `$03xx` lanes. Two bounded mechanisms were rejected.

Run `37083769287` repeated stock `A59E` inside the accepted snapshot replay.
The real first future column remained healthy (617 events, 317 exact later-stock
matches, longest exact run 25), but the second host-shadow call produced only
557 candidates, failed structurally on 60 events, and only **31** candidates
matched exact later-stock content. Its longest exact run was 22.

Run `37084288683` moved the experiment to the complete stock preparation
boundary: it cloned CPU plus low WRAM at `81:A52F` entry, applied +16 only to
the clone's camera X, ran the complete stock preparation routine on the
disposable state, harvested the resulting shadow strip, and restored the real
state. The accepted first future column again remained healthy, but the cloned
query produced only 314 second-column candidates and **zero** exact later-stock
matches.

Both experiments kept the sampled protected gameplay/camera/progression state
equal, and neither manufactured an additional guest descriptor lane. Because
the +16 preparation gate failed, the downstream liveness gate was not used to
promote either mechanism.

The architectural stop is therefore explicit: do not treat recursive `A59E`
or a camera-biased replay of `A52F` as a random-access future-column API.
The accepted +8 hook remains unchanged. Wider presentation still belongs in
host/native capacity, but the second and later columns need a semantic
presentation source that can address future world/resource columns directly.

The next controlled prototype on the rebased PR uses an independent later-stock
oracle only to prove that host-owned column +2 capacity can satisfy the exact
adjacency/content/lifecycle contract. That oracle is test scaffolding, not the
production content source. If accepted, the production follow-up is a bounded
host-side strip materializer backed by the recovered course/resource
presentation model.

Evidence:
`analysis/generated/widescreen-plus16-capacity-negative-2026-10-02.{json,md}`.


## +8 presentation-sequence divergence closure

PR #206 first established the event-relative boundary: meaningful P2 race state remains equal, P2 racer presentation first diverges at **`object-tail-141`**, VRAM first diverges at **`object-tail-142`**, and OAM remains equal through the retained early gap. The follow-up sequence discriminator closes why.

Through `object-tail-140`, P2 sequence selector `$136B`, sequence cursor `$11DD`, sequence identity `$11E1`, initialized flag `$11E5`, persistent override `$0DEB`, and working override `$0F4F` all match. At `object-tail-141`, control initializes sequence **1** while +8 initializes sequence **3**. Both use cursor **1** and initialized flag **1**, so this is different sequence selection rather than the same sequence advancing at a different rate.

The hidden writer is `83:EB57 -> 82:8952/8956 -> STA $0DE9,Y`; for P2, `Y=2`, so the indexed store targets `$0DEB`. The selector is derived from six-state presentation/frontend counter `$7710B1`: `83:EB3F..EB51` maps raw classes `0/1 -> sequence 1`, `2/3 -> sequence 3`, and `4/5 -> sequence 5`. The counter is clamped/reset by `83:C8EF..C8FB` and advanced modulo six by `83:C9E2..C9F2`. The already-proven stable host/frontend cadence offset therefore places control and +8 in different presentation-counter phase classes at the same semantic race event. The exact raw member within each two-value class is not needed to distinguish or explain the selected sequence.

The resulting chain is:

> Same authoritative P2 race state -> different `$7710B1` presentation/frontend phase class at `object-tail-141` -> P2 sequence 1 vs 3 -> `82:8956` emits `0x0A45` vs `0x0A8D` to indexed P2 `$0DEB` -> normal `$0F4F -> $0F97 -> $0FEB` presentation chain diverges at `141` -> `83:F0BB/F296/F2BB` resolves and stages different presentation data -> VRAM first diverges at `object-tail-142`.

The contemporaneous `$040F/$0F7B` and `$0C75..$0C7F` differences are downstream presentation/render staging, not earlier causes. The later `object-tail-168` two-pixel authentic-center regression likewise remains downstream.

This closes the first +8 presentation-state phase lane for the current Widescreen decision. Do not compensate by changing gameplay activation, collision, course semantics, or final x=255 composition policy. The subsequent earlier/additional `$03xx` strip-scheduling experiment is now accepted as described below.

The failed layer-mask and paused trace-host experiments remain useful negative instrumentation evidence: diagnostics that change event-relative cadence cannot decide this seam.

Evidence: `analysis/generated/widescreen-plus8-presentation-sequence-closure-2026-10-02.md` (clean full-renderer run `36978866214`).
