# Canonical authored 2026 GLB surface identity across independently verified exports

The one 2026 OpenSCAD source of record, SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`, has produced legitimately different binary GLB SHA-256 values in actual independent GHA model-export attempts. This does **not** necessarily represent different geometry. The current attempts' `mesh.extras.file_path` contains randomly named `.ur-art4k-staging-...` directories, and byte-buffer vertex/triangle enumeration can differ while retaining identical oriented polygons. A historical fixed binary GLB digest must never be used to authenticate a fresh exact-source GLB export; the existing current-success source SHA and exact-attempt receipt remain authoritative.

## Exact real-run evidence (November 4, 2026)

Three independently produced full source-verified **upright** actual 2026 GLBs, all 5 parent / 16 material child meshes, one source SCAD and original rendering camera:

| Existing qualification source | Exact model binary SHA-256 | Result of new canonical surface audit |
|---|---|---|
| [#3117 run #41830180568](https://github.com/gamesbyian/UR-Recomp/actions/runs/41830180568), artifact `13322867450` | `bdb2f5bb92735fe023adda73be53b982e1d9added5150eb092c08ae08cc0e5da` | same |
| [#3119 run #41868992057](https://github.com/gamesbyian/UR-Recomp/actions/runs/41868992057), artifact `13342244513` | `4ff9c9579f7d24fe14836f6bb16a9dd5b94864607dc7ed8d29e3a9e99a867175` | same |
| [#3120 run #41870339775](https://github.com/gamesbyian/UR-Recomp/actions/runs/41870339775), artifact `13344052870` | `a330b72b23a03f3cc3363e5718922d27a010f2d8278dc64379fa76574947bf03` | same |

Their independent in-memory 2026 GLB canonical fingerprint for the *complete oriented triangle multiset, exact float32 vertex positions, winding, duplicate triangle multiplicity, each source material RGBA, sixteen material names/parent identities and their world transform matrices rounded to 9 decimal places* is identical:

`bd4c68104c854226a5f769a3bf39b3a7ee56314b0f7e5e85cee98b933ad89932`

The full binary GLB bytes and raw SHA differ; this SHA is **not** an authentication replacement. It is a source-authoring geometry/content equivalence discriminator, limited to these declared model features. Vertex normals, triangle UVs, PBR shader state, lighting and arbitrary source XML metadata are outside this fingerprint. The original 1994 authored mesh, camera, joints, materials and likeness remain unrecovered.

## Method and qualification

`tools/art/fingerprint_authored_glb_surface.py` parses the *actual exported GLB* under the existing Trimesh offline dependency and rejects a wrong five-parent/sixteen-child graph. For each one-colour child material, it normalizes each triangle only by cyclically rotating the three float32 vertices to the lexicographically smallest winding-preserving start, sorts the complete triangle multiset, hashes it and records the parent world matrix and actual material RGBA. It then hashes a sorted, compact JSON manifest. Thus a different buffer index order, triangle iteration order, or ephemeral file path leaves the source surface fingerprint unchanged. Actual geometry, winding, colour or 2026 parent pose changes the fingerprint.

The new unit tests use synthetic 2026-style actual GLBs with shuffled vertex/triangle enumeration and random authoring paths, proving unchanged source surfaces and detecting negative changes to geometry, winding, material colour or saddle mount. The existing source fork-mass real GLB A/B workflow uses the resulting stable surface fingerprint alongside **exact per-export binary SHA checks**, without another OpenSCAD run. It verifies the unchanged source against the three-run frozen reference and that the *only* material-surface differences in fork1.4 occur in the `fork_and_frame` child meshes. There are no new recurring workflows or speculative original 1994 GLB claims.

## Reproduce

```sh
python3 -m unittest tests.unit.test_fingerprint_authored_glb_surface
python3 -m tools.art.fingerprint_authored_glb_surface \
  --glb /exact/source-validated/current/upright.glb \
  --glb-sha256 ACTUAL_SHA_FOR_THIS_ATTEMPT \
  --out /new/fingerprint.json
```

Only the 2026 experimental model authoring/export pipeline is tested. No native Windows art, source ROM, original 1994 camera/physical angle, original source material identity or shipping-likeness approval is claimed.
