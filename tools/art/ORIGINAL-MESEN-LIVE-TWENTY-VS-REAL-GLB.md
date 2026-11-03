# Source-authenticated twenty Mesen frames versus existing five real experimental GLBs

This is a source-screen-verified but 1994-pose-UNPAIRED diagnostic, not recovered 1994 geometry or owner likeness approval. It reuses the original source ZIP from merged PR #3088, the original frozen 16 fit / 19 withheld / strict six source index-plane split, the 2026 five real part-addressable GLBs from artifact #13063969312, and the preexisting SHA-pinned provisional P1:1205 camera (world right X, up Z, 7:6 pixel aspect, scale 9.5).

Independent locally executed research on the identical real artifacts found unpaired best IoU wins across forty original 2D observations: bank 29, upright 7, pedal 3, one exact bank/pedal tie (red frame1952), wheelie 0, stunt 0. Approximate best-score ranges: blue 0.381 to 0.630, red 0.395 to 0.670. These labels are the winners of similarity searches among only five 2026 authored poses, not proof the 1994 game presented 29 bank poses. The original 2D screen registrations are exact, but the original 3D joint pose identity remains unknown.

The new offline tool tools.art.evaluate_original_mesen_live_pose_matrix calls the exact #3088 source archive auditor first, then validates the real viewer GLB SHA identities, camera SHA, and every 64x64 index/alpha plane. Each GLB is rendered once with a frozen common camera and only the already source-derived lowest-alpha anchor translation is applied. It computes all 40 x 5 binary silhouette IoUs without any per-pose recentering, zoom, geometry fitting or label training. Any new source index plane absent from the precommitted 35 is marked unclassified rather than fit. This avoids contaminating frozen withholding simply by observing a new original Mesen frame.

Reproduce offline with numpy, Pillow and trimesh, plus the immutable source ZIP and extracted viewer artifact:

    python3 -m tools.art.evaluate_original_mesen_live_pose_matrix
      --original-zip /private/original-source-20.zip
      --model-review-dir /private/real-model-site/model-review
      --out /private/new/real-twenty-five-glb.json

Use the same command on one line with the arguments. The default camera, receipt and original role summary paths are committed in the repository. The output helper refuses to overwrite existing evidence. No additional emulator build, GLB export, default CI workflow, native renderer or shipping art is changed.

Interpretation: the original poses are more diverse than five consecutive frames, while the current five authored 3D poses with one provisional camera remain weakly discriminative. Do not select a supposed 1994 pose from the largest unpaired IoU. The next decisive experiment needs genuinely witnessed original wheel, saddle, pedal and motion transitions, a shared camera/rig hypothesis, protected fitting and holdout examples, and explicit uncertainty. The current original 1994 mesh, source-camera angle and independent owner likeness approval are still absent.

The initial exploration counted the red tick1952 exact pedal/bank IoU tie as pedal only because iteration checked pedal first. The reusable ranker now explicitly abstains rather than retrospectively assigning any original pose identity. In all cases the fixed camera and source alpha remain unchanged.

## Frozen real-artifact numerical result

The initial 40-observation local experiment is preserved in `analysis/data/racer-original-live20-five-real-glb-unpaired-diagnostic-20261103.json`: the actual source capture ZIP, real five-GLB source artifact, frozen original camera, 200 individual eight-decimal IoUs, precommitted role counts and negative original-3D/art gates are explicit. Original source roles among these 40 index-plane hashes are exactly **one historical fit, one historical withheld, zero historical strict-six and 38 unclassified live sources**. The full 2026 five-pose mean unpaired IoUs are upright 0.46812660, pedal 0.46552060, wheelie 0.24588637, stunt 0.17701848 and bank 0.48061737. The 40 nearest candidate outputs are **bank 29, upright 7, pedal 3, exact pedal/bank tie 1**. The tie is the red source tick1952 (IoU 0.67042254 each); choosing a winner based on Python iteration or alphabetical order would be unjustified. Model classification abstains on ties and never turns these experimental rankings into authentic source pose labels.

Numerical scores were independently computed from the original 20-frame PPU ZIP and the real GLBs with world transforms, under the same fixed 9.5 camera and 7:6 PAR as the repository renderer. The new module recomputes that experiment from immutable artifacts; the ROM-free regression checks its frozen score census but cannot replace an actual five-GLB replay. No new fit parameters were selected after inspecting the withheld entries.
