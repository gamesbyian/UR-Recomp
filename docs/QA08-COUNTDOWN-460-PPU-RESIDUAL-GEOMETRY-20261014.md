# QA-08: residual countdown source-PPU contour geometry, not HDMA channel proof

**Executed real original/native 2P source observation, 2026-10-14.**
The genuine full-256x224 original Snes9x countdown callback1855 is
57,344/57,344 RGB5-identical to the disposable global first-line
consumed-prime native PPU guest1856. The ch7-only and ch5+7 variants
remain 460 pixels different from *that same original*, although both
repair the stock split brightness seam. This is the real four-process
source negative in #1595, not a synthetic renderer demonstration.

The independently re-inspected 4-process source archive is
run 38642367882, artifact 11930109109, ZIP SHA256
a6aae4f82644c93b43f98f336d72c21d24846fea5f8377e18cbc54e37c1b3040.
The independent original-countdown Snes9x archive is
artifact 11925517895, ZIP SHA256
56ec0011a3559f5953578c495d080d0150f2a06fb7a76c2e437fab781e2b2ce6.
The actual P7 full source sha256 is
ed35731cde55e927165f173c1db29c27db3467cb8bc87 for
global prime and f717a2841b6fbc8497b601f75db24d7c36c750bba5df4f6f41258a127ddf94fb
for both ch7-only and ch5+7. All previous full route CRCs were
identical across four guests.

## Spatial morphology directly measured from all 57,344 source pixels

Comparing actual global PPU RGBA versus combined5+7 source PPU
RGBA, with **no masking, image registration or rescaling**, yields
exactly **460 changed RGB pixels**, no changed P7 alpha.
Eight-neighbour pixel connected-component analysis gives exactly
two components:

| Original 256x224 viewport | Residual changed RGB pixels | Bounding box inclusive (x0,y0,x1,y1) |
| --- | ---: | --- |
| Upper | **226** | (29,55,220,110) |
| Lower | **234** | (29,113,225,176) |

At each of two strong horizontal boundaries, y98 (upper) and
y133 (lower), the source changes total **128** pixels, with runs
x30..156 (127 consecutive pixels) and isolated x208 (one).
These are not a full 256-wide black-band discrepancy. Pixel
(223,113) is the special previously verified three-way difference:
original source BGRX FF383900, global native RGBA 3939FF00,
combined/ch7-only native RGBA 84A5A500. The actual original
black seam rows y111/y112 now contain **zero residual differences**.

The residual geometry therefore describes two very narrow expanding
and contracting contour boundaries, with half-width horizontal
discontinuities. It strongly motivates an effective scanline
window/clip/BG/OBJ composition investigation, **without identifying
which register, channel, graphics layer or executed 65816 writer
caused any particular changed pixel**. Such a silhouette can also
arise from several interacting raster sources. The native renderer
does not become production-correct merely because its experimental
global prime happens to reproduce both tested source frames.

## Source-qualified next probe

Read-only first enumerate all active HDMA channels' actually
transferred first-line A-bus bytes and destination PPU registers at
countdown guest1856 (not just existing ch5/7 guest2208 logs).
Then bind effective **per-output-row** window/clip/OBJ/BG/math
registers to the two real contour boundaries, as well as scanline112
high-OAM state and genuine final RGB. Use actual executed 65816
producer PCs and source WRAM tables before claiming an independent
channel; do not blindly apply global prime as shipping patch.
The strongest new dynamic-scene phase/pixel discriminator remains
the separately prepared genuine native guest2192/2224 source test.

The machine-readable numeric geometry and authentic source digests
are in analysis/data/qa08-countdown-460-source-residual-components-20261014.json.
The existing QA08 accepted comparator tools and original source ZIPs
are the truth source; synthetic values or a derived contour image
must never replace them. Original 256x224, 7:6 PAR, 4x genuine
fallback, real 342-wide source world and owner-vetoed Remastered
character remain unchanged. No gameplay, Modern, CPU/APU,
independent release ledger or CI scheduler is edited.

## Source-visible arrow colour and exact binary-mask discriminator

A separate complete source-array inspection establishes a **stronger
constraint than the shape**: every one of the 460 original/native
countdown residual positions is precisely a difference in coverage
of one bright-blue colour, native RGB8 **(57,57,255)**. None is a
background-to-different-background or blue-to-other-blue shade
change. The two genuine 256x224 native source masks obey:

- global consumed-prime: **9,286** such blue source pixels;
- channel7-only and combined5+7: **9,288** blue source pixels;
- intersection: **9,057** positions blue in both;
- global-only blue coverage: **229** positions;
- selective-only blue coverage: **231** positions.

The **460-pixel full RGB5 mismatch mask is exactly the XOR** of
these two source-blue coverage masks, over all 57,344 pixels,
without image padding/cropping or an excluded seam. Direct source
visual inspection identifies the graphic as the large right-pointing
blue **countdown arrow**, with the differences along its outer
triangular edge and long horizontal stem. This is evidence of
**raster coverage/displacement**, not a pixel palette equation defect.
It does not yet prove whether original guest BG scroll, BG mode,
window clipping or an OBJ effect is the effective source owner.

The next narrowly appropriate real observation therefore records
**all eight channels' genuine HDMA PPU BBUS transfers at guest1856**,
while retaining stock/global/ch7-only/ch5+7 source/guest controls.
The existing read-only all-channel observer and the single existing
native experiment runner are reused. Its output will identify
candidate source registers/transfer timing; no channel is declared
causal before its table bytes, actual executed 65816 producer and
final pixel consequence are connected.
