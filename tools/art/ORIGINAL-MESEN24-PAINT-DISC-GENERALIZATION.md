# Original Mesen24 source paint around the wheel: independent timeline cross-check

**2026-11-05, research only.** Extends the already merged original source-painted 2D census [#3050](https://github.com/gamesbyian/UR-Recomp/pull/3050), painted-axis/GLB analysis [#3051](https://github.com/gamesbyian/UR-Recomp/pull/3051)–[#3053](https://github.com/gamesbyian/UR-Recomp/pull/3053), and tied-wheel-ring/material fraction audit [#3055](https://github.com/gamesbyian/UR-Recomp/pull/3055). Those studies used **41 exact RGB images / 35 independent alpha silhouettes** from the original ROM-composed 2D corpus, and already reported that more source high-chroma paint occupies the wheel disc than the provisional 2026 GLB's visible blue fork material. This cross-check uses a **separately executed genuine 24-tick consecutive Mesen PPU source timeline for both racers** without running the emulator or refitting the original wheel detector or red/blue classifier. It is neither a genuinely prospective blind holdout nor independent historical 3D views.

## Pinned evidence input

- Run: [UR Windows Visual Atlas #42049555726](https://github.com/gamesbyian/UR-Recomp/actions/runs/42049555726), **latest-head successful attempt**, real model/source artifact **#13433963866**, immutable extracted ZIP SHA-256 `a7db1c808b9314f2c6ce893a9d746d35264123e193068ee291bfb464b18e90f2`.
- Original source manifest member: `real-model-site/model-review/original-mesen24/source-poses.json`, exact bytes SHA-256 `5664bf5300ee42d94dcaa72ca10e29ed7277b244f11a63a93440780e8884045b`.
- Original USA ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; source Mesen24 ZIP SHA `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`; original phase/orientation report SHA `6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20`.
- Each of 48 actual PNGs is 64×64 lossless RGBA, source-verified by individually recorded original PNG and decoded-RGBA SHA-256, original OAM 96/97, actual original 24 phase×64 orientation integer, and unique tick 1601–1624. Original model 3D or physical pose correspondence remains false.

**Frozen, reused functions**: `source_chroma_pixels` using the *existing* high-chroma classifier (`blue: B≥64,B>2R,B>2G`; `red: R≥64,R>2G,R>2B`), `ring_candidates` using existing 48-rim-sample gray-ring detector, 64px source canvas search box and sample threshold, and `disk_band_fractions` with the already fixed **7 logical pixel** wheel disc. These were defined for the earlier 41-RGB study and are **not retuned on new sprites**. All equally scoring rim-centre ties remain in an uncertainty envelope; repeated ticks do not count as independent shapes. For a binary-alpha shape with multiple genuine RGBA variants, average variants first, then give each shape one vote.

## Observed source-only prequalification result

The existing detector succeeds on all 48 signed source observations, always returning radius 7. Blue original source 24 ticks yields **19** distinct alpha masks, blue ring score 42–43 of 48 samples, with 1–3 tied ring centres per tick. Red original source yields **23** distinct alpha masks, ring score 43–44, with 1–2 centre candidates. No candidate was chosen based on the 2026 model.

| Exact source-only high-chroma measurement | Original blue, 19 equal-shape votes | Original red, 23 equal-shape votes |
|---|---:|---:|
| Mean fraction inside **all tied original 7px ring discs**, lower bound | **0.58260667** | **0.58674359** |
| Same, upper bound | **0.61296669** | **0.59078737** |
| Mean fraction at/below rim top, lower bound | 0.69053561 | 0.77837575 |
| Same, upper bound | 0.70602699 | 0.77837575 |

These numbers were independently calculated from the exact retrieved 48 authentic PNGs with unchanged original-classifier/ring formula; the new scripted source verifier and reducer must reproduce them in a separate execution before the numeric result is granted definitive source-receipt status. Retain at least one full 48-PNG auditor artifact, not source images in Git.

Earlier 35-shape original source wheel-disc result: **0.59102807–0.59558799**, versus **0.29678519** depth-visible 2026 GLB blue material under its *separate* frozen experimental +world-Y camera and hinge hypothesis ([#3055](https://github.com/gamesbyian/UR-Recomp/pull/3055)). The new two-player Mesen24 source-only fractions show the same broad original-colour-in-wheel phenomenon. The 2026 model fraction is an earlier, unpaired model comparison, **not measured at the Mesen24 source poses**, so do not compute a new 3D fit from the table or infer the original physical wheel or fork geometry.

## Implication for actual 3D reconstruction

The problem cannot reasonably be solved by simply stretching the 2026 saddle or doubling the fork diameter: the original coloured pixels occupy wheel/hub/spoke/crank/intersection space. **Original red/blue paint identifies a 2D source region, not one guaranteed 1994 physical fork.** The 2026 GLB currently paints one fork/frame material while original lower paint may be crank, hub, spoke, wheel or occlusion of several parts; part ownership and original 3D camera are underdetermined. A next bounded mechanical/visual question is how *source-authored paint allocation across the existing wheel, rim, hub, pedal and fork parts* affects source 2D disc occupancy, while holding all geometry, source model pivots and original Mesen raster evidence fixed. First use the existing Pages paint preview choices and the existing actual GLB z-buffer scorer; do not introduce a new rig or model-only fit oracle.

## Reproduce without regenerating original pixels

```sh
python3 -m unittest tests.unit.test_audit_mesen24_original_paint_disc
python3 -m tools.art.audit_mesen24_original_paint_disc \
  --source-artifact-zip /private/ur-experimental-model-review-actual-glbs.zip \
  --out /private/new/original-mesen24-paint-disc-crosscheck.json
```

The utility reuses all three existing source classifiers/detectors, decodes PNG losslessly with the repo's own bounded stdlib PNG reader, checks source PNG/RGBA/64px dimensions and fixed Mesen metadata, emits only numeric source hashes and per-tick fractions, then refuses output overwrite. No original ROM, 3D artifact, camera, material or runtime code is changed. The owner likeness veto, original camera, 1994 physical model and Windows ART/release gates remain unapproved.
