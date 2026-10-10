# QA-08: two-frame Baldosa OAM-source transition classifier

The pinned native 342×224 split-screen race has one strict frame-1856 PPU
source-overlap witness. PR #1116 separately adds a second independently
verified per-slot PPU capture at frame 1872, using existing native 2P guest
processes. A second frame can disprove assumptions about stable source
visibility without being an excuse to replace unknown or obscured riders.

Run `tools/compare_baldosa_wide_obj_frames.py` only **after** each complete
frame has passed `check_baldosa_wide_single_slot_source.py` and
`analyze_baldosa_wide_obj_overlap.py` provenance checks:

```sh
python3 tools/compare_baldosa_wide_obj_frames.py \
  --before baldosa-evidence/ws342_obj_overlap_frame1856.json \
  --after baldosa-evidence/ws342_obj_overlap_frame1872.json \
  --out baldosa-evidence/ws342_obj_source_temporal_1856_1872.json
```

The comparison rejects an incomplete four-slot/two-viewport source census,
invalid counts or source hashes, duplicated/reversed frames and identical
full-Original raster hashes. It records per-OAM-slot source-alpha deltas,
whether a formerly emitting slot became empty, changes to pairwise alpha
overlap, and per-slot final-Original-versus-isolated-OBJ RGB mismatches.

**Interpretation is deliberately limited.** Original-frame RGB equality
can occur coincidentally. Nonmatching source RGB can arise from BG/window
occlusion, another sprite, color math or other presentation effects.
A difference in source counts between moving frames does not indicate a
stable pixel owner or a safe interpolation mask. Both the single-frame
analyzer and this two-frame report remain read-only diagnostic data.
`safe_to_destructively_replace_original_obj` is always false. Neither
tool independently enables authored 342-wide riders or claims physical
4K coverage.

The actual merge/acceptance gate remains the separately validated native
source-frame artifact in #1116. This helper can be merged and unit tested
independently and does not add a new native CI job or duplicate renderer.

## Native CI evidence integration

With #1116 now merged, the same pinned Baldosa job runs the pure comparator
**after** the individually source-validated original 1856 and 1872 PPU
frames. It preserves `ws342_obj_temporal_1856_1872.json` in the existing
`baldosa-native-spike-evidence` artifact, asserts all four independent
OAM slots and the exact ordered two-frame provenance, and explicitly
requires `safe_to_destructively_replace_original_obj=false`.

The first genuine two-frame run observed 157 to 244 pre-composition
overlapping source pixels in *each* split viewport, while total
isolated OBJ emission increased from 1,280 to 1,310 pixels.
At frame 1872, the older strict "front OBJ RGB always equals final
raster" condition is **unproven**, even though every slot's isolated
source and full Original frame retained exact native provenance.
That is a reason to investigate BG/window/priority candidates,
**not** to reinterpret source RGB equality as an ownership oracle.
