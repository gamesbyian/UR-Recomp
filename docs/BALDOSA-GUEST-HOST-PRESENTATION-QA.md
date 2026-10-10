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

## Consolidated live-renderer integration gate (October 10)

The source of truth is `native/presentation/racer_hd_presenter.cpp`.
`racer_hd_begin_sim_frame()` explicitly refuses destructive source capture
unless `racer_hd_can_capture_frame_geometry()` accepts the scene, and
`racer_hd_draw_frame()` currently accepts **256×224** only. At genuine
**342×224**, the registered per-slot 96–99 OAM extraction is strictly
read-only, uses `RemoveFromGame=0`, and leaves the stock Original raster
untouched. The positive six-frame stock/4× widened captures therefore
**cannot** be credited as widened HD substitution.

PR #1144 (merged as `e9338cd`) extends the existing four OAM-slot
native processes to independently verify moving frames **1856, 1872,
1888**. Both temporal intervals are `observed-not-admitted` and set
`safe_to_destructively_replace_original_obj=false`. Source-only OBJ
alpha is upstream of the final BG/window composite; neither alpha nor
a footprint hit determines which rider should cover a given pixel.

**Integration decision:** preserve the first-party 342-wide world
materializer, stock raster, 4× presenter and Modern output composition.
Do not remove the 256-wide destructive-admission restriction merely to
make Remastered appear in widened scenes. The smallest legitimate new
renderer path must first establish a final-composite, per-slot
source-visible mask or equivalent proven paint ownership for both P1/P2,
including negative X, Y wrap, split seam, foreground overlap and the
case of a source-empty rider. If attribution fails for either affected
rider, retain the entire Original frame before removing any guest OBJ.
Reuse the three-frame/four-slot native evidence as an inexpensive
regression gate, and use the existing 2,473-frame route once for a
complete live validation rather than rerunning it for each hypothesis.

Acceptance must report **separately**: (1) unchanged guest WRAM CRC and
controller progression, (2) independently verified PPU/OAM source
emission and final visibility, (3) visible authored HD substitution only
on authorized riders and exact Original fallback otherwise, (4) correct
course-derived extra-world pixels at 342×224, and (5) actual final
drawable geometry and 7:6 PAR. Framebuffer density at 1368×896 does
not count as physical 3840×2160 evidence. The latter requires a
separately captured real SDL/desktop drawable, as specified by
`BALDOSA-PHYSICAL-4K-CAPTURE-ORACLE.md`.

Product integration should consume an existing presenter/output hook,
with presentation mode selected externally. Never transfer Modern
navigation, profile state, replay/ghost authority, event progression,
or guest result decoding into this renderer.

## Independent opt-in live-scene world expansion gate

The Baldosa world bridge historically widened only guest frames
1800..2450, which proves one scripted two-player interval but cannot
serve general moving-gameplay presentation. With
`UR_BALDOSA_WS342=1 UR_BALDOSA_WS342_LIVE=1`, the same existing Modern
`observe_widescreen_scene()` rule now reads guest `$7E:0313` and
`$7E:009F` and admits calibrated 342-wide course-derived pixels during
recognized active 1P/2P/VS races **regardless of frame number**.
Pre-race, results, unknown scene modes and failed calibration keep the
unmodified 256-wide Original fallback. The recognized scene plus
calibration decision is latched during `prepare_frame()`, not
independently re-inferred during the host's later draw callback.
Without `UR_BALDOSA_WS342_LIVE`, the old 1800..2450 bounded route
and its existing acceptance oracles remain unchanged.

The compiled production-bridge stub tests cover an unknown active
state, 1P setup/race/results, VS setup/race, rejected calibration,
all 1×..4× densities, the 342-wide edges and 112-line split.
The import adapter links the already-owned
`widescreen_output_composition.cpp` rather than implementing a
second scene classifier. This extends a real live presentation
**integration seam**, not proof of complete 1P/VS rendered routes:
those require a follow-up native capture, guest CRC equality and exact
Original raster oracles before enabling it by default. It does not
authorize wide authored HD OBJ replacement or physical 4K acceptance.

The opt-in live bridge additionally clears its 1P/2P/VS latch when the
settled frontend `$7E:009F=0xD7` is reached outside racing, and clears
prepared-wide admission at the start of every frame preparation, including
invalid-call failure. These safety controls prevent a stale prior event or
failed prepare from requesting guessed widened pixels on a later callback.

## Native live 1P observation (new validation route)

The 342-wide Baldosa host now samples the established Modern race-mode latch
on **every guest-frame callback** as well as during present preparation.
Scripted turbo guests can skip the entire pre-race desktop scene, so an
observer tied solely to `prepare_frame()` can miss real 1P/2P/VS selection
and incorrectly stay 256-wide for the subsequent event. The scene classifier
is still the one first-party implementation; the extra observation performs
no WRAM or PPU writes. The compiled bridge regression simulates a real
pre-race `0x3D` guest frame without a desktop preparation, then requires
the subsequent active 2P frame to widen. A settled frontend still resets
the latch.

The **existing Baldosa AOT native job**, with no additional AOT build, also
runs its already-imported genuine `race_1p` route once under the explicit
`UR_BALDOSA_WS342_LIVE=1` opt-in. It compares the complete native guest
CRC sequence to the independent original 1P run already in that job and
retains the pre-race mode sample, native preparation/present evidence, and
any genuine 342×224 captures. It distinguishes a real widening witness
from a calibrated-source or sparse-host-presentation blocker.

This diagnostic never awards release acceptance merely for a valid mode
latch or a screenshot: moving 1P world pixels, per-rider source/foreground
priority, Original-vs-HD parity and physical 4K output remain independent
requirements. The preexisting 2P 1×/4× and per-slot experiments remain
unchanged, and the live 1P flag is explicitly cleared before they resume.

## Native live 1P evidence and 4× cross-process parity (October 10)

Baldosa AOT workflow run
[38035461017](https://github.com/gamesbyian/UR-Recomp/actions/runs/38035461017)
reported `UR_BALDOSA_WS342_LIVE_1P observed-live-widening`, **5,447**
guest frames with exact stock-route WRAM CRC identity, a real pre-race
1P mode witness, **46** wide frame preparations, **6** native
342×224 desktop presents, and **6** saved complete original-density
PAM rasters. This settles whether the live 1P scene classifier can
produce real widened world pixels; it does **not** settle source-pixel
movement, 4× parity or any HD/depth question.

The same existing pinned AOT workflow now obtains an **independent**
live 1P **4×** route, preserving the same guest CRC and demanding
same-guest-frame all-pixel nearest identity via the preexisting 342-wide
density parity oracle. The original 1× source report also records
per-half/side margin differences and distinct captured images; a static
menu frame cannot masquerade as moving-world evidence. If shared
physical presentation frames are unavailable, the exact-pair oracle
fails rather than inventing host renders. The production-safe source
OBJ guard and existing bounded 2P observations remain unchanged.

Passing this evidence proves native logical source/density consistency
at the original pixels, not actual SDL 3840×2160 device capture,
independent original-emulator visual parity, authored widened HD
admission, or correct source-visible BG/OBJ priority.

## Native VS live-world execution and cross-density acceptance

The independently observed live 1P run at
[38054120133](https://github.com/gamesbyian/UR-Recomp/actions/runs/38054120133)
reported 5,447 guest frames, real 1P mode, 46 wide preparations,
6 source-wide captures with moving-world evidence, and **6/6 exact
same-guest-frame 1×/4× pixel matches**. That is live native scene evidence,
not a claim of authored HD replacement or complete result parity.

The next bounded QA-08 lane runs Baldosa's **actual upstream VS script**
(`baldosa/tests/routes/vs.txt`) three times using the same compiled
native host: a 256-wide, HD-disabled stock control, a live 342-wide
Original 1× candidate, and a live 342-wide Original 4× candidate.
Both candidates must match the stock route's entire frame-by-frame
WRAM CRC stream. The 1× native log must observe guest VS selection
(`$009F=0x3E`), and the two wide candidate processes must contribute
at least two same-guest-frame full-raster images with exact all-pixel
1×/4× parity and changing content. Sparse host presents cannot be
manufactured; a missing witness fails this acceptance.

This integrates the established scene classifier and calibrated world
extension into another genuine moving game mode without modifying
the guest, ROM, profile ownership, HD OBJ priority rules, or the
existing 2P evidence. Passing still would not prove terminal VS results,
per-rider HD occlusion, independent original-emulator screenshot parity,
or actual physical 4K output.

## Native ordinary two-player guest-scene parity

The live world gate now also runs the real `race_2p_split` script
independently at 342×224 Original 1× and 4×, against the already-run
original 256-wide 2P baseline. This is **not** the bounded
1800..2450 comparison: the guest must actually select ordinary 2P
(`$009F=0x3D`, distinct from VS 0x3E) before racing.
Both native candidates must retain the full baseline guest CRC stream;
the already-shipping all-pixel 1×/4× comparator requires at least two
identically numbered presented frames with different source imagery.

The existing 1P and VS live-world passes, bounded 2P (+43 margins)
source-sprite extractions, and production-safe HD overlap gates remain
unchanged. Still not certified: authored wide HD OBJ compositing or
foreground priority, independent original-emulator complete-result
fidelity, and physical 3840×2160 output.
