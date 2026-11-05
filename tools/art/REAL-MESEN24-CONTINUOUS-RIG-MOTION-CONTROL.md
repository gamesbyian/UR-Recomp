# ART-4K: actual 24-tick original versus one continuous 2026 rig (2026-11-03)

**Bounded, predeclared negative control.** This document measures whether the already-authored, unapproved five-parent 2026 unicycle can explain the *spatial locations* of genuine original 2D source-racer changes across 24 independently executed consecutive Mesen ticks. The comparison cannot recover original 1994 3D camera, skeleton, physics, original driving speed or authorial intent, and does not approve likeness or shipping art.

## Fixed sources, budget and registration

Original: independently executed no-skip MesenCE 1601–1624 original PPU source from [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103), canonical ZIP SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`, source ROM `859ec99f...d478`, source-held 64×64 OAM slot 96 blue and 97 red. Prior actual sparse source overlap 1601/1607/1618 verified all OAM/VRAM/CGRAM/P6 bytes. Red is evaluated in its **held OAM source** orientation; the previously authenticated **completed-screen** red mirror is a *different* source representation and is not applied here. Original PPU final screen ownership at all new ticks is unproven.

2026 candidate: one immutable original upright model GLB SHA-256 `efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5`, retained real model-review artifact #13063969312, **same two-DOF part-parent rig** from [#3101](https://github.com/gamesbyian/UR-Recomp/pull/3101), and one unchanged provisional orthographic 7:6 camera SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`. Each player receives **one** transparent fixed 4× source-model registration at *tick 1601* based only on the source's lowest occupied alpha span midpoint and the model's same anchor. Every subsequent candidate frame uses that exact unchanged registration, with no per-frame translation, scale, flip, camera, geometry or source-label fitting. Every original 64×64 source mask stays in OAM-local coordinates; moving blue screen X is not miscounted as source-shape motion.

Three continuous parameters were **predeclared before evaluating source scores** in [draft #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832):
- A: fixed neutral drive 0°, frame pitch 0°, 24 times
- B: drive advances +24° each tick (wrapped modulo 360), pitch 0°, 24 times
- C: same drive and a bounded one-period pitch `10° sin(2π step/24)` over 24 steps

The speed and frame wave are illustrative controls, not fitted original 1994 angular velocities. The 24 observed frames were already inspected, so **none is prospective blind holdout**.

## Actual source and model results

The original 24 authentic PPU source alpha observations changed on **all 23 of 23** adjacent ticks for **both** players, 660 changed-alpha pixel instances across blue edges and 659 across red edges. The model comparison was rendered on HP in 86.17 seconds (Python 3.12, NumPy 2.5.4, Trimesh 5.2.0, Pillow 13.0.0; no source emulator rerun for model scoring).

| Candidate | Blue mean source IoU | Red mean source IoU | Predicted changing edges | Blue/red change-support IoU |
|---|---:|---:|---:|---:|
| A: static | 0.48123178 | 0.36148543 | 0/23 | 0 / 0 |
| B: wheel/crank +24°/tick | 0.47668481 | 0.35809105 | 23/23 | 0.16220472 / 0.16050354 |
| C: same + ±10° oscillating frame | 0.48948655 | 0.36340147 | 23/23 | 0.12110523 / 0.11985899 |

For fixed drive B, the candidate produces 816 source-grid changed-pixel instances per player; **206** intersect the 660 genuine blue changes and **204** intersect the 659 red changes. Source changed-pixel recall is blue **0.31212121**, red **0.30955994**; candidate precision blue **0.25245098**, red **0.25000000**.

Adding ±10° upper-frame oscillation C raises predicted model changes to **1,247** instances per player, but the intersection **stays at 206 blue / 204 red**. The extra **431** predicted changing pixels per player contribute **zero additional source-change intersection** at this camera and registration. Recall remains unchanged; precision drops to blue **0.16519647**, red **0.16359262**. C slightly improves per-frame silhouette IoU for both players versus static, but produces worse temporal change support. Raw pixel change frequency alone is an insufficient recovery criterion.

**Decision:** Neither fixed-speed illustrative rig phase is a supported explanation of the 1994 source-racer motion. The candidate has not earned new geometry or source pose labels. Keep it experimental; diagnose which precise wheel/crank/fork/paint boundaries and observed source change clusters are missing, and whether the frozen camera/first-tick registration explains the residual before varying geometry. Do not sweep arbitrary per-frame parameters until identifiability improves. This is a bounded **negative** for these two motion hypotheses, not proof that no 3D model could reproduce the sprite sequence.

## Reproduce without another ROM replay

From the repository root, with optional NumPy, Trimesh and Pillow installed, supply the preserved #3103 source ZIP, the exact original upright GLB from retained artifact #13063969312 and the existing `analysis/data/racer-inverse-side-provisional-1205.json`:

```sh
python3 -m tools.art.evaluate_original_mesen24_continuous_pose \
  /private/verified/original-mesen-consecutive-1601-1624-20261103.zip \
  /private/verified/upright-efdc8425f252b4a0.glb \
  analysis/data/racer-inverse-side-provisional-1205.json \
  /private/new/art4k-three-arms.json
```

This offline renderer refuses the wrong source archive, wrong real GLB, changed camera and existing output. Its source geometry and camera remain frozen; all rig poses are absolute rest-based moves. Numeric receipt is `analysis/data/racer-original-mesen24-continuous-pose-control-20261103.json`, SHA-256 **`4fc431cbcdc21e2c84197869fd52e1131b5332215c27d44f48227fc577623b32`**. The accompanying cheap stdlib unit test recomputes source/model changed-pixel totals, intersections, precision, recall and IoU without rerendering any GLB or touching ROM evidence.

No owner approval, frame-accurate 1994 character animation, prospective generalization, final PPU 2D color ownership, art asset promotion or Windows release milestone follows.

## Follow-up: two predeclared actual upper-silhouette events

A subsequent *read-only* source-band audit of the exact same 24 original Mesen ticks localized all upper-band silhouette changes to one source event per racer: blue 1602→1603 has 27 upper changes, red 1605→1606 has 20. No other adjacent upper-band mask changes during the window. Blue lower band changes on every edge (527 of all 660 blue changed-pixel instances), as does red lower (454 of 659). The "upper" and "lower" regions are equal-height thirds of the occupied source-Y range, **not verified 3D body component IDs**. The blue event has another 20 middle/57 lower changes; red event another 41 middle/58 lower changes.

Before running a narrowly bounded real-model event check, the exact two source event ticks and **three after-pose candidates** were recorded on draft #2832. Both models at the before tick use the existing direct-drive +24°/tick rate and zero pitch, with the same frozen camera and source-anchor registration. At the after tick, only pitch changes among **0°, +10°, −10°**. Neither event tick nor angle is a prospective independent test, and the step size is reused from the earlier sine control rather than optimized to the original source. The genuine upright GLB/world-parent transformations and source original 24-tick ZIP are unchanged.

| Original source event | Original top-band changed pixels | Wheel-only model top changed | +10° step top changes / intersection | −10° step top changes / intersection |
|---|---:|---:|---:|---:|
| Blue 1602→1603 | 27 | 0 | 86 / 6 | 79 / 8 |
| Red 1605→1606 | 20 | 0 | 70 / 0 | 64 / 6 |

Whole-64px changed-pixel IoU blue for pitch 0/+10/−10 is **0.08823529 / 0.08474576 / 0.09130435**; red is **0.13868613 / 0.07818930 / 0.10775862**. The predeclared ±10° rigid upper-frame steps generate two to four times the original source top-band changes and intersect little of their actual location. For red, **27** (−10°) or **28** (+10°) additional predicted changing pixels also fall *outside the original occupied vertical envelope*, explaining why summed model changes across the three source bands need not equal whole-frame model changes. A sign change alone does not rescue the current fork/saddle pivot hypothesis. **This is a negative for the tested step amplitudes and pivot**, not an inference that the original 1994 upper frame lacks 3D motion. Do not sweep arbitrary angles to rescue a hand-picked retrospective frame.

The source-bound receipt is `analysis/data/racer-original-mesen24-event-pitch-control-20261103.json`, SHA-256 `fb64781ac7dfbb8de11012c2d569647358aca824cb6fc6cec073fbd795f39323`. The optional offline reproducer is `tools/art/compare_original_mesen24_event_pitch.py` with the *same four positional args* as the prior 24-frame comparison (original ZIP, actual upright GLB, provisional camera JSON, new no-overwrite result path). One cheap ROM-free test verifies the exact source-binding, all pixel-band totals and numerical pixel intersection metrics. No new original Mesen capture or generated shipping art.

**Next causal discriminator:** compare the observed upper change *location* with the projected source rig's frame/fork/saddle parts and fixed camera, including potential occlusion or missing localized deformation. Preserve original sprite paints and wheel/rim source region separately. Avoid geometry optimization until the pivot/camera hypothesis becomes identifiable.


**Receipt portability/safety qualification:** Both optional offline renderers now use the repo's `publish_text_once` atomic, exclusive hard-link publication, preventing check/write races with unrelated files. Both pinned result receipts use UTF-8 with **LF only**, independent of Windows or Linux newline defaults. The original HP output included non-deterministic elapsed runtime metadata and CRLF; those historical host details remain recorded above but are **not part of the normalized receipts**. The six fast receipt assertions pin canonical LF-only SHA-256, source/input identities and numerical spatial evidence. A different host's runtime belongs in stdout/performance logs, never the comparable content-addressed result.
