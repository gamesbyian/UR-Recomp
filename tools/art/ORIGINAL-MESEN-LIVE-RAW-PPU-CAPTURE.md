# ART-4K: bounded live original MesenCE raw SNES PPU-state capture

This is the **first source-data producer**, not yet 1994 original 3D pose reconstruction. Previously archived 59 source representations are authenticated ROM compositions but their 27-window chronology was a **curated registry**. This tool instead runs the authentic USA-ROM in the pinned MesenCE emulator under the existing deterministic 2P replay and captures consecutive held emulator-frame states.

## Trust boundaries

The original MesenCE source revision `a60e79feb4d6dcced5922d636f9211837d01e381` defines three SNES memory regions `SnesSpriteRam`, `SnesVideoRam` and `SnesCgRam`; `Core/Debugger/LuaApi.cpp` exports `MemoryType` enum entries as `emu.memType.snesSpriteRam`, `snesVideoRam`, `snesCgRam`. The bundled read-only mesen-for-ai bridge now surfaces these types through `cpu.read_memory`. It does **not** change the emulator or ROM, does not write PPU registers, and does not invent a frame recorder.

Each captured held frame is authenticated by the tool's real `run.step_frames` response and independent `run.status` frame tick before/after the dump. It records raw emulator sprite RAM (544 bytes), full 64 KiB VRAM, and 512 CGRAM bytes in strict 1024-byte maximum transport chunks, all as write-once binary files and SHA256 metadata. Frame ticks refer to the **Mesen bridge's actual emulated frame counter**, bound to the exact original controller replay; a boundary-snapshot is not necessarily the final presented pixel frame corresponding to the same input tick.

The original 1994 SNES PPU display composition is **not** reconstructed by this raw memory census: full 64×64 player alpha, scrolling, clipping, OAM priority, sprite size interpretation, final pixel colour and painter ordering still require additional independent decoding, viewport/phase evidence and tests. Likewise source 1994 camera, continuous source 3D pose, alignment to the experimental 2026 GLB, and approval are explicitly **false** in the report. Do not pass this raw state to `verify_original_racer_live_ppu_witness.py` by faking required binary alpha files or declaring original player-level pose correspondence.

The correct next gate after raw capture is a separate source-verified, output-specific **OAM + VRAM + CGRAM to raster** decoder. Show per-object evidence and screen crop, and verify it against the actual emulator framebuffer at the same held tick before claiming any particular source racer sprite alpha.

## Run

```sh
python3 -m unittest tests.unit.test_capture_original_mesen_ppu_raw

MESEN_BIN=/path/to/pinned/Mesen \
python3 -m tools.art.capture_original_mesen_ppu_raw \
 --rom reference/roms/retail/Uniracers_USA.sfc \
 --input-file tests/input/two-player-first-race.input \
 --mesen-for-ai-repo third_party/src/mesen-for-ai \
 --mesen-executable /path/to/pinned/Mesen \
 --advance-frames 1218 --capture-frames 2 \
 --out-dir /private/new/original-live-ppu-states
```

One precisely targeted GitHub Actions workflow tests the real emulator path when this producer/bridge changes; it is not scheduled and it retains its two-frame diagnostic artifact for only seven days. All project release-quality, ART likeness and gameplay gates remain untouched.
