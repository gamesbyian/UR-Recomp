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


## Executed original/native moving PPU results, verified on 2026-10-14

**The earlier unexecuted/source-only status is superseded for this
specific exact-head experiment.** Merged
[#1614](https://github.com/gamesbyian/UR-Recomp/pull/1614)
executed the source-guarded native guest run
[38665202913](https://github.com/gamesbyian/UR-Recomp/actions/runs/38665202913),
artifact **11940454106**, archive SHA256
**51593205e289a532666bc0163e66eb5f1da85c8c6046232e37b671f1f7482bf1**.
The independent exact original 37-callback archive ZIP retained its
accepted hash
6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3.
All **four** actual 2473-entry native route CRC series remain identical
(SHA256 4280056aef50acde83ca9ce82d0a12f8a5b7190a18e42a5d24401b65c44e205d),
despite real distinct disposable first-line DMA implementations.

The genuine source-window RGB5 comparator report SHA256 is
64f78d45b8ceb979e620f016e07145a4a4dec03605b39ad87568e86ca73440b8.
Its complete results were **independently rechecked from original
raw BGRX and native P7 bytes** by direct per-pixel RGB5 arrays, not
merely trusted from the producer summary. Exactly the documented
Snes9x RGB565 green6→5 normalization was applied, never pixel masking,
sprite removal, row shifting or image resizing.

| Real native guest ↔ genuine original Snes9x callback | Stock native wrong RGB5 | Global consumed prime wrong | Channel7 only wrong | Channels5+7 wrong |
| --- | ---: | ---: | ---: | ---: |
| **2192 ↔ 2191**, independently moving post-GO scene | 512 | **0** | **0** | **0** |
| **2208 ↔ 2207**, prior accepted post-GO scene | 512 | **0** | **0** | **0** |
| **2224 ↔ 2223**, second distinct moving post-GO scene | 512 | **0** | **0** | **0** |

In both *new* scenes the best original callback out of the
**37 real consecutive source callbacks** was precisely the
preselected original2191/native2192 and original2223/native2224
pairing. For native guest2192/global prime, the correct callback
has 57,344 matching RGB5 pixels versus **37,829** matching pixels
at the runner-up, a 19,515-pixel margin. For native2224 the next
best original callback has only **36,333** matching pixels, a
21,011-pixel margin. These are powerful visible **frame registration**
discriminators, but still *not independent 65816/input/camera
state parity*.

The real source P7 SHA256 at guest2192 is:
- stock 7e0cfab20c5342c242d7eeb0c77bff2d132ee1426a62d3a3759f43bd3f95027e;
- all three consumed-prime configurations
  fac9f37e04b752676346bd75345e6e988b88e5cf6703722618d8a968ec90b36c.

At guest2224:
- stock 8271ed54cc2f1c1841cbd0f1e0c6b77e278dce721a2e1efe1a6ba432897535b4;
- all three consumed-prime configurations
  d64e7b2fee2ff9f21b5fad7f4e8618ea27ad8846c6b6047ca9c511583bde6bd8.

Thus **three distinct active post-GO 2P original-emulator scenes**
are now independently source-size pixel-exact under ch7-only
consumed prime, combined channels5+7 and global prime.
The separate genuine countdown original1855/native1856 still
requires global prime to eliminate its **460 remaining** source
contour mismatches in selective ch7 / combined ch5+7.
Do not extrapolate the steady active-race pixel result backwards
into transition/countdown window correctness.

Permanent machine-readable source evidence:
[real 2P post-GO three-frame parity](../analysis/data/qa08-real-original-native-postgo-3frame-rgb5-parity-20261014.json).
The next determinant for a production correction remains all active
HDMA source channels and effective per-row window/BG/OBJ state at
the known two countdown contour components, plus independent
real moving 2P OAM pixel ownership, actual results, transitions
and 1P scenes. Cross-title (Gundam Wing) first-line correctness
and hardware HBlank still gate any global first-line DMA change.
Widescreen 342-wide PPU world, actual 4x physical Original, 7:6 PAR
and owner-approved Remastered art must retain their separate tests;
none is accepted by this source-only comparison.
