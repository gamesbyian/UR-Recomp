# Regional checkerboard flip preview (isolated media tool)

**Status: first-party deterministic offline prototype, not Windows runtime integration.** This uses none of the game's executable state. A synthetic render is not original game footage. [Canonical product specification](../../docs/REGIONAL-PRESENTATION.md).

## Islanding/reuse choice

The existing pinned `bsnes-plus`, `snesref` and UI-state capture/atlas tooling are sufficient to obtain a real menu reference. The original SNES window/HDMA and MOSAIC examples in PVSnesLib are research leads, not new dependencies. The MIT `gl-transitions` TilesWave shader is an algorithmic reference, but its source **has not been copied**. This is project-owned Python/Pillow code (Pillow already powers existing showcase tools). No additional emulator, shader framework, third-party vendor entry, registry dependency, or automatic CI workflow is necessary. Attribution and revisions are in `reference/catalog.yml`; the island requirements are in [the toolchain plan](../../docs/ISLAND-TOOLCHAIN-PLAN.md).

## Synthetic prototype, immediately reproducible

```sh
python3 tools/showcase/regional_checkerboard_wipe.py --synthetic-demo --outdir /tmp/ur-checker-synthetic
python3 -m unittest tests.unit.test_regional_checkerboard_wipe
```

Five PNG review frames per direction plus a hash manifest are written. Use `--all-frames` for all integer frames and `--flip-frames`/`--stagger-frames` for tunable offline timing. These are output frames, **not** a changed guest clock. Synthetic colours and grid dimensions are intentionally **not** presented as retail values.

## Real-menu calibration protocol (not yet completed)

1. Capture the settled original `MAIN_MENU` (`7E:009F=0xD7`) from the pinned ROM with the existing `analysis/ui-capture-manifest.json` and `snesref`/UI-atlas routes, retaining the exact screenshot, run/fixture/ROM identity and image SHA-256. Work in **unscaled logical pixels**, not JPEG or 1080p capture. Use existing `bsnes-plus` tilemap/CGRAM tools if cell size or palette origin is ambiguous.
2. Measure **checker tile width, height, origin/phase**, and identify an unobscured **medium-grey main-menu background pixel** by its source-image (x,y). Confirm that it really belongs to the background, rather than arbitrary UI foreground artwork. Preserve the screenshot hash and the observed source position.
3. Write a calibration manifest with the following **nonworking placeholders** (never substitute these values for measurements):

```json
{
  "schema": "UR-REGIONAL-CHECKER-CALIBRATION/1",
  "status": "measured-original-main-menu",
  "source_description": "USA ROM SHA-1, emulator pin, fixture, frame and capture provenance",
  "capture_tag": "main-menu-ready",
  "menu_sha256": "REPLACE_WITH_ACTUAL_SHA256",
  "logical_size": [256, 224],
  "tile_width": 0,
  "tile_height": 0,
  "offset_x": 0,
  "offset_y": 0,
  "grey_sample_xy": [0, 0]
}
```

4. Export both **verified same-sized full settled title frames** as lossless PNGs. Render with:

```sh
python3 tools/showcase/regional_checkerboard_wipe.py \
  --from-image /path/uniracers.png --to-image /path/unirally.png \
  --menu-image /path/main-menu.png \
  --calibration /path/menu-calibration.json \
  --direction both --outdir /tmp/ur-checker-review
```

The tool fails closed on the menu SHA, source size and grid bounds, and **samples** the grey channel values directly. The hash proves binding to the supplied image, but independent review is still needed to prove the measurement itself is authentic. The output manifest retains source hashes, sample position, RGB and per-frame hashes. It does not require network access.

## Deterministic geometry and limitations

For column c and row r, forward wave rank is `c+r`. Reverse rank is `(C-1-c)+(R-1-r)`. Each tile undergoes a diagonal-axis pinch and reopen with a **signed diagonal shear** to create an opposite corner-oriented motion in reverse. Source and destination pixels never blend; a compressed tile exposes the sampled medium grey. Cropped edge cells use the same grid alignment. The endpoints are pixel-identical to their respective input frames, and both directions share timing/geometry. This is a **stylized host-side projection** rather than a claim that original SNES hardware or Uniracers implemented the same flip. Shear/timing remain reviewable prototype parameters.

The tool works at logical image dimensions. The existing host presentation, **not this preview**, owns the 7:6 SNES pixel aspect ratio, nearest-neighbour display scale, 1×–4× density and 16:9 matte.

The ROM-free tests cover wave reversal, cropped-edge alignment, exact endpoints, no mixed RGB channels, deterministic previews, provenance mismatch failure and output hashes. A passing offline test does **not** establish feature completion: native host-only integration, secret-context gating, Authentic inertness, persisted state, input suppression policy and presenter regression coverage are separate future acceptance gates.

Keep generated images/video outside Git except a small specifically reviewed original-source witness. Never commit synthetic frames as stock footage or silently add extracted retail assets to the distributable game.
