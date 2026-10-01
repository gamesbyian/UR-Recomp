# Dessyreqt workspace mining and reconciliation

Recovered directly from Dessyreqt on 2026-09-30 and preserved under
`reference/imported/reverse-engineering/dessyreqt/`.

This note records what the recovered workspace contributes beyond the already-public 2014
Tabletop bot and TASVideos movie. Historical labels are evidence, not automatic canonical
truth; promotions should still be reconciled against the supported ROM/runtime.

## Corpus shape

The direct workspace contains exactly 80 tracked files:

- 17 Lua scripts;
- 9 SMV glitch/test movies;
- 45 course-map PNGs, one for every shipped course;
- 3 SRAM images;
- 2 Snes9x memory-watch files;
- 4 research documents/spreadsheets.

The transport ZIP was removed after extraction.

## Autonomous-player lineage

The recovered scripts expose a clear development progression rather than a single isolated
bot.

### `movebot.lua`

This is a race-driving bot. It reads race state, racer position/speed/facing, arrow direction,
reverse-control state and pitch, then writes controller input every frame. Its hand-authored
jump-area table covers 16 track IDs and 49 coordinate rectangles.

It establishes the core policy architecture later reused by the stunt bots:

1. determine intended travel direction from arrows, speed and facing;
2. decide whether the current position falls inside a hand-authored jump region;
3. jump and rotate while airborne;
4. compensate for reverse-controls sections;
5. keep driving until race state ends.

### `teststuntbot.lua`

This expands the movement policy into a stunt-capable prototype. Its coordinate tables cover
26 unique track IDs and 164 rectangles, adding brake regions plus tabletop/Z-input timing.
It reads both X/Y velocity and the tabletop-duration field.

The script's tabletop policy is historically informative: it targets duration 3 on ordinary
courses and duration 8 on track IDs satisfying `(track + 3) % 5 == 0`, while requiring the
air-time counter to equal 9. Those are historical policy constants, not yet game-rule
definitions.

### `tabletopbot.lua`

This is the mature full-game autonomous policy. It retains the race-driving and stunt logic,
covers 36 unique track IDs with 308 coordinate rectangles, handles brake/no-stunt regions,
and automates frontend progression through rider selection, tours, track screens, results,
stunt-result summing screens and the ending. It also contains paired player-state addresses
and two-player/VS menu handling.

The directly recovered copy is not byte-identical to the public 2014 Pastebin copy already
preserved at `reference/imported/tas-bots/uniracers-tabletop-bot-2014.lua`. The recovered
copy changes one coordinate rectangle from `{6725,1212,6872,1316}` to
`{6725,1212,7172,1316}` and adds Dragster-specific direction/rotation behavior. Preserve
both: the public source is the published artifact, while this recovered copy is a distinct
historical working-tree variant.

Operationally, the lineage is therefore:

`movebot → teststuntbot → tabletopbot`

with increasing track coverage, stunt policy and frontend autonomy.

## USJO lineage

The direct workspace recovers:

- `usjo14.lua`, internal version 14, dated 2008-02-14;
- `usjo14a.lua`, internal version 14a, dated 2009-11-19;
- `usjo14a.lua.bak`;
- `usjo14a_test.lua`.

This supersedes the formerly missing v13 as the newest surviving USJO evidence. Exact v13
bytes remain historically interesting but are no longer a technical dependency.

### v8 → v14

Version 14 retains the recognizable v8 optimizer but adds materially broader controls:
`assumeNothing`, Y-position acceptance bounds, whole-twist-only search, capped B duration,
a larger tabletop delay search, and trick-execution support. It also reads the boost meter as
a **16-bit word** at `7E:11CD`, correcting v8's low-byte-only read inside the historical
USJO lineage itself.

A normalized non-comment line-set comparison still shows strong continuity between v8 and
v14 (about 0.73 Jaccard similarity).

### v14 → v14a

Version 14a is a substantial refactor rather than a small patch. It decomposes the optimizer
into named state-machine functions, structured `gameState/currentStunt/bestStunt` records,
explicit strategy/state enums, and dedicated score/queue functions.

It adds direct message-queue reads:

- `7E:0CBB`: queue start;
- `7E:0CE1`: current queue index;
- `7E:0CE3`: first-new queue index.

Its final objective no longer estimates all pending stunt boost purely from completed-stunt
counters. `ScoreStunt()` uses:

`current boost + boost represented by queued stunt messages - boost at the no-stunt landing baseline`.

That is a much stronger historical model of delayed boost crediting.

`usjo14a.lua` and `usjo14a_test.lua` are very close siblings (about 0.93 normalized
line-set similarity), but their scoring path differs: the main 14a file scores from the live
16-bit boost meter plus queued messages, while the test branch retains a calculated
boost-plus-speed form. Keep both because that difference documents an active design choice.

## Boost/message evidence

The v14a queue parser maps message IDs to boost increments:

- 128: IDs 1, 9, 18;
- 152: IDs 2, 10, 17, 19;
- 176: IDs 3, 5, 11, 20;
- 200: IDs 4, 6, 12, 21;
- 224: ID 7;
- 248: ID 8.

This independently links the historical HUD/message queue to delayed boost accounting and
should be reconciled against Nitrodon's 119-message table and the ROM-side message routine.

The old calculated stunt increments remain:
twist 128/152/176/200, tabletop 152, Z-flip 128/152/176/200, roll
128/152/176/200, flip 176/200/224/248.

The direct `Docs/stunts.txt` records the same family with one discrepancy: it lists
Tabletop = 156 and Flip City = 252. Because the executable Lua and Nitrodon code evidence
support 152 and 248, treat the text file's 156/252 as historical notes requiring explanation,
not canonical values.

## Paired racer-state evidence

The recovered bot and memory-watch files preserve explicit player-2 counterparts:

- X/Y position: `0413/0417`;
- X/Y speed: `04B9/04BD`;
- facing: `0BA3`;
- arrow direction/visibility: `0FCD/0FCE`;
- tabletop duration: `0431`;
- Z-flips: `042D`;
- rolls/flips: `11FB/11FF`;
- checkpoint: `119B`;
- camera X speed: `04F7`.

Nitrodon's independent map corroborates the P2 facing, tabletop, roll, flip, Z-flip and
checkpoint slots. These are valuable two-player fixture targets even where exact semantics
still need local runtime promotion.

One caution remains: `Races2.wch` labels `0F63` as “Twists * 2”, while Nitrodon's map
describes that location differently. Do not promote `0F63` until writer/runtime evidence
resolves the conflict.

## Race/course evidence

`magicnumber.lua` contains start/finish X coordinates for all 45 track IDs and uses current
track `7E:00CE`, boost `7E:11CD`, laps remaining `7E:0EF1`, and player X `7E:0411` to
estimate boost sufficiency to finish. This is a historical optimization model, not a direct
course-format specification, but its 45-entry coordinate table is useful for:

- checking provisional stream-to-course identity;
- choosing deterministic finish/checkpoint probes;
- identifying wraparound/circuit start/finish cases;
- cross-checking reconstructed course dimensions.

The 45 recovered PNG maps remove the need to acquire course-map images merely to obtain a
complete local visual corpus. External VGMaps copies remain useful only as an independent
provenance/hash comparison.

## Glitch/collision fixtures

The nine SMVs include:

- Bowl halfpipe traversal, two variants;
- Jumpover halfpipe traversal in both directions;
- Griller and Megajump corkscrew traversal;
- Neon circle entry;
- Dragster go-left test;
- Down+Up test.

The dedicated halfpipe scripts show that the original investigation swept player X position
from savestate while replaying a fixed jump+roll+twist sequence. Historical comments record
successful starting-X examples including Bowl 4965/4934 and Jumpover 3034/3962.

These artifacts should be treated as deterministic collision-boundary fixtures, not merely
glitch curiosities. They are especially valuable after ordinary race physics is stable:
replay the SMVs unchanged first, then reduce one to the smallest position/input discriminator
that distinguishes correct collision behavior.

## Mapping/camera tooling

`mapper.lua` and `positiontest.lua` move the racer through a grid while freezing timers,
using camera position `0419/041D`, racer position `0411/0415`, track-X-size `0D49` and
background-color state `0B7E`. `mapper.lua` stitches emulator screenshots into a large PNG.

This historical approach explains how a complete hand-authored visual corpus could be made
without decoding the course format. The modern project should not reproduce that method as
its course extractor, but the maps are excellent independent visual validation targets.

`mappertest.lua` is largely a generic/borrowed emulator map-capture script with unrelated
game labels and should not be treated as Uniracers semantics without targeted evidence.

## Speed/camera experiments

`governator.lua` is explicitly marked obsolete in favor of `scum.lua`.

SCUM (Uniracers Speed Control Manager) attempts to hold racer speed near camera speed using:

- player X speed `04B7`;
- screen X position `1509`;
- air-time `0545`;
- camera X speed `04F5`.

Its historical constants are camera-speed max 16 and a 32-unit racer-speed scale, producing
a target near 480 units/frame. This is a useful hypothesis for camera/racer speed scaling,
but must be validated before it becomes a game-rule constant.

## Immediate project consequences

1. Stop treating v13 as an acquisition priority. v14/v14a are newer surviving evidence.
2. Preserve both Tabletop-bot variants and explicitly track their small policy delta.
3. Use the recovered P2 addresses to accelerate paired-racer deterministic checkpoints.
4. Add the 9 SMVs to the collision/glitch fixture queue, led by Jumpover.
5. Use the 45 local maps as visual geometry ground truth; external map acquisition becomes
   comparison-only.
6. Reconcile v14a's message-queue boost accounting with Nitrodon's message IDs and ROM code.
7. Use `magicnumber.lua` start/finish coordinates as cheap course-identity/finish probes.
8. Do not port historical bot code wholesale. Prefer exact SMV playback where prerecorded
   inputs answer the question; port only state-responsive policy components that add coverage.

## Controlled SRAM progression differential

The three supplied 8 KiB SRAM images form a compact controlled comparison.

`Clean.srm → All Silvers - No Hunter.srm` changes exactly 144 bytes:

- `0x069C..0x071B`: 128 contiguous bytes, all `00 → 02`;
- `0x10D3..0x10E2`: 16 contiguous bytes, all `00 → 02`.

`All Silvers - No Hunter.srm → All Silvers - With Hunter.srm` changes exactly 16 bytes:

- `0x10D3..0x10E2`: the same 16-byte block, all `02 → 03`.

Thus the broader all-silver progression state is isolated to two tiny regions, while the
difference associated with adding Hunter is isolated entirely to the 16-byte region. This is
a much better save-format starting point than broad SRAM archaeology.

Do **not** yet call either region a medal array or Hunter-unlock array. The controlled labels
make those strong hypotheses, but checksum/duplication/per-racer structure and exact value
semantics remain to be established. The machine-readable diff is
`analysis/generated/dessyreqt-sram-diff.json`.

## Named queued boost rewards

Joining v14a's queued-message boost parser with Nitrodon's message table removes the numeric
ambiguity. The queue values are:

- Roll / Twist / Z Flip: 128;
- Double Roll / Double Twist / Tabletop / Double Z Flip: 152;
- Treble Roll / Flip / Treble Twist / Treble Z Flip: 176;
- Roll City / Double Flip / Twister City / Z Flip City: 200;
- Treble Flip: 224;
- Flip City: 248.

This makes the discrepancies in Dessyreqt's tiny `Docs/stunts.txt` especially likely to be
transcription errors: it says Tabletop 156 and Flip City 252, while executable v14a and
Nitrodon's named queue evidence agree on 152 and 248. Preserve the text file unchanged, but
do not use those two values as game constants. Machine-readable reconciliation:
`analysis/generated/dessyreqt-named-boost-messages.json`.

The complete 45-track start/finish coordinate table extracted from `magicnumber.lua` is
stored separately in `analysis/generated/dessyreqt-course-landmarks.json`.
