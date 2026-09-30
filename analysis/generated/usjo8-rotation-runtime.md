# USJO v8 rotation-runtime probe

Source: GitHub Actions run `36771542800`, job `110079167441`, canonical USA ROM.

The trusted Dragster airborne-rotation differential was reused as a first runtime check of the recovered USJO v8 WRAM reads. Native and pinned Snes9x agreed exactly for every sampled recovered field.

Across left-rotation, right-rotation and matched jump-only control, `twists`, `tabletops`, `zflips`, `rolls`, `flips`, `z_rotation` and `z_pre_rotation` were all zero at every sampled checkpoint. Treat this as a negative control for those candidate meanings: ordinary L/R pitch rotation did not increment them in this fixture.

The `7E:11CD` boost candidate followed the same sequence in all three conditions: 0 through `rotation-post-008`, then 112 at `rotation-post-016`, 92 at `rotation-release-016`, and 76 at `rotation-settle`. `7E:11CE` remained zero, so the byte and 16-bit views are numerically identical over this sampled range. This constrains but does not resolve the historical width disagreement.

No recovered semantic name is promoted by this run alone.

## Matched X-button discriminator

Recovered USJO v8 maps its `xing` action to the SNES X button. A new fixture therefore held X for the same eight-frame intervention window while preserving the control's launch/timing.

At every sampled checkpoint, X was identical to jump-only control for all recovered USJO fields and for the existing gameplay summary. No sampled `zflips`, `z_rotation`, `z_pre_rotation`, tabletop count, speed, air-state or boost difference survived to a checkpoint.

This is a useful negative result, not evidence that X is irrelevant. The recovered controller uses timing/state-dependent X pulses for both tabletop and Z-flip logic, so the next pass should inspect per-frame WRAM transitions and then mirror the recovered cadence rather than lengthening a coarse hold.

PR #80 independently resolved `7E:11CD` statically as a 16-bit game field. Here its high byte stays zero and the runtime word follows 0 → 112 → 92 → 76 identically across L/R/X/control, providing dynamic corroboration without reopening the width question.
