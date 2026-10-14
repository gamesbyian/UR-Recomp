# QA-08: source-backed native BG3/racer colour constraints

**New direct original-native witness, 2026-10-13:** authenticated pinned Baldosa USA 2P native [run 38492408817](https://github.com/gamesbyian/UR-Recomp/actions/runs/38492408817), artifact **11863045863**. Downloaded artifact ZIP SHA256 `6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431`. Guest2208 unmodified 342x224 Original RGBA SHA256 `f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`; full **2,473** native guest CRCs agree.

## Source-observed PPU registers and exact native pixels

The original native PPU completed field has only **one colour register write**: `CGWSEL=$2130=0x02` at beam **V=239**, in blanking before visible row0. Genuine *completed and recording* baseline fields are both CGADSUB `0x04`, CGWSEL `0x02` and fixed RGB15 `0x0260` = RGB5 **(0,19,0)**. The true beam-order register replay has those values at every visible native tag 0–223. The pinned [beam-to-output crosswalk](QA08-PPU-RENDER-LINE-CROSSWALK-20261013.md) maps native tag N to original framebuffer row N. With these registers the pinned PPU allows colour math on **BG3**, not OBJ (CGADSUB bit2 set, OBJ bit4 clear); CGWSEL bit1 selects a subscreen operand when present.

The older independently accepted original/native PPU counterfactuals deleted only **upper front OAM slot98** and **lower front OAM slot96**, in independent native processes with matching guest CRCs. No such deletion is permitted in normal Original or Remastered shipping.

| Original post-GO guest2208 pixel evidence | Upper slot98 | Lower slot96 |
| --- | ---: | ---: |
| Exact affected rider/text positions | 13 | 13 |
| Final minus isolated rider source, RGB5 | (+13,0,0) | (+13,0,0) |
| Final after deleting only front rider, RGB5 | (28,0,0) | (13,19,0) |
| Native isolated source RGB5 values | (2,2,1)×1, (6,6,6)×2, (9,9,9)×8, (14,14,14)×2 | identical |
| Corresponding stock/source pixels | same X, lower Y +112 | all 13 exact |

The lower missing-rider colour contains green19, **exactly** the real fixed-green operand. The upper missing-rider red28 can be decomposed as red13+red15. Both are consistent with an ordinary BG3-main/subscreen colour-math configuration: a red13 BG3 text pixel as main, grey racer as subscreen when present, and distinct background/backdrop subscreen alternatives after deletion. That model explains the numerical constraints **without inventing OBJ red-only colour math**. It is still a hypothesis because actual per-pixel main/sub PPU layer ownership was **not measured**.

## How the new offline checker verifies the claim

`tools/qa08_postgo_colour_math_crosscheck.py` consumes that exact existing GitHub Actions artifact ZIP. It validates the authentic journal frame, complete guest-CRC count, both 224-line constant colour-register states, all **five raw 342x224 P7 payload SHA256** digests (unmodified Original, two independent isolated OBJ planes, two independent source-deletion Original frames), and all **26 individual RGB triplets** in the previously independently accepted front-text causal JSON. Values are converted back to native SNES 5-bit channels and checked for exact red-only +13 and identical cross-viewport source/stock pixel pairs.

The machine-readable distilled observed result is `analysis/data/qa08-2p-native-ppu-bg3-colour-constraints-2208.json`. The archived original native artifact is the evidence authority; this JSON is a derived research record, not another independent physical console acceptance. Unit tests use synthetic adversarial cases, including an altered racer source byte, not substituted original game evidence.

To reproduce with the existing artifact downloaded from run 38492408817:

```sh
python3 tools/qa08_postgo_colour_math_crosscheck.py --artifact /path/to/baldosa-native-spike-evidence.zip --out /tmp/qa08-2p-colour-constraints.json
```

## Remaining discriminator, not another colour overlay

The next narrowly targeted **source** witness would record native PPU main and sub-buffer layer/palette samples, actual per-pixel colour-math/window gate and the produced RGB at both affected coordinates (133,50) and (133,162), plus adjacent unaffected controls, in the exact stock 2P guest2208. Verify unmodified Original SHA and the same full 2,473 guest CRCs; keep recording strictly read-only and opt-in. Once the existing fixed/main/sub equation is actually source-proven, decide whether the current 4× presenter can preserve it without deleting overlapping riders. **Do not hard-code red13, infer source winner from RGBA matching, or promote the artistically vetoed procedural HD racer.**

No change to native physics, original renderer, Modern, release QA ledger, 256x224 geometry, 7:6 PAR, 4× Original fallback, widened world or physical hardware gate is authorized here.
