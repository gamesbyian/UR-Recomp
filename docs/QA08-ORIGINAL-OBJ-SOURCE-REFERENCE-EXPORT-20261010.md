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
