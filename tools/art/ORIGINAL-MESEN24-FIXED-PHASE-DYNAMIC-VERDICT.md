# Original Mesen24: source-verified moving-wheel mechanical controls

**Status:** Retrospective **actual** original USA Uniracers Mesen PPU / authored 2026 GLB experiment, all 48 original images and both 23-frame-edge timelines, at the previous independently qualified [research CI run #42172010215](https://github.com/gamesbyian/UR-Recomp/actions/runs/42172010215) (artifact [13483150035](https://github.com/gamesbyian/UR-Recomp/actions/runs/42172010215/artifacts/13483150035)). The 2026 rig is a procedural current-model hypothesis, not the physical 1994 model, original artist camera, or approved game art. This is a preserved experimental result, not a freshly reproduced 1994 playback run or prospective blind test.

## The question answered

The earlier static original 2D/source-2026 GLB study on [run #41892738666](https://github.com/gamesbyian/UR-Recomp/actions/runs/41892738666) established that 24 consecutive authentic original source sprites **for each racer** keep changing on **23 of 23** frame edges, whereas the original-orientation-only 2026 saddle and source-art 2D rotation controls predict visible changes on just one edge each. See [the exact original-source missing-phase diagnosis](ORIGINAL-MESEN24-PHASE-EDGE-COVERAGE.md).

Subsequent archived research already tested the proposed discriminator, so avoid running a redundant uncontrolled sweep: use one canonical unapproved 2026 OpenSCAD source, its actual exported five-part/16-material GLB, both original Mesen24 PPU sequences, the frozen 7:6 camera, the genuine exact 24-phase/64-orientation source IDs and the same per-role tick1601 original registration. Keep the existing +15° independent saddle mount but hold its *world-space attitude level* as the axle-root pose changes. Rotate the genuine 2026 wheel/rim/pedal parents using **either** of two globally predeclared sources of time, tested separately for both racers:

1. **ROM phase × 15°:** source phase index difference from tick1601 mapped to a hypothetical full-turn 2026 crank cycle.
2. **Fixed 24° per tick:** one unchanged artificial rate for both racers with tick1601 as the zero reference.

The original-ROM phase index is a **2D drawing-state index**; neither source convention is an experimentally recovered 1994 mechanical angle. No fitted phase per frame, user-specific speed, arbitrary camera or sculpt change.

## Authenticated 24-frame static and 23-edge temporal results

| Globally fixed control | Blue pooled silhouette IoU | Blue distinct-shape equal-vote IoU | Blue changed-alpha 23-edge IoU | Red pooled silhouette IoU | Red distinct-shape equal-vote IoU | Red changed-alpha 23-edge IoU |
|---|---:|---:|---:|---:|---:|---:|
| Source-art 2D rotation null (1/23 moving edges) | 0.82069294 | 0.82528384 | 0.09025788 | 0.82181906 | 0.82604553 | 0.10564399 |
| Original 2026 GLB saddle +15°, no moving wheel (1/23) | 0.55176933 | 0.55443157 | 0.01771117 | 0.58196450 | 0.58231923 | 0.01641587 |
| **Moving wheel: phase×15°, world-level saddle (23/23)** | 0.56757653 | 0.57006528 | **0.13202247** | 0.58549568 | 0.58761115 | **0.17943262** |
| **Moving wheel: fixed +24°/tick, world-level saddle (23/23)** | 0.56870778 | 0.57099250 | **0.16134061** | 0.58471835 | 0.58663941 | **0.15871833** |

The moving-wheel arms predict changed pixels on every real consecutive source edge for **both** racers. Absolute changed-alpha pixel agreement improves beyond the rigid 2D source rotation control under **both predeclared rates** (blue 141 TP and 207 TP respectively, red 253 TP and 213 TP). Both moving controls also slightly improve original distinct-shape silhouette IoU versus the static +15° saddle. Blue gains more with fixed-tick drive, while red gains more with ROM-phase drive: neither law consistently dominates both racers. **No per-player best-rate selection is permitted.**

Even the better moving-wheel arms still match fewer than one in five original changed-alpha locations (IoU ~13–18%) and are far worse than the original-art 2D rotation's **static silhouette** score (~82%). This remains incomplete original animation reconstruction; the presence of changed pixels on every edge is necessary, not sufficient, for original acting fidelity.

## Additional matched hub-cover controls were not a robust mechanical win

The same exact authentic real-GLB/ROM witness includes four additional predeclared experimental dark 2026 hub-cover treatments: two plain hub covers with the same fixed wheel laws and two variants whose housing stays axle-locked. The uncovered, world-level-saddle wheel control is the paired mechanical baseline for each. The visible hub cover sometimes improves 64px static silhouette and sometimes improves edge-change IoU, but it **fails** the stricter both-player/all-metric matched-control dominance test for both drive laws; for example the ROM-phase hub cover gives blue changed-alpha 0.14199 vs 0.13202, but red **0.17767 vs 0.17943**, a slight degradation. Do not confuse a provisional period-print housing hypothesis with authenticated original 1994 three-dimensional geometry or owner approval. Preserve the earlier objection to a one-sided welded casing.

## Pinning, independent verification and limitations

The two existing, separately successful historical archives contain different actual GLB byte hashes despite the **same canonical authored 2026 OpenSCAD source SHA**. Do not claim binary model identity. The source PPU alphas, source registration, six original/camera/model identity SHA values and all four original control results are byte-metrically unchanged between the archival runs. The [cross-archive SHA-bound auditor](audit_mesen24_dynamic_phase_witness.py) rejects substituted artifacts, missing original source frames, changed static controls, inconsistent per-edge TP/FP/FN counts and predicted motions that fail to cover the original 23 consecutive source edges. Its [compact source-locked score receipt](../../analysis/data/racer-original-mesen24-fixed-phase-dynamic-evidence-20261107.json) is retained independently of artifact expiration.

~~~sh
python3 -m unittest tests.unit.test_audit_mesen24_dynamic_phase_witness
python3 tools/art/audit_mesen24_dynamic_phase_witness.py original-static-archive.zip original-dynamic-archive.zip \
    --expected analysis/data/racer-original-mesen24-fixed-phase-dynamic-evidence-20261107.json
~~~

Exact original archaeological 3D recovery, original source animation-time model, original wheel/saddle physical pivots, authoring camera and full likeness remain unqualified; a retrospective original sprite sample reused through many research hypotheses is not a new blind holdout.

**Next best experiment:** repeat *only* these **two predeclared dynamic wheel laws** on the independently source-qualified wider outboard pedal/axle and mirrored-tread candidate chosen by the owner in [merged #3236](https://github.com/gamesbyian/UR-Recomp/pull/3236), preserving original source/camera/registration/phase, source-owned rig limits, both 24-frame/23-edge original PPU records and the original static/2D null controls. Report changed-pixel TP/FP/FN, shape and distinct-shape IoU for both racers; keep the earlier candidate results as measured controls rather than assuming a cosmetic improvement makes new motion fit. Qualify any new actual 2026 source GLBs and mechanical clearance before claiming even a source-2026 rig improvement. No shipping promotion without owner full-character visual approval.
