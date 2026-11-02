# ART-4K exploratory temporal pose-label baseline

This is a **ROM-free algorithmic primitive**, not authentic pose fitting or an art approval. It consumes externally measured per-frame **costs** for each of the five existing authored GLB poses. Lower costs are better. It never opens or changes original sprites, GLBs, camera, meshes or the Pages viewer.

Usage: `python3 tools/art/fit_original_racer_pose_sequence.py input.json --output report.json`.

Input schema example:

```json
{
  "poses": ["upright", "bank"],
  "change_penalty": 0.03,
  "frames": [
    {"id": "source-frame-1205", "family": "fit-connected", "costs": {"upright": 0.41, "bank": 0.37}},
    {"id": "source-frame-1206", "family": "fit-connected", "costs": {"upright": 0.40, "bank": 0.38}}
  ]
}
```

`costs` must be numeric nonnegative losses, e.g. `1 - IoU` after **identical source and camera registration**. The input order must already be authenticated chronological order. Every contiguous family segment is fitted separately, with no fabricated transitions across missing frames. Optional `transition_penalties` is a complete nonnegative pose×pose transition-cost table. Otherwise the constant `change_penalty` penalizes pose-label changes. This is a deliberately conservative *discrete baseline*; its transitions are not physically calibrated joint dynamics.

**Critical next step before claiming a source result:** bind source-frame IDs, chronological adjacency and SHA-pinned cost matrix to the authentic 109-edge original temporal ledger and 35 verified original silhouettes; freeze full animation-family holdouts before selecting penalties; compare independent and sequence selection on *actually contiguous frames*, with emission and motion terms separately reported. Test registration/camera hypotheses separately. Do not infer original semantic labels from this output. In particular, selecting bank for every original silhouette remains a possible degenerate optimum and should be reported rather than suppressed.

Independent evaluation must inspect transition plausibility, ambiguity, held-out families and source-provenance integrity; this tool has no model or art approval consequences.
