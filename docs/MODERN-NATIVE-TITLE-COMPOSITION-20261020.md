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
