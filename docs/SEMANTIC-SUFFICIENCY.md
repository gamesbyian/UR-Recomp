# Semantic Sufficiency Scoreboard

Last updated: 2026-10-01

This is a product-facing readiness map, not a decompilation-completeness score. A subsystem is judged by whether the project can **observe** its authoritative state, **explain** the behavior needed by the product, **modify safely** at the correct ownership seam, and **validate** the result.

Status values are `sufficient`, `partial`, `unknown`, or `not applicable`. `Sufficient` means sufficient for the current product decision, not total reconstruction.

| Subsystem | Observe | Explain | Modify safely | Validate | Disposition |
| --- | --- | --- | --- | --- | --- |
| Racer simulation / core physics | sufficient | sufficient | not applicable for ordinary modernization | sufficient | Preserve; reopen only for a new event-relative discrepancy |
| Stunt / reward / in-race progression | sufficient | sufficient | partial | sufficient | On-demand for product statistics/UI needs |
| Camera / screen-relative projection | sufficient | sufficient | partial | sufficient | Complete renderer-facing integration, not generic mapping |
| Sprite/OAM + active-display split-screen seam | sufficient | sufficient | partial | sufficient | Hard authentic-mode and Widescreen constraint |
| Gameplay object activation / liveness | partial | partial | unknown | partial | **Highest-value unresolved Widescreen semantic** |
| World preparation / VRAM streaming | partial | partial | partial | partial | Recover horizon from camera demand to prepared graphics |
| Course spatial/resource model | sufficient at loader/runtime surfaces | partial | partial | partial | Build presentation-complete contract; defer editor-complete tail |
| Frontend / principal progression | sufficient | sufficient for principal stock flow | partial | partial | Close finite save/load/progression acceptance only |
| Original graphics / animation-state identity | partial | partial | unknown | partial | Parallel exact extraction/round-trip lane |
| Toolchain / deterministic execution apparatus | sufficient | sufficient | sufficient | sufficient | Maintenance only |

## Evidence basis

**Racer simulation:** deterministic 1P fixtures cover acceleration, jump, rotation, landing and collision/contact; ordinary 2P covers isolated P1, isolated P2 and simultaneous movement. MesenCE independently matches the promoted Snes9x semantic checkpoints. Race update, input normalization, player-state marshal, collision/contact, geometry, surface sampling, stunt finalization and checkpoint/timer paths are all bounded well enough to preserve and diagnose the simulation.

**Camera and OAM:** the 2P fixture causally separates camera ownership and exposes per-camera position/velocity, split-screen mode, screen-relative racer coordinates and offscreen sentinels. The camera-control island and `Race_BuildRacerOAMState` connect world coordinates through projection/culling into OAM-facing state. The authentic active-display `$2104` seam is reproduced at scanlines 0 and 112 and has independent emulator/historical corroboration.

**Object activation:** the runtime `7E:C000` behavior plane feeds the bank-81 object/collision dispatcher, and object code `0x14` reaches the confirmed checkpoint/finish handler. What remains unknown is the general boundary at which ordinary objects/hazards/opponents become behaviorally active versus merely present, prepared or drawable. The recovered camera-filtered VRAM update lists are presentation/preparation evidence and must not be treated as gameplay-activation evidence.

**Preparation / streaming:** course loading and the camera/window work expose real VRAM-update construction and `$2116/$2118` emission, but the project cannot yet predict a general preparation horizon for additional horizontal visibility.

**Course model:** all 45 RNC streams are independently decoded and CRC-validated. The active decoded payload, resource-list cursor, reusable resource descriptors, `A000/C000` materialization, sector-neighborhood gather, surface sampler and checkpoint/finish resource family are grounded. The missing piece for Widescreen is a neutral presentation-spatial contract, not a complete editor format.

**Progression:** principal 1P/VS/2P routes are deterministic. The medal matrix, medal values, derived unicycle tiers and checksum boundary are statically resolved and reconciled with recovered SRAM snapshots. The remaining acceptance gap is a real progression-changing save/load fixture, not generic SRAM archaeology.

**Graphics / animation:** deterministic framebuffer/OAM evidence and historical source-pipeline evidence exist, but there is not yet a project-owned semantic asset manifest that maps authoritative animation state to extracted sprite/tile identities with an exact unchanged reconstruction regression.

## Highest-value next discriminators

1. **Activation timeline:** use the cheapest deterministic fixture in which a known world object crosses the classic camera edge. Capture the first frames at which it exists, becomes behaviorally processed, enters preparation/update lists, is drawn, and becomes visible.
2. **Preparation horizon:** in the same fixture, correlate camera/window edges with first VRAM/update-list membership. Prove one resource family before generalizing.
3. **Presentation-complete course contract:** on one representative course, recover world extent, runtime resource/chunk placement, camera-visible resource ownership, and object/event placement well enough to predict what a wider viewport needs.
4. **Tiny-margin Widescreen probe:** once those boundaries are interpretable, expose +8/+16/+24 source pixels and let the first failure choose the next semantic task.
5. **Graphics round trip:** choose one small racer/presentation asset family, extract tiles/palette, reconstruct unchanged data exactly, and tie selected frame/tile identity to named runtime/OAM state.
6. **Save/load progression acceptance:** create one real progression-changing run, persist it, reload it, and assert medal/tier/checksum state.

## Promotion rules

Object activation becomes sufficient when at least one representative ordinary object has a proven activation timeline distinct from preparation/visibility and the owning state/code boundary is known.

Preparation/streaming becomes sufficient for the first Widescreen implementation when one representative scrolling scene can deliberately shift preparation earlier for a requested margin without changing authoritative simulation.

The course model becomes presentation-sufficient when one representative course can answer: world extent relevant to camera travel, resource/chunk spatial placement, which resources own a visible region, where object/event cells sit relative to that region, and how those claims are validated at runtime.

Graphics/animation identity becomes sufficient for Phase E expansion when one animated family has deterministic extraction, unchanged reconstruction, semantic state/frame identity, and a compact regression.

Update this scoreboard only when evidence changes what the project can safely decide or do. Do not upgrade a capability because census bytes, screenshots, or homolog counts increased without changing product leverage.