# Widescreen reconnaissance contract

Status: Phase F preparation authority. This document defines the research harness and evidence needed before permanent widening changes.

The goal is not to make a pretty wide screenshot quickly. The goal is to discover every place where stock Uniracers equates "outside the classic viewport" with "irrelevant."

## Dependency rule

Do not begin permanent widening until the authentic 4:3 deterministic route is trustworthy enough to detect simulation drift.

The probe may be developed earlier if it remains read-only/diagnostic and does not alter stock behavior.

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

## Staged exposure sweep

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

`tools/widescreen_probe.py` now owns the dependency-free report contract. It reads `analysis/widescreen-policy.yml`, can emit a complete default margin-sweep skeleton, and validates completed reports before evidence is promoted. It is deliberately read-only: emulator/runtime invocation remains a separate concern.\n\nTarget report shape:

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

## Exit condition

Phase F0 is complete when a representative race plus split-screen/Vs. fixture set has:

- reproducible aspect/preset definitions;
- staged margin results;
- classified first failures;
- explicit scene policies;
- horizontal-domain ownership for proposed fixes;
- no unexplained simulation divergence.

Only then should permanent widening hooks graduate from experiments into the shipping path.
