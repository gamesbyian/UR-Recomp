# Original Uniracers Mesen24: shape-versus-motion decision

**Status: retrospectively qualified original-ROM evidence; current main includes a separate read-only audit. No 1994 3D mesh, joints, physical camera or animation law recovered. No owner full-character or shipping-art approval.**

## Exact experiment and scope

The authenticated original-ROM and real-GLB comparison ran in [historical Actions run #41892738666](https://github.com/gamesbyian/UR-Recomp/actions/runs/41892738666) at implementation SHA 68439277cd285e91b12ae1486ff0b90cf8cb4dc1. Source: 24 consecutive unskipped Mesen PPU ticks 1601–1624 for **each** racer, 48 original 64×64 OAM-local alpha masks; 19 distinct blue and 23 distinct red masks. The provisional 7:6 camera, old canonical 2026 GLB, source ROM, 24×64 pose report, original image anchors and first-frame registration were all held fixed. The compact original execution receipt is [the historical source and result JSON](../../analysis/data/racer-original-mesen24-saddle-temporal-evidence-20261104.json).

Four predeclared controls, identical for both players and all frames: original 2D rigid-rotation of source art, and the real 2026 GLB with an axle-root rotation and independent local saddle parent held at neutral, +15° or −15°. The 2026 angle is hypothetical, never recovered original 1994 physical motion.

**Important:** This historical evaluation predates the owner's preferred wider outboard pedals and mirrored orange tread, source-qualified in [merged #3236](https://github.com/gamesbyian/UR-Recomp/pull/3236). Its numerical scores do not validate or describe that later owner-preferred sculpt.

## Two-player evidence

| Fixed control | Blue pooled shape IoU | Blue unique-shape mean IoU | Blue 23-edge motion IoU | Red pooled shape IoU | Red unique-shape mean IoU | Red 23-edge motion IoU |
|---|---:|---:|---:|---:|---:|---:|
| Original sprite 2D rotation | 0.82069294 | 0.82528384 | 0.09025788 | 0.82181906 | 0.82604553 | 0.10564399 |
| 2026 GLB, neutral saddle | 0.50895141 | 0.51233488 | 0.02032520 | 0.55119306 | 0.55143555 | 0.01780822 |
| Same GLB, +15° saddle | **0.55176933** | **0.55443157** | 0.01771117 | **0.58196450** | **0.58231923** | 0.01641587 |
| Same GLB, −15° saddle | 0.48967116 | 0.49233279 | 0.02040816 | 0.52993562 | 0.53053689 | 0.01783265 |

Pooled IoU counts each of the 24 chronological source frames. Unique-shape IoU gives each SHA-distinct original alpha mask one equal vote regardless of how many times it repeats. Edge-change IoU compares the XOR changed-alpha locations on each of the 23 actual consecutive source edges with those predicted by the real 2026 rig. These are three independent tests with different implications.

**Scientific verdict:** A constant +15° improves the static projected silhouette for both original racers even under duplicate-resistant unique-shape scoring, but reduces agreement with true source chronological motion on both. Keep the hypothesis as a qualified static-art clue only. The source 2D rotation beats every 2026 3D arm in all three metrics for both racers. Even the 2D null explains only about 9–11% of observed changed pixels, so none of the candidates yet explains actual animation satisfactorily.

The original sequence is retrospective, not an unseen temporal holdout. The source’s draw-index does not reveal a 1994 3D wheel angle; original 3D model, physical joints, original camera and owner overall likeness remain unknown.

## Run the independent read-only audit

~~~sh
python3 -m unittest tests.unit.test_audit_mesen24_reconstruction_tradeoffs
python3 tools/art/audit_mesen24_reconstruction_tradeoffs.py \
    analysis/data/racer-original-mesen24-saddle-temporal-evidence-20261104.json
~~~

The audit uses Python standard library, checks both racers, all four fixed controls, historical exact ROM/Mesen archive/pose/axis/camera/2026 source SHA identities, historic CI run and head, valid numerical scores and the explicit non-approval constraints. A substituted model or extra tuned arm is rejected. It verifies the preserved aggregate report and its interpretation; it does not itself re-export or replay the original PPU.

## Next mechanical discriminator

Predeclare a fixed 2026 wheel/crank drive law *before* seeing any per-frame result. Keep the authentic same 48 original masks, source phase/angle IDs, frozen camera, initial anchor, both racer roles, the fixed saddle-only controls and original 2D rotation null. Evaluate every 23-tick chronological edge and both static shape measures. Ask whether real source-authored wheel/pedal movement improves temporal changed-pixel agreement on BOTH racers without destroying shape gains. Reject per-frame pose, angle, camera or registration fitting; report the full negative evidence if the model fails. None of those source-index to degrees hypotheses may be labelled recovered 1994 mechanics.
