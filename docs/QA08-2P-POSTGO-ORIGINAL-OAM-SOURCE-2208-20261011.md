# QA-08: genuine post-GO 2P original racer source at guest2208

**Status: native evidence pending exact-head AOT.** This change adds
a **read-only** original PPU source checkpoint to an already scheduled
four-process 2P OAM isolation loop. It does not change source
painter, guest state, BG/window priority, Modern, release authority,
or admit the owner-vetoed 4× racer artwork.

## Why this is the next useful source checkpoint

Original native 2P source slots 96/97/98/99 were separately
captured at genuine USA guest1856,1872,1888 and the 2P
countdown at1872/1888 was independently adjudicated:
the original lower source pair emitted hundreds of racer pixels
but its complete **final** original 342×224 framebuffer was
unchanged after removing both lower OAM slots at those two frames.
That proved a strong *countdown occlusion* fact, not that
lower racer source stays invisible during ordinary racing.

The same existing 2P route `race_2p_split.txt` executes guest
frame **2208**, well after the race GO phase. Its complete
342×224 uninstrumented Original frame (and independently
accepted 4× Original fallback) is already retained in the
standard graphics native artifact. Previous original
1P source at2208 is a **different guest mode** and cannot
substitute for actual post-GO 2P slot ownership.

## Exact bounded change

`native/presentation/racer_hd_presenter.cpp` adds the optional
`UR_RACER_HD_WIDE_SOURCE_POST_GO_FRAME` read-only frame selector
to the **existing PPU OBJ source dump path**. It can only work
when the *already required* source slot and source output
directory opt-ins are also set; it uses the exact old
`PpuBindOverlaySurface` / `PpuSetOverlayCapture` path
with **no RemoveFromGame** flag. It does not introduce any
new mutation or player graphics mode and preserves the original
1856/1872/1888 captures.

The existing `.github/workflows/baldosa-core-spike.yml`
sets this fourth source frame to **2208** and enables
the existing late stock-frame capture during the **same four**
already-required slot96,97,98,99 isolation guest processes.
For each slot, reuse the existing
`tools/check_baldosa_wide_single_slot_source.py` with
an explicit seven-full-Original-frame threshold,
including the previously captured stock source frame2208.

The validator requires:

- An exact native stock 342×224 **guest2208** frame, and
  **independent** source-process Original output at that frame.
- Slot/frame-specific original PPU source PAM with alpha
  emission counts, bounding box, raster SHA and unique
  native diagnostic log marker, even if the source is
  legitimately empty.
- **At least seven identical complete Original capture frames**,
  no altered full 342-wide Original pixels, and independent
  complete original-vs-source 2P guest CRC stream equality.
- Four distinct source slot96..99 records with genuine
  slot/frame identity and successful output; no inference of
  final BG/window/OBJ painter or remastered admission.

The artifact gains four source reports
`ws342_obj_slot_{96..99}_frame2208.json` and the four
P7 source planes matching
`ur-baldosa-ws342-obj-slot{slot}-frame002208.pam`
through the **existing** source-plane artifact wildcard.
No new standalone build, test route, emulator or
redundant stock run is added.

Until the native AOT succeeds, **do not** claim any particular
top/bottom slot was source-positive after GO, or assign
final visible pixel ownership from a source report. A
source-positive plane establishes only original pre-priority
racer emission. A genuine source-empty plane is also a
valid observational outcome requiring a different
investigation, not a reason to invent a HD racer.

After a verified native artifact, graphics QA may compare
the post-GO source and final Original pixels, first
without changing the game or enabling authored HD overlays.
The already accepted countdown cases and Original fallback
remain intact. This work is exclusive to source-backed
original/native PPU graphics and QA-08/10.
