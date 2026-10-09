# QA-08: Live-racer OAM pixel confinement

Status: **one exact native frame tested from archived acceptance; broader motion remains unverified**.

## The question this test answers

When Remastered replaces four stock 2P split OBJ slots, does anything else
change on screen? An approved sprite silhouette and unchanged guest WRAM
do not prove that the renderer preserved the backdrop, original HUD,
split-screen seam, indicators or other player viewport.

`tools/check_racer_hd_pixel_confinement.py` requires the two independent
Original raster controls for one native guest frame to be byte-identical,
and reads the real placement log for exactly four observed split OBJ slots:
top P1/P2 98/99 and bottom P1/P2 97/96. It constructs the region where
each 64×64 sprite could actually affect the 256×224 display, respecting
signed X, 8-bit Y wrap and the scanline-112 physical split.

Outside the **union** of those live object footprints, **every** pixel
at full 1×–4× presentation density must equal the nearest-expanded
authentic Original screen. No crop, brightness tolerance, fuzzy metric or
special HUD waiver is accepted. Within the footprints, differences are
allowed because HD artwork is intentionally not pixel-identical to the
SNES raster. Both viewport halves must contain a real change, preventing
an inert fallback from passing.

## First bounded archived witness (frame 1220)

- Workflow: `37870058381`, artifact ID `11589838890`
  (`native-racer-presentation-acceptance`).
- Original A and B: both 256×224 P6, identical SHA256
  `50070a38ea149241dc917fdd2742acbafcecb68b52771781f1ac93ef4bb207d0`.
- HD frame: 1024×896 P6, SHA256
  `cf0cee7c7aa641586b5ce8f3303335305784d4c9781192beeb67155e970f57d5`.
- Host logs: four real frame-1220 objects, x=104, top y=40 and bottom
  y=153, slots 98/99 and 97/96 respectively, density 4×.
- Independent full-density source comparison: **12,252 changed
  presentation-density pixels, all inside the four live OBJ rectangles,
  zero outside**; top 6,545 and bottom 5,707. The 1× logical-center
  sample changes 765 pixels.

This establishes that on that one approved static witness, HD did not
change any pixels beyond the actual racer bounding boxes. It does **not**
certify authentic sprite-vs-foreground BG priority *inside* those boxes,
correct pixels at crossings, or coverage on other frames/courses/modes.
The original archived capture is not a freshly executed verification of
the PR's new checker; the checker and regression are supplied to make
the same comparison repeatable on future native artifacts.

## Executable acceptance

```sh
python3 tools/check_racer_hd_pixel_confinement.py \
  --original racer-original-a-1220.ppm \
  --original-control racer-original-b-1220.ppm \
  --hd racer-hd-1220.ppm \
  --hd-log racer-hd.log \
  --frame 1220 --json-out frame-1220-hd-confinement.json
```

The native 2P acceptance route should invoke this checker against the
same live captures. Expand to 1×/4× and later moving frames with
nontrivial X/Y and camera positions, Y=250–255, scanline-112 crossings,
sprite overlap, object edges and 4:3/16:9. Do not borrow today's
x=104 constant for new captures; OAM placement comes from the native
frame log. QA-08 L4 still requires an authentic foreground occlusion
comparison and the actual draw/fallback census.

Owner: graphics/raster presentation only. The check never writes guest
state, changes gameplay or alters art admission.

## QA-08 same-viewport source-empty raster rejection (2026-10-09)

The first source-presence fix #1040 blocked an *entirely empty* viewport,
but the previous exact-density frame comparator permitted changes anywhere
inside the union of four live OAM bounding rectangles. Two **disjoint**
riders in the same viewport were therefore indistinguishable to that test:
one could have a nonempty Original PPU source footprint while an entirely
unemitted second racer gained HD pixels inside its own valid OAM box.

When `--source-obj-layer` is supplied, the pixel oracle now evaluates
the authoritative Original OBJ alpha **separately in each signed-X,
256-wrap Y, split-clipped 64x64 racer footprint**. It builds the union
of only source-bearing footprints. Every changed density subpixel must
fall inside that smaller union; a changed pixel in a registered but
source-empty, disjoint footprint fails as
`outside_source_visible_oam_pixel_samples`, even when it would have
passed the old `outside_live_oam_pixel_samples` bounding-box test.
The report includes `source_obj_opaque_by_oam_footprint` and keeps
the existing aggregate viewport counts for historical consumers.

Synthetic **4x** exact pixel comparisons and **1x** Y=250 modulo-256
wrap comparisons deliberately inject a false second top-viewport HD
rider while preserving the independent P1 source sprite. The old
rectangle-only and viewport-only checks would have passed; the
source-authorization test must fail. No host C++ gameplay authority
or ROM state changes are needed to run this checker.

This protects only source-empty *disjoint* regions and does not
infer sprite identity or SNES priority from overlapping original OBJ
alpha. The PPU's source plane is composited across OBJ slots. Foreground
BG/window/colour math, source pixels belonging to another object inside
the box, frame-phase alignment and the final displayed priority still
need same-state native/reference evidence. The new comparator runs in
the existing exact native frame-1220 job, but a disjoint-rider **native
moving-frame** screenshot and L4 release proof remain outstanding.
