# QA08 opt-in effective-CGRAM pixel observer (research staging only)

19 October 2026. **Unexecuted diagnostic source patcher. Do not merge into the clean product. No release/QA acceptance.**

## Why this is the next smallest experiment

The authenticated [grayscale spatial analysis in PR #1989](https://github.com/gamesbyian/UR-Recomp/pull/1989) shows 318,775 cycle-class wrong RGB5 positions in thirteen 2014 Snes9x callback/native P7 field comparisons. Exactly 24,096 source positions are cycle-wrong at all thirteen 112-field samples, and all 24,096 are exact in six surrounding 16-field controls but wrong at guest5184. Each of the four error types occupies a fixed spatial class over all thirteen captures. At original source-script frames5183/5184, two genuine **full 512-byte Snes9x CGRAM readbacks are byte-identical** (SHA256 `431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12`) and still have slot words `$6C..$6F = 56B5, 4A52, 4631, 4210`. The genuine *native CPU-submitted* guest5183 packet has `4A52, 4631, 4210, 56B5`. These are **different source stages and diagnostic PEs**; CPU submission does not itself prove what the native pixel resolver consumed.

This patcher is designed to collect that missing **native effective pixel stage** before anybody tries a renderer/timing fix. It reuses the already-tested historical Baldosa PPU pixel-resolver observer pattern from [#1782](https://github.com/gamesbyian/UR-Recomp/pull/1782), which logged effective source pixels, rather than introducing a new layer re-evaluator.

## Read-only source contract

`tools/qa08_late_effective_cgram_probe.py` targets only the pinned Baldosa title `10b864b9d14a7b7416dd909eb7b054c88faef101`, pinned SNESRecomp core `075fbe4c8e0d97b0013be541795c39cb644a9709` and the actual generated `src/gen/dispatch_v2.c`. It inserts only opt-in source-read log calls in `snesrecomp/runner/src/snes/ppu_legacy.c`:

1. **Already resolved main/sub pixels:** selected renderer layer, the original resolver's `pixel` index (**not a CGRAM lookup for direct-colour pixels; a `directcolor` flag is logged**), the RGB555 value reconstructed from its actual existing R/G/B outputs, `ppu->cgram[pixel & 255]`, and raw `ppu->cgram[$6C..$6F]`, plus INIDISP/CGADSUB/CGWSEL.
2. **Already composed output:** final RGBA buffer R/G/B, source x and y, physical PPU line, brightness, fixed colour and main/sub enable registers.

Both probes are restricted to guest **5176..5186 inclusive** and eight SHA-authenticated source coordinates that cover all four observed original→native RGB5 substitutions in both 2P bands. The actual legacy renderer uses `ppu_line = logical_source_y + 1`; this is reflected in the filter and both log labels. The independent source observation does **not** imply that the CPU source-frame counter, original emulator callback stage, renderer invocation, and physical beam clock are equivalent.

| Original → native gray | Upper x,y | Lower x,y |
| --- | --- | --- |
| 20→17 | 70,58 | 202,182 |
| 15→20 | 84,77 | 175,145 |
| 16→15 | 53,41 | 187,160 |
| 17→16 | 65,52 | 190,161 |

```sh
# Read-only source qualification; no write.
python3 tools/qa08_late_effective_cgram_probe.py --game /private/pinned-baldosa-uniracers

# Apply only to the SAME isolated disposable game/core checkout:
python3 tools/qa08_late_effective_cgram_probe.py --game /private/pinned-baldosa-uniracers --apply-candidate
# Run the already existing complete 5,484-field two-pad Windows input route,
# with UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE=1 and a separately compiled OFF control.
```

The Python tests establish a valid additive transform, exact pinned commit and generated-source guards, idempotence, eight-coordinate precision, malformed-source refusal and direct CLI fail-closed behavior. **They do not run an emulator, compile a Windows PE or assert output parity.** Log prefixes are `UR_QA08_LATE_PPU_SOURCE` and `UR_QA08_LATE_PPU_FINAL`. A 0/1 main/sub source label must be preserved, and the producer must not substitute an OBJ zbuffer word for its CGRAM colour or re-resolve a pixel. The selected pixel's actual source RGB555 is reconstructed from the already-decided five-bit R/G/B, avoiding a second PPU resolver invocation.

## Admission conditions for the future genuine Win32 run

The graphics producer must preserve the exact compiled PE SHA256, pinned source commits and patched-source hash, same consumed two-pad script SHA256 `ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194`, real **5,484-field guest CRC** SHA256 `b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568`, and both original 2014 Snes9x and new compiled Windows P7 full-raster hashes. Require an **instrumentation-OFF process of its own** with the same route to check for logger runtime interference, and reject changed guest bytes without conflating the control and instrumented PE identities. Prior RF062/#1976 logging noninterference failures make an unverified claim of harmless logging scientifically unacceptable.

If a genuine consumer receives effective native CGRAM and selected palette indices, compare them to the independently archived original 5183/5184 full CGRAM words at correctly qualified stages, with actual produced raster pixels at guest5184 and nearby unsampled original/native fields. The original 2014 CPU journal and native CPU source register writer still have different H-counter units and unqualified instruction clocks; do not label a host-frame difference as a CPU clock cause. The original guest4016 blackout, fixed medal chromatic error, 342×224/7:6/UHD Windows output and human HD character approval remain independent.

**Stop rule:** The observer exists to decide *which effective palette word was consumed by a wrong pixel*. It is a draft engineering instrument until a real Windows source execution, raw pixel witness and independent noninterference result exist. No palette swap, output recolouring, global video phase shift, brightness patch, original/native event acceptance, QA08/10 credit or 4K/HD-art release award follows from the patcher's local tests.



## New fail-closed Windows-log adjudicator

`tools/qa08_late_effective_trace_verify.py` is a separate ROM-free evidence reader for a **future, genuine** observer-ON/OFF pair. It refuses row-format drift, forged/duplicate/missing guest5184 pixel observations, invented source coordinates, reversed renderer-Y numbering, invalid direct-colour attribution, selected-RGB555 disagreement with an actually referenced CGRAM word, impossible PPU register values and absent source provenance. It requires *all eight* authentic guest5184 logical coordinates in **both the original resolver's actual main-screen selection and completed final source pixel**, and distinguishes optional sub-screen rows rather than treating them as main-screen ownership.

It also reopens the exact original 2014 Snes9x **inner** source ZIP SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`, verifies callback5183 original BGRX source member SHA256 `f0ee58c682776592d8a93003a42c508629c49973b206d6a6da2c71ec9dc993b7`, and independently checks the eight original RGB5 values against its real uncropped 256×224 bytes. For both ON and OFF experiments, it requires the exact 5,484-frame guest CRC transcript file SHA256 `b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568` and original script bytes SHA256 `ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194`. Unexpected effective-PPU source logs in the OFF control are refused.

```sh
python3 tools/qa08_late_effective_trace_verify.py \
  --on /private/actual-compiled-Windows-observer-ON.stderr.log \
  --off /private/actual-compiled-Windows-observer-OFF.stderr.log \
  --original-inner /private/authentic-original-2014-inner.zip \
  --native-outer /private/authentic-integrated-Win32-P7-outer.zip \
  --crc-on /private/actual-ON-complete-5484-guest-CRC.txt \
  --crc-off /private/actual-OFF-complete-5484-guest-CRC.txt \
  --route-on /private/actual-ON-route-bytes.txt \
  --route-off /private/actual-OFF-route-bytes.txt \
  --out /private/read-only-late-effective-result.json
python3 -m unittest tests.unit.test_qa08_late_effective_trace_verify
```

The result includes original/reference native RGB5 and newly observed compiled-native RGB5 for each real anchor, main layer/direct-color, the native main selected CGRAM index where applicable, the actual selected 15-bit source colour and all four native effective palette words. **Never infer a fixed pipeline stage from the per-field guest label alone**. A matching text log and archived CRC digest do not prove the executable actually consumed that script, that ON/OFF binaries or source images were unmodified, or that the renderer's effective sample has the original emulator's instruction/beam time. These still require independent binary/manifest/whole-P7 source qualification. Accordingly the report's `whole_P7_ON_OFF_noninterference_proven`, `compiled_Windows_PE_identity_proven` and `QA08_QA10_or_release_authorized` statements stay false.

Seven additional adversarial unit tests exercise log field parsing, eight-anchor main/final pairing, duplicate/missing sources, RGB555/CGRAM disagreement, direct-color avoidance, malformed frame/y/register/RGB and false guest/route SHA admission. **No real Win32 source output exists for this new logger yet.** The checker neither paints any pixel nor interprets test output as a product fix.


## October 19 correction: real renderer dispatch and span-path coverage

Reading the **exact pinned** `baldosa/snesrecomp@075fbe4...` source exposed a critical completeness risk in the first observer: `ppu_runLine` dispatches by `ppu->renderFlags & kPpuRenderFlags_NewRenderer`. The prior observer modified `ppu_legacy.c` only. `runner/src/desktop/host_main.c` ORs in `kPpuRenderFlags_NewRenderer` whenever the host activates native widescreen, regardless of its ordinary configured renderer bit. Therefore an apparently successful widened Windows execution could produce **zero old observer events**. Zero output would establish only that its legacy-only hook was not reached.

The supplementary **`tools/qa08_late_effective_span_probe.py`** stages a *distinct* read-only hook inside the true `PpuDrawWholeLine` new/span compositor in the pinned `snesrecomp/runner/src/snes/ppu.c`. Its insertion anchor is exactly the terminating `PpuWriteOverlayRenderLine(ppu, kPpuOverlaySource_Obj, y)` inside the composed output path, and requires the unique unmodified `static NOINLINE void PpuDrawWholeLine(Ppu *ppu, uint y)` definition. It checks `kPpuRenderFlags_NewRenderer`, the 11 guest fields 5176..5186 and the same eight authenticated original/native pixel centers. No sampling is enabled outside the environment-controlled diagnostic.

It reads the **already populated main/sub span PPU depth/palette words**, the exact PPU RGB555 source produced by the pure `PpuPixelColor` read, effective CGRAM index/word and slots $6C..$6F, INIDISP/CGADSUB/CGWSEL, direct-color mode, and the final already composed RGB8 from `ppu->renderBuffer`. Native result scanline `y` is the original logical `y+1`, and the *fixed PPU zbuffer column* (`x + kPpuExtraLeftRight`) is distinct from the *actual output framebuffer column* (`x + ppu->extraLeftRight`). The newer span renderer **does not use** `ppu_legacy.c`'s per-pixel `ppu_resolve_pixel` on this path, so the new observer must not invoke that resolver.

A host-added OBJ colour override can make `PpuPixelColor` differ from `ppu->cgram[pixel&255]` even for a real object winner. Rather than falsify a CGRAM-source claim, the span hook emits `UR_QA08_LATE_SPAN_OBJECT_OVERRIDE`, and the strict verifier **refuses** that row as CGRAM evidence pending a separately qualified object-colour attribution. The new log prefixes `UR_QA08_LATE_SPAN_SOURCE` and `UR_QA08_LATE_SPAN_FINAL` are renderer-distinct from `UR_QA08_LATE_PPU_SOURCE` and `UR_QA08_LATE_PPU_FINAL` from the old/legacy renderer. The checker refuses a mixed main/final renderer identity at a given pixel. An arbitrary text log alone cannot show which renderer actually consumed a given frame; its emitter flag and whole-frame source images need authentic compiled Windows verification.

**Staging on an isolated disposable checkout** should qualify and apply both independent patchers. Both must bind the exact same game/core SHA; neither qualifies one another's applied source.
```sh
python3 tools/qa08_late_effective_cgram_probe.py --game /private/pinned-baldosa-uniracers
python3 tools/qa08_late_effective_span_probe.py --game /private/pinned-baldosa-uniracers
python3 tools/qa08_late_effective_cgram_probe.py --game /private/pinned-baldosa-uniracers --apply-candidate
python3 tools/qa08_late_effective_span_probe.py --game /private/pinned-baldosa-uniracers --apply-candidate
```
The resulting source changes are **only in that disposable external checkout**, not UR-Recomp's production PPU. Compile and execute in a bounded real Windows experiment with the same full two-pad route, guest CRC, ROM identity, ON/OFF genuine P7 images and exact executable/source hashes. Distinct host-width/renderer choices require distinct measured source receipts. This double-observer source staging, like all proposed instrumentation, is **draft-only and does not promote a release acceptance verdict**.


## October 19: independently authenticate archived native RGB5 reference

The future log verifier now refuses source comparisons unless **both** reference renderers' pixels are re-opened from exact authentic ZIP bytes: the 2014 Snes9x original callback5183 BGRX member and the compiled integrated Windows guest5184 P7 member. The extra required `--native-outer` argument is the actual outer artifact **12151839452** with SHA256 `832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727`. It must contain nested P7 ZIP SHA256 `c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd` and the exact frame SHA256 `8dae60c1433aa26cd6edc20edda980d1dec17e8935a799d7edc6d0878ae387a8`. The verifier checks all 8 genuine archived native source RGB5 values **from those actual PNG-equivalent P7 bytes**, separately from the archived original values, rather than trusting hard-coded color-class pairs. All images are retained outside the repository; no copying copyrighted source frames to a PR.

The original and native archives were reopened independently for this extension. All eight native pixels have a zero fourth channel and the expected actual RGB5: (70,58)/(202,182) = 17; (84,77)/(175,145) = 20; (53,41)/(187,160) = 15; (65,52)/(190,161) = 16. This establishes the reference baseline, not any newly executed Windows observer result or proof of same beam stage.



## Source-qualified renderer-stage explanation to discriminate (not yet a fix)

The exact pinned Baldosa core was re-read directly at SHA `075fbe4c8e0d97b0013be541795c39cb644a9709`; upstream `runner/src/snes/ppu.c` Git blob `25dcfe03b6615138c04c376ec83f7a52ca5fe5de`, `ppu.h` blob `9263633cb6ed0aea4de47acab28a7269eeea9263`. Its actual register replay has an important asymmetry:

- `raster_reg_journaled` **explicitly returns false** for CPU/DMA palette-port writes `$2121` and `$2122`, although it journals other display-state registers.
- `raster_snapshot` copies `PPU_SAVESTATE_REGS_SIZE` starting at `ppu->inidisp` and some scroll/M7 latches; it does **not** copy the separate 512-byte palette memory.
- `ppu_rasterRenderBegin` restores that register snapshot for its replay field, and `ppu_rasterApplyLine` applies eligible writes in beam-line order, but neither explicitly restores/replays CGRAM port transactions.
- In the genuine source, the `case 0x22` second-write handler mutates `ppu->cgram[ppu->cgramPointer++]`, and `PpuPixelColor` returns `ppu->cgram[pixel&255]` unless a qualifying host OBJ colour overrides it.

This code establishes **a mechanism capable of rendering a historical field with newer palette memory while replaying older display registers** in the host's deferred per-field rendering model. It does not prove that this mechanism caused the archived wrong pixels. The observed genuine original Snes9x complete CGRAM snapshots at 5183 and 5184 retain `56B5,4A52,4631,4210` at `$6C..$6F`, while the native CPU-**submitted** 5183 packet has the rotated order `4A52,4631,4210,56B5`. That fact makes a deferred-CGRAM-consumption explanation testable, not yet established.

**Specific falsifiers for the active Windows experiment:** At guest5184, source-authenticated wrong pixel anchors must be checked for the actually selected PPU layer/index, the live CGRAM word at that index (or direct-colour/OBJ negative), main/sub math and final RGB. If the native span/legacy observer logs the older original CGRAM values for their winning pixels, an overly early native CGRAM update alone cannot explain the sampled final error. If the newer rotated words are confirmed at the winning indices in the same compiled PE, the precise missing step becomes correlating the original consumption phase and the native field's CPU/HDMA beam before considering a **palette replay/snapshot** repair. Any candidate must be benchmarked with exact original/native 263-frame RGB5 totals, guest CRC, ON/OFF logger noninterference, 1P/2P moving and result frames and clean Original fallback. No global recolour, guessed extra video shift, unqualified beam adjustment or CPU-clock modification is licensed by this memo.

The dedicated [research-only Windows workflow](../.github/workflows/qa08-native-effective-cgram-windows.yml) runs separately linked OFF/ON Windows PEs and exact source checks. It is scoped to this draft branch, retains **bounded text evidence only**, and does not alter the release workflow. Failure, including a missing observer row, incompatible native palette selection, changed guest CRC or expired source artifact, must remain a visible refusal.
