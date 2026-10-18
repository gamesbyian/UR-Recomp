# QA08: exactly register original 2014 medal painters to original video callbacks

**2026-10-18 | original Snes9x-only evidence | no native parity or production patch.**

## Decision

Two independent *real original 2014 Snes9x* archives already existed. The complete original 263-frame source archive has ZIP SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e` (artifact **12075111053**). The genuine [original medal painter/depth archive](https://github.com/gamesbyian/UR-Recomp/actions/runs/39164293633) has ZIP SHA256 `8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4` (artifact **12150037795**). Both used the pinned 2014 Snes9x ROM/core and completed the 5,484-frame USA route. The script files differ through three read-only dumps, but their **26 actual original logged input transitions** are byte-identical, canonical LF-record SHA256 `9c9072123a8eadceb7af228088a51bf074e362f81772500daf3ac83a382aa4f0`, independently established in [merged source evidence #1839](https://github.com/gamesbyian/UR-Recomp/pull/1839).

Replaying only the exact archived host source information, without a new emulator run, compares the last original painter RGB565 after OBJ/BG0/BG1/backdrop to the unmodified source video callback's BGRX8888 at the **same source-internal frame label**. The Snes9x 5/6-bit-to-8-bit replication `(v<<3)|(v>>2)` and `(v<<2)|(v>>4)` matches **10/10 observed pixels exactly** on labels **4031 and 4175**, both with **zero disagreement**. Frames are explicitly registered as original painter **4031 ↔ original callback labeled 4031** (human 1-based output 4032), and **4175 ↔ callback labeled 4175** (human 1-based output 4176). This does **not** equate painter frame4032 with callback label4031. The prior source depth witness [#1839](https://github.com/gamesbyian/UR-Recomp/pull/1839) examined painter labels 4032/4176, which are the **next** internal source fields and can have different winning sprites. No global image shift is introduced or authorized.

| Real original callback label | Pixel | Original final owner | Exact expanded callback RGB |
| --- | --- | --- | --- |
| 4031 and 4175 | 207,91 | OBJ112 | 115,56,74 |
| 4031 and 4175 | 205,115 | OBJ113 | 115,56,74 |
| 4031 and 4175 | 205,139 | BG0 | 132,134,132 |
| 4031 and 4175 | 225,96 | OBJ99 | 206,190,140 |
| 4031 and 4175 | 225,120 | OBJ98 | 206,190,140 |

These *differing authentic source temporal labels* reconcile the apparent changes in named OBJ slots across the two original observations. The successful comparator preserves both: original label4032 source painter wins OBJ113/114/97/96 plus BG0 at 207,91; source callback4031 is registered to **painter4031** (OBJ112/113/99/98 plus BG0 at 205,139). This is temporal source identity, not an emulator-clock adjustment.

## Reproduce and challenge

Download the *unchanged* two artifact ZIPs locally (no ROM asset inside these two evidence ZIPs) and run:

```sh
python3 tools/qa08_verify_original_medal_callback_registration.py \
  --original /private/source-263-original.zip \
  --painter /private/original-painter-12150037795.zip \
  --out /private/qa08-original-callback-registration.json

python3 -m unittest tests.unit.test_qa08_verify_original_medal_callback_registration
```

The stdlib-only verifier validates both complete ZIP hashes, source manifest and each BGRX frame hash, 263-callback population, actual original 26-transition consumed input identity, 252 real sprite calls, 360 original layer-depth observations, selected original frame labels, all four per-pixel renderer stages, same-source depth ownership and original RGB565->BGRX image values. Negative tests separately rehash forged synthetic observations to ensure shifted callbacks, altered pixel colours, fabricated sprite ownership and changed BG priority are **rejected by semantics**, not just blocked by outer ZIP SHA. No production PPU modifications, second emulator, new CI research factory or redistributed ROM pixels.

## Native-script intent comparator (not consumed-input evidence)

A separate read-only comparison of the exact original archived `original.script` and the imported native `reference/imported/reverse-engineering/baldosa-uniracers-recomp/tests/routes/race_2p.txt` removes **only** `turbo on`, extra diagnostic `dump` directives and comment/blank lines. Both then contain the **same 27 ordered controller/wait/until/quit commands**, including each P2 button mask and wait duration, with canonical LF-command SHA256 `f8c29ca70fbcaa37aca6616aaf5ed40cb5be954608a6e55ffd0e2c11b7521788`. This is useful evidence that the two movie descriptions express the same *intended* route. The native command interpreter and source movie may still sample those inputs at different guest/host boundaries. **No native consumed-input parity, beam equality or same-numbered source/native raster comparison is licensed by static script equality.**

## Strict stopping boundary

This authentic source-only registration proves **nothing about native guest/input/beam equivalence**. Native Windows #1835's 19/19 VRAM sprite-writer proof uses the *different* Baldosa `race_2p.txt` route with `turbo on`, whereas neither original capture did. No same-numbered native scanline/source callback equivalence, original/native medal colour, original/native blackout, 28-frame CGRAM timing or accepted USA event follows from this original-only comparison. Do not change native OAM slots, source frame count, INIDISP, RGB brightness, host output LUT, 342x224 world composition, 7:6 PAR, true UHD output, 4x Original fallback or release ledger on this evidence.

The next production discriminator is a genuinely **source-registered original/native beam/present/consumed-mask comparison** at selected result pixels. Clean [HDMA/V0 #1780](https://github.com/gamesbyian/UR-Recomp/pull/1780) remains a separate production patch on hold for latest integrated exact Windows PE/Modern acceptance; [premath #1807](https://github.com/gamesbyian/UR-Recomp/pull/1807) stays experimental; [HD racer #1826](https://github.com/gamesbyian/UR-Recomp/pull/1826) awaits new visual approval. Release QA remains independently owned.
