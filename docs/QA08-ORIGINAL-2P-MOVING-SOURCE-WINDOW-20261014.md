# QA-08: real two-player moving original/native PPU source window

**Source comparator staged, real additional native captures not yet executed.**
This adds verification before extending the expensive authentic guest route.
It neither creates raster pixels nor authorizes renderer changes.

## Real independently executed original reference

Accepted Snes9x USA 2P run 38543766102 / artifact 11884155561
contains 37 consecutive genuine unmodified 256x224 BGRX callbacks
2188..2224. All original video SHA256 hashes are pinned in the
source manifest. ZIP SHA256:
6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3.

Merged #1592 established significant moving two-player differences in
both split views between original callback2207 and original callbacks
2191,2223. Proposed *native* guest2192/2224 are only candidate frame
pairings, not independently proved guest/controller/camera equivalences.

The new comparator takes real, complete 256x224 source PPU RGB_ALPHA
P7 rasters at actual native guest2192,2208,2224 from **four separate
2473-frame guest processes**: stock, all-channel consumed-prime, only
channel7 consumed-prime and combined channel5+7. All processes must
have byte-identical full 2473-entry guest CRC transcripts.

For each new native frame and each renderer experiment, it compares
**all 57,344 RGB5 pixels against every one of the 37 original
Snes9x BGRX callbacks**. The output includes complete source
phase-ranking scores and both preselected callback2191/2223
comparisons. Source quantization uses only the previously accepted
Snes9x RGB565 green6→native green5 normalization. No masked seam
rows, crops, physical resizing, OAM substitutions or image shifts.

Known original callback2207 versus native global-prime2208 must remain
57,344/57,344 exact as a strict control. Source ZIP, original
manifest, each original image digest, native frame dimensions and all
guest CRC contents fail closed when changed or missing.

### Intended execution

Run tools/qa08_compare_original_moving_source_window.py with
--original-zip, four --<variant>-dir paths, four --<variant>-crc
paths, and --out for a machine-readable source comparison.
Variants: stock, global, channel7, channel57.

The separately staged read-only native host source capture extension
in PR #1599 can produce the additional actual P7 frames when applied
to a disposable pinned host and executed on the real USA 2P route.
A staged patch or source-only original archive alone is NOT
original/native moving-frame evidence. Do not invent these frames.

Even if a ranked source image is exact, callback ranking is **phase
discovery only**, not acceptance of corresponding executed 65816
instructions, camera or input consumption, per-scanline active OAM,
OBJ/BG/window/colour math, full event correctness or physical SNES
HBlank. Original remains canonical at 256x224 with 7:6 PAR and
genuine 4x fallback; Widescreen adds real world source pixels, and
unapproved procedural Remastered racer art remains rejected.

Three-project preflight: reuse existing UR/Baldosa original PPU capture,
strict native source file checks, and real original Snes9x archive.
Malmazuke source annotations remain advisory. No gameplay simulation,
Modern/storage, CPU/APU, cumulative scheduling, independent QA ledger,
production HD or Widescreen edits.
