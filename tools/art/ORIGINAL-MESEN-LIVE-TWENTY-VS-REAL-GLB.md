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
