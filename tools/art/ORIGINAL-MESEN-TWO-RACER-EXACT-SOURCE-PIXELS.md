# ART-4K: authenticated original two-racer OBJ pixel matching

## What was reconstructed

This is the first fully pixel-exact **2D sprite-to-original-screen correspondence** derived from an actually executed original USA-ROM emulator memory capture, not from hand-labeled 27-window sprite registry times or the provisional 2026 GLB.

Authenticated original [no-frame-skip Mesen replay #41574463232](https://github.com/gamesbyian/UR-Recomp/actions/runs/41574463232) supplied both independently repeated source OAM (544 bytes), VRAM (65,536 bytes), CGRAM (512 bytes) and the original 256×239 completed-screen P6 on emulator bridge tick **1219**. The complete exact source archive is #13203312348, SHA-256 `7106fadd8d37b134f53501a251c281e88fd0336514a123ed70b1855aedf513f7`. A separate [real Mesen source serialized PPU run #41582586941](https://github.com/gamesbyian/UR-Recomp/actions/runs/41582586941) established that OamMode **4** means **16×16** small and **64×64** large objects, original OBJ VRAM WORD-addressed tile base `0x6000`, second table WORD-address offset `0x1000`, at `ppu.scanline=225`.

The source producer `tools/art/audit_original_mesen_obj_screen_pixels.py` uses existing independently tested original OAM decoder and SNES planar 4bpp tile decoder, applies horizontal/vertical flags, tile number wrapping, original OBJ CGRAM palette selectors and palette-zero transparency, and reproduces pinned MesenCE's exact 5-bit to 8-bit channel expansion, `(v << 3) | (v >> 2)`. This exact conversion matters: an approximate `v*255//31` expansion falsely reported incomplete matches for colour pixels.

The original screen search does **not** segment sprite shapes or tune the emulator, rig or camera. It scans bounded upper and lower viewport translations and counts **exact matching RGB** for every opaque decoded 2D OBJ pixel; all three raw source arrays, original screen P6 and source register identities must match their authenticated SHA receipts and the two independent no-frame-skip replays must agree byte-for-byte. The bounded [actual-source proof run #41585156448](https://github.com/gamesbyian/UR-Recomp/actions/runs/41585156448) passed. Its numeric artifact #13207691999 ZIP SHA is `8a7ad0a8d01c0ed800e49eea0e9bb3bdc3ddc92a9f067d2943fff743eb255efb`, and embedded JSON SHA is `c80897b07b98a655d243a6ba9fc01b4c713f5ae92daa6cf75fe71dd27c671945`.

| Source OAM slot | 2D colour | Original measured OAM (x,y) | Exact displayed screenshot (x,y) | Exact opaque RGB matches |
| --- | --- | --- | --- | --- |
| **96** | Blue | (104, 153) | **(104, 160)** lower viewport | **323 / 323** |
| **97** | Red | (104, 153) | **(104, 47)** upper viewport | **327 / 327** |

The runner independently searched the opposite screen region too: its best scores were **137/323** for blue-in-upper and **139/327** for red-in-lower. Neither wrong-viewport candidate matched fully. Both genuine 2D OBJ rasters occupy 64×64 transparent planes with only 323/327 opaque source pixels.

**These source 2D silhouettes are not identical recolours.** Their 1-bit alpha masks overlap in **278** opaque pixels, their union is **372**, giving IoU **278/372 = 0.7473118279569892**; **45 pixels are blue-only** and **49 red-only**. Both source index-plane SHA, RGBA SHA and alpha-mask SHA identities are frozen in `analysis/data/racer-original-mesen-two-racer-obj-screen-exact-match-20261103.json`. This is evidence of distinct 2D sprite contents or poses, not proof of which physical original 1994 3D components differ.

## Source timing and geometry boundaries

The **held** original OAM x/y for both sprites is (104,153), but their **completed displayed** locations are different. This is consistent with the game updating sprite positions for split-screen composition and reading OAM at a later held scanline; the exact per-scanline OAM writes, phase relationship and draw priority have **not** been captured. A pixel-exact match means the original OAM/VRAM/CGRAM produced the right 2D colour source asset, and that those opaque pixels appear on this original screen. It does not certify that a single held OAM snapshot describes every displayed scanline.

Tick 1219 is still in the original two-player **race countdown**. A large graphic overlays other screen areas, so the scene is unsuitable as the final isolated 3D pose/animation reference. Use the now-merged bounded manual workflow for **post-countdown** screenshots and establish source PPU/time registration across real motion. The user-facing Pages model/pose viewer may use these proven 2D sprite rasters as original reference geometry, but the underlying 1994 3D unicycle mesh, skeleton, bone pivots, 3D camera, animation track, source-to-2026 GLB pairing, alpha per-scanning-line and owner likeness have **not** been recovered or approved.

## Reproduce from source SHA-bound artifacts

```sh
python3 -m unittest tests.unit.test_audit_original_mesen_obj_screen_pixels
python3 -m tools.art.audit_original_mesen_obj_screen_pixels \
  --original-no-skip-zip /path/to/artifact-13203312348.zip \
  --source-register-summary analysis/data/racer-original-live-mesen-ppu-serialized-registers-20261103.json \
  --out /private/new/exact-original-obj-screen-proof.json
```

The original archive expires around November 10, 2026; rebuild using the recorded original ROM, pinned Mesen revision, two-pad input replay and no-frame-skip source capture rather than substituting screenshots. The bounded numeric proof and its exact content identities remain committed permanently. No new regular GitHub Actions workflow is needed to rerun already authenticated 2D pixel matching.
