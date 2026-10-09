# QA-08: Foreground BG priority and isolated OBJ counterexample probe

Status: **diagnostic-only candidate detector; no original sprite-priority claim or player shipping admission**.

## Known problem

The current Racer HD host compositor paints the authored racer above
a *flattened* original PPU framebuffer. This preserves deterministic
guest animation, size/position, X/Y transforms, split-OBJ ownership
and the raster outside each racer footprint, but the original SNES
priority chain may place BG1/BG2 tiles, another OBJ, or color math
in front of particular parts of the racer. A 256×224 frame with a
correct HD replacement *position* can therefore still be visually
wrong at overlaps inside that bounding box.

The pinned SNESRecomp `docs/HOST_OVERLAY_EXTRACTION.md` explicitly
states that host promotion of scenery/OBJ beneath foreground pixels
needs a priority-aware plane export or intermediate compositing
seam. Do not infer this missing behaviour from one successful HD
pose or a 4× stock-pixel containment test, which allows any changes
*inside* the racer rectangle.

## Opt-in original-renderer layer witness

The existing PPU already writes a transparent ARGB32 copy of the
captured racer OBJ plane into `g_obj_overlay` when the exact
two-player HD presentation is armed. The new
`UR_RACER_HD_OBJ_LAYER_PAM=<path>` plus
`UR_RACER_HD_OBJ_LAYER_FRAME=1220` diagnostic exports this
read-only isolated layer as a 256×224 RGBA PAM/P7 file on the
specified presented frame. The output contains alpha, literal
RGB and exact logical positions; no simulation or VRAM write,
intermediate graphics policy mutation or rendering API change.
No opt-in means no file I/O.

The independently captured Original-A/Original-B 256×224 PPM
frames are the control, and the 4× HD screen is the treatment.
`tools/check_racer_hd_foreground_occlusion.py` analyzes the same
guest frame using the four live split-OBJ OAM placements. For each
opaque isolated OBJ pixel inside the actual racer footprints:

1. If isolated OBJ RGB exactly equals Original screen RGB,
   it is a direct Original-colour visible candidate. Whether HD
   changes it is tracked separately, as this is the expected art
   replacement situation.
2. If isolated OBJ RGB **differs** from the Original screen RGB,
   foreground BG priority, subscreen color math, another OBJ or
   other compositing effects *may* be responsible. This is an
   **ambiguous original-layer discrepancy** until attributed by
   an independent renderer-priority witness.
3. If HD **also changes** that ambiguous pixel, record a
   `potential_foreground_occlusion_overpaint_pixel` for targeted
   reference investigation. These are candidate bugs only,
   not proof that a BG tile should obscure the racer.

The diagnostic keeps the alpha channel, original control hash
discipline, exact 1–4× per-subpixel comparison and live split
scanline/X/Y wrap. It refuses missing layer data or mismatched
Original controls.

## Suggested exact 2P native capture

```sh
UR_RACER_HD=1 \
UR_RACER_HD_OBJ_LAYER_PAM=/tmp/racer-obj-1220.pam \
UR_RACER_HD_OBJ_LAYER_FRAME=1220 \
  ./UniracersSNESRecomp <retail-USA-ROM> --script <ordinary-2p-script>
```

Then:

```sh
python3 tools/check_racer_hd_foreground_occlusion.py \
  --original racer-original-a-1220.ppm \
  --original-control racer-original-b-1220.ppm \
  --hd racer-hd-1220.ppm \
  --obj-layer racer-obj-1220.pam \
  --native-log racer-hd.log --frame 1220 \
  --json-out racer-foreground-candidates-1220.json
```

*The precise reference/input/artifact/run SHA must be recorded before
any conclusion.* Initial frame 1220 may have no foreground-obscured
racer pixels, so probe additional frames near course objects, other
racers, vertical motion, split seams and overlap-heavy sequences.
Instrument only exact-approved native HD frames and use unchanged
independent stock screenshots at matching guest state.

## Stop condition for accepting foreground depth

A meaningful QA-08 L4 result needs a representative course/motion/
viewpoint census of **the actual native host output** compared
against authoritative stock rendering, plus a demonstrated
priority-aware correction whenever a foreground sprite or BG layer
should obscure any part of the HD racer. Explicitly distinguish
BG priority, main/subscreen color math, other OBJ depth, windows,
and still-unregistered poses. This probe creates the first
narrowly testable candidates but does not itself repair renderer
ordering. Zero candidates on one static frame is never whole-game
occlusion acceptance.

Ownership: racer renderer, host-only graphics and split-screen
raster. No menus, progression, gameplay, persistence, packaging or
CI optimization.
