# QA-08: independent native 1P authored Remastered gameplay admission

**Status:** bounded candidate; no native acceptance until CI actually runs the
candidate. 1P Remastered may never be inferred from the earlier 2P overlap
tests, or from a correct 4× Original screenshot.

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
