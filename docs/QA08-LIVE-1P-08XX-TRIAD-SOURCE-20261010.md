# QA-08: three real successive P1 race poses, exact source WRAM and OAM

**Source:** merged #1255, successful native AOT `38094430121`,
artifact `11684953572`, original game guest script
`baldosa/tests/routes/race_1p.txt`, genuine 1P
`race_1p_ur_ws342_live/log.txt`. Complete original-vs-native
5,447 guest CRC parity, 342-wide original course and source-PPU
scene unchanged.

## Consecutive dense host-cadence source states

The authentic guest WRAM and the native PPU original OAM at
these three consecutive 16-guest-frame sample boundaries:

| Guest frame | P1 semantic | Companion / selector / gate | Original P1 bottom OAM slot97 |
| --- | --- | --- | --- |
| **2208** | `0895` | `0DE0 / 0000 / 0001` | X96, Y96, tile00, large64 |
| **2224** | `08D5` | `0DE0 / 0000 / 0001` | X96, Y96, tile00, large64 |
| **2240** | `0855` | `0DE0 / 0000 / 0001` | X96, Y96, tile00, large64 |

In all three native guest observations:

- Original PPU `OBSEL=83`, unrotated OAM priority,
  P1 top slot98 X44/45 Y112 tile00 large64 but outside the
  **top** split viewport (no source-screen intersection);
- P1 bottom slot97 X96 Y96 tile00 large64 intersects the
  **bottom** 112–223 split viewport;
- original racer bank and existing conservative stock P2
  foreground safety classifier report eligible;
- P1 does **not** have a selected/authored HD asset:
  `registered=0 art=0 selected=0 fallback=2`.

The on-screen original OAM rectangle establishes a **geometric
upper bound only**. It cannot certify an opaque OBJ sample, final
BG/window priority or that an entire 64×64 authored sprite should
be drawn in a widened 342-column camera.

## Staged source visibility test sequence

1. Draft #1264 uses the **existing 1P fourfold guest run**, exact
   source frame2208 and **single original slot97** PPU source
   export with RemoveFromGame **off**. Require seven independent
   1×/4× Original frame matches and full 5,447 CRC equality.
2. If frame2208 has genuine source alpha and priority evidence
   supports preservation, collect exact separate frame2224
   (`08D5`) and 2240 (`0855`) original source planes and
   matching native original 1×/4× full-frame witnesses using
   the *same guest routes*. Never infer omitted images from
   WRAM IDs alone.
3. Author only genuinely source-derived/fidelity-reviewed 4×
   silhouettes and anchors, with separate palette/pose,
   foreground, split-screen seam and temporal acceptance.
   Preserve Original fallback wherever any guard cannot prove
   safe replacement.

The matched guest frame identifiers, companion `0DE0` and
stable original bottom P1 OAM anchor make this a narrow,
reproducible next art-family investigation rather than a
request for speculative new sprites or a second renderer.

**No 342-wide authored HD, 2P safe occlusion, complete-event
fidelity, player graphics option or beta gate is accepted here.**
