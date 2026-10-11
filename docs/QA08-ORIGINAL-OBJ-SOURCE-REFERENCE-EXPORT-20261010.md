# Original racer OBJ source-reference exporter

**Status: tooling only.** A PNG from this tool is a lossless crop
of actual native source OBJ pixels, **not** an authored Remastered
asset, final visible framebuffer or release-ready 4× art.

Once [QA08 live 1P isolated source](QA08-LIVE-1P-0895-OBJ-SOURCE-20261010.md)
is accepted in PR #1264, download its real native AOT artifact and
run:

```sh
python3 tools/export_native_racer_obj_source_reference.py \
  --source-file path/to/baldosa-ws342-live-1p-slot97/ur-baldosa-ws342-obj-slot97-frame002208.pam \
  --validated-report path/to/baldosa-evidence/ws342_live_1p_0895_source_obj.json \
  --output-prefix path/to/qa08-p1-0895-source
```

## Actual source PPU slots98/99 at authentic 1P frame2208

The earlier accepted native source slot97 frame2208 was
entirely transparent, which **correctly yields no PNG**.
Both slots96/97 were independently source-empty in #1271.
The authentic 1P frame2208 racers occupy original PPU **raster
rows 120..143**, not a presumed 1P split viewport above y112.
The #1276 native AOT run `38097914195`, artifact `11686843233`,
independently captured source slot98 with 285 opaque pixels and slot99
with 293 opaque pixels. Distinct slot numbers alone are not a proof
of final PPU priority or gameplay-character identity. The source-bounding
rectangles are `[101,121,132,143]` and `[36,120,71,143]`.

After recovering this accepted #1276 artifact, the same exporter
can produce a genuinely source-derived source-slot reference:

```sh
python3 tools/export_native_racer_obj_source_reference.py \
  --slot 98 \
  --source-file path/to/baldosa-ws342-live-1p-slot98/ur-baldosa-ws342-obj-slot98-frame002208.pam \
  --validated-report path/to/baldosa-evidence/ws342_live_1p_top_slot98_99_source.json \
  --output-prefix path/to/qa08-1p-frame2208-source-slot98
```

Change both `--slot`, the native source PAM and output prefix
to `99` to export that slot separately. The tool explicitly
requires **five** matching original/native 5,447-frame guest
CRC streams, seven independent complete Original 1×/4× image
matches, and both individually authenticated top-slot PPU source
planes in the machine-readable report, including no source
removal and no HD/final-BG permission. A forged or swapped
source slot, changed alpha digest, partial evidence, or stale
source-Original screenshot is rejected.

An actual source-empty top slot remains **metadata only**.
Do not synthesize an HD rider to fill it, and never treat
original pre-BG OBJ alpha as final foreground ownership.

For bottom slot97 the exporter requires the exact native read-only
source metadata and original/native 5,447 CRC parity. For slots98/99
it separately requires the accepted top-slot pair report's five
complete identical CRC streams and seven Original frame-pair checks.
Every case verifies actual exact-slot/full 342×224 RGBA source-PAM hash,
bbox and alpha counts, explicit non-destructive `RemoveFromGame`
**off**, and denied HD admission.

For actual opaque source pixels it emits:

- `qa08-p1-0895-source.png` with every original pixel in the
  native alpha bounding box, including transparent RGBA bytes.
  No interpolation, palette guesses, simulated fill, contour
  smoothing, background substitution or image generation.
- `qa08-p1-0895-source.json` with original full-source
  SHA256, exact pixel bounding box, cropped RGBA SHA256, PNG SHA256,
  visible RGBA palette counts, **original opaque-silhouette profile**
  and explicit non-HD/release flags. The profile records exact binary
  alpha SHA256, scanline/column occupancy, per-row extrema and source
  alpha centroid. These are native projected 2D source-image measurements,
  not wheel/saddle anatomy or recovered 3D proportions.

If the real PPU source plane is alpha-empty, the exporter **does
not create a PNG** (and removes any stale prior PNG), instead
retaining `source-empty-no-image` metadata. Any provenance,
dimension, frame, alpha count, bbox or hash mismatch rejects.
The RGB colour under a transparent pixel remains unmodified,
and the source is not replaced by a synthetic recolour.

Use this source-only reference to compare the actual unicycle
silhouette and approve future authored 4× art *after separate
original final-BG/OBJ priority and temporal consistency tests*.
Never use the raw original 64px source crop as a fake HD
replacement or a standalone signal for destructive OAM removal.


For cross-character alpha shape review, run the existing
[`tools/art/compare_native_1p_silhouettes.py`](../tools/art/compare_native_1p_silhouettes.py)
on independently verified PPU source planes 98 and 99. At native
frame2208 their **16 exact matching opaque alpha rows** after bounding-box
left-edge translation (absolute raster y128..143) and distinct
upper-source silhouettes are recorded in
[`analysis/data/qa08-live-1p-source-alpha-alignment-2208.json`](../analysis/data/qa08-live-1p-source-alpha-alignment-2208.json).
No original source image bytes are copied to the repository, and no
current artistic or source-final-visibility acceptance follows from
shape matching.
