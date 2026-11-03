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


## Critical cross-run contradiction: held framebuffer cannot yet be a source sprite oracle

The first held-buffer report above remains a faithful observation **of that particular run only**. The independently successful [second real original MesenCE run #41566836578](https://github.com/gamesbyian/UR-Recomp/actions/runs/41566836578) produced [raw artifact #13199267815](https://github.com/gamesbyian/UR-Recomp/actions/runs/41566836578/artifacts/13199267815), exact ZIP SHA-256 `24b70f3a3468d628d57c1bc1a43915e8abaecb6a66dc6156fcb4b685a73610e2` and manifest SHA-256 `acd5c844e243d50c421892f53aba5d128dc5561e71759281e9e12d9767421185`.

Both runs independently matched **the same USA ROM SHA, deterministic input stream SHA, Mesen executable SHA**, and all six source-memory SHA hashes for OAM, VRAM and CGRAM at ticks **1219/1220**. The exported original 256×239 RGB screen pixels **do not match**:

| Original Mesen held buffer comparison | Different RGB pixels (of 61,184) |
|---|---:|
| Tick 1219, first run versus second run | **10,258** |
| Tick 1220, first run versus second run | **22,776** |
| First run tick 1219 versus tick 1220 | **0** |
| Second run tick 1219 versus tick 1220 | **23,593** |

The full byte-level SHA and repeatability contradiction is preserved in `analysis/data/racer-original-mesen-screen-repeatability-discrepancy-20261103.json`. The reusable `tools/art/audit_original_mesen_held_rgb_repeatability.py` requires both exact archived original artifacts and recomputes these counts without using any 2026 reconstructed GLB, RGB similarity threshold or guessed original pose label. The older first-run receipt now explicitly points to its contradictory independent follow-up, so its historical zero changed-pixel observation cannot be generalized.

**Causal interpretation is unresolved.** Pinned MesenCE `LuaApi::GetScreenBuffer` renders `_emu->GetPpuFrame()` via `BaseVideoFilter::SendFrame`. The bridge reads that through `emu.getScreenBuffer()` inside its `endFrame` pause loop. Reproducible memory regions plus bridge ticks have **not established equivalent full original PPU serialized registers, scanout phase, presentation buffer identity, or same-screen provenance**. It is therefore premature to attribute this to any specific emulator bug or to claim that either run's pixels correspond to the captured OBJ entries. The image export remains a valid, hashed output sample; it is not yet a deterministic original pixel-registration oracle.

**Acceptance for any future original sprite-to-rig model mapping:** capture exact original Mesen PPU serialized registers (especially OBSEL/OamMode, OBJ tile base, offsets and scrolling), tie the *last completed source framebuffer* to an independently verified scanout boundary and replay frame, and demonstrate **cross-execution same-tick full-state and RGB reproducibility** before original screen pixel ownership is used as a geometry constraint. If the source display remains inconsistent, report both screens and mark correspondence `unresolved`. Preserve existing original OAM/VRAM/CGRAM evidence; never repair this by arbitrarily choosing the better-looking frame or tuning the GLB camera to whichever screenshot appeared.

The SHA-guarded cross-execution repeatability producer was also executed successfully against both original historical archived source ZIPs in [one-off Actions run #41573485431](https://github.com/gamesbyian/UR-Recomp/actions/runs/41573485431). Its [numeric artifact #13202910464](https://github.com/gamesbyian/UR-Recomp/actions/runs/41573485431/artifacts/13202910464), JSON SHA-256 `f365c913b9e21107d660117670b9405f0699a219fe8de74ad4d7181c923f9893` (2,153 bytes), reproduces the 10,258/22,776 cross-run and 0/23,593 within-run changed RGB counts. The temporary historical archive-fetch workflow is removed from the final branch; original Mesen P6 capture remains path-triggered and opt-in. The persistent capture manifest now has an additional explicit **false** flag for independent cross-run screen reproducibility, and the existing Mesen workflow tests that negative contract rather than its earlier tautological nonempty-set check.


## Resolved screen-buffer repeatability using explicit source no-frame-skip (November 3, 2026)

A controlled original-emulator experiment [Actions #41574463232](https://github.com/gamesbyian/UR-Recomp/actions/runs/41574463232) was executed with the same authenticated original USA ROM, input stream, pinned MesenCE revision and 1219/1220 held-tick replay as earlier contradictory source-screen captures, except that a **temporary** runner copy requested `Snes.DisableFrameSkipping=true`. Across **two independent original ROM sessions**, source OAM, VRAM and CGRAM SHA remained identical to each other **and to the earlier standard-settings runs**. This time original rendered 256×239 P6 buffers were **byte-identical between runs at BOTH ticks**, while **22,776 pixels changed within each run** from tick 1219 to 1220, identically in both runs. This directly resolves the observed cross-run inconsistency under the tested condition and strongly supports a **host-time-dependent SNES render-frame skip** in the pinned MesenCE PPU as its causal mechanism. The original 1994 scanout phase and source OBJ pixel ownership are *separate unverified questions*.

The exact [7-day source archive #13203312348](https://github.com/gamesbyian/UR-Recomp/actions/runs/41574463232/artifacts/13203312348) has ZIP SHA-256 `7106fadd8d37b134f53501a251c281e88fd0336514a123ed70b1855aedf513f7`. Its original evidence comparison JSON SHA-256 is `073b07dd88e2ba244f3dea718991062d457526b007e64401cd9261a3a2223291`; both per-session source manifest SHA are `44982369a2bdc8a13552c59eb12ba89aa328473508d3a2ff0444721105e2301d`. Per-tick original P6 SHA are 1219 `3db1ead6ef6da21dc5c085f38dbd3fe8c17e00d4eba7900ce1074beaa9358cfb` and 1220 `2fdc8dbdcf55d971209b09922802f81d0c31ad75af90ba0c5cf3137d9e1150d3`. Durable numeric summary: `analysis/data/racer-original-mesen-no-frame-skip-replay-20261103.json`.

**Durable implementation:** The repository-owned `third_party/src/mesen-for-ai/scripts/run_headless.sh` now interprets `MESEN_SNES_DISABLE_FRAME_SKIPPING=1` as a strictly sanitized JSON boolean `Snes.DisableFrameSkipping=true`. It accepts only 0/1, defaults to `0` (no behaviour changes for existing clients), and does **not** patch the Mesen binary or ROM. The ART-4K original PPU+P6 workflow explicitly sets `1`, validates the capture manifest’s requested setting, and tests the actual frozen original 1219/1220 P6 hashes. The opt-in is attached to the isolated runner environment and cannot silently change other repository Mesen usages. Changing this vendored script updated only the source-island attestation for mesen-for-ai to `a3360d1283aaf7776496f16ef8e4730e16e53a5f63c8af3208ce9aad8d121394`; both independent hygiene and bootstrap checks calculated that exact new digest before the manifest correction. The initial one-off workflow was removed after its actual source receipt.

**Remaining gate:** A repeatable exported RGB buffer alone does **not** prove which original PPU scanout phase or split-screen OBJ cell produced each pixel. Before claiming original 1994 anatomical part attribution or aligning the 2026 GLB to source poses, extract authenticated source PPU `OamMode`, OBJ tile base/offset, scroll, layer/window settings, and (as feasible) scanout/dual-buffer phase, then verify pixel predictions on independently captured held frames. The single-session provenance field `source_held_display_RGB_reproducibility_across_runs_independently_verified` remains false; the separate frozen two-session study is the cross-session evidence.
