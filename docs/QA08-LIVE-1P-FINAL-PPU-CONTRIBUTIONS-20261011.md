# QA-08 live 1P: actual final Original PPU visibility for slots98/99

**Status: native diagnostic candidate pending exact-head AOT acceptance.**
This is a read-only original-PPU correctness experiment, not Remastered
artwork, guest gameplay, a Windows output test, a second host graphics
pipeline or any change to shipping Original presentation.

## Concrete discriminator

Merged #1276 and its accepted native AOT run
[38097914195](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097914195)
(artifact `11686843233`) verified original 1P source slots98 and99 separately
at genuine post-GO guest frame **2208**, both at logical 342×224 with **5,447
identical guest CRCs** across five processes and seven identical complete
Original 1×/4× frame pairs. The source PPU emitted **285** and **293** opaque
pixels respectively. Offline exact-byte overlap work in
[PR #1316](https://github.com/gamesbyian/UR-Recomp/pull/1316) found the
sources spatially **disjoint** in this frame, with all source colours matching
the final Original RGB at their coordinates. This still cannot establish
that either slot *caused* those final pixels: another OBJ/BG could be painting
identical colours. Nor can raw 1P raster y112 be assumed to be a genuine
split-player viewport boundary. Both source planes are at y120–143.

The cheapest remaining falsifiable test is a **real PPU counterfactual**:
compare the exact fully rendered original frame with an independent native
execution where `RemoveFromGame` is armed for **one slot and only frame2208**.
If the final framebuffer changes, the removed source slot contributed the
changed pixels to native Original at that exact coordinate/time. If it does
not change, the slot was emission-positive but contributed no distinguishable
final pixels in that capture. Repeat independently for 98 and 99, never
erasing both in one execution or pretending one rider authorizes the other.

## Implementation and evidence contract

No extra build target, patched guest, new emulator framework or graphics mode.
The existing manual-first `baldosa-core-spike.yml` native run already builds
one pinned Baldosa executable and executes the unchanged deterministic
`race_1p.txt` route. The new step reuses that **same built executable** for
just two additional 5,447-frame one-player scripts, each with independent
native output directory and `UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual`:

- A genuine 342×224 Original frame2208 and the *two existing* individually
  isolated PPU source RGBA planes, with their already-validated native
  source reports, are mandatory. No synthetic stock image is admitted.
- Each single-slot PPU removal run must contain exactly **one**
  `UR_RACER_HD_WIDE_REMOVE_SLOT frame=2208 slot=98|99
  status=armed guest_unchanged=1` log marker and complete 342×224 final
  Original counterfactual output, with no authored Remastered host paint.
- The validator compares **all 76,608 logical RGBA pixels**, detects
  changed pixels only under that slot's real original source alpha, compares
  actual source hash/count with its independent PPU source report, rejects
  swapped frame/slot outputs, duplicate removal markers, missing baseline,
  non-independent paths and **any** guest CRC difference across all five
  (reference, each isolated source, each separate removal).
- It records per-slot emitted alpha, colour agreement with full Original,
  final PPU changed counts, source-positive-but-no-final-delta pixels,
  actual changed-coordinate examples and observed overlap between the two
  independent changed-pixel masks. A zero-final-delta source is a legitimate
  **negative**, not a test error. The shared raw scanline112 partition
  is labeled analytic only.
- Every native raster source, unchanged Original control, counterfactual and
  compact JSON report is retained in the *existing* workflow artifact. No
  ROM content or game save is distributed in the report.

The tool `tools/check_baldosa_oneplayer_top_final_contributions.py` has
synthetic adversarial unit cases for a genuinely contributing source,
source-alpha present with no visible change, unauthorized changed final
pixels, swapped/malformed source, missing or duplicate native slot marker,
missing/altered CRC, duplicate output path and invalid proof provenance.

**Interpretation:** This can certify the contribution of slots98 and99
at one real 1P frame after the native AOT accepts. It does **not**
reconstruct BG/window colour-math depth at every frame, authorize
`RemoveFromGame` in the actual 342-wide product, approve any 4× art,
certify motion continuity or change Windows/QA release status. Source-safe
Original fallback remains the full player-visible policy in wider scenes.
The next priority is repeated authentic moving frames and eventually
independent 2P source/depth, not unreviewed procedural racer generation.
