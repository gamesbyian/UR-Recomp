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

## First actual original-emulator result (November 3, 2026)

The [real pinned MesenCE original-source workflow #41560222232](https://github.com/gamesbyian/UR-Recomp/actions/runs/41560222232) **passed** at the first draft capture producer. Its [original raw PPU archive #13196973168](https://github.com/gamesbyian/UR-Recomp/actions/runs/41560222232/artifacts/13196973168), ZIP SHA-256 `a1aa2d04ca936a031d6f46d821d4ece14a7bdbad03b4774f7ab705d275cef6cc`, contains two complete source snapshots and manifest SHA-256 `f50accd67c36cc8455bcb0cc5f774f0efaa233ebc62d68fb33da2c10eb86e21a`. The actual emulator's executable SHA-256 was `bb827bae9ab4059b7940e9a83a23d890bf9109f1973cc3ceb6c228f34b51e2c5`. This seven-day archive is expected to expire **November 10, 2026**; all full-array SHA-256 identities and independent counts are preserved in `analysis/data/racer-original-mesen-live-raw-ppu-20261103.json`.

The emulator genuinely held at consecutive bridge ticks **1219 and 1220**, corresponding to two consecutive replay steps. All six original binary PPU memory files independently matched their declared SHA-256, and each frame's two region sizes passed exact bounds. Between these frames **OAM differs in zero of 544 bytes**, **VRAM differs in 38 of 65,536 bytes**, and **CGRAM differs in 17 of 512 bytes**. The identical OAM proves only identical OAM *at these held boundaries*. VRAM/CGRAM changes can change the visible sprite or backdrop without moving OAM. These figures do not yet establish which source racer, sprite cell, on-screen region or final PPU pixel changed; proving that requires source OAM decoding and same-frame framebuffer comparison, with separate 1P/2P and foreground/priority logic. Do not describe this as original 3D pose animation or recovered 1994 rendered frame cadence.

The bundled `mesen-for-ai` island changed intentionally to expose three pre-existing upstream `emu.memType` aliases. Both repository hygiene and bootstrap originally rejected its old tree hash. The new local source digest `4d7e5778417ce1f5c4d344227a2e70da311f257e2cc59b80b7a7d23880cd9527` was independently reported by both checkers and is attested in `third_party/manifest.json`, preserving the same pinned original upstream revision rather than disabling validation.

## Executed held screen capture, actual original ROM (November 3, 2026)

The exact [pinned MesenCE run #41565384581](https://github.com/gamesbyian/UR-Recomp/actions/runs/41565384581) **passed** with the screenshot option enabled and independent source memory/hash checks. Its [seven-day full original PPU + rendered P6 artifact #13199861365](https://github.com/gamesbyian/UR-Recomp/actions/runs/41565384581/artifacts/13199861365) has ZIP SHA-256 `b72a1c805423f14847b257fe807be84559aa2a9e8914314ce1b8d24532f95964`, manifest SHA-256 `e63c9e51d82befcd9720439aaf5e37a822837690c0b64f52759466999700c38d`, and actual emulator executable SHA-256 `8d501dcdea86837387df1c1bca1e7660d2a5b1adbe822beff4f82935a50fe94b`. The exact source ZIP is retained until November 10, 2026; compact permanent numerical evidence is in `analysis/data/racer-original-mesen-held-framebuffer-20261103.json`.

At **both** consecutive live original emulator bridge ticks 1219/1220, Mesen's *held rendered video buffer* was P6 **256×239**, 61,184 source RGB pixels, 183,552 RGB bytes; the complete P6 SHA-256 was `3db1ead6ef6da21dc5c085f38dbd3fe8c17e00d4eba7900ce1074beaa9358cfb`. **No RGB pixel changes** between the two held screenshots, despite changed source PPU VRAM (38 bytes) and CGRAM (17 bytes), with unchanged OAM. All **17** changed CGRAM bytes were in the lower 256 raw bytes (SNES background-colour indices 0–127); no OBJ palette index bytes (upper 256) changed. Thus *memory changed* does not by itself prove *on-screen original racer animation changed*.

**Important source timing limit:** the emulator's exported video buffer is acquired at the same held bridge tick as the raw PPU memory, but may represent the **previous completed screen scanout**, and split-screen code may change OAM within a frame. Capturing one OAM register state at tick 1219 cannot explain both source player regions or establish per-scanline pixel ownership. The record explicitly keeps the 1994 original PPU scanout phase, original OBJ sprite visibility, source-to-GLB pose mapping, 1994 3D rig/camera and owner likeness **unverified**. Next capture discriminator is the original emulator serialized PPU `OamMode`/OBJ base/offset state and source replay aligned to a verified framebuffer phase; the pinned MesenCE source `SnesPpu::Serialize` exports all three fields. Do not infer sprite dimensions from high-OAM size bits without it.
