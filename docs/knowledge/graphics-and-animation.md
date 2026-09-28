# Graphics and animation

## Original pipeline

Developer testimony says the unicycle was built as a detailed 3D source model and rendered down into tiny SNES frames.

The animation space included multiple dimensions:

- stunt rotations;
- tilt/stretch;
- saddle movement;
- pedal phase;
- wheel phase;
- ordinary orientation/state changes.

Mike Dailly's historical tool inventory also names dedicated **Unicycle Compression** and **Uniracers A0 plotter** tools.

## Current inference

**Inferred.** The ROM probably does not contain a simple linear sprite-strip model. It likely contains a heavily indexed and compressed animation corpus where several state dimensions select or derive a rendered frame.

That makes recovering **frame selection semantics** at least as important as extracting pixels.

## Development consequence

Asset work should proceed in this order:

1. identify deterministic ROM graphics ranges and upload paths;
2. recover the game's frame/palette selection state;
3. assign semantic asset/frame IDs;
4. prove original extraction and rendering;
5. only then introduce HD Presentation replacements.

For unicycles, a high-resolution replacement system can plausibly use new 3D source models rendered into the same semantic poses/states selected by the original game.

The important fidelity contract is not "copy the old sprite sheet." It is:

```
same original simulation state
 -> same semantic animation/frame selection
 -> stock sprite OR high-resolution replacement
```

## Other assets

The project has public reference leads for:

- unicycle sheets;
- menu arrow;
- track backgrounds;
- fonts/logo/HUD;
- stitched course maps.

These are useful visual references, but deterministic extraction from the canonical ROM is preferred for establishing what the game actually contains.

## Unknowns

Major unresolved questions include:

- animation indexing dimensions;
- compression format used specifically for unicycle frames;
- relationship between frame state and OAM construction;
- how palettes are selected;
- whether track/background themes use compact dictionaries or direct tile tables;
- which assets differ regionally.
