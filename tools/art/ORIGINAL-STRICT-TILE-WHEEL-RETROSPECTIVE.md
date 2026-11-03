# ART-4K retrospective six-tile-disjoint source test of the experimental wheel width

**Design:** Previously merged #3009 and earlier original-source holdout scored the unchanged experimental five-part upright 2026 GLB with a frozen provisional camera under wheel-width factors **1.00 and 1.10**. That numerical work predated the *source tile-disjoint* six-sprite selection frozen later in #3062. This report only **re-aggregates already-published, SHA-bound source 2D mask IoU scores** using the six source index-plane hashes selected independently of geometry scores. There is no new rendering, new camera, 3D pose pairing, model fit, or prospective blind evaluation.

The source-only freeze from #3062 selects 16 fit-connected 4bpp index planes, 19 withheld original 2D source index planes, six with **zero overlapping nonblank 8×8 source-tile bytes with every fitting plane**. Source original 4bpp indices are joined to binary alpha SHA via the previously authenticated merged 41-image lookup; the old original-source IoU table is joined only by exact binary SHA, with complete one-to-one coverage required. The script rejects changes to any of its three **Git blob SHA-1** inputs and checks the underlying historical original-ROM SHA, source manifest, original unapproved GLB SHA and frozen provisional camera. Its per-source mask values are preserved at eight decimal places.

## Retrospective measurements

| Source-original 2D holdout | Count | Original wheel 1.00 mean mask IoU | Experiment wheel 1.10 mean mask IoU | Mean difference | 1.10 wins |
|---|---:|---:|---:|---:|---:|
| All source-plane-disjoint withheld sprites | 19 | 0.38192089 | 0.41491323 | +0.03299234 | 19/19 |
| Strictly nonblank-source-tile-disjoint subset | 6 | 0.38543972 | 0.41730258 | +0.03186286 | 6/6 |

Across the six strict examples the individual positive differences range from **+0.02749146 to +0.03545053**. Thus the previously observed unpaired projected 2D overlap preference for wheel width 1.10 is **not confined to sprites reusing the fitting set's exact nonblank SNES 8×8 tile bytes**. The six strict differences are modestly smaller than the 19-source aggregate (+0.03186286 versus +0.03299234), and the absolute overlap still leaves the majority of the source raster unmatched.

**Critical limitations:** the strict six subset was defined *after* the earlier source experiments and their scores existed, even though the selection algorithm used source tile hashes and **did not consult geometry scores**. It must be called **retrospective**, not a new blind source holdout, and these original registry 2D shapes are not independently verified different 1994 source 3D views or live PPU frames. Repeated 2D silhouettes/tile pixels do not imply repeated source animated bone motion; the existing 2026 GLB and camera do not have a verified original source pose correspondence. These 2D IoU differences cannot justify silently changing the default rig, claiming authentic wheel width or awarding owner likeness approval.

## Reproduce exactly

Use the three existing committed numerical inputs, no ROM or rendering dependencies:

```sh
python3 -m unittest tests.unit.test_audit_strict_original_tile_holdout_wheel_width
python3 -m tools.art.audit_strict_original_tile_holdout_wheel_width \
  --root . \
  --out /private/new/strict-original-tile-wheel-retrospective.json
```

The immutable numerical summary is `analysis/data/racer-original-six-tile-disjoint-wheel-width-retrospective-20261103.json`. The tool's exact eight-decimal score table retains both candidate scores for all 19 withheld index planes, with six clearly tagged. The model/material/Pages reviewer remains unchanged. Next genuine advancement is original emulator OAM/PPU pose alignment or new independently captured source viewpoints; another unpaired camera tweak based on the six scores would spoil their usefulness.


## Historical numeric-summary SHA correction

The first draft's strict original-source join failed its exact 19-mask membership check. That was a **valuable integrity failure**, not a reason to weaken the source SHA gate. The older durable summary `analysis/data/racer-wheel-x-genuine-rom-holdout-20261101.json` had one manually transcribed original binary-mask key `eb15bfa0705657438d3b22a6c3dca27f2e0abafb4d3b8749c8ad7e18249ca23f`, whereas the [original real run #41287222152 numeric artifact #13075379369](https://github.com/gamesbyian/UR-Recomp/actions/runs/41287222152/artifacts/13075379369), original `wheel-holdout.json` SHA-256 `aa86e13348875a768351d926a2daa913c3428732e92c2f38f135bbeadf53398c`, and the separately authenticated 41-image source 4bpp lookup all agree on **`eb15bfa0705657438d3c22a6c3dca27f2e0abafb4d3b8749c8ad7e18249ca23f`**. The one-character error was corrected in the old durable numeric summary; both candidate IoU values (0.37825059 / 0.41355140) were retained unchanged. The new exact input Git blob is `49db7090f3455b2a9cc7ae946888fb4413877fd8`. No fuzzy hash association or nearest-mask substitution is permitted.

This correction also explains why the older source report's declared aggregate 19-mask scores were true but its manually transcribed mask identity failed a stricter later join. The original actual score artifact is authoritative for its exact source input identifiers; later summary authors do not get to invent one-character aliases.
