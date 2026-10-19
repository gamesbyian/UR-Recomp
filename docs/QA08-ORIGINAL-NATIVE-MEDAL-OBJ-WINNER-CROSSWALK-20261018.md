# QA08 original/native result medals: same winning OBJ slots, different video callbacks

18 October 2026 | **replayed authentic host raster evidence; no production correction or release gate.**

## Actual independent producer inputs

Reused the genuinely executed 2014 Snes9x painter artifact **12150037795**, SHA256 `8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4`, and the separately compiled RF017 Windows native physical 4bpp/OAM artifact **12134793278**, SHA256 `725ef03df3d43ff5d30b4bea944e32555974fb0b0e01af025da76ef88959b408`. The first contains **252 real original tile-call records**, **360 per-layer source-painter observations**; the second has **25 actual native 4bpp fetch writes**, **25 effective main-screen pixel owners**, **175 live OAM-line snapshots**, separately source-verified in merged [#1835](https://github.com/gamesbyian/UR-Recomp/pull/1835). No second emulator run or fabricated observer required.

This crosswalk inspects exactly two recorded *internal* labels, **4032** and **4176**, at five pixel coordinates each. It reconstructs original winning sprite writes independently in BOTH genuine original render passes (each source label was painted twice), and uses the actual final surviving source depth. It then compares the *same numerical internal native guest label* against the physical native fetch log's last 4bpp writer and effective PPU zbuffer. It compares **low 8 bits** of the original displayed tile ID to the native used tile ID, and original OAM tile name to native low OAM tile. It does not assume original/native complete execution or present-frame identity, and never compares a colour register word with an OBJ zbuffer.

| Pixel | Original last visible owner at both fields | Actual native winner | Tile low byte |
| --- | --- | --- | --- |
| (207,91) | BG0, original depth `27` | Native background, main enum `0` | No winning sprite |
| (205,115) | OBJ113, original depth `28` | OBJ113, actual final 4bpp writer | `a2` |
| (205,139) | OBJ114, original depth `28` | OBJ114, actual final 4bpp writer | `a4` |
| (225,96) | OBJ97, original depth `28` | OBJ97, after overlapping slot99 | `de` |
| (225,120) | OBJ96, original depth `28` | OBJ96, after overlapping slot98 | `de` |

**8/8 actual visible OBJ slot and tile-suffix comparisons agree, and 2/2 controls have a background main pixel with no winning OBJ.** All four contested x225 observations select the lower-numbered sprite, and the native encoded zbuffer agrees with that sprite's real final writer. Source-original painter and native PPU may visit contenders in different orders, which does not change the observed winner. The original 2014 full-word IDs like `15de`, native physical `used_tile=0de`, and actual register palette/priority bits are **not** themselves equal merely because the 8-bit tile suffix agrees.

## Why this helps, and what it cannot decide

The nearest visible rendering explanation, **wrong native last sprite slot or wrong tile-number suffix**, is unsupported at these ten observed source-internal labels. This is a negative causal discriminator for the **selected pixels**, not a blanket PPU correctness proof.

The independently authenticated [correct original video callback registration](QA08-ORIGINAL-MEDAL-CALLBACK-REGISTRATION-20261018.md) and [new medal phase discriminator in #1874](https://github.com/gamesbyian/UR-Recomp/pull/1874) remain crucial: an original painter labeled internal4032/4176 is the *following* original field relative to the correctly paired 2014 callback labeled4031/4175. In that correctly registered original/native video comparison **0/10 RGB5 pixels agree**, and the recurring original/native medal mask has 125/125 mismatched five-point samples across 25 source captures. Therefore **equal internal-stage sprite winner observations do not justify a global frame shift, native/OAM palette recolour, tile switch, suppressed pixels or release acceptance**.

Original painter input script and archived original callback execution share their exact 26 consumed original input transitions. The independent native Win32 4bpp producer used Baldosa's imported route; even though the scripts express the same 27 gameplay intentions after removing diagnostic commands, a **source-original/native actually consumed button+beam equivalence witness is still absent**. Modern product #1851 and its exact separate source P7 observer #1857 used another compiled PE; the 4bpp artifact does not inherit that PE identity by source similarity. This crosswalk proves only source-painter/native fetch anatomy at fixed named internal fields.

No CPU/APU/NMI clock, CGRAM register, PPU production code, Modern profile, sprite art, 342×224 world/pixel aspect, 3840×2160 display, release ledger or shipping renderer change occurs.

## Reproduce without another Windows or Snes9x run

```sh
python3 tools/qa08_verify_original_native_medal_owners.py \
  --original-painter /private/actual-source-artifact-12150037795.zip \
  --native-4bpp /private/actual-source-artifact-12134793278.zip \
  --out /private/qa08-archived-winner-crosswalk.json
python3 -m unittest tests.unit.test_qa08_verify_original_native_medal_owners
```

The stdlib-only tool refuses archive SHA drift, duplicate source fields, missing or changed observation populations, inconsistent original duplicated paint passes, altered native physical fetch/decoded OBJ values, source 4bpp/OAM mismatch, lost overlapping contenders and invented BG sprite winners. **A successful report cannot pass QA08, release or human art approval**. The next source-proven acceptance attempt must join original/native consumed input, actual source-present/beam chronology, and result CGRAM/main-sub operands before selecting any bounded production correction.
