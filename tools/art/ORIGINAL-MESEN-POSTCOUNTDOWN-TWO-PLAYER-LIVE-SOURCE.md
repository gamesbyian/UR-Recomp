# Authenticated original MesenCE two-player post-countdown source frames, 1601–1605

The original USA-ROM race is **visibly underway** after the countdown in the actual live MesenCE replay: [original-source workflow #41585842911](https://github.com/gamesbyian/UR-Recomp/actions/runs/41585842911) passed. Its seven-day [artifact #13208166875](https://github.com/gamesbyian/UR-Recomp/actions/runs/41585842911/artifacts/13208166875), ZIP SHA-256 `d7d3e312528563bae0940ed97258024103085576c385334253458af501744ab7`, contains five original 256×239 screenshots (PPM), raw original SNES **OAM 544B, VRAM 65536B, CGRAM 512B** for each original tick, and **the exact MesenCE serialized PPU registers acquired in the same run**. Source-only producer `tools/art/capture_original_mesen_ppu_registers.py` now accepts `--include-held-framebuffer` without requiring a second ROM replay and leaves its old default unchanged. All five source files/tick, source original ROM and controller replay identities, no-frame-skip state, and PPU frame counter were independently checked against the actual artifact. Only the bounded diagnostic workflow was temporarily added to execute this proof and then removed.

The screenshot shows two actual racers after the giant countdown graphic has cleared. Source gameplay has a track, split-screen, score and text graphics, so source racer pixels can be obscured. Do not assert a completely unobscured racer. The actual authored input commands at original steps 1580–1603 were **P1 Right and P2 Left simultaneously**; the observed replay masks are P1=128/P2=64 on captured ticks 1601–1604, then zero at 1605. These inputs are **injected controls**, distinct from independently established engine acceleration or animation-bone velocities.

| Original Mesen bridge tick | Held blue OBJ slot96 X | Held red OBJ slot97 X | OAM bytes changed | VRAM bytes changed | CGRAM bytes changed | RGB pixels changed from previous frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1601 | 82 | 48 | baseline | baseline | baseline | baseline |
| 1602 | 83 | 48 | **1** | 117 | 18 | 19,903 |
| 1603 | 84 | 48 | **1** | 318 | 26 | 19,858 |
| 1604 | 85 | 48 | **1** | 124 | 17 | 20,613 |
| 1605 | 86 | 48 | **1** | 115 | 26 | 20,821 |

All held PPU states report `ppu.scanline=225`, `ppu.oamMode=4` (small16×16/large64×64), source OBJ tile base `0x6000` and second-table offset `0x1000` (both **VRAM word addresses**). Both source raster contents change during these frames even when a held OAM position remains unchanged. This directly demonstrates the danger of using only OAM-position deltas as an animation metric. The source 2D racers are recognisable in the original completed screen, but pixel content includes frame changes and HUD/track overlap.

The previously source-verified fully opaque **blue 323/323 and red 327/327 exact RGB matching** occurred at original countdown tick 1219. An independent exploratory pixel decoder applied to the new original live post-countdown raw arrays found only **281/316, 277/316, 281/320, 282/323, 281/317** best blue matches, and **132/311, 134/319, 134/316, 128/314, 132/318** best red matches at bounded translations. **These are observed partial overlaps, not failed source geometry.** The held PPU register snapshot may be at a different point in the original per-line drawing sequence than the completed screen. Pixel rejection or 3D geometry fitting from residuals is not authorized until source PPU OBJ writes, track/HUD priority and scanout origin are independently matched.

The exact per-frame screenshot and OAM hashes, original replay ROM/binary, source blue/red alpha counts and explicit negative gates are frozen in `analysis/data/racer-original-two-player-postcountdown-actual-frames-20261103.json`. Original Mesen source files can be regenerated via this one-pass command using pinned MesenCE and the archived no-frame-skip headless launcher:

```bash
MESEN_SNES_DISABLE_FRAME_SKIPPING=1 \
python3 -m tools.art.capture_original_mesen_ppu_registers \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --input-file tests/input/two-player-first-race.input \
  --mesen-for-ai-repo third_party/src/mesen-for-ai \
  --mesen-executable /path/to/pinned/Mesen \
  --advance-frames 1600 --capture-frames 5 --include-held-framebuffer \
  --out-dir /private/new/source-original-2p-frame-witness
```

**Next source discriminator:** collect time/scanline-indexed original OAM writes to PPU OBJ registers (or derive a source-verified finished-frame OAM buffer), then match one held source sprite raster to a particular **completed** original screen scanout for each of the two racer viewports. Preserve the exact already-verified original 2D 323/327 match as positive control. Only after source-to-screen temporal correspondence is stable should the existing part-addressable GLB (#2832), its pose viewer and the strict source-family withheld silhouettes be used to search source **3D** pose/camera hypotheses. The original 1994 mesh, rig pivots, skeleton, depth and shader remain unknown, as does owner likeness approval.
