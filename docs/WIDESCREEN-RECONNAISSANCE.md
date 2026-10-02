# Widescreen reconnaissance contract

Status: Phase F preparation authority. This document defines the research harness and evidence needed before permanent widening changes.

The goal is not to make a pretty wide screenshot quickly. The goal is to discover every place where stock Uniracers equates "outside the classic viewport" with "irrelevant."

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

Representative checkpoint/finish activation is now mechanically separated from presentation and is no longer the default blocker. The highest-value unresolved domain is preparation/streaming and renderer-facing causal closure: use the first tiny-margin failure to decide whether the next work belongs to preparation, render/culling, camera/composition, or UI. Reopen gameplay activation only if a widened probe or a different object family actually changes authoritative simulation.

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
probe successfully produced full presented-frame captures at every margin, but
the +8 run failed the authoritative-state equality check against the 4:3
control.

Treat this as a blocking discriminator, not as a successful widening result.
The next Widescreen task must determine whether the divergence is caused by
host presentation cadence / fixture alignment or by a genuine simulation
dependency on the widened host path. Do not widen shipping presentation until
that distinction is closed. The retained workflow artifact from run
`36957020940` contains the per-margin state and framebuffer evidence.
