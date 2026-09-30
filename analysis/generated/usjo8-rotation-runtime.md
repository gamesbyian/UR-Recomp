# USJO v8 rotation-runtime probe

Source: GitHub Actions run `36769806636`, job `110073509186`, canonical USA ROM.

The trusted Dragster airborne-rotation differential was reused as a first runtime check of the recovered USJO v8 WRAM reads. Native and pinned Snes9x agreed exactly for every sampled recovered field.

Across left-rotation, right-rotation and matched jump-only control, `twists`, `tabletops`, `zflips`, `rolls`, `flips`, `z_rotation` and `z_pre_rotation` were all zero at every sampled checkpoint. Treat this as a negative control for those candidate meanings: ordinary L/R pitch rotation did not increment them in this fixture.

The `7E:11CD` boost candidate followed the same sequence in all three conditions: 0 through `rotation-post-008`, then 112 at `rotation-post-016`, 92 at `rotation-release-016`, and 76 at `rotation-settle`. `7E:11CE` remained zero, so the byte and 16-bit views are numerically identical over this sampled range. This constrains but does not resolve the historical width disagreement.

No recovered semantic name is promoted by this run alone.
