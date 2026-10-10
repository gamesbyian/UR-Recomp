# QA-08: 1P semantic animation phases and evidence-backed art priority

**Status:** accepted read-only temporal analysis of the authentic 1P
source guest log from merged #1231. Native AOT `38091207834`,
artifact `11684526840`, real `race_1p_ur_ws342_live/log.txt`
and 5,447 identical source/native guest CRCs.

## Why raw guest-frame frequency misleads

The existing first-party machine-readable native worklist counted
**3,355** missing 4× authored-asset *guest-state observations* across
3,430 post-script-entry frames. Its largest semantic state `0A4B`
appeared **1,521** times. This does **not** mean `0A4B`
should be the first new gameplay animation to paint.

Frame-by-frame analysis of the already retained source log
reveals three sharply different phases:

| Guest window | Distinct source semantic behavior | Native samples |
| --- | --- | ---: |
| **1721–3399** | Motion-rich phase: rapidly cycling `08D5`, `0855` and `0895` along with existing approved poses | **1,679** |
| **3400–3638** | Sequence through `0A45`–`0A5C` and related states, rather than the earlier three-state cycle | **239** |
| **3639–5150** | Continuous `0A4B` semantic identifier; gate changes from `0000` to `0100` at frame 3917 | **1,512** |

Exactly **278** consecutive `0A4B` observations occur at
frames 3639–3916 with gate `0000`; **1,234**
more consecutive observations occur at 3917–5150 with gate
`0100`. Nine earlier `0A4B` observations appear
within 3400–3638. This explains the previously reported
1,521 total without assuming a permanent visible unicycle.
The source guest trace alone cannot certify what the late
sequence signifies in original player-facing results.

## Better immediate gameplay-art targets

In the **1,679-frame motion-rich interval** (1721–3399):

| Racer semantic ID | Actual guest-frame observations |
| --- | ---: |
| `08D5` | **526** |
| `0895` | **515** |
| `0855` | **511** |
| Combined three-state cycle | **1,552 / 1,679** (92.4%) |

In that interval the authentic P1 semantic-selection census classified
**1,604** missing authored-asset observations,
**17** authored-but-unregistered compositions, and
**58** selected registered-art observations. Those totals cover
the interval exactly, but no retained statement says all of them
were source-visible OBJ pixels.

**Working priority:** investigate original per-slot OAM intersection,
opaque emission and final BG/OBJ depth for `08D5`, `0855`,
and `0895` in the moving race interval first. Only then
author approved 4× graphics for the proven visible composed poses.
Preserve their observed companion variants (`0D20`,
`0D40`, `0D60`, `0D80`, `0DA0`,
`0DC0`, `0DE0`) as exact registered
composition fingerprints, not arbitrary palette swaps.
The in-flight #1255 read-only original PPU OAM screen-intersection
probe adds an upper bound on potential source visibility; even a
positive OAM rectangle is not proof of source alpha or final priority.

**Do not** infer that late `0A4B` is a released result
animation without an independently verified scene classifier; do
not infer that any of these three repeated states alone identifies
the complete unicycle silhouette. Preserve stock Original fallback
and guest gameplay/PPU data integrity throughout.

## Evidence / acceptance boundaries

The archived log is read-only WRAM/selection provenance from one
actual scripted native 1P course. Guest state cadence may differ
from desktop-present cadence. Full event scoring/results and
45-course original-emulator fidelity are separate QA gates.
Neither this analysis nor its counts licenses authored wide-HD
replacement, player-visible graphics toggles or Windows beta
approval.
