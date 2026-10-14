# QA-08: independent original/native source-colour band agreement

**Source-backed, offline crosscheck against already executed original/native
archives. No new emulator/process or full same-frame RGB acceptance.**

## The three separate evidence sources

1. Original Snes9x run **38521827670** (artifact 11873899132)
   produced 96 actual live `$2131/$2132` channel5 register writes in
   eight original emulator frames, **48 paired transfers**, with
   all 96 values independently matching the original 65816-generated
   WRAM palette table. Its real original PPUW register journal and
   final 256×224 GO/t480 frame sources are independently hashed.
   The exact source archive, core, script, opcode and image SHA-256
   are in `analysis/data/qa08-original-snes9x-2p-hdma-live-pixel-source-handoff-20261014.json`.
2. Baldosa SNESRecomp native run **38504531564** independently
   observed **seven** live channel5/mode1 COLDATA writes, including
   a duplicate *first-line prime*, with actual source addresses,
   after-write live fixed RGB15, and exact guest frame2208.
3. Native source PPU run **38502862996** independently measured
   **26 genuine BG3-main/OBJ-subscreen text-overlap source pixels**
   in both viewports and real after-removal colour outcomes
   (upper red5=28, lower RGB5=(13,19,0)) at live fixed-colour
   sample positions (133,50)/(133,162).

The new read-only `tools/qa08_cross_original_native_live_colour_bands.py`
joins those **three separately executed** machine-readable source
records and requires precise original ROM/probe/run fingerprints,
all 96 original source/BBUS byte equalities, native seven-write
channel/mode/source, independent original/native six-register
sequence identity, the extra native prime and the independently
measured native PPU colour operands.

| Pair | Original Snes9x V | Native write-log tag | Same $2132 byte | Live fixed RGB15 after write |
| --- | ---: | ---: | --- | --- |
| upper red | 0 | 2 | `2F` | `026F` |
| upper green | 1 | 3 | `40` | `000F` |
| upper blue | 2 | 4 | `80` | `000F` |
| lower red | 111 | 113 | `20` | `0000` |
| lower green | 112 | 114 | `53` | `0260` |
| lower blue | 113 | 115 | `80` | `0260` |

Each of the six genuinely measured register transitions agrees
across **original emulator and native emulator**, after omitting
native's separate before-first-line priming transfer. Each native
source log tag exceeds the original emulator's associated V value by
two, as independently reported by their respective logging paths.
That is an **observed tag relation**, not a calibrated two-line
physical video delay. Their renderers and field boundaries differ.

The real native PPU pixels at output rows 50 and 162 use
fixed RGB15 `000F` and `0260` respectively, compatible with
the independent original register transitions' broad upper and
lower non-edge colour bands. The original Snes9x observer samples
the register at *write time*, **not original final 256×224 RGB at
those original row/XY coordinates**. No original/native camera,
controller stage, guest-frame pairing, crop offset or pixel
ownership can be admitted from this register agreement alone.
Original and native completed pixel SHA256 differ in geometry
and phase, and have **not been declared unequal** or equivalent.

The previously rejected procedural 4× racer remains unapproved.
Do not modify gameplay/oracle, the native PPU/host, Modern
storage or independent release QA based on this helper.
The original 256×224 logical world, correct 7:6 display PAR,
exact 4× Original fallback and real wider-world materialization
remain unchanged.

### Reproduce offline

```sh
python3 -m unittest tests.unit.test_qa08_cross_original_native_live_colour_bands
python3 tools/qa08_cross_original_native_live_colour_bands.py \
  --original analysis/data/qa08-original-snes9x-2p-hdma-live-pixel-source-handoff-20261014.json \
  --native analysis/data/qa08-original-native-channel5-hdma-coldata-source-handoff.json \
  --pixels analysis/data/qa08-2p-original-native-text26-obj-palette-fingerprint.json \
  --out /tmp/qa08-live-register-band-agreement.json
```
