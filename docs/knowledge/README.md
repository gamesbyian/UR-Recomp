# Uniracers project knowledge base

This directory is the project's synthesis layer: the smallest durable set of documents that explains how Uniracers currently appears to work.

It does **not** own raw evidence, chronology, milestone status, or source provenance.

- Evidence-backed claims and uncertainty belong in `docs/RESEARCH-LEDGER.md`.
- Recovered addresses and routine/data names belong in `docs/SYMBOLS.md`.
- Current implementation priority belongs in `docs/WORK-QUEUE.md`.
- Course-specific investigation detail belongs in `docs/COURSE-FORMAT.md`.
- External artifacts and provenance belong under `reference/`.
- Machine-generated measurements belong under `analysis/generated/`.

The knowledge base answers a different question: **what coherent model of the game follows from all of those sources together?**

## Epistemic labels

Use these labels consistently.

- **Confirmed**: reproduced directly from project-owned ROM/runtime analysis or otherwise established as binary/runtime fact.
- **Supported**: backed by multiple strong sources or one strong source plus local corroboration, but not yet fully reproduced.
- **Inferred**: the simplest current explanation joining confirmed/supported facts.
- **Working hypothesis**: useful model with a clear discriminating test.
- **Unknown/conflict**: evidence is incomplete or currently points in more than one direction.

Knowledge pages should be rewritten when the model changes. They are not diaries.

## Map

- [Game state and flow](game-state-and-flow.md)
- [Tracks, courses and RNC data](tracks-courses-and-rnc.md)
- [Movement, physics and stunts](movement-physics-and-stunts.md)
- [Rendering, camera and OAM](rendering-camera-and-oam.md)
- [Graphics and animation](graphics-and-animation.md)
- [Autonomous play and deterministic input](autonomous-play-and-input.md)
- [Progression, SRAM and results](progression-sram-and-results.md)
- [Builds, development history and hardware seams](builds-development-and-hardware.md)
- [Open questions and discriminating tests](open-questions.md)

## Core mental model

The current project model is:

```
front end / progression
        |
        v
 runtime mode + selected track
        |
        +----------------------+
        |                      |
        v                      v
 course selector          player/opponent state
        |                      |
        v                      v
 RNC stream             movement / stunt / boost
        |                      |
        v                      |
 decompressed course           |
        |                      |
        +----------+-----------+
                   |
                   v
        collision / camera / render
                   |
          +--------+--------+
          |                 |
          v                 v
      BG/tilemap         OBJ/OAM
          |                 |
          +--------+--------+
                   |
                   v
             SNES PPU output
```

The modern port should preserve the original simulation and state transitions. Presentation features may observe or reinterpret that state, but should not become a second independent gameplay implementation.
