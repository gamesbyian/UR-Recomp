# QA-08: one authentic animated 1P rider source plane at guest frame 2208

**Status: draft, not accepted.** The preceding accepted Native Original
342×224 1P frame 2208 has semantic P1 ID **0895**. It displays active
post-countdown unicycles with real course/HUD and 43 additional source
columns on each side.

The original PPU can already export one OAM slot's isolated **RGBA
source OBJ plane** without RemoveFromGame, independently of host HD.
This draft reuses that established source-only exporter for P1 bottom
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

The source source-only plane is captured **before original PPU
BG/window composition**. A positive proves emitted per-slot
source alpha, *not* that the same sprite pixel survived final
PPU priority or can be safely erased and repainted. The final
counterfactual would require independent genuine stock-vs-single-slot
removal at this same frame, separately tested without allowing
that diagnostic setting in normal gameplay.

**No HD asset is generated, no 342-wide authored HD admitted, and no
full-event or Windows beta release credit is granted.**
