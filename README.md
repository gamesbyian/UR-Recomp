# UR-Recomp

Experimental ROM-free static recompilation and modern-port project for **Uniracers / Unirally** (SNES, 1994).

## Project goal

Preserve the original game's simulation and behavior as the source of truth while building toward a modern native port with deterministic fidelity, true widescreen presentation, modern-resolution rendering, documented course/asset formats, and eventually a level editor and custom-course pipeline.

The first milestone is deliberately smaller:

> **Boot a verified stock ROM through the current SNESRecomp stack and reach a playable race with stock presentation.**

No widescreen, asset replacement, or gameplay changes should begin until that baseline is trustworthy.

## Copyright / ROM boundary

This repository must not contain copyrighted game ROMs or extracted game assets. Users supply their own legally obtained ROM locally. Generated outputs that substantially reproduce game code or assets stay local unless their redistribution status is deliberately reviewed.

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
6. Do not commit ROMs, saves, extracted copyrighted assets, or generated game-derived output.
7. Prefer deterministic tests over subjective "feels right" judgments.
8. Document unknowns explicitly.

## Current work

Start with `docs/WORK-QUEUE.md`. Important discoveries belong in `docs/RESEARCH-LEDGER.md`; chronological execution attempts belong in `docs/BRINGUP.md`.

## Status

**Pre-bring-up scaffold.** No compatibility claim is made yet.
