# Semantic propagation pass — finish/checkpoint objects and collision geometry — 2026-09-30

This pass propagates two already-supported anchors: the checkpoint/finish state machine at `81:8050` and Nitrodon's recovered bounce trace.

## 1. Runtime course-object dispatch now exposes a concrete object code

The object/collision dispatcher at `81:82E6` derives an index from `CurrentPlayerCollisionState` `$0F09`, reads a byte from the active runtime object map at `7E:C000,X`, masks bit 0, and dispatches through the 15-entry jump table at `81:8320`.

The dispatch arithmetic preserves the object's even code as the byte offset into the jump table. The table entry at offset `0x14` is `81:8050`, the already-confirmed checkpoint/finish handler.

Therefore:

- runtime object code **`0x14`** selects the checkpoint/finish behavior;
- `7E:C000` is not merely opaque collision scratch: at least part of it is a materialized per-cell/object behavior map;
- the active course representation can now be searched for `0x14` cells and correlated against known checkpoint/finish locations.

### Handler semantics

`81:8050` does more than a generic checkpoint tick:

- it gates against per-player finish state `119D/119F`;
- snapshots race time;
- decrements `0EF1/0EF3` laps remaining;
- advances `1199/119B` next-checkpoint state;
- branches into lap/final-finish handling;
- emits message ID `0x0F` on one lap-state transition when enabled.

This supports naming code `0x14` as **checkpoint/finish course object** rather than a generic trigger.

### Consequences

1. Course-format work now has one concrete runtime behavior code tied to a visible gameplay feature.
2. A cheap next discriminator is to locate `0x14` in the materialized Dragster `7E:C000` region and compare its spatial positions against known finish/checkpoint coordinates.
3. If corresponding bytes can be traced back into the decoded RNC payload, this provides a direct bridge from packed course data → materialized object map → race-state mutation.
4. The remaining jump-table entries should only be decoded opportunistically when needed by hazards, boosts, arrows, collision or editor tooling.

## 2. Bounce trace is more informative as collision-shape construction than as isolated coefficient evidence

The recovered bounce trace enters `81:9E2A` with current-player state already marshalled.

The traced path:

1. scales `$0F7B` by 8 and uses it to read four words from bank `21` beginning at `21:99A8` in this sample;
2. takes the high byte of the fourth word as a selector;
3. uses that selector to choose a 16-byte row from table `20:BC9F`;
4. adds the table's alternating byte offsets to the two base bytes from the third loaded word;
5. produces eight coordinate pairs in DP scratch `$00..$13`;
6. mirrors those coordinates when facing is reversed;
7. offsets the resulting points by 8 and stores at least the first world-space point into per-player `$125B+` storage.

This strongly supports `81:9E2A` as collision/contact-shape construction from a compact base record plus orientation/template offsets.

Separately, `81:9546..961B` consumes four matrix-like elements loaded into `02C0/02C2/02C4/02C6`, multiplies them by current-player X/Y velocity, sums the cross-components, and writes the transformed velocity pair back to `0F9F/0FA1`.

### Consequences

1. The old note that the bounce trace merely contains mysterious “coefficient loads” undersells it. It contains both **collision-shape generation** and a later **2×2 velocity transform**.
2. The `20:BC9F` table is a high-value candidate for collision-shape templates or orientation-dependent vertex offsets, not a generic physics coefficient table.
3. `125B+` is part of derived per-player collision/contact geometry. Exact field boundaries remain open, so do not assign individual vertex names yet.
4. The four values feeding `02C0/02C2/02C4/02C6` form the actionable transform boundary for bounce response. Their upstream selector/source should be traced only when a collision fidelity defect or editor/physics implementation needs exact surface semantics.
5. The recovered trace is now a suitable deterministic fixture for validating collision-shape construction and the velocity transform, rather than only an archival curiosity.

## Stop rule

This pass closes the highest-value semantic fan-out available from the current static evidence. Next work should be driven by one of three concrete hinges:

- mapping runtime `0x14` object cells back into decoded course payloads;
- reproducing the recovered bounce path as a native/reference fixture;
- decoding another course-object code only when it blocks hazards, boosts, arrows, editor behavior, or fidelity.
