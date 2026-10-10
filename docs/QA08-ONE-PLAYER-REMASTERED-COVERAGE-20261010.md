# QA-08: independent native 1P authored Remastered gameplay admission

**Status: bounded native source-visible fixed-width 1P authored rendering accepted.** Merged #1228 exact AOT run `38089648874` (artifact `11683487886`) and independent no-new-guest pixel-locality checker #1245. This is **not** sustained in-race Remastered art, wide 342-column HD, P2 foreground priority or Windows beta approval.

## Measured starting evidence

Merged #1221 / native run \`38085717011\` preserved actual 1P source-world
\`race_1p_ur_ws342_live/log.txt\` in artifact \`11682517633\`.
This is a real, independently executed **5,447-guest-frame** 1P route;
it enters a 1P title/race scene after frame 550 and has a scripted 1P
progress marker at guest frame 1720. The Modern scene observer identifies
race mode 1, and the title-owned widescreen materializer displays authentic
1P source pixels at 342×224. Its existing HDR census shows:

- All **5,447** guest decision frames were Original fallback, with **0**
  actual native Remastered host presents in this widened 1P run.
- **2,117** frames refused \`unsupported-geometry\` while real world
  expansion was active; this is deliberate because the current safe
  authored-racer presenter admits 256×224 only.
- **3,329** frames refused \`p1-selection-or-art\`; 1 was rejected for
  overlapping source OBJ.
- The source 1P route's own 1×/4× wide Original output is pixel-exact,
  but even true physical 3840×2160 on its own does not grant authored HD.

These denominators cover **all guest decision frames**, not just the
interval after the original race start, and are not a claim about missing
asset *poses*: \`p1-selection-or-art\` combines unregistered states with
unavailable artwork. The existing code returns at the geometry gate before
checking art, so 2,117 is not a count of eligible authored sprites either.

## First native trial and controlled correction

The initial AOT run `38088295593` executed the full 1P guest without
changing any of its **5,447** baseline CRC values. The native host
reported **four** post-script-entry P1-only HD presents
(1728, 1744, 1808, 1840). Specifically:

- At **1728 and 1744**, the actual host emitted authored pixels
  (`UR_RACER_HD_PIXEL_CHANGE ... changed_from_underlay=1`),
  each with one source-visible rider instance. The pinned native PPU
  logged `top_opaque=0` and **bottom_opaque=315 / 316**. These
  were initially promising *bottom-only* source-positive compositions, and
  their retained HD images were subsequently accepted by #1228. A top-only checker would falsely miss them.
- At **1808 and 1840**, the host returned HD but
  `source_instances=0 changed_from_underlay=0` and retained
  1024×896 PAMs showing no independently proved authored pixels.
- The first strict 1P checker incorrectly treated pre-race pixel
  telemetry as a post-entry admission, ending the AOT workflow with a
  source-checker `ValueError` despite valid native guest execution.
  No graphical defect or new guest divergence was established by this
  checker error.

## First genuine native 4× source captures, inspected

The follow-up exact-head run `38088866579` passed native, unit, Modern
and hygiene acceptance (artifact `11683931484`). It retained real
**1024×896** guest-frame 1728 and 1744 P1-only HD candidate PAMs,
with unchanged full **5,447-frame** native guest CRC against the
independent stock route. Their original images are stored as
`baldosa-guarded-1p-4x/ur-baldosa-frame-001728.pam` and
`...-001744.pam`. The first classifier returned
`guarded-1p-real-art-unproven` despite a source-positive bottom
viewport because it erroneously required a **top-band** authored
pixel. The later accepted run #1228 fixed this evidence-only bug.

**Actual visual review:** both frame1728 and frame1744 still display
the huge light-purple original countdown **0** overlay, alongside
wheeled riders and the checkered starting track. The race milestone
at guest1720 therefore does **not** prove unobstructed sustained racing.
Do **not** classify these images as polished Remastered gameplay or
original-vs-Remastered source depth parity. The nearest-composed Original
and the underlying countdown overlay remain visually dominant.
Even the corrected 1P authored pixel evidence remains a *bounded
early-race* experiment, not a default product mode.

The new diagnostic also retains each actual source-PPU underlay
**after original OBJ removal** and compares it pixel-for-pixel to
the authentic native 4× authored image. A source-empty split region
must remain identical to the underlay. This proves local host
composition, but cannot reconstruct an independent untouched
Original framebuffer or prove BG/window occlusion fidelity.

The revised checker scopes all host pixels to the actual
post-script-entry interval and accepts actual changed HD pixels in
**either** host band, as long as the source footprint is nonempty,
the native 1024×896 screenshot exists and the guest CRC is identical. A new **explicit, read-only** diagnostic
`UR_BALDOSA_HD_EARLY_1P_CAPTURE=1` expands only this isolated
1P screenshot window from 1800 back to 1700; the ordinary 2P
capture window, first-party OBJ source guards and shipping graphics
mode are unchanged. Its purpose is to retain actual original/HD
raster evidence at **1728/1744**. Neither the initial red workflow
nor an HD-presented log by itself is beta/admission credit.

## Final accepted 1P measurement and strict locality

Merged **#1228** reached the exact source-safe positive state:
`guarded-1p-real-art-observed` with **5,447 / 5,447** independent
guest CRCs identical, original 1P script race entry **1720** and end
**5447**. There were **3,727 scoped race guest frames** but only
**233 actual desktop-present calls**. The guest safely armed P1-only
HD in **58** frames, and **four** HD host presentations occurred:
1728, 1744, 1808 and 1840. Exactly the first two retained images
showed genuine changed authored pixels; 1808/1840 were source-absent.

| Genuine native authored sample | Original source bottom opacity | Actual P1 bottom changed pixels | Top changed |
| --- | ---: | ---: | ---: |
| Guest frame 1728, semantic 0439 | 315 | **3,422** | **0** |
| Guest frame 1744, semantic 01B9 | 316 | **3,526** | **0** |

The accepted source-PPU post-OBJ-removal versus actual 1024×896
host image comparison preserves all **source-empty top pixels**
exactly. Its native PPU post-removal underlay hashes and full 4×
source hashes are retained in `guarded_1p_hd_source_band_parity.json`
(artifact `11683487886`).

Merged **#1245** adds an independently tested whole-raster *source
OAM footprint* oracle: every changed authored pixel must remain in
the source-derived P1 slot97/98 64×64 signed-X/wrapped-Y rectangle,
never merely the correct screen half. The independently examined
native changed-pixel bounding box was **X448..523, Y448..531**
for both real frames, entirely inside original P1 bottom slot97
at **X96, Y96**. The tests explicitly reject phantom top pixels
and out-of-slot bottom edits. No new native build was needed for
this read-only checker.

**The visual limitation is unchanged:** these are countdown-obscured
early-race samples, not visually established HD racing. The only
accepted live post-countdown 342-wide 1P frame is Original fallback;
the source/4× cross-density proof and runtime semantic art-gap ranking
are separate #1231 work in progress. The existing conservative
source-and-occlusion gates remain mandatory.

## Experiment

The native job has already compiled the Baldosa guest and first-party
racer/Original compositor. Reuse that **same binary and script** for
an independent real 1P \`race_1p.txt\` process, opting into the existing
\`UR_RACER_HD_P1_ONLY=1\` path, fixed stock width (256×224), 4× native
density, and explicit *absence* of both archival unsafe overlap fixture
flags. No extra toolchain/codegen, custom renderer or guest input route.
Require the entire native 5,447-frame guest CRC stream to match the
separately executed existing 1P baseline.

\`tools/check_baldosa_guarded_1p_art.py\` consumes the existing
authoritative per-guest admission + sparse host-present census parser,
checks original script provenance and any actual source-positive authored
pixel deltas in native **1024×896 PAM** captures. This keeps simulated
frames, real desktop draws and visibly changed original output distinct.
It will accurately retain a **zero-HD negative** if the existing P1-only
source/OAM guard still rejects all gameplay frames.

A positive is a *fixed-width 1P evidence candidate*, never consent to
enable 342-wide Remastered sprites or P1/P2 shared foreground erasure
during normal 2P gameplay. Any actual native authored image must be
visually inspected for silhouette, depth, track contact and temporal
consistency before UX/admission decisions.

## Next implementation if positive

Build narrow source-visible P1-only artwork coverage and replacement
eligibility for a real 1P event independently. Only after sprite ownership
and track priority survive source comparison should 342-wide Remastered
racer coordinates be admitted inside the existing single compositor.
Retain Original fallback at every unregistered/unsafe frame. Do not
change original game state, invent filler animation or claim release
readiness from 1P coverage alone.
