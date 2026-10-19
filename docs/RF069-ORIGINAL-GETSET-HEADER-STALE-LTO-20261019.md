# RF069: avoid a mixed 2014 original Snes9x getter/setter binary

**October 19, 2026. No gameplay correction or USA event admission.** This addresses a **confirmed binary producer defect** in the authentic original stack reader evidence, not a speculative 65816 timing mismatch. The previous source RF044/RF063 instruments were staged correctly, but the original 2014 libretro Makefile does **not** declare its `getset.h` dependency in the `%.o: %.cpp` compilation rule. The research workflow bootstrapped and **compiled the stock original first**, then changed `getset.h` and a subset of `*.cpp`, then used incremental `make`. LTO could legally link an inconsistent mixture of stock and instrumented inline getters/setters across translation units.

## Independently inspected executable, rather than trusting source text

I independently downloaded the **exact 2014 original emulator binary** from [authentic RF066 original/native run 39219862021](https://github.com/gamesbyian/UR-Recomp/actions/runs/39219862021), artifact `12171087892`, and disassembled `snes9x_libretro.so` SHA256 `9682cd2c2732541487c88cfef84f0d1b5a1005d4de0b00e95d43bac1cf9215c0`. On the real linked C++ functions:

| Original physical getter/setter symbol | `getenv@plt` instrumentation guard in its emitted function? |
|---|---|
| `_Z10S9xGetBytej` | **No** |
| `_Z10S9xGetWordj9s9xwrap_t` | **No** |
| `_Z10S9xGetWordj9s9xwrap_t.constprop.0` | **No** |
| `_Z10S9xSetBytehj` | **Yes** |
| `_Z10S9xSetWordtj9s9xwrap_t15s9xwriteorder_t` | **Yes** |

This maps exactly to the authentic RF066/Zoo result: **903 true original stack getter returns but 0 RF063 getset read entries**, whereas all **903 real original stack setters were logged**, with 1 physical NMI checkpoint. No claim is made that a read wasn't performed. The actual Snes9x source includes both getter and setter probes; the **binary is not coherent with that claimed instrumentation**.

## Small source-authentic repair and stronger acceptance condition

After original source staging, the RF065 real C++ compile workflow now does `make -C "$SRC/libretro" clean` **before** the patched rebuild, rather than removing only the final `.so`. Then [`qa01_rf069_original_getset_binary_audit.py`](../tools/qa01_rf069_original_getset_binary_audit.py) independently uses `nm -an` and `objdump --disassemble` to inspect every emitted named genuine 2014 `S9xGetByte`, `S9xGetWord`, `S9xSetByte` and `S9xSetWord` variant (including `.constprop` clones), requiring a real executable `getenv@plt` call on each such entrypoint. A string present somewhere in the ELF is not sufficient; missing variants, an unguarded clone or unreadable symbols fail the pilot. The emitter's source/guest bus calls are **unchanged**, no new ROM activity and no timing retime, frame shift or masking.

The workflow retains the actual stock-original and freshly rebuilt source/core digests plus the machine-readable per-symbol binary qualification as `rf065-original-stack-source-build-receipt`. A green build is **not** a proof that the real original game executed a getter, returned a particular value, or matches the native emulator; it just excludes the specific stale-getter mechanism for future runs. Run once against genuine original Snes9x. If the clean build's full executable guard test passes, stage the same clean compilation in a separate **temporary original Zoo one-shot**, preserving real ROM/movie/converted controller inputs, old native executable, original game clocks, 78 unmasked full-WRAM pairs, Zoo +5163→Bowl +267 and earned ranked/cold SRAM controls. Reopen and independently qualify **actual** source RF044/RF063 read-entry events and cross-check their physical addresses, values and real RF045/RF064/RF066 post-call getter returns. Refuse all original/native first-consumer causal-window claims until that replay succeeds.

**Still 0/45 complete USA events and 0/12 Windows release QA gates.** A prior genuine trace with missing read probes is retained as the trustworthy **negative coverage baseline**, not rewritten as a previously proven match. The debug build and this tool are never promoted to the shipping product.
