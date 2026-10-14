# QA-08: original two-player countdown source versus the HDMA prime experiment

**Accepted genuine original/native pixel result, 2026-10-14:** the archived original Snes9x run has completed. Its corrected global consumed-prime native countdown source frame matches original RGB5 **57,344/57,344**, with no masked row or pixel. This is independent from the previously accepted post-GO exact frame; production HDMA has NOT changed.

The authentic two-process native experiment run38628505396, retained in
artifact 11925446617 (ZIP SHA256
298c73f095c2ecdebc99c0e7392dbc4112fecd61eb8feb5106fb2921e1cdd0ec),
found after global first-line HDMA consumption:

| Actual guest scene | Changed full original-size native PPU RGBA pixels |
| --- | ---: |
| 2P frontend / 400 | 0 |
| 2P countdown / 1856 | 971 |
| 2P post-GO / 2208 | 512, exact accepted original brightness seam |

Direct independent pixel inspection of the original-size 256x224
frame1856 PAM pair shows **512** of the 971 differences are the known
full-width output y111 and y113 rows. The other **459** are
source RGB changes in thin top and bottom contour bands, with unchanged
alpha. Two eight-neighbor components comprise 482 upper-view pixels
(y55..111) and 489 lower-view pixels (y113..176). The changed
output includes half-width rows y98 and y133 (128 pixels each).
Contour geometry resembles clip/window boundaries but no effective
window-register writer has yet been proven as causal for these pixels.
Do not assume that shifting native PPU registers implies a physical
SNES effect or which native version is correct.

The new one-shot authentic original replay reuses the same pinned USA
ROM, input script and original Snes9x/libretro/snesref implementation
as the accepted post-GO 37-frame archive. It captures just 17
**consecutive genuine original callbacks 1848..1864** with no
scaling, line-mask, framebuffer synthesis or altered guest instructions.
It independently verifies the original route script SHA, full t480
WRAM SHA and source callback length/format. The exact executed native
before/after frame1856 PAMs and their full CRC transcript are read
from the independently SHA-pinned #1577 archive. No new native
player process is needed.

tools/qa08_compare_original_countdown_prime.py compares every RGB5
pixel of every original callback against both the true stock and
globally consumed-prime native P7 source, using only the previously
justified original RGB565 green6-to-native-green5 quantization.
It retains the preselected original callback1855 -> native guest1856
phase hypothesis and **all seventeen** per-frame score pairs.
Best-scoring frame is discovery, not independent frame-phase parity;
genuine original/native guest state alignment and OAM/window timing
must still be checked before using this as acceptance of either
native renderer.

Regardless of the outcome, shipping HDMA startup, 1P/2P sprite
source-alpha and occlusion, channel5 colour math, real Widescreen
world margins, fixed Original 7:6 PAR and artist-approved HD racer
remain independently gated. No gameplay, Modern or release ledger
files are changed.

## Executed original countdown source: exact 971-pixel correction

Actual green [Snes9x original replay 38630121814](https://github.com/gamesbyian/UR-Recomp/actions/runs/38630121814),
artifact **11925517895**, was independently downloaded and inspected.
Whole artifact ZIP SHA256:
56ec0011a3559f5953578c495d080d0150f2a06fb7a76c2e437fab781e2b2ce6.
Original source captured all 17 expected native-size unmodified 256x224
BGRX callback frames1848..1864; accepted exact original route script
and t480 WRAM receipts remained unchanged. Native before/after P7
frame1856 hashes were independently pinned in the source accepted
#1577 artifact ZIP SHA 298c73f095c2ecdebc99c0e7392dbc4112fecd61eb8feb5106fb2921e1cdd0ec.

| Native guest1856 compared with real original callback1855 | Matching RGB5 pixels | Wrong pixels |
| --- | ---: | ---: |
| Pinned native non-consuming prime | 56,373 / 57,344 | 971 |
| Pinned native global consumed-prime counterfactual | **57,344 / 57,344** | **0** |

Both independent native versions select **original callback1855** as
the highest-scoring frame across all 17 genuine original callbacks.
Next-best original callback for global-prime is frame1856 with
48,058 equal pixels, a **9,286-pixel ranking margin**; stock's
runner-up has 47,510 equal pixels. At the prespecified original
frame1855/native guest1856 pairing, the consumed-prime raster is
pixel-perfect after only established Snes9x RGB565 green6 -> RGB5.
Every one of the 971 changed actual native RGBA pixels is an
improvement toward original source output: all 512 split-seam pixels
and all **459** extra narrow contour/window-shape pixels. Corrected
original/native differing-pixel row list is exactly EMPTY.

Thus the narrower channel7-only pilot (#1580) remains a deliberately
unexecuted architectural discriminator: preserving stock channel5
might be less invasive but cannot be called source-faithful without
its own complete original/native raster and effective-register test.
The global first-line consumption hypothesis now has two distinct
actual full-source exact original/native 2P witnesses, guest1856
countdown and guest2208 racing. This still does not authorize a
global emulator/core fix, given upstream Gundam Wing startup behavior,
other games, all untested frames, scanline112 OAM/window routing,
1P and genuine 342-wide/4x Original presentation requirements.

The completed original experiment workflow is intentionally switched
to manual-only to prevent recurring source recompilation. All source
artifacts remain retained for independent reanalysis.
