# ART-4K: freeze an exact original-tile-disjoint 2D holdout

**Source evidence only.** The authored original-ROM registry is not a live 1994 PPU capture, and the experimental 2026 GLB poses are not registered with it. This protocol restricts which original 2D silhouettes can be used as fit and holdout sources; it does not recover original 3D views, anatomical parts or timing.

The new `tools/art/freeze_original_racer_tile_disjoint_holdout.py` consumes two separately SHA-verified historical artifacts from earlier accepted experiments:

- the frozen original 41-PNG `source-corpus.json`, SHA-256 `e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e`, authored from original ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`
- the authenticated 8×8 source-tile lineage numerical report, SHA-256 `cccb78328307003b3f8148aa20ef7cca27c905e77610be2b3ffd1aa7e7d5f33f`, from source-only [run #41554638043](https://github.com/gamesbyian/UR-Recomp/actions/runs/41554638043) (producer in PR #3061). Its exact historical authored-registry SHA is `05372395d04d5403c7b80859c171f06d754f1322a676d66f4ce5d7b3aec948ad`.

First the original 27 authored windows are grouped by *transitively shared exact 4bpp index-plane hashes*. All windows in the connected component containing `first-1205-1220` become fit-only, even when there is no direct overlap with the first window. No original index plane appears in both fit and withheld. Only then do the independently authenticated *nonblank source tile* reuse edges define the stricter held-out subset.

**Predeclared numerical gates:** 16 fit-plane identities; 19 withheld-plane identities; 304 cross fit/withheld pairs; 13 positive pairs sharing any nonblank 8×8 ROM tile; six withheld planes with **zero** exact nonblank payload matches to *any* fitted plane. This is a conservative source-content leakage check on top of mask hash disjointness; a shared tile is not itself an original 3D part or a live motion transition. The six identities must be frozen before comparing experimental geometry variants or adjusting any camera.

ROM-free controls:

```sh
python3 -m unittest tests.unit.test_freeze_original_racer_tile_disjoint_holdout
```

Authenticate both original numerical witnesses and produce the report:

```sh
python3 -m tools.art.freeze_original_racer_tile_disjoint_holdout \
  --source-zip /path/to/authenticated/original-source-corpus.zip \
  --tile-lineage-json /path/to/authenticated/art4k-original-tile-lineage.json \
  --out /private/new/tile-disjoint-holdout.json
```

The output is a strictly **source-only** 2D index-plane SHA selection with corresponding authored representation IDs. It must never be treated as evidence that the original game presented those source masks in that chronology, or that the 2026 GLB camera/pose matches them. The experiment retains all 19 original withheld source shapes in the general holdout, while tagging a second, stricter six-shape source-tile-disjoint subset. A future geometry comparison must report both and must not choose its model after seeing the six-shape scores.

Implementation is pure stdlib. Future independent original-emulator PPU/OAM frames can replace the review-registry chronology, but that is a **separate** original-capture gate.
