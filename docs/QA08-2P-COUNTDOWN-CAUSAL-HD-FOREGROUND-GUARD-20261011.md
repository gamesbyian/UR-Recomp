# QA-08: original PPU countdown foreground anti-overpaint guard at two moving frames

**Status:** a strictly bounded, offline, non-destructive visual acceptance
*negative guard* for eventual 342-wide 2P Remastered captures. It is not an
art producer, video filter, game/presentation change, general depth mask,
HD shipping gate, or a substitute for source-registered 3D likeness review.

## Why original source pixels cannot be painted blindly

The existing authentic PPU frame1872 2P original (342×224) simultaneously
shows 330 opaque lower slot96 pixels and 325 opaque lower slot97 pixels,
including 244 shared coordinates (**411 distinct source pixels**).
A native `RemoveFromGame` counterfactual of **both** slots96/97 only at
guest frame1872 produces a byte-identical complete Original raster
despite both source planes being populated. Every original final image
pixel at those 411 coordinates is `RGB(57,57,255)`, matching the visually
identifiable blue countdown "2". The original slot sources must remain
present to resume correctly after the countdown, yet those 411 pixels
are *demonstrably invisible in the final Original at each of these exact frames*.

Native **accepted exact-head [run 38118239801](https://github.com/gamesbyian/UR-Recomp/actions/runs/38118239801)**
artifact `11694303573` retains the stock, both independent OBJ source
planes and actual paired-removal 342×224 PPU output, including the
single authentic slot96-97 arm marker. Its PPU route finished and
original/removal guest CRCs matched. The prior run `38117375415` was red because the first version
of a validator used the 5,447-frame **1P** CRC count instead of
2,473 for this **2P** route; its correction in
[#1330](https://github.com/gamesbyian/UR-Recomp/pull/1330)
is now **native-green** on exactly the reviewed branch head.
The official successful AOT artifact contains the independent,
native-produced causal report
`baldosa-evidence/ws342_pair96_97_countdown_causal_1872.json`,
including **all four 2,473-line guest CRC stream parity checks**,
the exact native PPU pair-removal arm status, source slot hashes,
full stock/removal framebuffer hashes, positive source emission and
zero final pixel change.

## Regression contract

The source-tested extension [#1334](https://github.com/gamesbyian/UR-Recomp/pull/1334) independently repeated the native pair-removal test at **guest1888**, where lower source96+97 emit 322+324 pixels on **409 distinct original source coordinates**. It again found **zero final Original pixels changed**, despite 78 different lower source-alpha support positions relative to1872. Exact-head native green AOT [38119117927](https://github.com/gamesbyian/UR-Recomp/actions/runs/38119117927), artifact `11694649120`, includes two accepted native causal reports for frames1872 and1888. Original and removed PPU RGBA SHA at1888 are both `7de0e805f07234d0b7b6c4c526eea79b5c6c523ff594c09ddc9970de238eede7`.

The new standard-library-only
`tools/check_baldosa_2p_countdown_hd_foreground_guard.py` takes
the **actual native original/source96/source97/pair-removed PAMs**,
the successful native AOT's own
`ws342_pair96_97_countdown_causal_1872.json` report (including stock
and source SHA256, authenticated OAM pair removal, four 2,473-frame
CRC stream equality, zero final delta and denied HD permission), and one proposed
**candidate full RGBA presentation capture at 1×, 2×, 3× or 4×**.

For each authenticated frame separately (either **411** source-alpha-union positions at1872 or **409** at1888), it
requires *every* candidate subpixel to equal the genuine stock
Original RGBA byte-for-byte, including alpha, **not only the blue
channel or one sampled subpixel**. Any mismatch fails with a bounded
`[logicalX,logicalY,subX,subY]` example; other output coordinates
remain outside the scope of this specific guard. It fails on
altered stock/source hashes, a non-identical pair-deleted PPU frame,
missing source, changed source emission/blue-cover counts,
inconsistent source-slot/frame identifiers, incorrect output
raster density/header, aliased candidate and any claim that the
native proof authorizes remastering. It never erases or paints pixels.

Extract successful two-moving-frame native evidence artifact `11694649120` into a
temporary directory, which already contains the report and all
necessary source PPU images:

```sh
python3 tools/check_baldosa_2p_countdown_hd_foreground_guard.py \
  --stock native/baldosa-ws342-captures/ur-baldosa-ws342-001872.pam \
  --source96 native/baldosa-ws342-obj-slots/ur-baldosa-ws342-obj-slot96-frame001872.pam \
  --source97 native/baldosa-ws342-obj-slots/ur-baldosa-ws342-obj-slot97-frame001872.pam \
  --without-pair native/baldosa-ws342-counterfactual-pair96-97-frame1872/ur-baldosa-ws342-001872.pam \
  --candidate native/baldosa-ws342-captures-4x/ur-baldosa-ws342-001872.pam \
  --causal-evidence analysis/data/qa08-original-2p-countdown-pair-native-causal-zero-1872.json \
  --frame 1872 --density 4 --out native/qa08-countdown-protection-1872.json
python3 -m unittest tests.unit.test_check_baldosa_2p_countdown_hd_foreground_guard
```

To independently validate moving frame1888, use the same invocation with the frame1888 stock, source96/97, pair-removed native PAMs and `ws342_pair96_97_countdown_causal_1888.json`, with `--frame 1888`. The CLI exits nonzero for **one changed subpixel** on either frame. The synthetic
adversarial tests cover the exact 1×/4× positive, changed hidden
foreground at a single 4× subpixel, allowed changes elsewhere,
forged native/source hash, plausible-but-different deleted raster,
wrong 1P CRC length, bad source or art permission, and malformed
candidate output.

## Real Native 4× Original control (no new build)

The same genuine successful native artifact includes the 1368×896 4×
Original density capture from frame1872. Independently expanding
the complete original 342×224 RGBA to 4× and comparing that whole
capture shows **zero pixel differences across all 1,225,728**
physical Original output pixels. Crucially, the same 4× image has
**zero unauthorized overpaints at all 6,576 protected source
subpixels** (411 × 4 × 4). The successful moving-frame native Original
4× source output at1888 independently preserves **all 6,544** protected
output subpixels (409 × 16), and its **entire 1,225,728-pixel** 1368×896
output is also an exact 4× Original repeat (zero changed pixels). Both
frames together test **13,120** source-backed hidden-racer 4× subpixels. The original stock, counterfactual, both source planes and
real 4× capture SHA/count witness at1872 is preserved in
[`analysis/data/qa08-native-2p-countdown-4x-foreground-preservation-1872.json`](../analysis/data/qa08-native-2p-countdown-4x-foreground-preservation-1872.json).
No copyrighted ROM-derived frame bytes are committed.

## Explicit non-admission

A passing future Remastered candidate only shows that it did
**not** overpaint the causally hidden source pixels in the chosen
independently proven native countdown frame (1872 or1888). The checker does not authenticate that
the candidate came from the same guest execution, check broader
2P occlusion, derive what hardware background/window painted the
numeral, establish frame-by-frame safety, validate 3840×2160 physical
output, approve source removal or revive owner-rejected procedural
unicycle artwork. Those still require their independent native,
visual-art and release sign-offs. Preserve full Original fallback.
