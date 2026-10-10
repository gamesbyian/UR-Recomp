# QA-08: actual later 1P Original widescreen source frames

**Status: accepted native Original 1P late-race source/density parity and read-only WRAM semantic worklist.** Merged #1231, exact AOT `38091207834`, artifact `11684526840`. **Authored wide HD remains unapproved.**

## Why another frame matters

The currently retained first six **real native** 1P 342×224 screenshots at
guest 1536..1616 all show the enormous countdown numeral over the course.
They establish camera/margin pixels but do not permit a useful judgement of
moving rider quality, track contact, HUD alignment, depth or widescreen
composition during sustained race action.

The already-executed independent 1P route contains 5,447 guest
simulations and identifies the first 1P race-mode transition near guest
550 and a later actual race-script milestone at 1720. It has two distinct
real native 342-column 1×/4× runs with matching guest CRC, sharing the
same title-owned calibrated world provider, controller stream and original
PPU. The current \`UR_BALDOSA_WS342_LATE_CAPTURE_AFTER\` knob can capture
exactly one extra authentic late PPU frame per such process, without
changing guest behavior or adding *any* new emulator run.

## First native execution: later race captured, trace needs correction

The first live native AOT run `38090776774` retained genuine 1P
**342×224 Original PPU guest frame 2208**, screenshot source SHA256
`8e81014ae6b7285b8d4a79985cc6ba146b309e913fc0e7e3cb8800730f3f0f05`.
Direct inspection confirms a **live 1P race**, two visible unicycles,
the running clock (0:08:1), full course track and the title-owned
"BIGGER BOOSTS" race message. There is no giant countdown numeral.
The same real guest process retained the six older early frames, giving
seven source captures total. No source or guest execution defect has
been demonstrated by that observation.

The strict new semantic worklist stopped the AOT workflow before its
second independent 4× source run: it incorrectly required the pre-race
frontend selector 0x3C in the 1700..5150 active race window. The guest
leaves that transient selector once the race begins. The revised
read-only recorder gates on its explicit single 1P diagnostic opt-in,
bounded guest window and normal native admission census, and the
analyzer separately requires exactly the genuine scripted race
milestone, terminal and all 5,447 original/native CRCs to match.
That first attempt was repaired by the later accepted native run; its first failure is retained as diagnostic history, not a present blocker.

## Final native acceptance and measured artwork priorities

The corrected AOT run `38091207834` **passed**. Its independent
source/4× images at exactly seven guest frames (1536, 1552, 1568,
1584, 1600, 1616 and **2208**) all agree at **every logical RGBA
pixel**, and every 4×4 expanded pixel block is identical to its
independent actual 1× source. The entire **5,447-frame original
guest CRC sequence** is unchanged in both runs. Post-countdown 2208
is genuinely moving 1P Original gameplay: 55,580 logical pixels differ
from countdown 1616, and all four expanded margin bands have actual
source variation (top-left 2853, top-right 2011, bottom-left 2410,
bottom-right 1678). Its native Original source SHA256 is
`8e81014ae6b7285b8d4a79985cc6ba146b309e913fc0e7e3cb8800730f3f0f05`,
with independently generated 1368×896 4× SHA256
`b8257c7f94a4b97b343626f773be912b8967a9a1849ef3574fd8d755ef3bab7a`.

The read-only census covered **3,430 actual post-milestone 1P
guest frames** after script milestone 1720, with **3,355
missing authored asset samples**, **17 existing authored assets
whose runtime composition does not match registration**, and **58
registered/selected authored states**. These classifications sum
to 3,430, but they are **source semantic selections, not rasterized
HD witnesses**. Source slot/background visibility has *not* yet
been tested for the missing states.

| Exact missing semantic/composition state | Guest-frame samples |
| --- | ---: |
| `0A4B:0A4B:0000:0000:0100` | **1,234** |
| `0A4B:0A4B:0000:0000:0000` | 287 |
| `08D5:08D5:0000:0000:0000` | 282 |
| `0855:0855:0000:0000:0000` | 275 |
| `0895:0895:0000:0000:0000` | 272 |

The first two `0A4B` fingerprints cover **1,521** of 3,355
missing-art sample frames (approximately 45.3%). Existing approved
pose IDs `01B9` and `0539` with companion `0C24` are
among the smaller 17 authored-but-unregistered observations.
Do **not** simply paint 0A4B: first resolve whether it
corresponds to a displayed/occluded player OBJ or an off-screen
semantic state. The current priority is a **read-only guest
source-OAM geometry/source-emission visibility census** for the
highest-frequency states, followed by source-derived approved 4×
art where the evidence supports it.

All accepted witnesses and negative release claims are retained in
`ws342_live_1p_late_source.json`,
`ws342_live_1p_density_parity.json`, and
`ws342_live_1p_semantic_worklist.json` in artifact `11684526840`.
This accepts bounded 1P Original widescreen/density authenticity,
not 342-wide authored racer replacement, full race outcome parity
or integrated Windows graphics UX.

## The proposed acceptance

Set \`UR_BALDOSA_WS342_LATE_CAPTURE_AFTER=2200\` for the existing 1P
1× and 4× runs, with the opt-in environment removed immediately
afterward. Keep all six existing countdown screenshots. Require:
 
- exactly seven captured 1× and 4× native Original PAMs, including six
  early and the same single real late guest frame;
- exact full 5,447-frame independent CRC equality against existing
  1P stock run for both captures;
- actual native one-player 0x3C scene selection, real guest script race
  milestone, a later callback in the bounded 2200..2450 range;
- 342×224 vs 1368×896 native source/4× Original pixel identity across
  **every pixel** of all seven matched frames;
- nontrivial four 43-column side-edge/source bands and changing PPU
  pixels since the countdown witness.

## Source-derived Remastered asset worklist, same run

An additional strictly read-only `UR_RACER_HD_1P_STATE_TRACE=1` switch
samples the **actual guest WRAM** in this same 1× native 1P execution.
It reports each observed P1 semantic frame, composition primary/companion
words, selector, companion gate, registry acceptance, existing authored
asset availability and precise fallback reason **before** the 342-wide
geometry gate. Its separate analyzer
`tools/check_baldosa_1p_art_state_worklist.py` verifies that the
5,447 original/native guest CRCs match and every observed semantic
sample belongs to a real native guest census frame after the script
race milestone. It ranks up to 25 *exact* frequently needed missing
asset/composition states, distinguishing:

- semantic pose with no authored 4× pixels yet;
- authored pose available, but its exact runtime composition unregistered;
- already registered/selected authored pose that remains blocked by
  geometry or visual occlusion policy.

These are **guest-state frequencies, not presented HD frames**. They
will guide the next approved artwork/reuse batch without guessing
poses or bypassing sprite depth. No guest mutation, PPU alteration,
second compositor, additional native process or asset approval results.

The opt-in diagnostic exports an authenticated late screenshot, exact
source/4× SHA256s and an explicit source-only/non-release status.
Even exact late 1P source imagery does **not** authorize destructive
OAM removal, authored Remastered sprite replacement, SDL hardware
4K or a production graphics setting. Use the source image to choose
a bounded visual defect or HD-art registration target, not to invent
racer pixels.
