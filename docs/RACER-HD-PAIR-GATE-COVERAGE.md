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
