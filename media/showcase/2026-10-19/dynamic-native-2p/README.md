# Genuine dynamic widescreen 2P cinematic capture: candidate, not accepted footage

## Objective

The October 10 600-frame native race clips replay `press right+p2:right` throughout the post-GO movement. That causes two nearly co-located unicycles on visually similar flat track spans. The October 19 recruitment cut is therefore authentic but not an effective display of Uniracers' jumping, flips, twists or player separation.

This lane proposes **two genuinely independently controlled native Original-mode wide recordings** of 900 consecutive guest frames each: `p1-leads` and `p2-leads`. The captured result is only acceptable if the real in-game output visibly contains different racer progress, actual airborne moments or rotation, and both correct split-screen cameras. Avoid any editorial simulation of different locations.

## Available reusable implementation

- `tools/showcase/build_dynamic_2p_routes.py` takes the **exact pinned Baldosa** `tests/routes/race_2p_split.txt` source, retains every boot/menu/racer selection action and actual GO gate, then applies two different independent-controller routes only after GO. It refuses unexpected source grammar and keeps normal game speed in footage.
- `tools/showcase/stage_continuous_native_capture.py` is the existing disposable, read-only SDL2 `SDL_RenderReadPixels` FFV1 recorder; no guest code, physics, track or rendering changes.
- `tools/showcase/validate_continuous_native_capture.py` independently checks an exact 900-frame ID index, successfully completed FFV1, real guest CRC equality with the **same script run without recording**, native host logs and immutable ROM/source identity.
- `tools/showcase/audit_dynamic_native_2p.py` checks each MP4's decoded 900-frame 1080p/60-fps output, lossless source SHA, control/recording CRCs, both source-frame IDs, immutable route source SHA, and ten independent decoded images per variant. It generates separate visually reviewable contact sheets.

The official SNES manual identifies `B` as jump, `L/R` as airborne flips/rolls, `A` as airborne twist. **These are controller attempts only.** Success, actual air time, stunt execution, clean landing, course type and satisfying separation are unknown until actual video review. Route profiles deliberately let one player move ahead alone, then bring the other into play and alternate jump/stunt pulses, rather than having synchronized continuous inputs.

This is **Original-mode 342×224 actual world geometry**, not authored HD Remastered racers or runtime physical-4K movie capture. The 1920×1080 result, if produced, is only the 960×540 captured SDL drawable delivered via nearest-neighbor doubling.

## Reproduction command for a permissioned native runner

### Single-command bounded runner

After checking out this UR-Recomp branch and the exact pinned Baldosa checkout (with its pinned SNESRecomp submodule), install the existing runner's SDL2, Xvfb, FFmpeg, Ninja, and Pillow dependencies. Supply your own legally obtained USA ROM; the script refuses a mismatched SHA and does **not** publish any ROM bytes.

```bash
bash tools/showcase/run_dynamic_native_capture.sh \
    /absolute/path/to/pinned/baldosa \
    /absolute/path/to/your/Uniracers_USA.sfc \
    /tmp/ur-dynamic-native
```

The shell script stages all source modifications in the disposable Baldosa checkout, builds **once**, runs two candidate routes twice each (capture off/on), rejects any full guest-WRAM CRC disagreement, checks lossless FFV1 and 900 contiguous IDs, then writes both 15-second 1080p MP4s, 20 decoded source witnesses and two contact sheets under `/tmp/ur-dynamic-native/published`. It commits nothing. Control logs, index TSV and lossless FFV1 masters stay in `/tmp/ur-dynamic-native/working` for independent analysis and must **not** be merged as ROM-bearing outputs.

Re-use the exact successful historical native producer workflow `.github/workflows/ur-continuous-native-footage-once.yml` from source commit `4748ae337f38d801039260ca6ed849fd2ca1d7a3`. Its Linux SDL2/FFmpeg/Xvfb host, pinned upstream Baldosa, SNESRecomp framework, private legally provided ROM gate and existing native source patching are required.

Build **once**; call the route generator:

```sh
python3 tools/showcase/build_dynamic_2p_routes.py --self-test
python3 tools/select_three_project_reuse.py --lane baldosa-integration --include-conditional
python3 tools/showcase/build_dynamic_2p_routes.py \
  --source baldosa/tests/routes/race_2p_split.txt --output /tmp/dynamic-routes
```

For each generated `p1-leads.txt` and `p2-leads.txt`, use the pinned `baldosa/tools/run_route.sh` once with no recording, then a second time with:

```sh
UR_NATIVE_VIDEO_START=<calibrated-go-plus-111> UR_NATIVE_VIDEO_COUNT=900 \
UR_NATIVE_VIDEO_OUTPUT=native-p1-leads-lossless.mkv
```

Use `native-p2-leads-lossless.mkv` for the other. Capture must fail on noncontiguous IDs, process/FFmpeg termination, missing private ROM, failed identical-input control CRC, source pin mismatch or unreadable video. Then encode genuine MP4s from the FFV1 master and run `audit_dynamic_native_2p.py` using the generated controller manifest. Keep the lossless master plus per-frame TSV and full logs as bounded evidence; only source-qualified MP4s, a provenance receipt and sampled witness/contact sheets may go into `media/showcase/2026-10-19/dynamic-native-2p/`.

**No synthetic frame doubling/interpolation or editorial race-position composites** are acceptable. A 900-frame source window is 15 seconds of native host presentations at nominal 60fps. It does not certify true wall-clock 60 Hz or whole-game original-native parity. Input semantics are verified in two published scripts, but the trick visuals remain a scientific unknown until inspected.

## Video selection gate

An independent reviewer must watch both candidate clips, cross-check (a) the actual P1/P2 upper/lower frames and racers, (b) distinct source-relative track positions, (c) visible jump/trick frames and landings, (d) normal authentic racer sprites and HUD, and (e) that the 43-column extension is genuine source world. Record guest-frame start/end for 2–4 energetic sequences and explain exactly which are visually supported. Only then replace/reorder the existing close-together footage in PR #1994 or its successor.

If both candidate captures are flat or stunt inputs fail visually, report that scientific negative. The next attempt should use an independently verified different original course selection through an existing game menu fixture, **not** synthetic ramps/physics or manipulated footage.

## Current execution

The source-only scripts and workflow integration specification are staged here. The initial automatic native workflow submission was blocked before running, so no output clips or player separation claims exist as of this update. Do not merge empty video claims or claim capture success. A permissioned runner or existing team media agent can execute the above reusable pipeline. Restrict CI to one bounded build, two distinct predeclared routes and no per-experiment workflow residue. 

## Topology-specific production plan (source-grounded candidates, not yet filmed)

The [45-course canonical corpus](../../../../analysis/data/course-corpus.json) identifies the following official courses and stock family/slot combinations:

| Priority | Exact source course | Original menu tour/slot | Expected visual attraction | Evidence status |
| --- | --- | --- | --- | --- |
| 1 | **Looper** (stream 11) | Shuffler, race slot 1 | A complete, visible loop if encountered | Source course name, family and menu index only; loop passage not yet visually confirmed |
| 1 | **MegaJump** (stream 12) | Shuffler, circuit slot 2 | Rising ramp, steep takeoff, airborne racer | Real course identity; ramp and takeoff still to inspect |
| 1 | **Jumps** (stream 13) | Shuffler, stunt slot 3 | Repeated ramps and aerial rotation | Existing independent original-menu Jumps route is confirmed; 2P transition requires new execution |
| 2 | **Hill Climb** (stream 23) | Walker, stunt slot 3 | Strong slope / altitude and changing track profile | Walker is a tier-zero tour; second Down edge inferred, not proven for 2P |
| 3 | **Two Loops** (stream 42) | Hunter, circuit slot 2 | Multiple loop structures | Hunter unlock/stock navigation not verified; deliberately not scheduled |

Names are **search candidates**, not proofs that a hill, full loop or ramp is encountered in the first 900 filmed frames. The route generator `tools/showcase/build_topology_2p_routes.py` retains the exact original two-player boot/rider selection, uses stock menu edges and source-tested Crawler/Shuffler tour selection, then hard-gates `7E:009F` tour/track/now-playing, active race `7E:0313==01`, and the **actual selected course identity `7E:00CE = stream_index-1`** before GO. The 2P adaptation of those menus remains prospective until real native execution. It cannot silently substitute Dragster for a failed selection.

On a permissioned native machine already configured for the existing capture runner, the **initial three-course scout** can be executed with:

```bash
bash tools/showcase/run_dynamic_native_capture.sh \
  /absolute/path/to/pinned/baldosa \
  /absolute/path/to/owned/Uniracers_USA.sfc \
  /tmp/ur-dynamic-topology --topology
```

This produces one `looper-p1-leads`, one `megajump-p2-leads` and one `jumps-p1-leads` 15-second source-run video from a **single pinned native build**, after three pairwise control/recording full-WRAM CRC comparisons. Use `--topology-hill` for a fourth, `hill-climb-p2-leads` prospective case once the lower-cost three-course scout succeeds. The validated early menu path into Shuffler and Jumps is taken from `tools/probe_original_non_dragster_course_entry.py` and its exact original course-byte gate. There is no Hunter unlock shortcut or forced track-memory write.

**Visual admission test:** Independently verify from continuous decoded video at least one recognizable actual ramp/steep slope/closed loop, genuine racer airborne frames and physically plausible landing, camera divergence from distinct P1/P2 track progress, unaltered original HUD and sprites, and consistent visual geometry beyond the center 256 columns. Compare the scene against source video/hash and sidecar ordinals. A name containing 'Jump' or 'Loop' and a button press never establishes the event occurred. If the segment shows no visible topology, retain the negative and extend the *genuine* source recording through that course before changing the editorial storyboard. Do not fabricate a loop, stitch unrelated players as one execution or crop both racers into a falsely shared arena.


### Guest-frame alignment across different courses

The original SDL2 framework prints `script f=<frame> dump cinematic-go ok` from its native `ScriptDump` method. The capture runner now parses the single source-control GO clock and captures **900 consecutive original guest presentations** starting at `max(1990, go_frame+111)`. It rechecks that the same GO guest frame occurs in the recorded run, verifies full-WRAM CRC equality, hashes `capture-clock-<case>.json` and requires the FFV1 sidecar's actual first/end frame IDs to equal the derived window. Fixed original Dragster 2100/2999 is not reused blindly for new course topologies. Missing, duplicated or different GO markers reject the run.

### Real independent rider track positions

The bounded post-GO routes now emit three read-only scene dumps (`cinematic-lead`, `cinematic-middle`, `cinematic-late`) from the actual native guest. The existing framework's `dump` command consumes **zero simulated frames**. Its genuine 128KiB WRAM image contains P1 and P2 world X at `7E:0411/0413` and world Y at `7E:0415/0417`, independently recovered in the project's original/non-Dragster course entry probe. The verifier checks exact semantic dump guest frame IDs, **byte-identical full WRAM in capture-off and capture-on runs**, and retains the source X/Y words, raw differences and original state hashes in the publication manifest. No game-memory editing is performed, and raw WRAM images stay outside the repo. Raw X/Y differences are not course-geodesic distances or proof of airborne rotation. They are concrete evidence the two riders actually moved independently, complementing the necessary visual-screening gate.

## Fail-closed final hill + loop + ramp highlight montage

`tools/showcase/assemble_authentic_topology_reel.py` assembles a 1080p, 60fps **silent, editorial hard-cut montage of real footage only**, but refuses to create a video until a separate authenticated source capture and substantive independent visual review both exist.

The reviewer provides a JSON manifest conforming to `UR-DYNAMIC-TOPOLOGY-VISUAL-REVIEW/1`. It records an actual identifiable hill, loop and ramp seen in three **distinct** captured original courses, a named visual reviewer and honest observation method, real native video SHA256s, chosen source ordinals and frame counts (180–420 each), on-screen separate riders, retained full 2P view and an observation explaining concrete geometry and racer movement. Three real guest read-only position witnesses must also exist for every route, including an actual P1/P2 raw coordinate difference of at least 32 world units (a raw displacement witness, not proof of separate course-arc locations). A course's *name* or scripted B/L/R presses cannot substitute for visual evidence.

Only after verifying the same real 900 consecutive native source frames, manifest SHA and written independent observations will this work:

```sh
python3 tools/showcase/assemble_authentic_topology_reel.py \
  --ledger /tmp/ur-dynamic-native/published/dynamic-racing-provenance.json \
  --review /tmp/ur-dynamic-native/accepted-topology-visual-review.json \
  --out /tmp/ur-dynamic-native/true-hill-loop-ramp-reel.mp4
```

The tool first checks the review without encoding when `--out` is omitted. It then source-hash verifies each MP4, trims *exact original frame ordinals* (no optical interpolation), joins the visibly separate course shots and checks the emitted total decoded frame count, writing an immutable source/shot/output SHA256 ledger alongside the film. It cannot silently pull from an unreviewed course or mislabel ordinary track as a loop. The recipe's raw footage remains unchanged. Trailer #1994 can source these highlights only **after** this independent acceptance.

**As of the source-only PR, no legitimate review manifest or rendered hill/loop/ramp reel exists.** A permissioned native runner with a legal original ROM and actual visual source footage is indispensable; a fake acceptance manifest would violate the project's evidentiary policy.
