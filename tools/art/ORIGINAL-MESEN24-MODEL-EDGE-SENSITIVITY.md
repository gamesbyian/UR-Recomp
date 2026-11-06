# Exact original Mesen24 source-edge sensitivity audit, no model rerender

The same authenticated original USA Mesen 24-tick blue/red PPU frames are retained for retrospective reconstruction diagnostics. A physical 2026 GLB candidate may fit **every individual static silhouette better** yet match fewer real chronological changing pixels. Pooled motion IoU weights all 23 genuine adjacent original source transitions, and a few large source events may materially influence it. Excluding such transitions in a *sensitivity calculation* can locate a difficult source edge, but they **must remain in the actual qualification score**.

Use the existing no-render analyzer on an original completed source-verified research artifact (from #3185 or future successors). Pass the exact full JSON artifact SHA256, and one or more paired candidate/control names **from that same original Mesen+GLB run**:

    python -m tools.art.audit_model_pose_edge_sensitivity \
      --source-report /verified/original-all24-saddle-only-generalization.json \
      --expected-sha256 8531418406006a447fbf8a0e234bdf2fe393587cd87c56fc35c53f458c00a747 \
      --pair axle_root_hub_cover_fixed_tick_24deg axle_root_saddle_world_level_fixed_tick_24deg \
      --pair axle_root_hub_cover_rom_phase_15deg axle_root_saddle_world_level_rom_phase_15deg \
      --out /tmp/source-original-temporal-edges.json

The auditor authenticates the exact original USA ROM/Mesen/camera/2026 SCAD hashes, rejects missing/duplicated source frames, demands all true 23 adjacent edges, conserves original changed-source pixel TP+FN, checks per-edge and pooled IoU against TP/FP/FN, and verifies source static 64×64 image original-alpha counts. Outputs contain 24 per-original-tick static gains, 23 per-original-edge motion deltas, and the three largest positive/negative leave-one-edge-out influences. No ROM bytes or original sprites are copied. Every result explicitly disclaims a recovered original 1994 production mesh/camera/kinematic joint, source-image region being an original physical part, prospective blind holdout, or shipping art approval.

The previous source-qualified 2026 wheel-rotating housing (#3185) improves **24/24** blue source frames under both frozen drives, red **24/24** under the ROM-phase drive, and red **23/24** under fixed-tick drive. Its genuine red original motion IoU declines under both hypotheses. Under fixed-tick drive, edges **1621→1622** and **1605→1606** contribute the two strongest negative leave-one-out influences, approximately -0.00488 and -0.00454 toward the overall -0.01275830 pooled motion delta. These are retrospective diagnostics, not a reason to remove those original frames or fit each role separately. The next source-owned 3D joint comparison (#3190) tests whether the same 2026 dark physical shell rotating with the wheel versus remaining locked to the axle changes this conservation trade-off.
