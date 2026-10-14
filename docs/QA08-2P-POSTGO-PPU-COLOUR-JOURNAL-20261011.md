# QA-08: original 2P PPU colour register history at post-GO

**Status: first exact-head native AOT experiment pending.**
This is an original source-faithful PPU register observation, not
a renderer change, host pixel rule, game/CPU/WRAM edit or artist
licence. It reuses the original native 2P guest and **one already
scheduled stock 342×224 process** at guest2208. It starts from
the proven source-only post-GO AOT work in [#1340](https://github.com/gamesbyian/UR-Recomp/pull/1340).

## Why an actual register history is necessary

In accepted actual USA native 2P guest2208, independently
captured upper/lower slot98/96 Original OAM source planes
have 317/313 emitted alpha pixels. Original final RGB differs
from isolated source at **exactly 13 front-slot positions
in each viewport** by **+13 native SNES red-channel quanta**,
without changing green or blue. A separate genuine native
PPU counterfactual from successful
[AOT 38122996301](https://github.com/gamesbyian/UR-Recomp/actions/runs/38122996301)
proves all **13 of those positions change final Original pixels**
when their source slot is deleted. These observations establish
actual source involvement and a repeatable pixel colour
signature, **not which hardware component creates it**.

The independently pinned 2P SNESRecomp framework
`baldosa/snesrecomp@075fbe4c` already includes a
**real frame/scanline PPU raster register journal**:
`ppu_rasterDebugDump` captures the completed field's
base display register state and actual line-tagged
$2100–$2133 writes (with drop counts) plus the next
recording field. Its PPU snapshot struct provides
`cgadsub` ($2131), `cgwsel` ($2130) and
`fixedColor` (maintained by $2132/COLDATA writes).
The beam driver's `ppu_rasterBegin/RenderBegin/ApplyLine/RenderEnd`
already drives that journal and preserves guest state.
No separate emulator, API extension or new register
instrumentation is required.

## Narrow native capture and safety

`native/presentation/racer_hd_presenter.cpp` adds an **explicit
`UR_QA08_PPU_COLOUR_JOURNAL_FRAME` opt-in** at the existing
342×224 Original stock PPU presentation seam. It is
disabled in every normal game/player process, requires
the actual requested native guest frame, and refuses to
run when a source-slot or destructive PPU counterfactual
probe is armed. It asks the **existing pinned PPU** for
one completed raster journal and records the current
end-of-render colour registers. An optional 512 KiB
buffer is allocated only at that one frame and released
immediately. A guest-WRAM/OAM/CGRAM/VRAM digest before
and after must agree; no guest bytes, PPU registers,
pixels or gameplay route are altered.

In the already existing native original 2P stock route:
`UR_QA08_PPU_COLOUR_JOURNAL_FRAME=2208` selects the
same source-backed post-GO guest2208. The baseline
2P guest CRC and the journal-enabled candidate must
have exactly **2,473 identical CRC records** and the
complete unmodified Original PPU frame2208 must match
SHA256
`f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`.
No extra route or new test harness is constructed.
The diagnostic variable is unset before any later
source isolation or PPU-removal route.

The strict dependency-free analyzer
`tools/check_baldosa_2p_ppu_colour_journal.py`
requires **one** exact native journal record, an armed
and completed raster journal, zero dropped writes in
both completed and recording fields, correct counted
line-tagged PPU register entries, original full
stock P7 raster hash, unchanged complete guest CRC,
and no guest-state mutation. It reports the
actual end-sampled `CGADSUB/CGWSEL/fixedColor`,
completed/recording field baseline CGADSUB and
bounded per-scanline real colour register writes
`$2130/$2131/$2132`. The accepted native JSON
and original raw log are preserved in the standard
native evidence artifact. A fail-closed empty,
truncated or unarmed journal is not reclassified
as proof that colour math never occurred.

Adversarial regression cases cover invalid
frame/line/register bytes, stale raster evidence,
dropped or inconsistent entries, exact 2,473-line
CRC disagreement, forged/changed full source raster,
duplicate logs and valid observations with **zero**
colour-register writes. Zero writes may be
legitimate when the effective colour registers
were set earlier; never assume a register write
must occur inside this particular frame.

## Limits and next decision

Even a native fixed-colour red operand equal to 13
with colour-addition enabled in a completed field
does **not** prove that the source-pixel colour
differences were produced by that operation:
subscreen selection, the actual per-scanline
state, SNES OBJ math eligibility, window masks,
native priority and another composited layer
remain possible. End-of-render sampled registers
are **not** the register values at every rider
pixel. No fake red 2D/3D overlay or general
hardware owner label may be inferred.

If the accepted native register journal shows a
plausible real colour-addition path, the next
proper experiment is a narrowly selected
read-only line-state and subscreen/source
priority evaluation at original upper racer
scanlines **47–78** and lower **159–190**,
including unaffected adjacent source controls.
If it contradicts the red-addition hypothesis,
preserve the contradictory data. Do not alter
Original rendering, 4K, artistic HD or the
independent release gate from this research.

## Follow-on: lossless tagged CGADSUB chronology (same native capture)

The original journal checker now derives, **from the existing unmodified
completed/recording PPU entries**, an explicitly *line-tagged* CGADSUB
timeline per field. It partitions all native tags 0–261 into contiguous
inclusive intervals, starts from that field's independently recorded
baseline, applies each original $2131 write, preserves the index and byte
of **every** $2131 write, and retains same-line multiple-write order.
Unrelated $2130/$2132 writes remain separately visible in the original
colour-register list. This is a pure offline checker change: **no new
native process, PPU hook, guest input, workflow or shipping asset**.

The interval's effective value is the value *after the final write bearing
that tag*. Earlier writes on the same line are retained as events; they are
not silently collapsed out of the evidence. Native PPU raster line tags
are **not yet aligned to final 342×224 screenshot Y**, and neither
CGWSEL/fixed-colour baseline history nor pixel-specific window masks or
subscreen eligibility are reconstructed here. Therefore neither the 13
front-racer red-quanta changes at y47–52/y159–164 nor any other pixel
receives a proved arithmetic operand or layer owner from these intervals.

Fail-closed parsing also rejects forged duplicate JSON object keys and
Python bool-as-int pseudo-frame/count/drop/scanline fields. The unit suite
covers no $2131 writes, distinct tagged writes, multiple writes on one
tag, explicit scanline end coverage, and adversarial JSON. The current
pinned native journal experiment must independently pass exact Original
raster and all 2,473 guest CRCs before these derived intervals may be
treated as a measured actual frame. Keep the existing production Original
fallback and withheld Remastered likeness approval.
