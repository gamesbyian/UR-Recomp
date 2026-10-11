# UR-Recomp: evidence-backed technical motion graphics

Four **committed 1920×1080 H.264 MP4s at 30 fps**, independently decoded and frame-count checked. Artifacts include representative frames and per-clip SHA-256 manifests. No guest code, source-of-truth research ledger, native renderer, Modern frontend, master trailer or Agent 3 art files have been touched.

| Movie | Duration | Precise claim |
| --- | ---: | --- |
| [01. Original centre pixel parity](01-source-centre-parity.mp4) | 6 sec / 180f | 2P Original at native guest frame 1856: **0/57,344 RGBA centre pixel differences** between independent fixed and wide PPU renders; separate guest CRC streams **2473/2473** agree. Editorial grids, not real PPU pixels. |
| [02. Recorder non-interference](02-recording-noninterference.mp4) | 6 sec / 180f | Capture-disabled and capture-enabled native guest WRAM CRC streams agree byte-for-byte on recorded 2P route; the real source video has 600 consecutive guest IDs. Editorial bars, not actual CRC magnitudes. |
| [03. Genuine PPU raster anatomy](03-source-raster-xray.mp4) | 6 sec / 180f | One **real composited** 342×224 PPU source frame, exact 256×224 centre, 43 authentic extra source columns each side, and an editorial split-screen coordinate guide. No separate recovered BG/HUD/OBJ layers or recovered sprite masks asserted. |
| [04. Same-function 65816 → AOT C → real native play](04-machine-code-to-native.mp4) | 9 sec / 270f | Real `MainLoop` at `80:8881`, US retail opcode `20 C6 AC` (`JSR $ACC6`) independently checked against the original ROM; the **same routine's** generated `L_8881_M1X0` C from pinned Baldosa, separate real host glue, and real continuous native gameplay sampled from 60fps down to 30fps without interpolation. |

**Provenance:** Accepted [Original centre parity QA](../../../../docs/QA08-NATIVE-STOCK-CENTER-PARITY-20261010.md) run `38083079741`, artifact `11681138053`; [native continuous capture](../recruitment/continuous/README.md) run `38089655141`, artifact `11683697184`. Footage came from **960×540 physical SDL captured natively**, delivered 1080p; it is **not** a physical-4K or Remastered-wide capture. Original-source 342×224 PNG SHA256: `4dd40af5c80aa670de15c474f02c89f8e9ac7b6f689e894e67da66f59a18e79c`.

**Correspondence exhibit:** The ROM instruction is verified in `04-mainloop-bytecode-evidence.json` by `tools/showcase/verify_mainloop_codegen.py` against canonical USA retail ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. The generated C comes from [Baldosa pinned guest commit 10b864...](https://github.com/gamesbyian/uniracers-recomp/blob/10b864b9d14a7b7416dd909eb7b054c88faef101/src/gen/bank00_part01_v2.c), Git blob SHA1 `cc9ef833a5c7c0809aaab53ea00c182158241b83`. [Source exhibit](mainloop-aot-source-exhibit.txt) marks omitted code explicitly. The adjacent `GameRunOneFrame` C is separate host integration code, not the generated MainLoop.

Reproduction (checkout with original ROM, source videos, Python3/Pillow/FFmpeg/DejaVu):
```sh
python3 tools/showcase/render_technical_motion.py --repo-root . --outdir media/showcase/2026-10-10/technical-motion
python3 tools/showcase/render_technical_source_xray.py --repo-root . --outdir media/showcase/2026-10-10/technical-motion
python3 tools/showcase/render_technical_code_to_gameplay.py --repo-root . --outdir media/showcase/2026-10-10/technical-motion
```

The path/branch-limited `.github/workflows/technical-evidence-motion.yml` encodes, independently decodes and commits only this lane's assets. Read `provenance.json`, `03-provenance.json`, `04-provenance.json`, and `04-mainloop-bytecode-evidence.json` for exact identities. The workflow is inert after merge to main. Agent 1 owns final trailer assembly.

**Scope:** Source-centre pixel parity, native capture non-interference, generated-instruction correspondence, original/native gameplay equivalence and 4K physical output are separate evidence claims. No whole-game certification is implied.
