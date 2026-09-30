# UR-Recomp

Experimental static recompilation and modern-port project for **Uniracers / Unirally** (SNES, 1994).

## Project goal

Preserve the original game's simulation and behavior as the source of truth while building toward a modern native port with deterministic fidelity, a true-view **Widescreen** feature, an **HD Presentation** feature, documented course/asset formats, and eventually a level editor and custom-course pipeline.

The stock native baseline is already beyond first boot and race entry. The current critical milestone is stricter:

> **Explain and eliminate the first meaningful native/reference divergence on a deterministic stock route, then use that evidence to finish the semantic map of the gameplay/rendering boundaries needed by the modern port.**

Widescreen and HD Presentation should advance only behind a trustworthy 4:3 simulation/reference gate.

## ROM policy

This is currently a **private research repository** and intentionally contains the canonical project ROM, `reference/roms/retail/Uniracers_USA.sfc`, so repository-hosted analysis and CI can operate on the same input.

That is an explicit project choice, not an assumption inherited from SNESRecomp's public-release model. Before any public release or visibility change, the ROM and any other proprietary game-derived material must be removed and the full Git history audited/re-written as needed.

Preserved development builds and source archives live under `reference/roms/` and are never aliases for the canonical retail input.

See `docs/ROM-SAFETY.md`.

## Framework

Target framework: https://github.com/RetroPortingToolKit/snesrecomp

The framework revision is pinned by the repository rather than floating on upstream `main`.

## Working principles

1. Original behavior is the oracle.
2. Fix configuration/runtime behavior rather than hand-editing generated C as a permanent solution.
3. Stock 4:3 behavior comes before the Widescreen feature.
4. Recomp correctness comes before prettiness.
5. Every reverse-engineering claim should be traceable to evidence.
6. Keep generated bulk code/assets out of Git unless there is a specific reason to version them.
7. Prefer deterministic tests over subjective "feels right" judgments.
8. Document unknowns explicitly.
9. Treat public-release hygiene as a separate gate from private research convenience.

## Current work

Agents should start with `AGENTS.md`, which routes tasks to the smallest current authority. For human project orientation, start with `docs/PROJECT-PLAN.md`, `docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`, and `docs/WORK-QUEUE.md`. Tool selection/bootstrap is documented in `docs/TOOLCHAIN.md`.

## Status

**Native bring-up is established; fidelity and semantic recovery are the active critical path.** The canonical game boots, navigates deterministically into gameplay, and supports native/reference replay and state comparison. The strongest current discriminator is the exact 2014 replay, where native and the pinned Snes9x reference have diverged by the dense frame-440 sampling window. Current work is to bracket that first causal divergence, map the responsible routines/state transitions, and expand the comparative four-ROM/multi-analyzer code atlas around the core simulation and rendering boundaries needed for finish fidelity, Widescreen, HD Presentation, and course tooling.
