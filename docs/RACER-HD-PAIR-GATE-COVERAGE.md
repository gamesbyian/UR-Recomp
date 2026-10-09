# Racer HD: pair-gate coverage and player-local capture feasibility

Status: **Measured limitation; P1-only host composition not yet admitted.**

## Retained reference census

The canonical dense 2P route is `tests/input/two-player-p1-win.input`,
Snes9x guest frames 1180–3820 inclusive. The authoritative input is the
`racer-hd-after-p2-0578-0ec3.json` produced by Racer HD broader frequency
census run [37756792263](https://github.com/gamesbyian/UR-Recomp/actions/runs/37756792263),
artifact `racer-hd-broader-frequency-03f9` (ID 11539984901),
raw JSON SHA256 `98e954af3116892af0247cd90cd1c427d4fdcec2b95a9761922115b00807a6a5`.
The registration-matching model is `tools/measure_racer_hd_fallback_frequency.py`;
numbers below describe **eligible registration/host-capture upper bounds**, not
assertions that the player saw exactly this many HD-rendered frames.

| Classification of 2,641 observed guest frames | Frames | Player-frames |
|---|---:|---:|
| Neither player has an approved contextual registration | 1,431 | 0 |
| P1 selected, P2 unsupported | 984 | 984 selected but pair-blocked |
| P2 selected, P1 unsupported | 56 | 56 selected but pair-blocked |
| Both contextual registrations selected | 170 | 340 pair-gate-eligible |
| Total | **2,641** | **1,380** independently selected of 5,282 observations |

The current pair-only compositor's **maximum** selector-admitted visible
coverage is therefore 340/5,282 = **6.44%** of player-frames, rather than
the **26.13% independent selection** often quoted from the fallback census.
The latter remains a useful content-coverage metric but cannot stand in for
on-screen host presentation. The 340 are a ceiling before the live OAM size,
geometry, approved-asset, capture and frame-draw checks.

## Actual temporal structure of the retained pair-eligibility trace

The original dense trace from the cited Snes9x artifact was recovered and
reanalyzed, retaining the original 2,641 consecutive guest-frame observations.
Hash-bound evidence is in
[`analysis/generated/racer-hd-pair-temporal-eligibility-2026-10-08.json`](../analysis/generated/racer-hd-pair-temporal-eligibility-2026-10-08.json).
It uses the archived `racer-hd-after-p2-0578-0ec3-trace.json` file from
run `37756792263` / artifact `11539984901`, member SHA256
`1c4197035338422592a6946a4746aa8cc77e360255f9c15dcd2a20b31c7d6ebd`.
Its 170 pair-eligible frames comprise **49 runs** (20 one-frame, ten
two-frame; longest 16 frames). There are **49 entry and 49 exit edges**,
or 98 changes in pair-registration eligibility over 2,640 consecutive
guest-frame boundaries. At least 4,942 / 5,282 player-frame slots
(**93.56%**) remain stock under the *default pair-only capture policy*,
even before failed live geometry/OAM/capture checks.

The trace also contains a **759-frame uninterrupted ineligible period**
(guest frames `3062..3820`), another 661-frame interval (`1306..1966`),
and 387 frames (`2050..2436`). Under the default pair-only presenter,
these are extended unavoidable Original-only stretches, about 12.6, 11.0
and 6.4 seconds respectively at approximately 60 guest frames/second.
The first 441 observed guest frames have 59 eligible frames, whereas the
remaining 2,200 have only 111; the coverage profile is highly
non-uniform across a moving play sequence. The priority is whole motion
and game segments, not a prettier isolated sprite or a percentage gain
concentrated in a three-second window.

These figures are measured on a real moving reference sequence, but
**do not count actual native replacement draws**. The 98 edges mark
potentially rapid Remastered/Original transitions, not a verified
screen-flicker defect. Each frame still needs a same-frame native selector,
geometry, OAM, capture, and pixel/priority witness, especially at the
one-frame bursts, player crossings and 16:9 view. Host priority compositing
is another separate blocker: pinned SNESRecomp
`docs/HOST_OVERLAY_EXTRACTION.md` states that a promoted OBJ plane
drawn over the flattened framebuffer needs additional foreground/occluder
planes or an intermediate composition hook for authentic depth.
Do not promote overlapping racer/foreground visuals until this is tested
against stock same-frame pixels and corrected where necessary.

## Why the existing capture API offers a P1-only opening

HDMA writes high OAM `0xA5` above split scanline 112 and `0x5A` below it.
The original visible OBJ assignments are:

| Player | Top half | Bottom half | Slots contiguous? |
|---|---:|---:|---|
| P1 | 98 | 97 | **Yes**, `PpuSetOverlayOamRange(ppu,97,2)` |
| P2 | 99 | 96 | **No**, only `PpuSetOverlayOamRange(ppu,96,4)` also removes P1 |

The pinned SNESRecomp PPU owns one contiguous OBJ capture range per frame.
A genuine **P1-only** host replacement could select an existing approved P1
registration, capture only OAM slots 97 and 98, draw P1's two viewport copies,
and leave P2's stock OBJ slots 96 and 99 untouched. P2-only substitution
cannot use the same mechanism without a new PPU extraction/compositor seam.

**Do not simply change the current `p1 && p2` gate.** The lower viewport has
the opposite front-to-back order: P2 slot 96 takes precedence over P1 slot 97.
Drawing P1 over a flattened PPU image containing stock P2 would *incorrectly
cover P2* where both sprite rasters intersect. The upper viewport has P1
slot 98 ahead of P2 slot 99, so the lower viewport is the immediate
discriminator.

A conservative first admissible case could require **provably disjoint visible
64×64 OAM bounding rectangles for P1 and P2 in scanlines 112–223**. Handle
signed 9-bit X, modulo-256 Y wrap, actual OBSEL sizes and viewport clip.
If either OAM placement is unknown, either rectangle may intersect, or the
original source uses a non-authorized asset, fail closed to the full stock
frame. The pure rectangle test is only a filter: foreground/background
priority and other OBJ overlap still need a real native visual acceptance.
No hard-coded approximate track position or assumed player distance suffices.

The **984 P1-only candidate frames are a content-coverage upper bound, not
the predicted shippable gain**. The number surviving actual rectangle and
raster safety checks is not yet measured. Issue
[#887](https://github.com/gamesbyian/UR-Recomp/issues/887) owns that validation
before any partial-capture runtime admission.

## Opt-in first implementation (not shipping admission)

The native presenter has a diagnostic-only `UR_RACER_HD_P1_ONLY=1`
gate. With the ordinary `UR_RACER_HD=1` master switch enabled and
**only** an approved P1 selection available, it attempts two-slot capture
`[97,99)` rather than the normal full `[96,100)`, preserving stock P2.
This new route is disabled by default. It requires both live P1 placements
to satisfy the same 64×64 size contracts as the full-pair renderer, valid P2
placement data, identical top-half OBJ priority levels, disabled hardware OAM
priority rotation and provably
**nonintersecting** P1/P2 lower-view rectangles after signed X,
modulo-256 Y, visible-field and scanline-112 clipping. Unknown or
overlapping cases return to the complete stock frame without arming OBJ
removal. The experimental path is restricted to the measured `OBSEL=$83`
16px/64px size pair, with both 64px P2 OBJ sizes and canonical racer
OBJ tile families (`00/08` P1, `80/88` P2). Its split-small-OBJ test checks **both** the native high-OAM X bit
and modulo-256 Y before rejecting an inactive copy. On the upper scanlines
high OAM `0xA5` gives inactive P1 slot97 a 16px size and X-high=1;
on the lower scanlines `0x5A` does the same to inactive P1 slot98.
Both active large P1 copies have X-high=0. The inactive copy therefore
appears at signed X `LOW_X - 256`: with low X at most 240 its 16px
bounds never touch the visible field, even when Y overlaps that half.
Low X of 241 exposes the first pixel at X0 and must fail closed if Y
also intersects. This is the title's measured HDMA/OAM geometry, not a
general SNES sprite rule.

Capturing slots 97/98 must never erase an *actually visible* small
OBJ that the host replacement is not going to draw. The earlier
Y-only filter was overly restrictive and could block otherwise safe
P1-only replacements. The X-high/Y combined predicate retains that
non-erasure constraint without treating horizontally hidden copies as
visible.

The pure helper `racer_p1_only_no_stock_p2_occlusion()` is unit
tested with horizontal adjacency, single-pixel overlap, vertical offset,
Y wrapping, small-object split aliases, malformed OAM and priority mismatch.

The live native path still needs expanded deterministic 2P OAM acceptance
and a mixed stock-P2/HD-P1 image comparison before the opt-in flag is
eligible to become a player-facing default. It is **not** counted in the
shipping coverage figures above. The original 256×224 pair path remains
unchanged when the flag is absent.

## QA-08 full-pair inactive-OBJ edge guard (2026-10-08)

The default full-pair capture originally removed OAM slots 96–99 and reconstructed
only the two *large* racers per half. In the title's active-display high-OAM
split ($A5 at the top and $5A at the bottom), the other two slots remain
16×16 small OBJs with X-high set. They are usually invisible at negative X,
but LOW_X=241..255 exposes pixels at the left edge if their modulo-256 Y
falls in the opposite viewport. Removing them without reconstruction
silently loses Original pixels. The P1-only experimental guard already knew
about this failure mode; the full-pair path did not test it.

`racer_hd_full_pair_preserves_split_objs()` now gates the default full-pair
`RemoveFromGame` capture *before* the PPU removal is armed. It checks both
players' inactive upper/lower aliases, X=240/241, 8-bit Y-wrap and scanline
112, expected OBSEL=$83 16/64 geometry, fixed OAM sprite ordering and equal
per-viewport racer OBJ priority. Unsupported or uncertain combinations leave
the complete stock frame untouched. Pure regressions:
`tests/native/racer_oam_placement_test.cpp`; live gate:
`native/presentation/racer_hd_presenter.cpp`.

The existing `tools/measure_racer_hd_fallback_frequency.py` now also emits a
`host_presenter_pair_gate.temporal_upper_bound` block: contiguous
pair-selected run lengths, single-frame eligible bursts and actual
*registration eligibility* switches between adjacent observed guest frames.
The scanner refuses duplicate guest frames and never interprets gaps as a
stock-to-HD transition. This enables disciplined temporal family ranking
from fresh dense traces. None of these model counts is an observed native
HD draw/flicker count; a live per-present witness is still required.

**Evidence classification:** source-confirmed missing safety check plus
boundary regression added, not yet a reproduced moving-frame pixel loss or
a passed native/packaged 2P visual run. No new HD pose is admitted, no artwork
or guest state changes. A bounded running capture comparing stock against
enabled HD at X=240/241 and 250/255 Y-wrap, plus real baseline placement
counts, is still needed. Conservatively rejecting an unsafe capture can
*increase* Original fallback and does not improve the 6.44% selector-pair
upper bound in the retained 2,641-frame 2P trace. Review the temporal
Original/HD transitions before claiming Remastered visual completeness.

## Next pose priorities when the whole-pair policy remains

The same exact census ranks missing player-local families *with the opposite
player already registered*. A verified and approved new family can promote
two player-frame slots through the **existing** pair gate:

| Missing local family | Frames with supported opponent | Maximum pair-gate gain |
|---|---:|---:|
| P2 `0x0544 / 0x0EB0` | 29 | +58 player-frames |
| P2 `0x0545 / 0x0EB1` | 29 | +58 |
| P2 `0x057B / 0x0EC6` | 28 | +56 |
| P2 `0x0548 / 0x0EB4` | 27 | +54 |
| P2 `0x057C / 0x0EC7` | 24 | +48 |

These are opportunity ranks, **not** artwork admission. The retained
`0x0548/0x0EB4` analysis already establishes 54 unsupported P2
player-frames over eight episodes, 34 distinct synchronized witnesses,
one exact stock RGBA hash, original envelope `[16,6,43,36]` and stock
contact `[49,72]`. Only 27 of those frames have the opposite player
already registered, hence a new `0548` pose alone can unlock **at most
54 pair-gate player-frames** under present host policy, not 108. It remains a
new pose: no same-player exact or palette-normalized approved reuse was
found. Fresh authored review, temporal coherence and hash-bound provenance
remain mandatory.

## Decisions

1. Keep the existing shipping two-player HD substitution intact until native
   OAM priority and compositor acceptance support a separate P1-only path.
2. Capture real player/OAM placements under the dense reference route to
   determine what proportion of the 984 P1-only frames are overlap-safe.
3. Prefer evidence-backed **whole-pair unlock gain**, not raw independent
   frequency, when selecting the next reviewed animation family.
4. If the OAM or background-occlusion test cannot be made sufficient, keep
   the stock path. A high coverage percentage is not permission to render
   a sprite on the wrong depth plane.
