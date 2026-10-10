# QA-08: one authentic animated 1P rider source plane at guest frame 2208

**Status: native-accepted source-empty result.** Merged #1264, exact AOT run `38095455347`, artifact `11685169167`; all four completed relevant CI checks including native SUCCESS. The accepted Native Original 342×224 1P frame2208 has P1 semantic ID **0895**, displays real post-countdown unicycles with course/HUD and 43 extra source columns per side, yet the original PPU's isolated **slot97 has zero opaque pixels** on that frame.

The original PPU can already export one OAM slot's isolated **RGBA
source OBJ plane** without RemoveFromGame, independently of host HD.
This accepted experiment reused that established source-only exporter for P1 bottom
OAM slot **97** at the exact accepted frame 2208, within the already
scheduled *same 5,447-frame independent 1P native 4× process*.
It does not launch another guest, add a renderer or remove a sprite.

The strict new oracle `tools/check_baldosa_oneplayer_0895_source_obj.py`:

- Requires all **5,447** original guest CRCs match stock exactly,
  actual frame2208, native slot97 and exactly seven independently
  aligned Original 342×224 1× / 1368×896 4× frames, all pixels exact.
- Uses the established per-slot PPU source checker to validate
  native isolated plane dimensions, source/guest ID, original PPU
  alpha/bounds and the native `UR_RACER_HD_WIDE_SOURCE` log.
- Records independently observed source alpha in each scanline112
  screen half and the source plane SHA. Counts isolated source
  RGB matches and differences against the full Original final
  framebuffer. A source pixel having the same colour as the
  final framebuffer **cannot establish layer ownership**.
- Accepts a real **source-empty** slot as a meaningful negative,
  not a trigger to generate or paint a phantom 4× sprite.

## Native result: genuinely empty isolated original P1 slot97

The non-destructive, separately rendered **342×224**
source plane `baldosa-ws342-live-1p-slot97/ur-baldosa-ws342-obj-slot97-frame002208.pam`
is entirely alpha-empty:

| Independently verified native value | Result |
| --- | --- |
| Guest frame / semantic WRAM | **2208 / 0895** |
| Original isolated OAM slot | **97** (P1 bottom rectangle from OAM) |
| Isolated PPU source-alpha opaque pixels | **0 / 76,608** |
| Source-alpha bounding box | **342,224,-1,-1** (empty sentinel) |
| Exact native full-guest CRC parity | **5,447 / 5,447** |
| Independent full Original 1× / 4× source matches | **7 / 7 frames** |
| Raw isolated source RGBA SHA256 | `9b6357cacc96805cd8a1fcc3edc28d935f47f22b41fd2dbeb21f438b3b7bd58c` |

The native source log expressly says
`UR_RACER_HD_WIDE_SOURCE frame=2208 slot=97 status=empty top_alpha=0 bottom_alpha=0`.
There was **no** guest mutation or original OBJ removal, and the
completed original source framebuffer remained pixel-exact.

This disproves the inference that a P1 WRAM semantic ID plus
intersecting original OAM rectangle is itself evidence of
emitted visible P1 artwork. The real finished Original frame still
shows unicycles. Their original source ownership is unresolved:
source slot96, other OAM slots, or different internal PPU planes
must be investigated before drawing or erasing a replacement.

Follow-on [#1271](https://github.com/gamesbyian/UR-Recomp/pull/1271)
samples the adjacent original bottom **slot96** in the already
executed independent 1× guest run at exactly frame2208, keeping
the accepted 4× slot97 negative as the control. Source alpha
alone still cannot establish final BG/window winner attribution.

The original source-only plane was captured **before original PPU
BG/window composition**. A positive proves emitted per-slot
source alpha, *not* that the same sprite pixel survived final
PPU priority or can be safely erased and repainted. The final
counterfactual would require independent genuine stock-vs-single-slot
removal at this same frame, separately tested without allowing
that diagnostic setting in normal gameplay.

**No HD asset is generated, no 342-wide authored HD admitted, and no
full-event or Windows beta release credit is granted.**
