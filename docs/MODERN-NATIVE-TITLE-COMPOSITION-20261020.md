# Modern native title: original-source art + 16:9 host composition (2026-10-20)

**Status: review candidate; no native screenshot or human visual approval claimed.**
Exclusive lane is the *actual title screen* on the integrated Baldosa/Modern
native executable. No second frontend/window, guest writes, new game input
routing, Authentic change, or trailer assets. The five-item Modern root and
its child destinations remain distinct owners.

## Original-first art and provenance

The hero is now the game's **real** 238×81 retail title raster, not
a guessed logo or remade unicycle. `native/product/modern_title_retail_reference.hpp`
consumes the already-retained canonical
`native/product/regional_title_retail_asset.hpp` and validates the
existing source/Europe BGR FNV64 digests before drawing. The retail payload
was obtained from independently verified USA/Europe snesref captures
(workflow `37401751411`; asset `11385114202`; original USA SHA-256
`859ec99fdc25dd9b239d9085bf656e4f49c93a32faa97bd6ed478`).
No new binary art file, AI logo redraw or alternate pixel atlas was created.
Corrupt title payload skips retail drawing and falls back to the same
stock-yellow text grammar the existing Modern root uses.

A framed original title plate is centred separately for logical 342 and
256 widths, with a simple segmented floating track ribbon, the original
yellow/blue/grey hierarchy, a discreet 2D unicycle glyph motif below the
plate, an always-readable controller prompt and a short reveal/exit motion.
The lower motif is an **unapproved visual candidate**, not HD playable
rider art. Human review may reject/reposition it without changing source
bitmap identity or gameplay. The original 16×16 BG2 glyph atlas and animated
3D arrow raster remain unbound; no claim of finished original-type fidelity.

## Real host / controller integration

`tools/baldosa_modern_profile_activation_spike.py` modifies its already
pinned native `SnesDesktopHostGame` descriptor to use its existing
`native_widescreen`, `prepare_frame` and `compute_viewport` callbacks.
Only a visible Modern title/root asks for a logical **342×224** field. With
original **7:6 pixel aspect ratio**, that source is a physical ~16:9 frame.
No 256-wide guest screen is stretched to fake a widescreen title.
Active stock guest setup, races, results, and all Authentic output keep their
original guest viewport. The source presents a separately authored fixed
256×224 fallback rather than cropping the 342 raster.

`native/product/modern_title_presenter.hpp` runs without SDL, guest state,
save or profile authority. Boot enters `Intro`; an edge-triggered native
P1 A/Start or keyboard Enter begins the `Leaving` phase. After 14 native
guest-frame ticks the existing root owns the screen. Other input is
swallowed while title is active. Root's existing physical input latches
track presses/releases; holding A/Start across the handoff cannot
activate Play without a fresh physical edge. Returning to root from a
real observed stock main menu skips the title to avoid a repetitive boot
sequence. Earlier native smoke modes 1..14 intentionally start directly
in the old root so their proven route signatures remain stable. Mode 15
enters through the actual title using the real native P1 semantic pad
handler, presses A at frame 60 and lets the title transition to root.
Source scripts never write `g_ram`, guest input words or stock menu IDs.

## Real frame capture route (not simulated evidence)

For native capture, supply an existing writable directory in
`UR_BALDOSA_MODERN_TITLE_CAPTURE_DIR` when launching the **real**
Baldosa Modern candidate. The first title frame with age >=40 and the
first root frame after title confirmation are written once each as:

- `modern-native-title-342x224.pam`
- `modern-native-root-342x224.pam`

An original/fallback 256-width output uses `256x224` instead. Each
P7 RGB_ALPHA file is a *host source pixel raster*, accompanied by a
`UR_BALDOSA_MODERN_TITLE native_capture=1` line containing observed
guest frame, dimensions, actual RGBA FNV1a64 and path. These captures
do **not** certify final SDL drawable pixels, GPU present, a physical
monitor, real gamepad or an accurately scaled 4K Windows build. The
independent #2041 manifest/auditor owns the exact-executable, final-output,
positive/negative and human-review envelope. A file path or log alone
does not satisfy that audit.

## Tests, competition with other visual lanes and acceptance

The C++17 painter test is `tests/native/modern_title_presenter_test.cpp`.
`python3 -m unittest tests.unit.test_modern_title_presenter_cpp` compiles it
and verifies both source-retail digest-correct art variants on *real* 342
and fallback 256 source buffers, bounded drawing, controller transition
phases, and Authentic-gated native host hooks. The existing
`tests.unit.test_baldosa_modern_profile_activation_spike` covers the
pinned C descriptor's safe transform and refusal of competing compositors.
The full exact-candidate native Windows build, 342-source/1080-display
screenshots, Authentic comparison, keyboard/physical-pad ownership,
reduced motion, contrast, logo/track styling and human visual approval
remain **unverified** until independently executed.

Three-project reuse preflight equivalent to
`python3 tools/select_three_project_reuse.py --lane modern-product --include-conditional`
was performed against the live register, matrix and lane registry. Adopt
the Baldosa native core and existing Modern controller/paint, reuse UR's
candidate evidence discipline, consult Malmazuke as source reference only;
do not fork a frontend, replace the guest, or port conditional framework
deltas without a measured blocker.

Parallel visual PR handoffs are explicit:
- #2038 owns shared stock visual language and actual font/cursor art.
- #2040 owns opened Modern destination and profile child panels.
- #2041 owns independent final-output screenshot and hardware approval.
- #2042 owns animated root-cursor and reduced-motion controls.

The native root C++ file is a narrow **shared integration point**. Merge
the source/destination/motion presenters together without replacing their
individual callbacks; re-run unit, native boot and original-vs-native QA
on the merged head. `docs/WORK-QUEUE.md` and release quality ledger remain
owned by integration/QA. No USA event, Windows QA or visual-release gate is
promoted by this title PR.

## Bounded Windows source-bound capture workflow

The existing `.github/workflows/baldosa-windows-native-bridge.yml` builds the
exact pinned Windows AOT executable. For this **title branch only**, it now
runs `tools/capture_baldosa_modern_title_win32.py` against that very binary
with the verified USA retail ROM and a bounded `tests/input/baldosa-modern-title-native-capture.script` fixture containing only Baldosa's established `turbo on / wait 180 / quit` commands. It neither asks the guest to race nor waits for an impossible stock menu while the Modern host owns input. It uses
the original host `--no-launcher --config --script --framedump` arguments
and actual native P1 semantic A at frame 60. The runner accepts only
**both** 342×224 P7 files with ordered guest-frame witnesses, matching
native-emitted RGBA FNV64, correct source-safe paths, nonblank pixels, and
the registered exact retail title raster crop digest. It records the real
PE executable SHA256 and writes `native-title-receipt.json`, retaining
the native log and PAM files as a 14-day CI artifact even if a check fails.
`tests/unit/test_capture_baldosa_modern_title_win32.py` proves that fake,
blank, dimension-mismatched or missing-witness captures do not pass.

This is not a second CI build, an independent simulator or a test fixture
masquerading as source evidence. The new job step is branch-gated inside the
already-running native Windows bridge, while the independent #2041 final
SDL drawable/perceptual review remains a separate check. Do not promote a
green test if the job was skipped, another head built, or an artifact omitted.

**Reduced motion:** the same `UR_REDUCED_MOTION=1` opt-in used by #2042
leaves the retail title visible with a steady prompt and no intro or
exit movement. A fresh confirm edge still hands off safely to the
established Modern root. This is not yet a player-facing persistent Options
setting, nor a completed reduced-motion/assistive-technology certification.

## Exact packaged-native evidence: 2026-10-20

The [title workstream Windows AOT run 39410474581](https://github.com/gamesbyian/UR-Recomp/actions/runs/39410474581)
compiled the **real pinned Baldosa Windows x64 native title**, ran the
existing host's 180-frame bound, captured the title/root from both the
Modern painter and `RtlDrawPpuFrame` post-OSD presentation buffer, and
accepted the independently verified original USA retail logo bitmap.
The immutable artifact is GitHub Actions artifact **12259586510**
(`modern-title-native-source-pr2043`, 14-day retention).
The executable SHA256 is
`e6e7a3e3bc0746005f54379536fae27c70870d440816d2fba7b41f19fc783fd0`.

| Witness | Real clock | Source dimensions | SHA256 |
|---|---|---|---|
| Title painter `modern-native-title-342x224.pam` | guest frame 48 | 342×224 RGBA | `3aab97798e1652bc8b3e55eea5da410856a763f9aa05cc517bac40d5b5864a28` |
| First root painter `modern-native-root-342x224.pam` | guest frame 80 | 342×224 RGBA | `dc17581d373169420b71c013390d3d186f032973ec2fcbf76e85416443482fb8` |
| Title host-present `presented-title.ppm` | present frame 32 | 342×224 RGB | `319305142850fe2af563bc79039b395d575b65932192dd4f24be0e478b7a0cf5` |
| Root host-present `presented-root.ppm` | present frame 80 | 342×224 RGB | `88e2f5c58fe06e399fde51fdd12e9462f078aa0bba8fb2519f076ee0f6bfdb6b` |

`presents.csv` records **11 actual native host presentations**, guest
frames 16,32,48,64,80,96,112,128,144,160,176. The retained title
retail-crop area and root menu panel region each agree with their
independently captured Modern painter output **pixel-for-pixel (100%)**,
aside from explicitly excluded original host OSD. This evidences the
actual native CPU presentation path through post-`ComposeOsd`, not
the GPU's final SDL drawable or a physical display.

One earlier run [39409224712](https://github.com/gamesbyian/UR-Recomp/actions/runs/39409224712)
correctly failed the provisional **0..24** present collection window:
Turbo emitted only frame16, while the source title capture was taken at
frame48 after the entrance animation settled. Comparing the original
238×81 retail art against that real frame16 present is only 50.6692%
without alignment, **100.0000% after accounting for the intended +4px
vertical title-entry motion**. The corrected capture covers 0..180,
retains source-bound images from **both** states, and does not dilute
its pixel-match gate. C++ regression also tests the exact 4px entry
shift and held-confirm latch semantics.

**Independent manual screenshot inspection on the native artifact:** the
original logo remains unscaled/source-faithful, the small wheel vignette
no longer crosses the subtitle, and the safe-area prompt remains visible.
The separate root image still visibly contains the old narrow 240-wide
engineering shell. This is correctly reserved for #2038/#2040 combined
root styling rather than an approval of the temporary menu. No aesthetic
signoff is inferred from the matching screenshots.

**Still required before a visual-acceptance claim:** independent final
SDL drawable capture at real 16:9 and 4:3, all resolutions/4K, true
physical input devices, keyboard/Start/Back parity, reduced-motion and
regional native journeys, scrolling/clipping/contrast assessment, human
typography/background/logo review, and same-executable Authentic
isolation. QA #2041 owns the final-output acceptance envelope.

## 4:3 responsive title and extracted launcher correction

The baseline native Modern host initially inherited the stock 320×240
SDL window base even while rasterizing the Modern title at 342×224: the
first Windows screenshots correctly qualified the logical source image,
but the default consumer window remained an old 4:3 drawable with extra
letterboxing. The pinned host actually exposes `SnesDesktopHostGame`'s
`window_base_width` hook. The title now uses that original host callback
to choose a 428×240 logical *window* base in Modern boot, preserving
320×240 in Authentic mode. The `prepare_frame` callback checks the
actual drawable each frame: widths at 16:9 or 16:10 display the 342×224
source title/root, while 4:3/3:2 uses separately composed 256×224.
Neither mode changes the guest raster or original simulation code.

The existing packaged-Windows CMD test originally insisted on the root
presenter painting immediately after boot without a user Confirm edge.
That contradicts the title-first product interaction. The test now
requires `UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern`
*exactly once* on genuine ordinary modern launch, and forbids a silent
root paint; the separately qualified native P1-A route remains the
positive test of title→root access. First-racer, Options, original
SRAM and existing negative CMD launcher gates remain unchanged.

A second invocation of the pinned native AOT test now uses a real
`[Graphics] WindowSize = 960x720` guest-independent native window,
requires a 256×224 output in **both** host painter P7 and post-OSD
presented P6 captures, and tests the same USA retail logo crop digest,
title-first/controller handoff/ordered-root evidence and RGB pixel
consistency. It is not synthetic 342 cropping. Each run has a distinct
bounded user-data/output root and shares the same exact Windows
executable digest. C++ `static_assert` checks 4:3, 3:2, 16:10, 16:9,
overflow-bound dimensions and Authentic width, while the Python unit
suite tests 256-specific P6/P7 geometry. **New Windows outcome
pending at this branch head**: do not treat these edits as successful
native 4:3/physical display approval until the Windows workflow and
artifact are independently inspected.
