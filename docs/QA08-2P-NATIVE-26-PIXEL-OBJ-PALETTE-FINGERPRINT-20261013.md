# QA-08: genuine 2P BG3/OBJ four-shade palette fingerprint

**Re-observed from the exact strict original/native run [38502862996](https://github.com/gamesbyian/UR-Recomp/actions/runs/38502862996), accepted/merged in [#1453](https://github.com/gamesbyian/UR-Recomp/pull/1453).** Evidence artifact ID **11867670354**. Downloaded ZIP SHA256 `5d669af7f333598612540e5bf1d7e6d7fd59d6b459f9e249054cbc85438bf4ed`. Source report `baldosa-evidence/ws342_native_text26_2208.json` uncompressed SHA256 `1eec27bc0b2fe801ec0f554e1057003c0bfa77afe32e8e176d39a57e445ebfe1`.

The independently exact-original accepted native USA 2P route at guest2208 compares **2,473 guest CRC records**, stock 342×224 PPU RGBA SHA256 `f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`, and 78 real compositor records: stock, only upper front OBJ98 removed, and only lower front OBJ96 removed at each of 26 text-covered rider pixel positions. **All 26 source occupants are already source-proven**, but this palette survey is a derived observational index, **not additional native or physical hardware acceptance**.

## Exact top/bottom shared raster colours, distinct OBJ palette classes

Both viewports use **BG3 main pixel `F21B`, RGB15 `000D` (RGB5 13,0,0)** at all 13 corresponding positions. Their real OBJ subscreen has *different original PPU tagged palette indices*, yet identical source RGB15 and 5-bit shades. The 13 pairs repeat at native displacement **(0,+112)** for the *same source/text intersection*. Do **not** generalize this displacement to full character geometry: the independently measured post-GO isolated source alignment is **(−13,+112)**.

| Pixels **per viewport** | Racer subscreen RGB15 / RGB5 | Upper native OBJ tag | Lower native OBJ tag | Final composite RGB5 |
| ---: | --- | --- | --- | --- |
| 1 | `0442` = **(2,2,1)** | `A6B8` | `A4C8` | **(15,2,1)** |
| 2 | `18C6` = **(6,6,6)** | `A6B3` | `A4C3` | **(19,6,6)** |
| 8 | `2529` = **(9,9,9)** | `A6B5` | `A4C5` | **(22,9,9)** |
| 2 | `39CE` = **(14,14,14)** | `A6BA` | `A4CA` | **(27,14,14)** |

The native pixel composer permits BG3 colour math here, not OBJ colour math directly. CGADSUB=04 and CGWSEL=02 select the subscreen as the second colour operand, so for these 26 pixels **`final_RGB5 = min(31, BG3_R13 + OBJ_R), OBJ_G, OBJ_B`**, channel-by-channel. `A6` and `A4` are PPU source Z-tag classes for different OBJ palette/math groups, not interchangeable palette indices. The accepted native emitter stores real pixel layer tags; matching RGB alone would **not** prove identical palette addressing.

In the destructive native *test only*, removing OBJ98 empties the upper subscreen at those 13 pixels, and **live** red fixed operand `000F` gives RGB5 `(28,0,0)`. Removing OBJ96 empties the lower subscreen at those 13 pixels, and **live** green fixed operand `0260` gives RGB5 `(13,19,0)`. In both tests, the other viewport's 13 OBJ source pixels remain unchanged. Saved field baseline `0260` is **not** the upper live fixed colour after HDMA.

## Reproduce independently from the existing native archive

```python
import hashlib, json, zipfile
from collections import Counter

archive = "/path/to/baldosa-native-spike-evidence.zip"
raw = open(archive, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "5d669af7f333598612540e5bf1d7e6d7fd59d6b459f9e249054cbc85438bf4ed"
with zipfile.ZipFile(archive) as z:
    src = z.read("baldosa-evidence/ws342_native_text26_2208.json")
    assert hashlib.sha256(src).hexdigest() == "1eec27bc0b2fe801ec0f554e1057003c0bfa77afe32e8e176d39a57e445ebfe1"
    data = json.loads(src)
    assert data["native_compositor_pixel_records"] == 78
    stock = data["samples"]["stock"]
    for upper in (True, False):
        sample = {xy: pixel for xy, pixel in stock.items()
                  if (int(xy.split(",")[1]) < 112) == upper}
        assert len(sample) == 13
        assert set(p["main_zbuf"] for p in sample.values()) == {"0xF21B"}
        print("upper" if upper else "lower",
              Counter((p["sub_zbuf"], p["sub_RGB15"], tuple(p["original_RGB5"]))
                      for p in sample.values()))
```

The compact, non-image derivative `analysis/data/qa08-2p-original-native-text26-obj-palette-fingerprint.json` captures the four authentic classes, per-viewport counts, source archive and report hashes, and the exact upper/lower native palette tags. This is useful when preparing **faithful presentation/HD-design reference** without overpainting the red HUD, but it does **not** authorize copying the overlap's final red-shifted colours into the rider texture.

**Boundaries:** 26 sampled text-overlap pixels do not establish source/final ownership for every sprite pixel, physical SNES priority or HDMA midline timing, any unsampled pose, or authentic 3D materials. The owner-vetoed procedural HD character remains unapproved. Preserve original 256×224/7:6 PAR, true source-backed 342×224 world, and pixel-exact 4× Original fallback.
