# Source-authentic Mesen24: why orientation-only 3D misses motion

**Exact witnessed source (not a new guess):** Original USA Uniracers Mesen no-frame-skip PPU observations for both racers, 24 consecutive ticks 1601–1624 each, from [real historical original-ROM/2026-GLB Actions run #41892738666](https://github.com/gamesbyian/UR-Recomp/actions/runs/41892738666), actual stored artifact **13354178658**. The contained detailed result, real-model-evidence/original-all24-saddle-only-generalization.json, is SHA-256 **fbc5534aacaac13d3ab9eae3463853abe0009bf9c7ab56a87bf8968d4039e137**. It records actual 23 consecutive-frame per-edge true/false-positive/false-negative changed-alpha counts on the original 64×64 source coordinate grid. The 2026 authored GLB remains a *separately proposed* mesh, not recovered 1994 source geometry.

## New independently checked failure diagnosis

All **23** genuine source consecutive transitions change pixels for **both** racers. For every fixed control in the previous shape-versus-motion test, the prediction changes visible pixels on **only one** of those transitions. All others are frozen because the controls model original orientation-index changes, while original phase-driven sprite activity keeps evolving.

- **Blue:** Original sprite changes on 23/23 transitions, **660 total original changed-alpha pixel locations** across those transitions. Every tested model predicts changes only at **1602→1603**.
- **Red:** Original sprite changes on 23/23 transitions, **659 total original changed-alpha pixel locations**. Every tested model predicts changes only at **1605→1606**.

| Frozen control | Blue predicted changed pixels | Blue matching changes | Red predicted changed pixels | Red matching changes |
|---|---:|---:|---:|---:|
| Rotated original 2D sprite control | 101 | 63 | 105 | 73 |
| Real 2026 GLB, saddle neutral | 93 | 15 | 84 | 13 |
| Same GLB, saddle +15° | 87 | 13 | 84 | 12 |
| Same GLB, saddle −15° | 90 | 15 | 83 | 13 |

The reported matched/false-positive/false-negative totals independently reconstruct every candidate's previously published chronological 23-edge IoU. The complete [source-locked derived counts](../../analysis/data/racer-original-mesen24-sparse-edge-coverage-20261107.json) retain the omitted originals and precise source-change location. The [small audit](audit_mesen24_edge_coverage.py) can recompute that table from the exact historic original-ROM/GLB witness and rejects other ROMs, camera, model, original alpha shape groups, missing or out-of-order source transitions, scores inconsistent with TP/FP/FN, source/candidate evidence disagreement, and substituted ZIP contents.

## Interpretation and next discriminating experiment

The shape improvement from a +15° saddle pose remains a meaningful, bounded silhouette observation. Its poorer motion score on these 24 source frames is partly explained by an incomplete **orientation-only time law**: the static 3D model is not being asked to animate the original phase sequence. This diagnostic **does not prove** that the 2026 moving wheel/pedal geometry will reproduce the 1994 source animation, nor that the original game used that particular mechanical joint.

Before fitting any more sculpting features, predeclare **one globally fixed, source-index-driven 2026 wheel/crank phase law** for BOTH players; keep original tick1601 anchors, original source phase and orientation identities, 7:6 camera, and all other fixed model/candidate parameters unchanged. Then evaluate every one of the 23 actual source edges and all 24 static frames. Report both full chronological and equal-vote distinct-source silhouette IoU, per-edge changed alpha TP/FP/FN/IoU, how many of 23 original changed transitions the model actually predicts, and the original 2D rotation null.

A useful candidate must explain substantially more than one original source edge **for both racers**, with no per-frame fitted phase, camera, sprite mask, registration or saddle pitch. A new 2026 model that merely replays the 2026 GLB with a nominal rotating crank but produces no visible pixel changes is still a negative result. Avoid claiming a 1994 source wheel motion angle, 3D character recovery, owner full-likeness approval or shipping-art qualification.

## Reproduction from the original Actions artifact

Download the real-GLB artifact **13354178658** from the qualified historic run and pass the downloaded ZIP as the first argument:

~~~sh
python3 -m unittest tests.unit.test_audit_mesen24_edge_coverage
python3 tools/art/audit_mesen24_edge_coverage.py historical-artifact.zip \
    --expected analysis/data/racer-original-mesen24-sparse-edge-coverage-20261107.json
~~~

No new emulator/GLB export, network dependency inside the auditor, auxiliary runner or shipping change is necessary. The stricter archivally pinned witness SHA and the two independently retained aggregate reports permit another agent to repeat the scientific comparison without guessing what was tested. If the historical GitHub Actions artifact expires, retain the derived counts explicitly as *historically witnessed* evidence, not a newly replayed original source run.
