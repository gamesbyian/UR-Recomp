# UR-Recomp

Experimental static recompilation and modern-port project for **Uniracers / Unirally** (SNES, 1994).

## Project goal

Preserve the original game's simulation and behavior as the source of truth while building toward a modern native port with deterministic fidelity, true widescreen presentation, modern-resolution rendering, documented course/asset formats, and eventually a level editor and custom-course pipeline.

The first milestone is deliberately smaller:

> **Boot the canonical Uniracers ROM through the pinned SNESRecomp stack and reach a playable race with stock presentation.**

No widescreen, asset replacement, or gameplay changes should begin until that baseline is trustworthy.

## ROM policy

This is currently a **private research repository** and intentionally contains the canonical project ROM, `Uniracers (USA).sfc`, so repository-hosted analysis and CI can operate on the same input.

That is an explicit project choice, not an assumption inherited from SNESRecomp's public-release model. Before any public release or visibility change, the ROM and any other proprietary game-derived material must be removed and the full Git history audited/re-written as needed.

See `docs/ROM-SAFETY.md`.

## Framework

Target framework: https://github.com/RetroPortingToolKit/snesrecomp

The framework revision is pinned by the repository rather than floating on upstream `main`.

## Working principles

1. Original behavior is the oracle.
2. Fix configuration/runtime behavior rather than hand-editing generated C as a permanent solution.
3. Stock 4:3 behavior comes before widescreen.
4. Recomp correctness comes before prettiness.
5. Every reverse-engineering claim should be traceable to evidence.
6. Keep generated bulk code/assets out of Git unless there is a specific reason to version them.
7. Prefer deterministic tests over subjective "feels right" judgments.
8. Document unknowns explicitly.
9. Treat public-release hygiene as a separate gate from private research convenience.

## Current work

Start with `docs/WORK-QUEUE.md`. Important discoveries belong in `docs/RESEARCH-LEDGER.md`; chronological execution attempts belong in `docs/BRINGUP.md`.

## Status

**Analyzer bring-up in progress.** No compatibility claim is made yet.
