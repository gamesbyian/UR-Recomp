# QA-08: exact original PPU split OBJ image pairs in moving 2P

**Status: read-only multi-frame source observation, with automatic replayable
regression and pending PR unit acceptance.** No new emulator process,
guest input, rendering patch, source OBJ deletion, accepted artwork or
Windows release authority. This is a stricter **per-slot source-image**
observation than OAM placement geometry or PPU final-screen colour matching.

## Real native source discovery

The completed [Baldosa native AOT run 38097914195](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097914195)
artifact `11686843233` preserved 12 independently source-isolated 342×224
original PPU RGBA planes, covering the four original racer OBJ slots
96–99 at each of genuine moving two-player guest frames **1856, 1872
and 1888**. Their existing `ws342_obj_slot_*.json` reports require
the unmodified whole Original PPU image in six bounded samples, original
source log metadata and native guest CRC parity enforced by the existing
workflow. This change does **not** rerun any of them.

On each real frame, independently exported source slots **98 and 97**
contain the exact same nontransparent RGBA image at the exact same
logical X coordinate after translating Y by **+113** from slot98's
upper-band source into slot97's lower-band source. Likewise,
**99 and 96** are RGBA-identical under the same translation.
The identity includes every actual RGB and alpha byte, not just a
matching normalized opaque area or palette-similar drawing.

| Guest frame | Top98 = bottom97 source pixels | Top99 = bottom96 source pixels | Exact dy |
| --- | ---: | ---: | ---: |
| 1856 | 321 | 319 | +113 |
| 1872 | 325 | 330 | +113 |
| 1888 | 324 | 322 | +113 |

The six pair proofs examine **1,941 actual upper emitted pixels and
1,941 matched lower emitted pixels** in all four channels. Both
bottom-slot bounding boxes also exactly equal the corresponding
top-slot bounding boxes shifted by `[0,+113]`. The original racer
identities/poses can vary from frame to frame, so this is *per-frame
split presentation duplication*, not a promise that successive
animation states are identical.

## How to reproduce on the accepted AOT artifact

Extract **only** the existing original source and report paths from
artifact `11686843233` into a temporary directory and run:

```sh
python3 tools/check_baldosa_2p_split_obj_rgba_symmetry.py \
  --native-artifact-root path/to/extracted-baldosa-native-evidence \
  --out path/to/qa08-2p-split-source-rgba.json
python3 -m unittest tests.unit.test_check_baldosa_2p_split_obj_rgba_symmetry
```

The validator refuses missing or swapped slot/frame PNG-free P7 RGBA,
changed exact source SHA, source count or geometry, an unproven
original full PPU raster, inconsistent four-process same-frame
main-image SHA, wrong original source/OAM trace attribution, an altered
one-byte colour/alpha, or any shifted pixel outside the exact +113
raster mapping. It requires all **12** independent original source
exports with accepted existing read-only `status=passed` evidence,
six identical Original full-raster samples, and exactly the three
actual moving guest frames. Neither source RGB coincidence nor 2P
rectangular OAM placement would be sufficient.

## What is and is not learned

This independently strengthens the model of the original's split
source-ripping/OAM switching: the hardware slot names are screen
presentation aliases of two underlying **source images** in these
three observed 2P frames. Source slot numbering alone must therefore
not become independent-character identity for 2P HD art registration
or a reason to paint four different stylized unicycles.

The source image can be emitted without ultimately winning a final
screen pixel. Exact RGBA equality after translation **does not** prove
that both source instances own the final raster, or establish their
BG/window/other-OBJ priority, HD visibility, source removal safety,
lifetime beyond the sampled frames, 1P's y112 presentation semantics,
physical 3840×2160 output or complete-course correctness.

Treat the six matches as a strict sampled graphics QA invariant and a
valuable character-model reference. Retain conservative Original
fallback where slot attribution or foreground occlusion remains
uncertain. Current original-character-likeness veto and no-unapproved-
procedural-HD policy remain fully effective.
