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

## Reproduction request for a permissioned native runner

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
UR_NATIVE_VIDEO_START=2100 UR_NATIVE_VIDEO_COUNT=900 \
UR_NATIVE_VIDEO_OUTPUT=native-p1-leads-lossless.mkv
```

Use `native-p2-leads-lossless.mkv` for the other. Capture must fail on noncontiguous IDs, process/FFmpeg termination, missing private ROM, failed identical-input control CRC, source pin mismatch or unreadable video. Then encode genuine MP4s from the FFV1 master and run `audit_dynamic_native_2p.py` using the generated controller manifest. Keep the lossless master plus per-frame TSV and full logs as bounded evidence; only source-qualified MP4s, a provenance receipt and sampled witness/contact sheets may go into `media/showcase/2026-10-19/dynamic-native-2p/`.

**No synthetic frame doubling/interpolation or editorial race-position composites** are acceptable. A 900-frame source window is 15 seconds of native host presentations at nominal 60fps. It does not certify true wall-clock 60 Hz or whole-game original-native parity. Input semantics are verified in two published scripts, but the trick visuals remain a scientific unknown until inspected.

## Video selection gate

An independent reviewer must watch both candidate clips, cross-check (a) the actual P1/P2 upper/lower frames and racers, (b) distinct source-relative track positions, (c) visible jump/trick frames and landings, (d) normal authentic racer sprites and HUD, and (e) that the 43-column extension is genuine source world. Record guest-frame start/end for 2–4 energetic sequences and explain exactly which are visually supported. Only then replace/reorder the existing close-together footage in PR #1994 or its successor.

If both candidate captures are flat or stunt inputs fail visually, report that scientific negative. The next attempt should use an independently verified different original course selection through an existing game menu fixture, **not** synthetic ramps/physics or manipulated footage.

## Current execution

The source-only scripts and workflow integration specification are staged here. The initial automatic native workflow submission was blocked before running, so no output clips or player separation claims exist as of this update. Do not merge empty video claims or claim capture success. A permissioned runner or existing team media agent can execute the above reusable pipeline. Restrict CI to one bounded build, two distinct predeclared routes and no per-experiment workflow residue. 
