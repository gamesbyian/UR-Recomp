# Dragster checkpoint/finish activation versus presentation runtime boundary

Date: 2026-10-02  
Fixture: deterministic Dragster finish tail  
Evidence run: GitHub Actions run 36954104693, artifact `uniracers-object-activation`

## October 8 phase-order correction (supersedes the old slot-8 causal wording)

The **first observed progression change at frame 2903 remains correct**.
However, the collision word `0x2020` / C000 index 8 in this
October 2 report was taken from a **postframe** P1 WRAM snapshot. The
ROM-proven USA frame path calls bank-82 object dispatch (83:CD4E)
**before** bank-81 contact/surface resampling (83:CD73).
P1's preceding frame-2902 stored word is `0x2024` / slot 10 / object
code `0x14`. It is the stronger *candidate input* to the frame-2903
dispatcher; which word the handler actually used has **not** been
captured instruction-by-instruction. Both slots select the same handler
family and masked upper control class.

Read the original timeline below as a description of *observed frame-end
state*, not proof that slot 8 fired the finish transition. The 114-frame
presentation-before-progression separation remains directly supported.
The accepted interpretation and phase-aware analyzer are in
`docs/COURSE-CONTACT-MARSHAL.md` and
`tools/correlate_dragster_finish_spatial_event.py --contact-sequence
analysis/data/dragster-finish-contact-transition.json`. This addendum
preserves the historical raw observations and replaces only the
unsupported same-frame causal inference.

## Product result

For the representative Dragster checkpoint/finish family, gameplay activation is
not camera-window activation.

The object family exists in the authoritative course behavior plane before the
race, its graphics are loaded during course setup, its finish/checker
presentation becomes visible before the gameplay event, and the gameplay event
occurs only when the racer's collision/contact-derived C000 selection reaches
the checkpoint/finish handler.

That separation is mechanically sufficient to constrain Widescreen: widening
the presentation rectangle must not widen or otherwise alter the collision /
contact domain that selects gameplay object codes.

## Event timeline

The dense deterministic tail captures one ordinary checkpoint/finish event.

| Stage | Evidence | First observed point |
| --- | --- | --- |
| authoritative object exists | `7E:C000[6..14]` are nine stable `0x14` bytes throughout the probe; they were materialized during course load | before active race |
| resource graphics prepared | course loader performs resource-level VRAM DMA for resource `0x24` before materializing its runtime A000/C000 contribution | during course load, before active race |
| actual finish/checker pixels visible | fixture-specific right-edge framebuffer discriminator crosses threshold at `object-tail-060` | guest frame **2789** |
| unmistakable finish-post structure visible | direct inspection of retained framebuffer sequence | about `object-tail-159`, guest frame **2888** |
| gameplay behavior event | progress changes `3/0/1 -> 1/1/0`; collision-derived C000 index is 8 and code is `0x14` | `object-tail-174`, guest frame **2903** |

Thus the first finish/checker pixels are already visible **114 guest frames**
before the checkpoint/finish behavior transition.

## Gameplay activation evidence

At the behavior transition:

- P1 X = 25256;
- camera X = 25186;
- collision/contact word = `0x2020`;
- dispatcher-derived C000 index = 8;
- `7E:C008 = 0x14`;
- checkpoint/gate/laps changes from `3/0/1` to `1/1/0`.

The preceding sample, frame 2902, still has progress `3/0/1` while selecting
the same checkpoint/finish object family. Static recovery already establishes
that `81:82E6` derives its C000 index from current-player collision/contact
state `$0F09`, not from camera position or presentation-update state.

## Presentation evidence and limits

The compact camera-filtered update-list counts `$0DCD/$0DCF` are zero at the
sampled visibility and behavior boundaries, and the retained per-frame dumps do
not show direct `$2118` or DMA-to-`$2118` activity there. This is useful
negative evidence only for that compact update-list mechanism.

It does **not** mean presentation preparation is absent. Ordinary course-render
PPU setup continues in the same frames, including repeated `$2116/$2117`
destination programming, and VRAM snapshots change from frame to frame.

The retained evidence also does not isolate a distinct object-specific
"draw-eligible but not yet visible" state for this background feature. For this
representative family, the safe contract is therefore:

1. graphics/resource preparation happens before the race;
2. authoritative behavior cells exist before the race;
3. actual framebuffer visibility begins at frame 2789;
4. gameplay behavior is selected later, at frame 2903, by collision/contact.

Do not invent a separate draw-eligibility boundary unless a future product
question requires finer renderer archaeology.

## Regression contract

`.github/workflows/object-activation-probe.yml` now asserts that the retained
deterministic fixture continues to satisfy:

- C000[6..14] remain nine `0x14` checkpoint/finish cells;
- first right-edge finish/checker ingress is `object-tail-060` / frame 2789;
- first semantic checkpoint/finish progression is `object-tail-174` / frame 2903;
- visibility precedes gameplay behavior.

The framebuffer ingress detector is intentionally fixture-specific. It examines
only the entering four-pixel right edge and the known stripe Y band, where the
ordinary dark rail contributes at most four classified pixels before arrival;
the finish stripe raises the count to 52 on the first positive sample. The
threshold is 16 pixels.

## Widescreen constraint

Treat gameplay activation and presentation exposure as separate domains.

A widened camera/render rectangle may reveal this feature earlier. It must not
cause `$0F09 -> 81:82E6 -> 7E:C000` to select or dispatch the checkpoint /
finish behavior earlier than the authentic collision/contact interaction would.

The representative object-activation question is therefore closed for current
Widescreen planning. General object-family activation should be reopened only
if an implementation or fidelity discrepancy demonstrates a different
mechanism.
