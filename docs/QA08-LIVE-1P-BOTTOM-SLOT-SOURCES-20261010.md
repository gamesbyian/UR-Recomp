# QA-08: genuine bottom OBJ source slots 96 and 97, one live 1P frame

**Status: native-accepted, both original bottom slots source-empty.** Merged #1271, exact native AOT `38096082799`, artifact `11685889818`, all four CI workflows green. Original PPU slot attribution is separate from stale semantic WRAM, one-point OAM snapshots, HDMA scanline changes and 4× authored artwork.

Merged #1264, native AOT `38095455347`, artifact
`11685169167`, captured a real **transparent** source
plane from **P1 slot97** at guest **2208**, semantic
`0895`, during active post-countdown 1P. Full independently
executed 1×/4× 342-wide Original pixels and 5,447 guest
CRCs remained identical. This was a defensible negative:
zero source OBJ alpha despite live WRAM `0895`
and a valid large64 source screen rectangle.

## Exact result: both bottom sources empty, Original unaffected

At real live 1P source frame **2208** (WRAM semantic `0895`),
the independent native original PPU isolated bottom OAM slots
**96 and 97** each produce **0 opaque RGBA pixels**. Both
source planes use the full 342×224 original logical field;
each has bounding box `[342,224,-1,-1]` (empty sentinel)
and identical all-transparent RGBA SHA256
`9b6357cacc96805cd8a1fcc3edc28d935f47f22b41fd2dbeb21f438b3b7bd58c`.
They were captured from **different actual guest processes**,
each using the same original ROM and controller route with
`RemoveFromGame` **off**.

The full independent **5,447** stock/1×/4× guest CRCs
matched and **seven** source 342×224/1368×896 Original
frame pairs stayed exact across every pixel.
Machine-readable report:
`ws342_live_1p_bottom_slot96_97_source.json`.

Crucially, directly inspecting the original frame2208 image
shows both racing unicycles **above** the horizontal green/blue
divider at scanline **112**. The empty bottom planes
are not evidence that the game's source racer sprites have
vanished; they are evidence that the prior choice of
bottom sprite source was wrong for this *visible* scene.

The correct next experiment is the separately isolated
**top PPU OAM slots 98 and 99**, not new 4× art. [#1276](https://github.com/gamesbyian/UR-Recomp/pull/1276)
adds strictly read-only native top probes, with original
complete-image and guest-CRC acceptance, and retains this
bottom result. The source OAM begin-frame y-coordinate
and WRAM semantic state alone cannot substitute for
what scanline-HDMA-dependent native PPU renders.

## Historical experimental design

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
