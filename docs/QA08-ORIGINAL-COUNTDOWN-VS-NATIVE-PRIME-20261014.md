# QA-08: original two-player countdown source versus the HDMA prime experiment

**Source adjudication requested October 14, 2026; until original Snes9x
run completes, no original countdown result is claimed.**

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
