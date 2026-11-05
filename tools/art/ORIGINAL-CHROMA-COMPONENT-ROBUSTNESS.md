# Original-ROM painted connected-component and robust 2D axis witness

Small offline source-only continuation of #3047's occlusion/colour-variant analysis. It uses the same **authentic original-USA-ROM 64×64 composited sprite PNG corpus** (41 distinct original RGBA images representing 35 unique binary silhouettes across 59 labelled representations). It requires an exact original corpus manifest SHA, original ROM SHA and each PNG's decoded RGBA/binary alpha identity. No ROM pixels, PNGs or actual source painting are committed. One binary source silhouette continues to have one aggregate vote; alternate original colours are recorded without manufacturing novel 3D poses.

The existing original-chroma-axis descriptor uses all high-chroma P1 red/P2 blue pixels, with the top/bottom 3 occupied source rows and the SNES 7:6 physical-X pixel aspect. This tool **does not change or overwrite that historical descriptor**. It additionally partitions exactly those same source coloured pixels into 4-connected and 8-connected components, picks the largest 8-connected source region, and reports its own original source painted axis in *separate* fields. All ties, original pixel counts and full original axes remain available.

Independent actual source-corpus offline proof at fixed original images and classifier:
- 41 unique original colour images, 35 independent binary silhouettes; 28 P1 red and 13 P2 blue distinct RGBA examples.
- Under 8-connected adjacency, **29 images contain one painted component, 9 have two, 3 have three**. Under stricter 4-neighbour connectivity, 26 have one, 10 have two, 5 have three.
- The largest 8-connected region accounts for at least **95.45% of each original image's high-chroma player pixels**, so the painted-axis geometric cue is predominantly one coherent original 2D shape. This does **not** establish the original game 3D fork as its single physical anatomical source.
- Across 41 original colour variants, the robust largest-component axis differs from the original all-painted-pixel axis by a mean of about **0.845°**, maximum **6.63°**. Using the same retrospective 2026 5-degree GLB blue-frame hinge projection under the provisional side camera, that source-only perturbation changes **6 of 41** individual RGB-variant proposed hinge bins.
- Among six original binary masks carrying multiple authenticated colour variants, selecting a hinge using the original all-painted axis gives RGB-variant disagreements on three masks; the largest-connected-region alternative gives disagreement on only **one**. That makes connected-component cropping a promising **source descriptor sensitivity study**, not a proven better historical 3D joint or a verified semantic segmentation rule.

The original camera, 3D geometry and source-labelled 1994 PPU/OAM timing remain unknown. All thresholds and 2026 rig candidates have been inspected on the same source corpus; the comparison is in-sample. The original high-chroma pixels may include sprite-painted highlights rather than one rigid structural bar. Do not promote any candidate angle or apparent connectivity to shipping likeness.

Run (using the existing original source-corpus ZIP extracted privately into source-corpus.json and stock PNGs):

    python3 -m unittest tests.unit.test_audit_original_racer_chroma_components
    python3 tools/art/audit_original_racer_chroma_components.py \
      --corpus /private/source/source-corpus.json \
      --out /private/new/original-painted-components.json

This uses no optional NumPy, machine-learning segmentation, external source search, new CI workflow, new model, exporter, Pages site or gameplay code. Reports use the repository's existing no-replace publication guard. The next engineering task is to compare **original 2D painted-component endpoints** against each depth-visible 2026 GLB fork endpoint under all tied source wheel-centre positions, and demand cross-source consistency before adjusting canonical geometry.
