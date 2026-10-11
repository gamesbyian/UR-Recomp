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

## Actual top-viewport racer source reference (once native verified)

The earlier accepted native lower slot97 source frame2208 was
entirely transparent, which **correctly yields no PNG**.
Both bottom slots96/97 were independently source-empty in #1271.
The two visible Original unicycles sit above original scanline112,
so #1276 now tests **top source slots98/99** separately. Their
alpha and final PPU ownership remain unknown until native acceptance.

After a **successful** #1276 native artifact, the same exporter
can produce a genuinely source-derived top-slot reference:

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

The exporter requires actual source-PAM filename, complete 342×224
RGBA file, exact slot97/frame2208 native read-only source metadata,
a **5,447 original/native CRC match**, seven independent 1×/4×
source frame pairs and explicit non-destructive `RemoveFromGame`
**off**/HD unreleased flags.

For actual opaque source pixels it emits:

- `qa08-p1-0895-source.png` with every original pixel in the
  native alpha bounding box, including transparent RGBA bytes.
  No interpolation, palette guesses, simulated fill, contour
  smoothing, background substitution or image generation.
- `qa08-p1-0895-source.json` with original full-source
  SHA256, exact pixel bounding box, cropped RGBA SHA256, PNG SHA256,
  visible RGBA palette counts and explicit non-HD/release flags.

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
