# ART-4K: source-authenticated sparse Mesen 2D pose capture in one replay

**Purpose:** avoid separate original-ROM emulator compilations/replays for every new 2D animation or pose sample. Reuse the existing no-frame-skip pinned MesenCE original capture path and one controller replay, but take **at most 24 deliberately spaced real bridge ticks** instead of only a contiguous 1–5-frame window.

The source-owned code is `tools/art/capture_original_mesen_ppu_raw.py` and `tools/art/capture_original_mesen_ppu_registers.py`. Their **default contiguous behaviour remains unchanged**. The sparse option adds a clearly marked `source_requested_capture_ticks` to the evidence manifest, and the existing SHA-verifying source-file validator only permits gaps when that explicit, strictly increasing, bounded list is present. Every frame between first boot and the last sample is still executed in the source Mesen bridge, with controller masks updated at their original replay steps; only the expensive *snapshots* are sparse. This is **one original emulator replay**, not independently executed multiple capture runs and not random access or savestate synthesis.

## Single-pass example

```bash
MESEN_SNES_DISABLE_FRAME_SKIPPING=1 \
python3 -m tools.art.capture_original_mesen_ppu_registers \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --input-file tests/input/two-player-first-race.input \
  --mesen-for-ai-repo third_party/src/mesen-for-ai \
  --mesen-executable /path/to/source-built/pinned/Mesen \
  --capture-ticks 1601,1613,1625,1661,1701,1741,1801,1881,1961,2081,2201,2361 \
  --include-held-framebuffer \
  --out-dir /private/new/sparse-original-poses
```

The example ticks are **a sampling plan, not proved distinct pose labels**. The existing first-race input replay has P1 Right/P2 Left through step1603 and neutral thereafter; it does not assert jumps, wheelies, bank angles, stunt controls or even continuous motion at every later tick. Inspect actual decoded source 2D index planes, alpha mask SHA and visible racer differences first. If repeated samples are redundant, **stop** and author a new explicitly identified and verified gameplay controller route rather than claiming animation coverage or expanding runs indiscriminately.

Allowed: 1–24 integer decimal bridge ticks between 1 and 2500, strictly increasing, no duplicates. `--capture-ticks` cannot be combined with `--advance-frames` or `--capture-frames` in the CLI. The original contiguous defaults 1218+2, 1600+5 and their raw source provenance stay intact; no sparse marker is emitted for legacy captures. The existing no-skip requirement is enforced by the PPU-register tool.

## Verification and stop rule

Synthetic ROM-free tests must prove exactly the selected snapshots, correct replay step index = bridge tick −1, intact source OAM 544B / VRAM 65536B / CGRAM 512B, optional completed P6 (plus selected PPU registers) in the *same* emulator hold, valid SHA-bound input, and strict refusal of duplicate, out-of-order, missing or forged manifest tick lists. The capture must reject pre-existing output directories. The old consecutive source capture validator must still reject missing intermediate frames.

Before treating a new **real** sparse run as evidence, authenticate the actual original USA ROM, Mesen source/executable SHA, input-replay SHA, no-skip setting, run artifact ZIP, complete PPU register identities, each raw file and completed P6 SHA and actual executed source bridge ticks. When a candidate sample has screen-text overlap, reuse the source-verified [#3080](https://github.com/gamesbyian/UR-Recomp/pull/3080) orientation/red-colour analysis *as a hypothesis*, not an automatic global postprocess. Do not call an inferred 3D pose or owner likeness accepted until the canonical #2832 experimental rig has been independently paired and tested against original-fit versus 19 withheld and strict six tile-disjoint original silhouettes.

**Cost rule:** do not add another default heavyweight CI workflow or recompile Mesen merely to validate this opt-in Python capture schedule. Focused ROM-free tests and hygiene are appropriate for the source change. One fresh original-ROM run is justified only when a defined set of actual, pose-diverse samples would change a real inverse-graphics modelling decision. No default Windows game, GLB geometry, renderer or release gate changes.
