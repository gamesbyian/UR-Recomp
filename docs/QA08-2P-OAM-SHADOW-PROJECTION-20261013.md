# QA-08: source-indexed split racer OAM shadow, not a visibility boolean

**Status: offline structural interpretation only.** Existing native 2P
captures establish real isolated Original PPU source slots 98/99 (upper),
97/96 (lower) at guest2208. The accepted post-GO upper/lower source
translation is **(-13,+112)** for both racers; the final raster has
foreground/colour-math ambiguity. See
[post-GO original source](QA08-2P-POSTGO-ORIGINAL-OAM-SOURCE-2208-20261011.md),
[paired sources](QA08-2P-POSTGO-SPLIT-OBJ-SOURCE-PAIR-20261011.md)
and the [PPU colour chronology](QA08-2P-POSTGO-PPU-COLOUR-JOURNAL-20261011.md).
Nothing in this tool changes original rendering or claims the winner of
a contested pixel.

## Source-backed register correction

The existing
[`summarize_paired_player_slots.py`](../tools/summarize_paired_player_slots.py)
labels the raw byte at `$1599` as
`screen1_player1_visibility_raw`. That historical output **must not**
be read as a per-racer display-visible flag. The preserved Baldosa
`decomp/ram.txt` identifies `$7E1599` as the high-OAM shadow byte for
reserved sprites **96–99**. The SNES OAM layout places four 2-bit fields
in this byte: one X bit 8 and one sprite size-select bit for each slot.
The pre-existing [split decoder](../tools/decode_uniracers_oam_split.py)
already decodes `0xA5` and `0x5A` into complementary pairs. These are
the known active-display OAM byte values on scanlines 0/112, while a
single WRAM checkpoint captures neither the intervening physical
OAM writes nor the resulting completed PPU pixels.

Bank 82's recovered graphics path computes `$1501..$1510` as four
4-byte reserved-sprite OAM records before writing OAMDATA.
Their low-level bytes are `xLow, y, tile, attributes`; the ninth X
bit is in `$1599`. The earlier source analysis relates
`$1501/$1505` to camera-2 candidates and `$1509/$150D` to
camera-1 candidates, with offscreen sentinels.
`$121B/$121D` are separate source-labelled offscreen words.
**Neither zeroed $121B/$121D nor a constant $0DDB=1 proves a
malfunctioning split/culling path**; the latter enables updating the
second camera in the reconstructed bank-81 camera-control chain.
Existing source evidence is narrower and stronger than an unknown
sentinel: [`docs/SYMBOLS.md`](SYMBOLS.md) identifies a **`0x70` offscreen
fallback** for P1 `$1509/$150A` and P2 `$150E`. The separately accepted
[original/native Jumpover offscreen experiment](RESEARCH-LEDGER.md)
observed **P1 `$121B=1` for 18 frames** simultaneously with P1
screen X/Y `0x70`. Those observations establish a real offscreen branch,
but an isolated `0x70` value is not a generally safe *visible pixel*
predicate: distinguish active camera, viewport, OAM physical write
schedule and final PPU result before applying a replacement mask.

## Why `0x70` alone cannot classify visibility

The **existing known active-display high-OAM bytes**, `0xA5` for the top
half and `0x5A` for the lower half, reverse X-bit-8 for the two sprite
pairs. Holding a hypothetical low-X byte `0x70` fixed illustrates why
a WRAM screen-coordinate byte alone has no visibility semantics:

| High-OAM byte | Reserved slots 96/97 X9 | Slots 98/99 X9 |
| --- | --- | --- |
| `0xA5` (top-half rip) | `0x170` (signed -144) | `0x070` (+112) |
| `0x5A` (bottom-half rip) | `0x070` (+112) | `0x170` (signed -144) |

This table is **pure OAM bit arithmetic on synthetic low-X values**,
not a new real native capture, complete sprite bbox, output pixel
owner or proof that every source sentinel is used identically.
It explicitly leaves sprite size, Y wrapping, priority, window,
intervening writes and actual 342-wide physical OAM unresolved.
A sampled `$1599` shadow still must not be equated with the active
PPU high-OAM byte at either scanline.

## Reusable diagnostic without more GHA runners

```sh
python3 tools/qa08_decode_split_oam_shadow.py \
  path/to/existing/native-wram-captures \
  --checkpoint endurance-1740 \
  --checkpoint endurance-2580 \
  --checkpoint endurance-3420 \
  --out /tmp/qa08-oam-shadow.json
python3 -m unittest tests.unit.test_qa08_decode_split_oam_shadow
```

This reads existing **exact 128 KiB** `<checkpoint>.wram.bin`
dumps; it never launches a guest, attaches a PPU or changes game
state. It records SHA-256 per input, raw per-slot OAM records,
separately decoded high-table bits, signed-9 coordinate
interpretations (including possible wrapped X), raw second-camera
and offscreen words, and observed changes between checkpoints.
No particular X/Y value is automatically classified as hidden.

### Discriminators before safe HD or Widescreen promotion

1. Capture or recover **same-frame, same-process** native WRAM shadow
   together with the isolated actual PPU source slots, physical
   active-display high-OAM writes, and unchanged full Original raster.
2. For each viewport, compare `$1501..$1510` candidate coordinates
   and the effective per-line OAM high-table byte to genuine isolated
   source-alpha bbox. Identify actual sentinel writer branches
   around bank-82 projection, not from unvalidated thresholds.
3. Separately prove contested OBJ-versus-OBJ and BG/window/math
   output priority on split-line and crossing-racer examples.
4. Leave authentic 256×224, 7:6 PAR, 4× Original fallback and
   real 342-wide world untouched. The procedural 4× racer remains
   vetoed for aesthetic likeness pending multi-pose official
   reference review.

No number in this report is a measured original hardware pass.
Native research fingerprint novelty, host WRAM snapshots and
synthetic unit checks remain below source PPU and final-raster
acceptance. Physical hardware display/input gaps remain open.
