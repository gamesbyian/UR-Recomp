# Baldosa guest-frame vs host-presented HD coverage

Status: QA-08 measurement and acceptance, **not** shipping Remastered validation.

The pinned native Baldosa runner advances authoritative SNES guest frames independently
of SDL's desktop render callback. A frame where a guest's PPU source-OBJ capture
was armed **but no desktop frame was requested** is not evidence of missing
visible racer pixels. Conversely, when an actual host callback follows an
armed destructive source capture, the callback must render HD, not silently
fall back to stock after the stock sprite has been removed.

## Observed native discrepancy

In the successful native source-visibility experiment
[run 38020177899](https://github.com/gamesbyian/UR-Recomp/actions/runs/38020177899),
the default guarded Baldosa 2P route preserved **2,473/2,473** original
guest WRAM CRCs. The original conservative source-rectangle guard refused
full-pair destructive capture on **74 guest frames**. Exactly **three**
actual desktop presentations were associated with those refused frames,
and all presented **Original**. The remaining overlapping guest decisions
were not necessarily displayed at all. Counting 74 stock *host frames*, or
counting unpresented armed frames as failed HD output, would be incorrect.

The existing `tools/measure_racer_hd_live_draws.py` now explicitly reports:

- `guest_frames_observed`, `guest_frames_with_host_presents`,
  `guest_frames_without_host_presents`, plus the measured fraction
- actual `host_present_calls` (which may repeat for one guest frame)
- `armed_without_host_present_guest_frames` and frame IDs, distinct from
  `armed_with_hd_host_present_guest_frames`
- `overlap_refused_guest_frames`, `overlap_refused_with_host_present_guest_frames`,
  `overlap_refused_without_host_present_guest_frames`, and
  `overlap_refused_stock_host_present_calls`

The historical `armed_without_hd_draw_guest_frames` field remains for
backwards compatibility; it includes an armed guest with **no host present**.
Use its explicit counterpart above before inferring a graphical issue.

## Acceptance and safety boundary

The existing Baldosa AOT native CI, **not a new runner**, analyzes its
already-executed **production-safe** 2P log with that same census parser.
It requires the native guest census to agree with the 2,473-entry baseline,
positive actual host presence, explicit sparse/no-present accounting, and
consistent overlap-refused stock host outcomes. The existing guest-CRC
comparison and prohibition on archival unsafe-overlap flags still apply.

Synthetic regression covers 74 overlap-refused guest frames with only
three stock host renders, a later unpresented armed guest, a real repeated
HD host callback with one pixel witness per callback, and a fatal attempt
to present Original after destructive admission. It rejects the latter.

No claim is made that all 2,473 frames reached a window, that guest 2P
WRAM CRC identity establishes full original-emulator race parity, or that
the sparse presenter delivers safe 342-wide Remastered racer sprites,
correct BG/window priority or a physical 3840×2160 output.
