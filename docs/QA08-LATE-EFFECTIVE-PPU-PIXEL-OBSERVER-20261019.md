# QA08 opt-in effective-CGRAM pixel observer (research staging only)

19 October 2026. **Unexecuted diagnostic source patcher. Do not merge into the clean product. No release/QA acceptance.**

## Why this is the next smallest experiment

The authenticated [grayscale spatial analysis in PR #1989](https://github.com/gamesbyian/UR-Recomp/pull/1989) shows 318,775 cycle-class wrong RGB5 positions in thirteen 2014 Snes9x callback/native P7 field comparisons. Exactly 24,096 source positions are cycle-wrong at all thirteen 112-field samples, and all 24,096 are exact in six surrounding 16-field controls but wrong at guest5184. Each of the four error types occupies a fixed spatial class over all thirteen captures. At original source-script frames5183/5184, two genuine **full 512-byte Snes9x CGRAM readbacks are byte-identical** (SHA256 `431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12`) and still have slot words `$6C..$6F = 56B5, 4A52, 4631, 4210`. The genuine *native CPU-submitted* guest5183 packet has `4A52, 4631, 4210, 56B5`. These are **different source stages and diagnostic PEs**; CPU submission does not itself prove what the native pixel resolver consumed.

This patcher is designed to collect that missing **native effective pixel stage** before anybody tries a renderer/timing fix. It reuses the already-tested historical Baldosa PPU pixel-resolver observer pattern from [#1782](https://github.com/gamesbyian/UR-Recomp/pull/1782), which logged effective source pixels, rather than introducing a new layer re-evaluator.

## Read-only source contract

`tools/qa08_late_effective_cgram_probe.py` targets only the pinned Baldosa title `10b864b9d14a7b7416dd909eb7b054c88faef101`, pinned SNESRecomp core `075fbe4c8e0d97b0013be541795c39cb644a9709` and the actual generated `src/gen/dispatch_v2.c`. It inserts only opt-in source-read log calls in `snesrecomp/runner/src/snes/ppu_legacy.c`:

1. **Already resolved main/sub pixels:** selected renderer layer, the original resolver's `pixel` palette index, the RGB555 value reconstructed from its actual existing R/G/B outputs, `ppu->cgram[pixel & 255]`, and raw `ppu->cgram[$6C..$6F]`, plus INIDISP/CGADSUB/CGWSEL.
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
