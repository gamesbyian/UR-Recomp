# QA-08: authentic original Snes9x source-pixel and PPU-write checkpoint reader

**Reader prepared, genuine new images pending archived original workflow run.**

The existing original-USA 2P `snesref` original-core route has independent
semantic checkpoints `go` and `t480`, at original emulator
frames **1989 and 2473** on the hash-pinned 2P script. Its source
libretro frontend automatically writes complete **256x224 BGRX8888**
pixel arrays `<tag>.fb.bgrx`, corresponding `<tag>.info.json`,
and with the patched core, an actual per-write `<tag>.ppuw.tsv`.
These are original interpreter source captures, **not** the native
Baldosa widened 342-pixel screenshot or player-approved HD art.

The new **offline** `tools/qa08_original_snesref_raster_source.py`
checks both full original screenshots, exact published original
checkpoint frame and same-tag framebuffer frame, raw image dimensions
and size, enabled original BG1/BG2/BG3/BG4/OBJ, default clipping/math,
non-truncated exported source PPU writes, exact original PPU-write
journal count and valid real Snes9x beam sequence
**V225..261, then V0..224**. It keeps SHA256 of all source
images, their metadata and the entire PPU write trace, plus actual
HDMA/CPU/DMA register provenance counts for `$2130–$2132`.
Four sample RGB points per original image are **literal 256x224
original coordinates**; even x90 is *not* automatically admitted
as the same camera pixel as native widescreen x133. Source chronology,
frame identity and image bytes must be accepted before selecting
corresponding original/native pixels.

```sh
python3 tools/qa08_original_snesref_raster_source.py \
  --root /path/to/qa08-original-opcode-dumps \
  --out /tmp/qa08-original-snes9x-pixels.json
python3 -m unittest tests.unit.test_qa08_original_snesref_raster_source
```

An independently executed original 2P source archive can supply these
already-produced outputs. The tool runs zero new games or emulator
processes, does not alter the original PPU/dma/guest/core, and must
not promote a positive match of **two original checkpoints** into
identical original/native 2P input state, final composed RGB
parity or physical SNES hardware. The original Snes9x PPU
journal records actual writes but still cannot replace the true live
per-pixel source operand or subscreen/window winner. If there is
a genuine original/native pixel difference, use the paired
state/camera/beam and HDMA sources to locate it before patching
rendering. Preserve native 256x224/7:6 original PAR, 4x
Original fallback and actual wide-world geometry.
