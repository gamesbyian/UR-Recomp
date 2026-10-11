# QA-08: original 2P post-GO front OAM versus HUD/text colour

**Status: candidate native causal experiment, final PPU counterfactual
result pending exact-head AOT.** This is an isolated original/native
source-visibility research task stacked on
[#1340](https://github.com/gamesbyian/UR-Recomp/pull/1340), which
has already passed native AOT source-capture acceptance.
No host renderer, gameplay, Remastered art, persistent files or
Windows release gate is altered.

## Independently authenticated original starting point

Native original USA 2P at genuine guest2208 was captured by
[successful AOT 38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291),
artifact `11695173178`. Four separate PPU OAM slot source
processes for source96/97/98/99 agree with stock over seven
complete Original 342×224 captures and the entire unchanged
2P guest CRC route. All racer sources are emitted after GO:
upper source98=317, upper source99=313, lower source96=313,
lower source97=317. Actual original source upper/lower
registration changed from pre-GO `(0,+113)` to `(-13,+112)`
after GO, source pairs exact. See
[#1342](https://github.com/gamesbyian/UR-Recomp/pull/1342).

At exactly **13 positive source pixels** in upper front
slot98 and **13** in lower front slot96, final stock Original
RGB differs from source by exactly `(+107,0,0)` (red-only).
The 13 affected upper/lower positions match under a
**screen-fixed (0,+112) raster-row translation**, distinct
from the post-GO per-racer source displacement
`(-13,+112)`. The full Original image visually shows
original coloured **“GIVE YOU”** text across the racer
sprites at these positions, but a pixel colour relation
cannot establish whether exact PPU colour math, BG/window,
OBJ priority or another native presentation stage produced
it. Source RGB generally matches final at 304/317 and
300/313 on the two front planes.

**Unanswered causal question:** Does deleting the original
upper/front slot98 or the original lower/front slot96
make each of those text-tinted pixels change in the final
Original PPU, or is the text itself the final owner?
RGB mismatch alone cannot discriminate. Nor can either
racer's apparent front/rear priority after GO be inferred
from the pre-countdown frame.

## Single bounded genuine native experiment

This PR uses the **same pinned Baldosa AOT build**, unchanged
stock full Original, read-only source-slot PPU planes,
guest route `race_2p_split.txt` and existing
single-slot diagnostic `RemoveFromGame` PPU flag.
Run exactly **two** additional independent native guest
processes: delete only OAM **slot98** for guest2208, then
in an unrelated full route process delete only OAM
**slot96** for guest2208. Capture both genuine original
342×224 PPU counterfactual frames using the existing
bounded one-late-frame capture option. All 2,473 full
guest CRCs must be bit-identical across stock,
front+rear source probes and the matching removal route.

`tools/check_baldosa_2p_postgo_front_text_causality.py`
requires the actual original SHA and all four hard-verified
post-GO source SHA IDs, seven full Original frame
source-probe proofs, strict source slot + guest2208 identity,
four independent same-route CRC streams, exactly one
native `RemoveFromGame` arm marker for the correct
front and frame, and the unmodified Original and
independently removed native RGBA PPU files.

It classifies **all** 76,608 original RGBA pixels per
front-slot deletion into source-visible versus no effect,
source-unique versus overlapping with the rear rider,
source RGB matching or differing from the final Original,
the exact text `(+107,0,0)` subset and whether those
13 text-tinted pixels change after actual PPU removal.
It preserves bounded before/after RGB samples and refuses
*any* PPU change outside the actual emitted front source.
**Either zero or nonzero native text-overlap contribution
is a legitimate observed result.** No presumed PPU
priority shortcut is accepted.

```sh
python3 tools/check_baldosa_2p_postgo_front_text_causality.py \
  --native-root path/to/native-runner-temp-with-CRC-and-PPU-sources \
  --out path/to/native-2p-postgo-front-text-causal.json
python3 -m unittest tests.unit.test_check_baldosa_2p_postgo_front_text_causality
```

Seven adversarial synthetic tests cover positive and
negative final Original contribution, exact red-only
offset, rear-source reveal, overlapping equal-colour
source, forbidden outside-source final pixels, malformed
PAM sizes and alpha/RGB discrimination. The raw PPU
counterfactual captures, native removal logs and bounded
source/CRC analysis JSON stay in the **existing** AOT
artifact; no ROM-derived sprite bytes are committed.

**Not admitted:** The result is a source-faithful one-frame
PPU causality measurement, NOT a hardware colour-math
oracle, general text mask, 3D rig/pose provenance, right
to erase original 342-wide sprites, approval of previously
rejected procedural HD art, new frontend control or
release QA certification. Keep Original fallback and the
existing artistic gate unchanged.
