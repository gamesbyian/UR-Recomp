# WIDE-07: actual USA original/native moving-course raster discriminator (2026-11-13)

**Scope:** independent read-only, actual hosted original-game Snes9x and native renderer captures. This is a directly executed partial visual witness and a first-difference localization, **not** a complete USA course, original extended-world margin oracle, accepted WIDE-07, QA-08 gate or physical Windows witness.

## Reproducible producers

- **Original USA interpreter:** [GitHub Actions 43539425650](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650), [bounded primary artifact 14090194177](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650/artifacts/14090194177), exact experiment SHA `b3ae92f0e587471674487921ea3c887bce06b3ac`, artifact ZIP SHA-256 `fd8faa2bf09fd2dcc89e860a9d0ff75edf5465380032361e176fc7e9ea3dad78`. Pinned Snes9x 1.63+1bcc369, canonical USA ROM verified. It compiled and ran the *real* reference emulator with `tests/input/widescreen-product-acceptance.script` on GitHub-hosted Ubuntu. The retained artifact has full source framebuffer BMP/BGRX, WRAM (128 KiB), SRAM (8 KiB), VRAM, CGRAM, OAM, per-scanline PPU writes/registers, source original scripts, and producer/source checksums.
- **Native original-view and 342-wide candidate:** [GitHub Actions 43538102121](https://github.com/gamesbyian/UR-Recomp/actions/runs/43538102121), [fixed/wide artifact 14089774982](https://github.com/gamesbyian/UR-Recomp/actions/runs/43538102121/artifacts/14089774982), exact experiment SHA `6577ec379e7c18126c5a5b8f71c1c69a0be142fb`, artifact ZIP SHA-256 `2f96da98f76dd9ec400d19bb3bd3554e915e1348b841ed3250bc55cc8a8c8318`. The same deterministic stock-course script captured both fixed 256x224 and wide 342x224 native images. The wide image is compared only in its central 256 pixels (`x=43..298`); the original game did not expose an 86-pixel margin oracle.

## Direct observed RGB5 results

Parse actual 24-bit BMP pixels (BGR file storage, top-down logical rows). Compare original Snes9x 256x224 to native fixed 256x224, plus native 342-wide center crop, at the matching **script checkpoint names**. SNES-style RGB5 means `RGB8_channel >> 3`, with no spatial tolerance or masked pixels. The original and native reach the same scripted states at different reported frame counters; **semantic checkpoint pairing is not proof of equal absolute guest frame/NMI timing**.

| Script checkpoint | Original frame | Native frame | Source/native exact RGB5 pixels | RGB5 differences | Native fixed/wide center difference |
|---|---:|---:|---:|---:|---:|
| Menu ready | 500 | 506 | 30,512/57,344 | 26,832 | 0 |
| Race entered | 1035 | 1045 | 56,882/57,344 | 462 | 0 |
| Race after 900 right-held frames | 1936 | 1946 | **57,344/57,344** | **0** | **0** |

At the moving after-scroll checkpoint, all 57,344 centre pixels agree in RGB5, and *every* original/native RGB8 channel differs by at most 2 units (the expected scope of a conversion-depth comparison, although the specific converter has not been independently proved). This is a real original/native positive observation on a moving USA course, not yet a cross-clock qualification.

At the earlier race-entered checkpoint, **all 462 differing RGB5 pixel coordinates equal the exclusive-or boundary of the large blue directional arrow mask** (blue greater than 240, red/green below 130). The arrow occupies 9,697 pixels on either producer. Shift the native blue overlay down exactly one image pixel: mask disagreement falls from 462 to 24, those confined to the small secondary overlay element around y155–157. That is a causal *localization*, not permission to shift the shipping renderer by a pixel. Determine if this is controller/movie phase, guest-frame registration, source display timing, or a real overlay placement error before changing the game.

The menu has 26,832 RGB5 disagreements and does not receive source/nonnative equivalence credit from the race scene. Its animated state/phase needs independent registration if directly relevant to release visuals.

## Rerun the comparison

After downloading both above Actions artifacts without altering their members:

```bash
python3 -m unittest -v tests.unit.test_compare_wide07_original_native_rgb5
python3 tools/compare_wide07_original_native_rgb5.py \
  --original-zip path/to/agent-hosted-script-evidence-original.zip \
  --native-zip path/to/agent-hosted-script-evidence-native.zip \
  --out /tmp/wide07-original-native-rgb5.json
```

The consumer verifies source-linked receipt identities and BMP SHA-256 where provided, rejects duplicate ZIP members, checks fixed/wide original-centre comparison and reports arrow localization with **zero automatic gate/event credit**.

## Next executable fidelity discriminator

**Owner:** UR Fidelity Execution. **Location:** generic `script_linux` hosted runner on a fresh `experiments/*` branch. **Inputs:** exact two source-verified archived producers, existing real original `.regs.json`, `.ppuw.tsv`, `.vram.bin`, `.cgram.bin`, and the native fixed/wide BMPs. **Action:** align an actual matched source/native guest-cycle or stable PPU/HDMA event around the race-entered blue arrow, then use the original USA tilemap/scroll to independently predict the widened horizontal margins at one **moving** course frame. An original 256-wide screenshot alone cannot certify unseen extended-world pixels; derive those pixels from source game RAM, tile composition and per-scanline scroll.

**Completion:** either reproduce an original-derived same-event central/edge pixel match with identified original scroll/tile provenance, or produce one exact first differing source-visible raster/tile/scroll value and a runnable source-level correction test. Do not repeat static reachability analysis, repeat a native-vs-native center comparison, or credit a USA course from this bounded result.

Formal counters remain **0/45 USA courses and 0/12 Windows gates** until independent complete-event and exact-candidate acceptance.


## Follow-up: actual full guest memory and original PPU agreement

**Second independent hosted execution, 2026-11-13.** The native-side original/342-wide guest capture is [Actions run 43540488054](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054), original [artifact 14091441914](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054/artifacts/14091441914), exact experiment source `0c86c706b58f0f72969ceb9d0fa200d765bdf209`, independently downloaded artifact ZIP SHA-256 `4cdad8847df27145ba256494586ddddf9bccc13307356b9b8acac0fe408284d7`. This experiment preserved full original-view and wide-view WRAM, SRAM, VRAM, CGRAM, OAM, PPU registers, frame metadata and BMPs for the three already source-matched scripted checkpoints.

I reopened and CRC-checked the original Snes9x and new native ZIP archives, compared all of their actual binary memory bytes, and separately checked native fixed/342-wide memory (no masking or byte normalization). At each of the three script checkpoints, **all 131,072 native fixed-vs-wide WRAM bytes match**. Native SRAM, VRAM, CGRAM and OAM also match between fixed and wide at every checkpoint.

| Script checkpoint | Snes9x vs native WRAM | Snes9x vs native SRAM | Snes9x vs native VRAM | Snes9x vs native CGRAM | Snes9x vs native OAM |
|---|---:|---:|---:|---:|---:|
| Main menu | 24 / 131,072 differ | **0 / 8,192** | **0 / 65,536** | 8 / 512 | 2 / 544 |
| Race entered | 19 / 131,072 | 17 / 8,192 | **0 / 65,536** | **0 / 512** | **0 / 544** |
| Race after 900 right frames | 19 / 131,072 | 17 / 8,192 | **0 / 65,536** | **0 / 512** | **0 / 544** |

The **same 19 WRAM differing addresses and values, and same 17 SRAM differing addresses and values** remain across both race snapshots, despite 900 frames of sustained scripted movement. Native rendering's fixed/wide guest memory stays byte-identical. Actual original/native RGB5 is 57,344/57,344 identical pixels at the second racing checkpoint; no implied extrapolation to other camera positions.

Of the 19 differing WRAM bytes, **14** have both original and native values equal to their corresponding different SRAM bytes at offset `0x0E6B + WRAM offset`. Those 14 WRAM offsets are `00C6,00C8,00C9,0187..018E,0191..0193`, matching 14 SRAM differences at `0F31,0F33,0F34,0FF2..0FF9,0FFC..0FFE`. This **value-correspondence is a known lead**, already analyzed with real source material in [the 2026-10-18 Bowl crosswalk](QA01-BOWL-SOURCE-SRAM-CROSSWALK-20261018.md); it is not independently proven memory-copy direction, execution, writer attribution or harmlessness.

**Existing causal research should be reused, not repeated.** The project's [R-SEED-014/R-SEED-015 research record](RESEARCH-LEDGER.md) already traced `00C6` as a frame-decremented cursor-animation counter, `00C8/00C9` as palette phase/timer fields, and `01D1..01D4` as old stack-page residue with no ordinary writes observed in its source-specific reverse trace (run 36511207129). The imported [RAM map](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt) labels `0187..018E` menu-sprite animation frames and `0191` menu colour phase.
These are **prior bounded observations and imported-symbol leads**, not an automatic declaration that this new run's bytes are harmless or never consumed. `0192..0193` and `01CF` still require scoped reader relevance if proposed as exceptions. First perform the actual offscreen PPU/source tile and arrow-origin discriminators; only trace persistent state bytes further if a real player/animation/progression consequence is discovered.

The five remaining WRAM offsets are `01CF,01D1,01D2,01D3,01D4`. The three remaining SRAM offsets are `0EF1,0EF6,10A7`. `10A7` is independently observed as differing in an older Zoo result-relative sample and tentatively labeled `sCutsceneTimer2` in the imported map, but neither observation proves its role in *this* first-race route. Determine actual readers/writers or future consumer effects before waiving any difference. Source/native samples are semantically script-aligned rather than independently CPU-cycle aligned.

**Actual original/native PPU register crosswalk at these checkpoints:** Both producers report the same source brightness, HDMA-enabled channel mask (`0x7C` at race entry, `0x3C` after scroll), main/subscreen enables (`0x17/0x10`), colour math (`0x04`), and BG1/BG2 vertical scroll (race `203/101`, after scroll `208/104`). BG1/BG2 horizontal scroll is also equal **modulo 1,024**, consistent with the SNES 10-bit horizontal scroll field: original race `152/76` versus native `152/76`; original after scroll `11242/5621`, native `1002/501`. These are top-level/per-capture register observations; source-vs-native per-scanline HDMA-write timing and original 342-wide offscreen margin pixel prediction are not yet established. The reported differences in original wider accumulated H-scroll counters must not be misclassified as different camera positions.

**To reproduce**, download the two original GitHub artifacts above. Run:

```bash
python3 -m unittest -v tests.unit.test_compare_wide07_original_native_rgb5
python3 tools/compare_wide07_original_native_rgb5.py \
  --original-zip original-usa-snes9x-evidence.zip \
  --native-zip native-guest-state-evidence.zip \
  --require-memory \
  --out /tmp/wide07-full-original-native-checkpoints.json
```

The updated existing comparator validates actual original producer WAV-independent PPU image hashes, full original WRAM/SRAM receipt hashes, native full WRAM receipt hashes, exact image sizes, original/native differences, native fixed/wide differences and the narrowly documented SRAM value correspondence. It **does not waive masked internal bytes** or infer complete-event, CPU-cycle, actual offscreen source tile or Windows-release acceptance. **Counters stay 0/45 and 0/12**.

The next best experiment remains a true **original-USA-sourced moving offscreen tile and per-scanline HDMA/scroll oracle** for the widened margins, together with the specific transient arrow-mask shift. Don't run another identical fixed-vs-wide CRC scan or rediscover the same 19-byte static set. If original registered offscreen pixels disagree, fix the earliest actual tile/scroll/PPU value and rerun; otherwise advance course qualification with the source-matched 900-frame observation as one bounded positive subtest.
