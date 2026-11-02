# ART-4K: live original-game PPU/OAM temporal witness gate

**Evidence correction:** The existing 35 source silhouettes are genuinely recomposed from the canonical original USA ROM. However, the existing 27 windows and 109 adjacent integer `guest_frame` pairs come from a curated authored registry, not an independently executed live-emulator PPU animation trace. See merged #3025. Prior 19 changes / 90 holds quantify that *registry*, not proven live 1994 timing. The 2026 GLB pose and motion experiments remain valid descriptive source-mask comparisons.

This ROM-free **validator contract** prepares for an actual source-emulator capture without inventing it. There is **no captured live trace shipped or claimed** here, no new emulator, no C++ runtime changes, and no new workflow. Use the existing pinned Snes9x original-source emulation and a deterministic replay/capture path. A separate producer must actually extract and retain each rendered 64×64 original racer alpha mask per emulator frame, and bind it to the actual emulator frame index, recorded input replay frame index, P1/P2 identity and live PPU/OAM snapshot hash. Include the actual emulator executable/source revision hashes and canonical original ROM SHA.

The manifest schema `UR-ART4K-LIVE-ORIGINAL-PPU-FRAME-WITNESS/1` requires `source_kind=live-original-emulator-PPU`, `recorded_by_live_emulator=true` and `registry_sequence_reused_as_live_capture=false`. Each `frames[]` entry needs `emulated_frame_index`, `input_replay_frame_index`, `player`, `binary_alpha_file` under the relative `frames/` directory, the SHA-256 of that **raw 4096-byte binary alpha array**, and the hash `oam_sha256` of the corresponding captured PPU/OAM state. The current schema guarantees local file identity, monotonic chronology and elementary capture provenance declarations; the future live capture producer and independent emulator receipt must also prove the source was actually executed. **A manifest can falsely claim live provenance**, so do not regard a passing validator alone as independent emulator proof.

Run:

```sh
python3 -m unittest tests.unit.test_verify_original_racer_live_ppu_witness
python3 tools/art/verify_original_racer_live_ppu_witness.py \
  --manifest /private/source-emulator/ppu-witness.json \
  --out /private/new/verified-live-original-edges.json
```

Only successive emulated frame numbers **and** successive replay-frame numbers for the **same player** form a temporal edge. Gaps never imply frame holds, duplicate/backward timestamps are rejected, and P1/P2 are separate tracks. The resulting counts are derived from actual provided binary mask bytes; there is no hardcoded 109/19/90 expectation. No source-index-to-2026-rig-time mapping or art/likeness/3D camera claim is made.

**Next required engineering witness:** instrument original Snes9x at a documented PPU/OAM display boundary using a deterministic input replay. Store complete window captures, not just changed frames, including frame index, replay tick, player identity, original ROM hash, framebuffer alpha (with explicit segmentation method), actual OAM bytes and source emulator executable hash. Independently verify the instrumented original core against the pinned unmodified source and audit timing: paused vs advanced frames, sprite disappearance, interrupts, frame repeats, player context and rendering vs CPU-step boundaries. Only then join live alpha hashes to the ROM-composed authored registry and determine true original animation cadence/holds and genuine source-frame identity. No acceptance credit until that live producer and reviewer exist.
