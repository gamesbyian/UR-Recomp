# ART-4K authentic original raster temporal motion witness

This is a strictly **1994 USA ROM-derived 2D observation ledger** for the original racer source. It is neither a recovered 1994 3D rig nor a mapping onto the five experimental 2026 GLB poses.

The existing ROM compositor's immutable `source-corpus.json` contains registered original guest-frame windows, original P1/P2 representation identities, PNG SHA, decoded RGBA and binary alpha-mask SHA. Prior art research has established 91 registered temporal frame observations, 59 representation identities and 35 distinct silhouettes in 27 windows. Existing audits count those pixels and classify source-colour axes, but **do not preserve and inspect temporal edges**.

New `tools/art/audit_original_racer_temporal_motion.py` first revalidates the complete original ROM receipt via the existing `freeze_racer_source_family_splits.validate_corpus`. It independently reopens and SHA-checks every original 64×64 PNG and decoded alpha, recomputes the visible bottommost alpha x2/y2 midpoint, and calculates the original player's P1 red / P2 blue image-space chroma axis. For each player, it walks **only consecutive entries inside the same registered source window** and records actual source guest frame numbers, delta, whether they are truly adjacent integers, original representation identities, three mutually exclusive transition classes, visible bottom-alpha midpoint change and original 2D painted-axis delta.

The three transition classes are (1) **identical source RGBA hold**, (2) **colour change with identical silhouette** and (3) **binary silhouette change**. An unchanged chroma-axis slope does not imply an unchanged image; different original binary silhouettes can share the same angle. Absent player observations break that player's tracked sequence, rather than silently bridging across missing data. Every edge retains its original guest-frame step; no gap is rounded into one frame of movement.

The output contains per-window and per-player counts, exact source frame pairs and a summary of bona fide consecutive guest-frame pairs, holds and different source changes. Source representation SHA and the authenticated USA ROM/corpus digest bind the result. The source bottom-alpha midpoint is a visible raster anchor, **not** independently identified physical tire contact.

## Reproduce

    python3 tools/art/audit_original_racer_temporal_motion.py --corpus /private/verified-original-corpus/source-corpus.json --out /private/new/original-temporal-edges.json
    python3 -m unittest tests.unit.test_audit_original_racer_temporal_motion

No source ROM bytes, raster images, original 3D model or second viewer are created. The tool is stdlib only and reuses existing art-source modules. The existing opt-in, path-triggered original-ROM GHA research producer runs it after actual original source recomposition and emits the immutable numeric JSON report alongside silhouette, visual redundancy, colour-axis and experimental GLB comparison evidence. No extra scheduled agent/workflow.

## How this should guide the continuous 2026 rig

The single draft OpenSCAD rig already has parameterized `ride` and `stunt_cycle` poses, and its exporter supports source-owned sampled time. The separate **real GLB acceptance PR #2996** validates two actual authored samples without inventing original-game time mapping. This original raster witness is a chronology for comparing possible future sampled paths, not an automatic time synchronizer. Construct later registered frame-wise hypotheses on original windows 1205–1220, 1230–1239, 1244–1252 and 1261–1267, with genuine holds, independent original source masks and visible contact motion. Do not fit all parameters on the one ten-frame family and then describe its duplicates as holdouts.

Correct 2D motion evidence is necessary but insufficient: the 1994 3D camera, the true part hierarchy, the source sprite-to-2026 pose correspondence, owner character likeness and shipping art remain explicitly **unverified**. The source authoring rig #2832 remains draft, and the existing Pages 3D viewer remains the only visual comparison surface.
