# QA-08: original 2P rendered-frame window, first direct visual alignment discriminator

**Instrumented original experiment, not native pixel parity yet.**

The repository's pinned `snesref` original-USA run already reproduces the
authentic controller script, original frame1989 GO, original t480 frame2473,
original 55 fetched opcode bytes, 18 executed palette writer PCs, 2
actual selector indices and 96 genuine live PPU $2131/$2132 writes.
The original emulator is separately from Baldosa SNESRecomp's
native guest2208 PPU. The previous 256×224 `go` and `t480`
original screenshots cannot identify a pixel match to a 342×224
native source capture in a *different race phase*.

## New observation: 37 frame window without changing guest inputs

The **existing one-run** original Snes9x workflow now enables the
already implemented `SNESREF_FRAME_DUMP_*` read-only video callback
for **zero-based callback indices 2188..2224**, inclusive, at every
frame. Crucially, `SNESREF_FRAME_DUMP_NATIVE=1` records the actual
core-reported dimensions. The source front-end labels an emitted
`frame_002188_256x224.raw` with its *pre-increment*
`g_frame` while the script's `retro_run` count is one-based,
so that file records original script-run frame **2189**.
No guessed `0/1` compensation may be applied downstream.

The existing real original script is *identical* byte-for-byte;
the video callback changes only retained output, not controllers,
WRAM or any PPU/HDMA register. Expected total is 37 × 256 × 224 ×
4 bytes, with no ROM or SRAM archived. Every full raw BGRX
frame is SHA-256 verified in a compact manifest and six
literal original coordinate samples are retained for later
spatial discrimination.

Run `tools/qa08_auth_original_2p_frame_window.py` requires exactly 37
genuine 256×224 raw frames (no extras, missing, or silent hi-res
crop), valid four-byte BGRX pixels, at least five distinct
full-frame hashes, source USA ROM/script/final-WRAM fingerprints,
unchanged 55 original opcodes and 18 real writers, actual original
96 HDMA colour writes and independent GO source image metadata.
Adversarial unit tests reject source reordering/cropping,
stale/all-identical video, alpha contamination, fake original frame
and forged original ROM/input/live register certificates.

The originating accepted native 2P frame2208 available from
the existing QA-08 native artefact is a different
**original-source-sized 256×224 framebuffer** as well as a
widened 342×224 source PPU image, so it can be compared directly
against each original 256×224 candidate **without any arbitrary
+43 crop** in the first pass. Then separately compare actual
guest HUD clock and stable course features, the upper/lower
racer pose and traceable WRAM camera and racer state before
declaring matched phase/input or an output pixel discrepancy.

This makes original source output independently testable, but
`frame_002208` having the same numeric suffix as native
guest2208 is *insufficient* proof of identical game state.
The original Snes9x retains a historical Uniracers-specific OAM
workaround; all conclusions describe original emulator observations,
not physical SNES cycle or HBlank acceptance. Continue independent
2P split sprite owner/source and 26 native BG3/OBJ comparison,
preserving 256×224, 7:6 PAR, exact 4× fallback, real
wide-world materializer and HD art aesthetic veto.

## Independent source-size native reference comparison

`tools/qa08_rank_original_native_2p_frames.py` requires exactly
the SHA-pinned **native guest2208 256×224** original-source image
`baldosa-fixed-source/ur-baldosa-original-source-002208.pam`
from native run **38504531564** (artifact **11867072862**),
P7 SHA-256
`a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f`.
This is distinct from the native **342×224 wide-world frame** and
therefore requires **no invented horizontal +43 crop**. It rejects
any other native asset bytes and also authenticates the original
37-frame source manifest, each raw frame's reported SHA and the
existing true native 2P route/guest CRC receipt.

The original BGRX8888 bytes and Baldosa native RGB_ALPHA P7 bytes
both encode RGB values; their fourth bytes are different and are
**ignored** for an unscaled RGB-only comparison. The offline tool
reports the exact fraction of equal 24-bit RGB pixels and channel
absolute differences across the whole frame, upper/lower play
regions and split edge. Rankings are diagnostic candidates,
not guest input parity, pixel acceptance or a promise of the same
scene. In particular, it does not add a pixel shift, solve camera
registration or treat frame-number equality as phase equality.

```sh
python3 tools/qa08_rank_original_native_2p_frames.py \
  --original-window /path/to/qa08-original-source-window \
  --original-manifest /path/to/qa08-original-37frame-window.json \
  --native-256-p7 /path/to/ur-baldosa-original-source-002208.pam \
  --native-evidence analysis/data/qa08-original-native-channel5-hdma-coldata-source-handoff.json \
  --out /tmp/qa08-original-native-rgb-candidates.json
```


## Full-original pixel motion census: next independent 2P scene selection (2026-10-14)

The already accepted original Snes9x run [38543766102](https://github.com/gamesbyian/UR-Recomp/actions/runs/38543766102)
artifact 11884155561 was **re-read**, not rerun. The entire source ZIP
SHA256 6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3
and its 37-frame manifest SHA256 29856fa4f13bfc679b60240de80bd48b8c035801b56e0fbb3e17472a06836787
match the previously accepted original. Every individual 256×224 BGRX
source frame SHA also matches the manifest, and RGB565 channel expansion
is individually checked. No framebuffer alteration, crop, invented PPU
callback or guest input occurred.

The original-only source sample candidates use original callbacks
**2191, 2207, 2223**. The **proposed** native guest sampling frame
numbers would be 2192, 2208, 2224 respectively, based on the previously
accepted *2207→2208* pair. The proposed earlier/later mappings are
**not independently proven**. They are candidate follow-ups only if
the unchanged native host actually presents those frames and their
route/controller/guest phase checks pass.

| Authentic Snes9x callback pair | Top visible original RGB changed (rows0–110) | Split rows111–112 changed | Bottom rows113–223 changed | Total changed of 57,344 |
| --- | ---: | ---: | ---: | ---: |
| 2191↔2207 | 18,257 | 0 | 17,248 | **35,505** |
| 2191↔2223 | 13,021 | 0 | 16,069 | **29,090** |
| 2207↔2223 | 15,440 | 0 | 20,715 | **36,155** |

This establishes that the two proposed additional samples are
**genuinely visually different moving 2P original scenes** with
large changes in both viewports, not duplicated render frames or
only a split-seam change. It does *not* attribute these differences
to rider animation rather than scrolling scenery, specific OAM
pixels, camera shift, course progression or HUD state.

Reproducer:
\`python3 tools/qa08_rank_original_postgo_motion.py --original-zip /path/to/accepted-original-artifact.zip --out /tmp/qa08-original-moving-diversity.json\`.
The strict source report is
[\`analysis/data/qa08-original-postgo-moving-frame-diversity-20261014.json\`](../analysis/data/qa08-original-postgo-moving-frame-diversity-20261014.json);
synthetic test inputs cannot earn native pixel acceptance.

**Next useful source-grade experiment:** extend the existing three
read-only native PPU capture selectors within the same original USA 2P
route (without adding duplicate game/CI factories) to capture
additional guest2192 and2224 256×224 frames *when presented*.
Reapply the pinned real-original RGB5 comparator against original
callbacks2191 and2223, retaining guest CRCs, effective channel-5/7
and OAM split source. On any missing native frame, reject the trial
rather than fabricating an image or accepting nearest captured time.
Reconcile global-prime versus channel-7-only findings from the
independent current discriminator before selecting a production
renderer correction. Nothing here grants an HD art or Widescreen
sprite replacement admission; original 256×224, PAR7:6 and genuine
4× Original remain invariant.


## Disposable native moving-source selector, ready for the next genuine AOT

The optional source-only staging tool
[qa08_patch_extra_original_source_capture.py](../tools/qa08_patch_extra_original_source_capture.py)
attaches **two additional exact read-only Original PPU source selectors**
to the already present Baldosa host callback. It validates unique
pinned source anchors before editing a *disposable checkout*.
The two new opt-ins are
UR_QA08_ADDITIONAL_SOURCE_FRAME_A=2192 and
UR_QA08_ADDITIONAL_SOURCE_FRAME_B=2224. Any other value does
not trigger the new capture path. The unchanged already-shipping
host source is not modified by the repository change itself.

This method reuses the real source draw callback, exact 256x224
source-field guard, guest frame identity, existing P7 binary
writer and existing QA08 accepted-CRC route. It does not
synthesize absent frames or use 342-wide presentation cropping,
does not change a pixel in the source renderer, and leaves
Original, 7:6 PAR, 4x fallback and widened geometry untouched.
Negative/source-drift tests reject altered anchors and duplicates.

**No native output from 2192 or 2224 is claimed here.**
The patch must be used within a future independently executed pinned
2P AOT job and must verify that *actual frames* were presented and
retained as genuine original-source-sized P7, with exact guest CRCs,
before using original Snes9x callbacks2191/2223 in source pixel
comparisons. Source-frame phase remains unproven for these new
candidate pairings. Avoid rerunning this expensive AOT until
the separately executing channel5+7 HDMA discriminator is classified.
