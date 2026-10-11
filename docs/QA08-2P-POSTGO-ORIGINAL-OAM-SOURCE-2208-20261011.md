# QA-08: genuine post-GO 2P original racer source at guest2208

**Status: accepted native AOT [38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291), artifact `11695173178`; first tested head `4e9cef954c4ed7c387c2ae5b3db419a09452620e`.**
All four source-only probes and seven full Original frame controls passed. The
subsequent one-line workflow diagnostic change merely replaces a hard-coded
print label with the *source-validated* frame ID, satisfying the existing
automatic workflow policy test; it changes no source gating or guest route. This change adds
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

## Native source-positive witness

The exact native original 2P guest2208 returns **all four source slots
nonempty** with independently passed log/SHA/CRC and seven stock
Original controls. Source bounds are **inclusive** native logical
342×224 pixels:

| OAM source slot | Viewport | Source alpha | Source bbox [xmin,ymin,xmax,ymax] |
| --- | --- | ---: | --- |
| 96 | lower | **313** | [107,159,136,190] |
| 97 | lower | **317** | [94,159,123,190] |
| 98 | upper | **317** | [107,47,136,78] |
| 99 | upper | **313** | [120,47,149,78] |

Every independent source report refers to the same unchanged
post-GO full Original `342×224` RGBA SHA
`f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`.
The exact source metadata are retained in
[`analysis/data/qa08-original-native-2p-postgo-obj-sources-2208.json`](../analysis/data/qa08-original-native-2p-postgo-obj-sources-2208.json).
No ROM-derived pixel plane is checked into Git.

The authenticated original source proves that both racers keep
emitting after the countdown. It **does not** by itself establish
final PPU BG/OBJ/window ownership. The observed source-coordinate
upper/lower registration is analyzed separately in the stacked
[#1342](https://github.com/gamesbyian/UR-Recomp/pull/1342)
without assuming the countdown translation continues unchanged.
No current 2P authored HD sprite is approved for shipping.

After a verified native artifact, graphics QA may compare
the post-GO source and final Original pixels, first
without changing the game or enabling authored HD overlays.
The already accepted countdown cases and Original fallback
remain intact. This work is exclusive to source-backed
original/native PPU graphics and QA-08/10.
