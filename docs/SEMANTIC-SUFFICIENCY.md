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
| Gameplay object activation / liveness | sufficient for representative checkpoint/finish family | sufficient | partial | sufficient | Preserve collision/contact activation independently of widened presentation; reopen on discrepant object family |
| World preparation / VRAM streaming | partial | partial | partial | partial | Recover horizon from camera demand to prepared graphics |
| Course spatial/resource model | sufficient | sufficient for representative presentation questions | partial | sufficient on representative contract + sampled family invariants | **Presentation-sufficient; four header shapes preserve the same two-level spatial/resource contract** |
| Frontend / principal progression | sufficient | sufficient for principal stock flow | partial | partial | Close finite save/load/progression acceptance only |
| Original graphics / animation-state identity | sufficient for first racer family | sufficient for first racer family | partial | sufficient for first racer family | Phase E family expansion is unblocked; extend exact mappings on demand |
| Toolchain / deterministic execution apparatus | sufficient | sufficient | sufficient | sufficient | Maintenance only |

## Evidence basis

**Racer simulation:** deterministic 1P fixtures cover acceleration, jump, rotation, landing and collision/contact; ordinary 2P covers isolated P1, isolated P2 and simultaneous movement. MesenCE independently matches the promoted Snes9x semantic checkpoints. Race update, input normalization, player-state marshal, collision/contact, geometry, surface sampling, stunt finalization and checkpoint/timer paths are all bounded well enough to preserve and diagnose the simulation.

**Camera and OAM:** the 2P fixture causally separates camera ownership and exposes per-camera position/velocity, split-screen mode, screen-relative racer coordinates and offscreen sentinels. The camera-control island and `Race_BuildRacerOAMState` connect world coordinates through projection/culling into OAM-facing state. The authentic active-display `$2104` seam is reproduced at scanlines 0 and 112 and has independent emulator/historical corroboration.

**Object activation:** the runtime `7E:C000` behavior plane feeds the bank-81 object/collision dispatcher, and object code `0x14` reaches the confirmed checkpoint/finish handler. The deterministic Dragster tail proves the representative family is materially present before the race, becomes framebuffer-visible at guest frame 2789, and does not trigger its checkpoint/finish behavior transition until guest frame 2903, when collision/contact-derived C000 index 8 selects code `0x14`. Camera position and the `$0DCD/$0DCF` presentation-update lists do not participate in that activation decision. This is sufficient for the current Widescreen rule: exposure may widen without widening gameplay activation. Generalize only if another object family demonstrates a different mechanism.

**Preparation / streaming:** course loading and the camera/window work expose real VRAM-update construction and `$2116/$2118` emission, but the project cannot yet predict a general preparation horizon for additional horizontal visibility.

**Course model:** all 45 RNC streams are independently decoded and CRC-validated. Dragster now has a presentation-complete neutral contract: the header dimensions resolve to a 1024×16 grid of 64-unit sectors and a 65536×1024 world domain; a 16,384-entry u16 coarse table maps sectors to 32-byte fine records; each fine record maps 16×16 world cells through packed surface words to exact C000 slots, paired A000 blocks and owning tail resources. Resource `0x24` therefore has mechanically located checkpoint/finish-bearing cells in world space. `tools/build_course_presentation_contract.py` provides deterministic rectangle queries and preserves the map/landmark corpus as validation surfaces. Editor-complete packed-field naming remains intentionally deferred.

**Progression:** principal 1P/VS/2P routes are deterministic. The medal matrix, medal values, derived unicycle tiers and checksum boundary are statically resolved and reconciled with recovered SRAM snapshots. The remaining acceptance gap is a real progression-changing save/load fixture, not generic SRAM archaeology.

**Graphics / animation:** the retained ordinary-2P MesenCE fixture now binds persistent racer presentation IDs `$0FE9/$0FEB` to concrete frame identities `0x0540`, `0x0542`, `0x0544` and `0x057E`. `83:F296` resolves those IDs through the three-byte table at `20:8000`; `tools/extract_racer_presentation_family.py` extracts the exact table-bounded 30/34-byte packed presentation streams, losslessly reconstructs them, and resolves the fixture's player-color selectors to exact 32-byte BGR555 palette assets `0x06/0x07` loaded at CGRAM `$B0/$C0`. `analysis/generated/racer-presentation-family.json` is the compact semantic manifest/regression surface. Full meanings of every packed word inside the frame stream remain an on-demand extension, not a blocker for original asset identity.

## Highest-value next discriminators

1. **Classify the first true +8 presentation boundary:** the old +8 "authoritative divergence" is closed as a harness false positive. The widened host path is already three guest frames earlier at the first frontend `$009F` milestone (443 versus 446) and stays consistently three guest frames earlier through the retained race tail, while event-relative position, velocity, camera and checkpoint/finish/lap state match every retained tag. `$0E95` differs transiently at four late-tail samples and reconverges without downstream race-state change. Use the repaired event-relative gate and now ask what widened pixels first fail or become newly correct.
2. **Renderer-facing causal closure:** preserve the now-proven separation among authoritative object existence, collision/contact activation, resource preparation, and framebuffer visibility while completing the camera/window → preparation → emission chain. If the +8 presentation boundary lands in preparation/emission, hand off the exact evidence rather than duplicating that lane.
3. **Tiny-margin Widescreen follow-through:** retain the existing +8/+16/+24 captures and repaired harness, but keep active interpretation at +8 until its first presentation boundary is classified. Do not promote permanent widening or expand margins yet.
4. **Graphics round trip (closed for the first racer family):** the ordinary-race racer family now has deterministic semantic frame IDs, exact packed-stream and palette extraction, byte-identical reconstruction and a compact manifest. Extend to additional frame IDs or decode deeper packed-word/tile semantics only when an HD/native-rendering task requires them.
5. **Save/load progression acceptance:** create one real progression-changing run, persist it, reload it, and assert medal/tier/checksum state.

## Promotion rules

Object activation becomes sufficient when at least one representative ordinary object has a proven activation timeline distinct from preparation/visibility and the owning state/code boundary is known.

Preparation/streaming becomes sufficient for the first Widescreen implementation when one representative scrolling scene can deliberately shift preparation earlier for a requested margin without changing authoritative simulation.

The course model is presentation-sufficient for current Widescreen work: Dragster answers world extent relevant to camera travel, resource/chunk spatial placement, which materialized resources own a queried world region, where checkpoint/finish-bearing cells sit relative to that region, and how those claims trace through runtime lookup/materialization. A four-course sample spanning `256×4`, `128×8`, `32×32`, and `16×64` confirms the same coarse-table, 32-byte fine-record, packed-slot, and 32:1 A000/C000 ownership invariants. Reopen course-format semantics only when a widened probe or another course violates this contract.

Graphics/animation identity becomes sufficient for Phase E expansion when one animated family has deterministic extraction, unchanged reconstruction, semantic state/frame identity, and a compact regression.

Update this scoreboard only when evidence changes what the project can safely decide or do. Do not upgrade a capability because census bytes, screenshots, or homolog counts increased without changing product leverage.