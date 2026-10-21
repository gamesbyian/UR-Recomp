# Modern native title: original-source art + 16:9 host composition (2026-10-20)

**Status: source-bound native Windows title/entry verified (342/256, A/Start/Enter, reduced motion and bounded Authentic inertness); independent SDL/physical/human visual approval still HOLD.**
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

## Corrected title-first packaged Windows acceptance

The [prior exact-head Win32 run 39411604926](https://github.com/gamesbyian/UR-Recomp/actions/runs/39411604926)
**passed** pinned AOT compilation, native title→root P7 capture,
post-OSD P6 source pixel matching and PE dependency checks, but the
general extracted-CMD acceptance failed later in an unrelated test
expectation: the old launcher test required
`UR_BALDOSA_MODERN_ROOT painted=1` **without a confirm input**, whereas
the title-first product now deliberately waits at Press Start.

The now-corrected harness requires a one-shot
`UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern` from the
**exact packaged executable** during an untouched cold Modern launch,
and explicitly rejects any premature root paint. Test-only scripted
journeys that start directly at root continue bypassing the title by
their existing fixture IDs, while the separate P1-A native route 15
establishes actual title→root reachability.

The pinned Windows source-bound acceptance includes **three independent
fresh processes** using the same PE/ROM hashes and isolated profile roots:
1. A default 342×224 widescreen title and root with the original retail
   logo and post-OSD native host-presented RGB matches.
2. A **real 960×720 4:3 native drawable** composed at 256×224, with the
   source-retail 238×81 logo independently centred, no 342-pixel crop.
3. `UR_REDUCED_MOTION=1`: stable original title art on at least two
   separate native presents before P1 A, then a direct root handoff
   with a logged native transition. The first root frame is captured
   even when the title intentionally skips the fourteen-frame exit.

These routes are test-only output captures on the real game process,
not a second renderer or a fake SDL/window simulation. No physical
gamepad, final SDL texture/readback, physical 4K/4:3 monitor or human
approval is claimed until #2041's independently recorded review.
The three-process acceptance is **pending a successful exact-head
Windows CI result**; earlier standalone 342-width acceptance cannot
substitute for the added 4:3 and reduced-motion tests.

### Visual polish, held input, and ownership

The primary original bitmap itself has no duplicate narrow-font brand
label above it. The full title is already image-based, so the duplicate
text was redundant. C++ tests now verify the **complete retail-art RGB
digest** at both aspect widths rather than treating a redundant text
label as logo proof. The stock-colour subtitle and safe-area controller
prompt remain. Keyboard Enter and physically distinct P1 A/Start
latches are independently tested for held-through-transition input
suppression. The reduced-motion path is free of artificial delay and
now records the same native title→root witness as the normal path.

When the shared/menu animation/destination branches integrate, the
existing title presenter and its native host preparation callbacks
must remain a dedicated first render/edge owner. The root's changed
selected-state motion, 320×204 wide panel, source-derived cursor,
child modal contracts, and independent final-output screenshot
instrumentation belong to #2038, #2040, #2042 and #2041 respectively.

## Exact-head full native title acceptance: final green owner candidate

Branch commit `bebab7c426564156640e1849c79ecb5f635f0912`
passes **all three** required native checks, each on exactly this
branch, not older source or an unrelated synthetic fallback:

- [Tooling unit run 39484356608](https://github.com/gamesbyian/UR-Recomp/actions/runs/39484356608): success, including real compiled C++ retail title bitmap CRC, 342/256 safety, physical-held A/Start/Enter, reduced-motion stage and native QA verifier regression contracts.
- [Baldosa exact pinned Win32 x64 AOT run 39484356731](https://github.com/gamesbyian/UR-Recomp/actions/runs/39484356731): **success**, including the actual unchanged extracted Windows CMD launcher, original guest and profile/save journeys, title-specific acceptance and PE dependencies. Pinned Windows game executable SHA256 `40dcea66009e6a84eef7df51f447c626bf94fbc6393048c52727276fcbd23425`.
- [Native authority/staging 39484356639](https://github.com/gamesbyian/UR-Recomp/actions/runs/39484356639): success, pinned host source and whitelist intact.

The exact title screenshot/guest-frame evidence is stored in the
Windows run's 14-day retained artifact
`modern-title-native-source-pr2043` (**artifact ID 12292508492**).
I downloaded and independently inspected the four source-bound
`native-title-receipt.json` files:

| Actual Windows process | Painter captures | Real host-presented RGB matches | Accepted |
| --- | --- | --- | --- |
| Modern native widescreen, 342×224 | guest title 48, root 80 | 11 native presentations, original title ROI 1.000, root panel ROI 1.000; title present32, root present80 | **Yes** |
| Modern 960×720 4:3 window, native 256×224 | guest title 48, root 80 | 11 native presentations, independent original title ROI 1.000, root panel ROI 1.000; title present32, root present80 | **Yes** |
| `UR_REDUCED_MOTION=1` at widescreen | guest title16, root64 | 11 native presentations, title ROI 1.000 on all pre-confirm frames16/32/48, root ROI 1.000; normal 14-frame motion intentionally bypassed | **Yes** |
| `UR_EXECUTION_MODE=authentic` Modern root toggle `0` vs `1`, same source PE | **180** original guest frames in each run | All **11** overlapping real 256×224 host-presented RGB frames exactly identical; WRAM CRC timeline SHA256 `d1322d5d99e57113b9af6b7695b084beada390938d7b1015531eccadc2ca5847`; no Modern ink | **Yes** |

All 3 Modern launches share the verified same executable digest
and use independent user-data directories and original USA retail ROM
checksum `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
The title's actual original retail logo pixels were verified inside
each source raster; independent P6 comparisons protect against source
pixels that never reach the native host compositor. The Authentic test
only certifies 180 bounded frames of **same-executable Modern-hook
inertness**, without claiming a cycle-accurate snesref oracle.

**Disposition:** The title owner's native implementation and its unit /
AOT / 4:3 / reduced motion / Authentic source-buffer acceptance are
**complete and green** on this pinned branch. The independent #2041
GPU/SDL *final drawable*, 4K/physical pad and human visual review are
still open. The integration rehearsal #2053 must reconcile its
currently older title/host/capture code with these owner blobs while
retaining sibling #2038, #2040 and #2042 menu/cursor/animation
contracts. Do not promote the merged release gates or merge this PR
based solely on isolated title-native checks.

## Native keyboard Enter route in the actual Windows executable

The original source-bound title artifact tested P1 A using the real
`ur_baldosa_modern_root_gamepad(0, kGamepadBtn_A, ...)` physical-edge
path. The on-screen prompt additionally supports keyboard Enter, but
pure C++ input-coalescer tests alone do not prove the full SDL desktop
keyboard handler actually reaches the transition.

The title PR now extends the **existing test-only** native Windows smoke
selector with mode `16`, leaving modes 1..14's historical direct-root
fixtures and mode 15's P1 A title route unchanged. At guest frame60,
mode16 calls `ur_baldosa_modern_root_key(SDLK_RETURN,1)` then key-up
through the same production handler used for a physical desktop Enter.
A separate fresh Windows game process (`--confirm keyboard`) must
emit exactly one `native_keyboard_enter=1 frame=60` receipt, the same
real root-entry event and exactly verified original logo/source and
post-OSD host-presented title/root P7/P6 pixels. The verifier rejects a
forged P1-A receipt standing in for Enter, duplicate native key receipts
or stale/out-of-order root entry. The expanded native acceptance runs
**five distinct scenarios against the same compiled PE**: widescreen P1,
genuine 4:3 P1, reduced-motion P1, widescreen keyboard Enter, and
original Authentic root off/on.

This is real native **handler** reachability, not a tested physical
keyboard model or final SDL drawable. It does not alter source guest
simulation, race timing, title logo pixel provenance or the product's
normal input mapping. **New native Windows CI outcome still pending**
for the keyboard route; existing 16:9/4:3/reduced/Authentic green
witnesses remain recorded above.

## Independent native P1 Start acceptance

The prompt advertises `PRESS A / START / ENTER`. Earlier native Windows
journeys verified **P1 A** and **keyboard Enter** independently, but not
P1 **Start** through the actual host/gamepad path. A separate test-only
mode 17 now applies a true P1 Start press/release at native guest frame60
using `ur_baldosa_modern_root_gamepad(0, kGamepadBtn_Start, ...)`, while
preserving the same original 14-frame title transition and shared-root
render flow. Each P1 button retains its own edge latch; this is not a
synthetic guest-SRAM write or physical-device test.

`tools/capture_baldosa_modern_title_win32.py --confirm start` now requires
an **exclusive** `UR_BALDOSA_MODERN_TITLE native_p1_start_button=1 frame=60`
receipt, title-before-root causal order, matching original 238x81 source
logo, actual native painter P7 and post-OSD host-presented P6 pixels, and
an executable SHA. A and keyboard receipts cannot substitute for Start,
and duplicate/out-of-order Start acknowledgements are rejected by
ROM-free tests. CI archives its bounded native source artifact alongside
the existing A, Enter, 16:9, true 4:3 and reduced-motion cases.

**Validation status (supersedes the pending note):** source head
`f5ffe656eebe` passed the actual Windows AOT bridge [39527871045](https://github.com/gamesbyian/UR-Recomp/actions/runs/39527871045), tooling
[39527871120](https://github.com/gamesbyian/UR-Recomp/actions/runs/39527871120),
native staging [39527871033](https://github.com/gamesbyian/UR-Recomp/actions/runs/39527871033)
and hygiene [39527871133](https://github.com/gamesbyian/UR-Recomp/actions/runs/39527871133).
Downloaded source-bound Windows artifact **12314145908** reports the same
actual PE SHA256 `86130c051465dec239b3982337e107ab30d905a866f8a2dea7b3a70581e8d4fe`
for **A, Start, Enter, 342x224 wide, 256x224 real 4:3 and reduced-motion**
routes. Original 238x81 title logo and selected host-P6/source-P7 ROIs
agree exactly. Authentic Modern off/on retains identical 320 guest
WRAM CRCs and 20/20 host-present RGB frames. These are specific bounded
source/host results, not a whole-image SDL or physical acceptance: the
diagnostic host OSD differs in a 44x12 top-left area (528 pixels) and
must not be mistaken for original title artwork.

## Title rim pixel determinism follow-up

The decorative 18px lower unicycle ring formerly used a per-scanline
`std::sqrt` call. Its 37 scanline extents are now computed by bounded
**integer** squared-distance comparisons, preserving exactly the
previous raster positions (0,5,8,...,18,...,8,5,0) while avoiding
cross-platform floating-point dependencies. A compile-time pole bound
and the entire fixed 37-row extent/symmetry oracle were added to
`tests/native/modern_title_presenter_test.cpp`. This changes only the
host title painter, neither source logo pixels nor timing, root routing,
input, guest memory or Authentic. Unit/native Windows checks on this
**new follow-up head** must be recorded separately before claiming
verified screenshot parity; prior native evidence remains attached to
its original SHA. Do not self-award art approval.

**Visual holds:** original 16x16 lettering and source cursor treatment
across the combined Modern root; final SDL3 drawables on exact integrated
#2053 head, physical 4K/7:6 display and controllers, independent human
aesthetic review, and original-stock idle attract/demo #2079 (real guest
state and input wake required; no artificial clock-based handoff).


## Native entry/exit frame evidence retention

The title-owner native capture verifier previously compared only a steady
title frame and a settled root frame, discarding the real intermediate
host-presented frames. It now optionally requires **original-source-compatible
entry and leaving pictures** for every moving-title Windows capture, while
leaving the separate reduced-motion path's static checks unchanged:

- At real native present frame 16 the 238×81 retail logo must agree in
  colour and pixels with the captured settled logo **shifted exactly +4px**
  vertically, proving actual entry art rather than only an entry state label.
- At real present frame 64, after the native P1 confirmation at guest frame
  60 and before root at frame 80, the full retail logo must remain stable,
  and the uncovered y=192 blue sweep must occupy its near edge without
  painting the far edge. A static or full-width substituted frame fails.
- Both real source-host P6 `presented-entry.ppm` and
  `presented-leaving.ppm`, along with their frame indices and SHA256,
  survive into the same exact-executable receipt/ZIP as the established
  title/root images. Raw numbered frames are removed only after approval.
  No new runner or extra game build is introduced.

This is native post-OSD P6 source-host compositor evidence, not SDL3 final
drawable pixels. The existing title and root P7 ROI comparisons retain
their independent source provenance; neither human visual quality, physical
4K scaling nor full-frame pixel identity is inferred. Synthetic adversarial
fixtures exercise missing +4px entry and missing exit sweep. **New exact-head
Windows outcome remains pending** until the corresponding real native run
and retained artifacts are checked.

## Held physical confirmation: native route 18

The existing `ModernRootPhysicalEdges` C++ unit test proves title/root latch
logic, but a separate **actual pinned Win32 game** fixture now probes the same
edge across the full native callback boundary. Test-only smoke mode 18 presses
P1 A once at genuine guest frame 60 **without releasing**, sends a second
physical down to the production P1 handler at frame 80 after the title has
entered root, checks that no root command/menu/modal/guest stock route was
activated through frame 120, and only releases at frame 150.

`tools/capture_baldosa_modern_title_win32.py --confirm held` requires
independent chronological native handler markers at frames 60, 80 and 120,
plus the established title→root and exact original-logo/native-present
images. The verifier permits the frame80 root paint and repeated-input call
to occur in either legitimate callback order; it does not accept a missing,
duplicate or out-of-order held guard. The reduced-motion path is distinct.
The existing branch-restricted Windows AOT workflow now retains a sixth
self-contained fresh-user-root capture directory in its original title ZIP.
ROM-free negative fixtures reject source-only false positives.

This probes **host-owned, held physical semantic input**, not an attached
USB pad or an accepted physical-hardware gate. No customer-visible key,
guest input/physics, SRAM or root menu logic has changed. Exact-head Windows
native artifact and independent evidence review are pending.

## Accurate native title transition copy

Real native screenshots revealed the transient string `SELECTING RACER` when
P1 A/Start or Enter enters the **five-destination Modern root**, even on a
fresh install without a racer profile. No racer is selected by the title
confirm itself. The brief 14-tick exit footer now reads **READY TO ROLL**
and uses the corrected centred width of 13 glyphs. This remains presentational
only: no input, menu state, profile creation or guest semantics change.
The actual native Windows capture and 4:3 clipping checks must be rerun on
this exact revision; historical screenshots retain their previous text.

## Indefinite idle prompt cadence

The title intro age deliberately saturates at 4095 frames to avoid overflow
and keeps the original 238x81 artwork fully revealed. The same saturated
counter previously drove the thirty-tick bright/grey button pulse, making
it permanently bright after about a minute of idle. The painter state now
uses an independent, exact **60-tick modulo prompt timer** (30 bright,
30 grey), matching the previous first 4095 frames and continuing indefinitely.
`UR_REDUCED_MOTION=1` remains fully steady. Native C++ regression renders
actual prompt ink before/after the age cap, through a full new pulse, and
after 4200 reduced-motion ticks; it does not fabricate any guest attract
demo. Genuine stock idle demo remains unresolved under #2079.

## Native original idle-attract source preflight (diagnostic-only)

Before releasing a Modern-owned title to the stock guest's attract sequence,
check that the original cartridge is actually progressing beneath the overlay
on the **same source/executable**. Issue #2079's independent original Snes9x
trace proves first MAIN at frame 440, original title at 943, and actual
split-screen demo race at 1531. Those are source states, **not** a license
to trigger a host cutover after a guessed 503-frame timer.

The opt-in `UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE=1` adds three inert,
source-WRAM-derived diagnostic markers to the existing native post-frame
observer. Only a genuine main D7 followed by the original title 84 and
race flag 01 can advance those markers; the host title must remain visible
for all three. No alternate emulator loop, input injection, forced guest
mode, guest WRAM write, reallocation or normal shipping frontend behavior
is introduced.

The separate fresh-user-root Windows native script waits 1800 guest frames
without any button commands. The verifier rejects absent/reordered/duplicate
markers, altered first-cycle intervals, unexpected source values, missing
Modern owner state, binary/ROM source ambiguity and non-Windows execution.
Its bounded output retains exact candidate PE/script/log SHA256 and a small
machine-readable first-cycle receipt. These are **only observational source
facts**. The host does not yet reveal the demo nor implement the wake-back
handoff. Such user-visible behavior, controller consumption, native P6 and
independent final SDL display captures remain acceptance blocks until this
probe passes and the integration owner concurs. Any conflicting Windows
observations are surfaced as failures, not silently normalized to a timer.

### First native observer result: source checkpoint boundary

Fresh original USA ROM, exact merged title/motion head
`3deb66a75fb43a2a3f14631a81e0360c157c055b`, actual Windows AOT
[run 39542072254](https://github.com/gamesbyian/UR-Recomp/actions/runs/39542072254)
produced these *genuine* passive after-frame WRAM observations with no
physical or synthetic input: **MAIN $009F=D7 at frame440**, original title
`$009F=84` at **frame943**, and *first post-frame* `$0313=01` at
**frame1532**. The last differs by **exactly one frame** from the separate
original emulator reference's **visual demo-race start frame1531**. The original
probe incorrectly required them to be identical and made the first native
Windows run red despite all six title/held-motion screenshots passing.
It is not evidence of a gameplay divergence: these are **different observed
events**, displayed demo entry versus race-state flag after the guest tick.
The corrected verifier pins all three actual Windows guest-state event
frames, both reference facts and their 503/589 post-frame intervals; it
continues rejecting missing/reordered/fabricated guest states. A future
presented original demo P6 plus final SDL capture is required to assert the
visible start frame. Do not replace this observed +1 boundary with a guessed
timeout. Original run's diagnostic ZIP SHA256:
`818cf7380a5b1ddb52d718d7218cb18b9ef1ebe9e572089d2d1f039225811297`.

## Test-only true stock-demo reveal/wake candidate

After native frame440 MAIN / frame943 attract-title / frame1532 post-frame
race-flag were independently observed, the title lane prepared **a strictly
opt-in preview**, `UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW=1`, never enabled
by default. In that preview only, the host watches the actual guest MAIN D7
followed by authentic title 84 and *releases title overlay painting* to show
the original game's actual 256-wide framebuffer. It keeps host input focus
and **never changes guest state or queues demo inputs**. Any first recognised
P1/P2 or keyboard wake is consumed and restores the settled Modern title;
a held P1 A remains latched and cannot also confirm Play. Only a genuinely
separate press may transition to the five-way root.

The additional CI-only route 19 drives original guest source to the real
two-player demo, wakes via the actual P1 semantic gamepad handler at frame
1600, checks the title still owns the UI at frame 1640 and performs a fresh
confirmation at 1660; the original root must own the view by 1690. A
**genuine P6 native host screenshot witness**, not a synthetic rendering,
requires moving 256×224 original demo at 1568/1584, 342×224 restored title
at 1616, and 342×224 root at 1696. Only the four chosen P6 image
samples, process log, CSV and hash receipt are retained, not transient
anonymous guest saves or a ROM. The source-marker observer explicitly
distinguishes *host title visible* from *its stale title phase stored in
memory*.

This is an experiment pending the first same-executable Windows run and
separate independent **SDL final drawable / physical controller** checks;
it does NOT establish the real consumer-default attract behavior, UX of
the still-running guest after wake, 1P Play eligibility while a demo is
running, independent P2 hardware behavior or final title art approval.
Until those gates pass, the product defaults to the existing host title.

## Recovery of original stock gameplay authority after attract wake

A user can wake the genuine stock attract demo back into Modern title/root
while original guest is still in a split-screen race. Preview now guards
**Play, Practice and Multiplayer** until actual live guest state shows
`$009F=D7` and `$0313!=01`. This is checked on each fresh gameplay
activation, not a timer, guest WRAM write, forged MENU event or a profile
rebind. Records and Options remain navigable. An early Play press shows
`ORIGINAL DEMO RUNNING` without calling profile validity (avoiding
the permanent stale-profile state for an anonymous/uncertain guest).

A separate **test-only mode 20** waits until the source cycle completes:
on the genuine P1 hardware semantic path it wakes during demo at1600,
enters root on a new button at1660, attempts Play at1710 and asserts that
it was denied *without stock route or stale profile*. Only after the source
naturally re-enters D7 around frame3759 **and has maintained the exact
original stock-menu route's 60 successive settled observations** may the
source admission predicate turn true. A press at frame3770, while D7 is
real but still settling, must remain denied; at frame3900 the native test
asserts the root is still reachable
and no guest writes occurred. A 3900-frame no-guest-input script, explicit
source log verifier with adversarial unit cases and same-PE evidence receipt
support this separate acceptance criterion. If native menu return differs
from the original reference, it fails and the actual Windows log decides
follow-up. P6 evidence is still sourced from the same previous original-demo
wake visual route.

This narrows the outstanding **safe gameplay after demo** issue. The first
valid human Play with an actually named profile and resulting original 1P
course remains a separate consumer journey, along with real SDL/physical
controller signoff. The preview is not switched on by default.

## Additional native original-attract wake owners (test-only)

The first P1 A wake is already demonstrated. Expanded opt-in test fixtures
exercise **keyboard Enter wake on actual 4:3 SDL dimensions** (native 256×224
restored title and 256×224 root, original guest demo unmodified) and **unjoined
P2 A wake in widescreen** (256×224 original demo, 342×224 restored title,
342×224 root). Every first wake is consumed by the real host input handler;
a separate Enter or genuinely P1-owned A confirms the five-way root after
releasing the waking button. Unjoined P2 must not select the P1 root or
join a race on its own. Route markers are distinct and fail when substituted.

These are the real original guest source states, one native AOT PE, exact
P6 present-frame receipts and independent ROM-free negative fixtures, NOT
physical two-pad signoff nor true final SDL pixel/hardware QA. Source guest
state and Authentic mode remain untouched; default attract is still disabled.


## Native attract artifact byte-integrity correction (2026-10-21)

An independent download audit of **owner head `557f0c7dbe9777481ef32185fc04d282918bc5a9`**,
Windows [run 39554168185](https://github.com/gamesbyian/UR-Recomp/actions/runs/39554168185),
artifact **12325690656**, found a packaging-only provenance defect despite
passing gameplay and presentation checks:

- All **nine retained original demo → Modern title → root P6 image files**
  in the P1-wide, keyboard-4:3 and P2-wide archive cases match their recorded
  SHA256. One fourth trio from the long real-main recovery was listed in its
  receipt but **not included in the ZIP**, due to the upload allowlist.
- All five source/preview/recovery native log receipts hashed their
  **LF-normalized in-memory strings**, but Python `Path.write_text` on Windows
  translated the actually archived log files to **CRLF**. Consequently,
  their recorded digest did not match actual downloaded ZIP log bytes.
  Normalizing archived CRLF to LF reproduces the old digest; **that is a
  diagnostic explanation, not an acceptable audit workaround**.

The corrected native capture producer `persist_exact_native_log` writes
explicit UTF-8 bytes and returns their exact SHA256. The Windows upload
allowlist retains all three actual P6 recovery screenshots and its presents
CSV. A new independent, ROM-free
`tools/verify_baldosa_modern_title_artifact.py --archive <path>` rejects
mismatched original log bytes, any missing photograph listed in a receipt,
wrong geometry, mixed executable hashes, duplicate archive entries, or
unsupported claims of final SDL/release approval. Adversarial unit tests
reproduce both historical failures. Original Windows screenshots are not
repainted or retrospectively credited to the fixed candidate; new exact-head
CI is required for an independently auditable retained artifact.

**Still open:** genuine first named-profile Play after the original guest
returns to settled MAIN, independent final SDL output and real hardware
controller/display approval. The attract preview remains opt-in; Authentic
is unmodified.


## Exact two-process named-racer Play after original attract (candidate)

Original demo/wake source admission now has an independent **named-player
end-to-end consumer test**. This adds no shipping input path: the first
fresh native Windows game uses existing test-only P1 X then A controller
semantic edges to create a real canonical stock-preset racer via the
shipping frontend/store. It exits, preserving the actual user root.
The **same native executable** is cold-booted again with that selected
profile, its typed product state and real guest SRAM. There is no
temporary Python profile serializer, fabricated result or anonymous
profile→named hot-swap.

In this second game, smoke mode 23 lets the real cartridge reach its
original attract race, consumes a genuine P1 wake at frame1600, opens the
root via a distinct P1 A at1660, and refuses named Play at1710 while
demo is racing and at3770 while D7 is not source-settled. At frame3900
it requires **60** uninterrupted source MAIN observations and a playable
named profile, then presses genuine P1 A through the existing root →
original stock-menu route. The native log verifier requires an
**actual stock 1P menu 0x3C acknowledgement**, not merely `stock_requested`,
a synthetic guest menu byte or a root screenshot. The second original
script allows the source route to run through frame4800; if it does not
reach the 1P stock menu, the test is red and retains its bounded log.

The final two-process capture uses the same Windows AOT source as the
previous five attract scenarios. Retain only process logs/PE digest and
the three pre-SDL P6 demo/title/root images, never the user's profile,
raw SRAM or ROM. Even on success, **a completed named 1P event, save,
independently checked final SDL pixels, physical controller and art
approval are separate gates**. Keep stock attract opt-in until the
full product owner/integration QA accepts the player journey.

### Exact-head Windows named-bootstrap failure and correction

Run [39558575645](https://github.com/gamesbyian/UR-Recomp/actions/runs/39558575645)
at `b911b670` passed the original six-way title captures,
genuine source attract, native keyboard 4:3 wake, unjoined P2 wake and
natural/60-observation original-menu recovery. Its **first failed step**
was the new two-process named profile fixture, *before* named Play could
be tested. Preserved process A log in original artifact **12326931914**
records real Modern root, X/A first-racer controls, then
`first_racer_created=0 reason=canonical_create_rejected`.

Source inspection found the diagnostic test had mistakenly set
`UR_BALDOSA_MODERN_PROFILE_SELECT=0` for its profile-creation boot.
That flag intentionally disables the native profile writer by
`activated()`, although the anonymous root still paints. Production
native fresh-profile creation requires `PROFILE_SELECT=1` and explicitly
supports a missing `host-state-v1.txt` as `DEFAULT no_host_state=1`.
The test harness now uses a separately tested bootstrap environment
builder, requires the genuine default-root admission marker and real
first-racer creation, and leaves the existing user-root and source save
writer unchanged. `human_button_actions=0` in CI receipts reflects
semantic scripted input rather than mislabeling these as physical humans.

Do not credit a named-profile original 1P stock handoff until the
**corrected head** passes Windows source admission and
`stock_entered players=1 menu=3c`. Archive failure is evidence of a
harness gating mistake, not a genuine profile save corruption.

## Named-profile source clock correction (2026-10-21)

The exact real Windows x64 owner run [39559925092](https://github.com/gamesbyian/UR-Recomp/actions/runs/39559925092), head `b9309e36d2464d7c7bed0d9fdcd1de55fa430d85`, original artifact **12327198452** (ZIP SHA256 `7523b277e1f5b24d74e74b7fbdbcc33aec70b9699359b94aa9d8ea075860e313`) proves that actually bootstrapped named P1 racer SRAM changes original-game first-cycle observation from anonymous MAIN440/TITLE943/DEMO1532 to **named MAIN437/TITLE940/DEMO1529**. Both preserve their measured 503/589-frame intervals. The stock guest naturally recovers MAIN and reaches 60 consecutive D7 observations at frame3815 (versus 3818 anonymous), then the real native router emits `stock_requested players=1`, diagnostic `named_play_requested frame=3900`, and `stock_entered players=1 menu=3c`. The named game was genuinely captured and safely entered; the old verifier rejected it because it required anonymous timestamps and reversed the source/router logging order.

Correction: a strictly *named-SRAM-specific* checker validates all three original source phases and source pixels/visibility flags, exact observed cohort, one 60-observation native recovery, a single real 1P stock entry and event order. Adversarial tests reject anonymous substitution, altered timestamps, duplicate events, wrong overlay visibility, premature routing and reordered logs. No original clock, guest state, production preview default or controller logic changes. This earlier run and screenshots are evidence for the bug, not a green judgment about the new code; fresh exact-head Windows/tooling qualification is required. Human aesthetic approval, final named-case SDL P7, physical pads, 4K/7:6 display, and all release ledger gates remain HOLD.

## Actual final SDL entry/sweep evidence expansion (2026-10-21)

The original/native P6 title entry/lift and exit-sweep screenshots were already
qualified; the combined SDL screenshots previously showed only a settled
title and completed root. The title lane now adds
`tools/capture_modern_title_entry_sdl_win32.py` to the **existing Windows AOT
bridge**, strictly on draft title PR #2043. It reuses the existing Baldosa
`SDL_RenderReadPixels` hook and the project's exact lossless P7→PNG
converter, in two requested drawable configurations: 1280×720 (342 logical)
and 1024×768 (256 logical). Six fresh original-game processes each capture
draw/guest frame 16 entry, 40 settled, 64 confirmed exit, 100 root, and
reduced-motion draws 16/40. A genuine semantic P1 A is supplied at frame60
through the existing in-game route. No turbo, test renderer, guessed art,
guest write, animation clock or second frontend is added.

The source/PE/ROM-bound validator refuses absent native game/title markers,
wrong logical/drawable geometry, source/SDL frame drift, missing/blank or
truncated final SDL pixels, static entry logo, changed logo during exit,
missing confirmation prompt motion, no visible root handoff, and any
reduced-motion frame changes. The real raw P7, exact PNG, native process log,
source SHA, executable digest and conservative no-release-credit receipt
remain in the same branch-gated CI artifact for independent review.

**Status:** pending actual Windows run at the introducing source head. A
unit mock verifies rejection conditions only. Physical USB pads, 4K/PAR,
human aesthetic approval, original font/arrow artwork and all release
ledger gates remain separately on HOLD.

### First native SDL motion pilot failure, exact cause (2026-10-21)

On owner head `5a3b3b4ab7d05dfb67e9e11971e90e62ffbabc79`, the Windows
bridge [run 39569920371](https://github.com/gamesbyian/UR-Recomp/actions/runs/39569920371)
compiled the genuine x64 game and **passed its existing full native title
capture step**, including named original-demo/Play recovery and Authentic
control. The **first failed step** was the *new* SDL-motion collector, before
launching any capture process. Its accidentally truncated local USA ROM SHA256
was 53 hex digits, whereas the actual registered/captured canonical value is
the immutable 64-digit `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
This was a harness transcription error, **not** an original game or rendered
pixel failure.

The correction uses the exact source-registered 64-digit value, adds an
explicit 64-digit regression test, and separates each input admission reason
(executable, original-ROM identity, requested geometry, source hash, capture
directory and timeout) before any native launch. Do not waive the hash, forge
a screenshot, or attribute earlier source P6 evidence to the new final SDL
cohort. Fresh Windows SDL, physical controller and visual-art acceptance remain
open until evidence from the corrected source head is independently checked.

### Full original-title character identity still missing

The retained `regional_title_retail_asset.hpp` stores **only** the
238×81 `UNIRACERS/UNIRALLY` original-wordmark crop (origin 10,1).
The original authentic *full* 256×224 title at native frame320 also has
large, rounded original rendered unicycles and a rainbow airborne course,
as proven in the original Windows Authentic P6 screenshot. Those originals
are **not** present in the 238×81 crop. The bottom Modern strip's dark blue
segments and integer-drawn wheel are conspicuously provisional original-
inspired shapes, not source-authentic racer art. Do not claim the source
cropped title contains the two unicycles, or promote that geometric wheel
under the project's current 4× character-likeness veto.

Highest-value next title-art dependency: a correctly rights/provenance-gated
way to use the real original title character/course art in the widescreen
native composer, reviewed against the original full frame without distorting
or reconstructing an unsupported 3D form. Existing title and stock-attract
source rendering can supply evidence; a proposed image-only mock, extracted
ROM pixels or new high-res horse-shaped rider do not grant shipping approval.
