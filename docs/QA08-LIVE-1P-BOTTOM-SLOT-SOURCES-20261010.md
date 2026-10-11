# QA-08: genuine bottom OBJ source slots 96 and 97, one live 1P frame

**Status: native candidate, no merged acceptance yet.** Source-owning
original PPU slot attribution is separate from semantic WRAM,
screen-rectangle geometry, or HD artwork.

Merged #1264, native AOT `38095455347`, artifact
`11685169167`, captured a real **transparent** source
plane from **P1 slot97** at guest **2208**, semantic
`0895`, during active post-countdown 1P. Full independently
executed 1×/4× 342-wide Original pixels and 5,447 guest
CRCs remained identical. This was a defensible negative:
zero source OBJ alpha despite live WRAM `0895`
and a valid large64 source screen rectangle.

## The next smallest discriminator, without any new guest process

The existing real **1× 1P world process**, which already generates
the original worklist, now exports **bottom slot96**
non-destructively at guest2208, while the existing genuine
**4× 1P process** continues to export slot97 as before.
Each process still executes precisely the existing 5,447
guest frames; there is no new emulator route, renderer,
native art asset, input pattern or deliberate guest write.

`tools/check_baldosa_oneplayer_bottom_oam_sources.py`
requires for both slots, independently:

- original 1P control, 1×, and 4× guest CRC streams identical
  for all **5,447** guest frames;
- exactly seven matching 342×224 and 1368×896 actual
  Original full-scene image pairs, all pixels identical;
- exact native isolated-OBJ PPU slot/frame/filename,
  alpha count, bounding box and source log provenance;
- independently repeated Original-frame pixels unmodified
  under both non-destructive source captures;
- source alpha RGBA SHA256 and source RGB matches/differences
  against final Original for each real OAM slot.

The decisive outcome is factual: if source slot96 has
opaque PPU pixels while slot97 remains empty, the
visible scene's original bottom racer sources are
not equivalent to their screen-aligned OAM rectangles.
If both are empty, inspect the other source slots or
background planes before authoring anything. Even
an RGB match against the final display **does not prove
the original final visible pixel owner**, because
coincidental colours and BG/OBJ priority can coexist.

**No sprite removal, new Remastered asset, player
graphics toggle, 342-wide HD or completed-event
release acceptance is authorized by this diagnostic.**
