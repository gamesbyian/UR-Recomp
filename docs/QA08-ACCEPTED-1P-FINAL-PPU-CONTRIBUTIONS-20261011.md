# QA-08: accepted live one-player original PPU final contributions

**Accepted bounded native graphical evidence, 2026-10-11.** The first
authentic 1P top-slot source alpha planes were accepted in native AOT
`38097914195` (artifact `11686843233`). The subsequently completed
exact-head native AOT [`38115756178`](https://github.com/gamesbyian/UR-Recomp/actions/runs/38115756178)
(artifact `11693865103`, branch head
`1a056857f81f2d53f27274e9f53950e61beed05f`) used **two separate
single-frame native PPU slot-removal counterfactuals** against that
unchanged Original control, both in the existing real one-player USA
Race route.

## Actual verified frame2208 result

| Source OBJ OAM slot | Original emitted alpha | Different native final Original pixels after separately removing this slot | Changed outside its original alpha |
| --- | ---: | ---: | ---: |
| **98** | 285 | **285** | 0 |
| **99** | 293 | **293** | 0 |
| **Distinct union** | **578** | **578** | **0** |

All **5,447** CRC lines matched across the exact five native guest
streams independently required by the new removal validator. The prior
five-way original source/1×/4× proof retained seven pixel-identical
Original source captures and established both source planes' exact
slot/frame SHA. The source planes at live frame2208 are geometrically
disjoint, and the two independently measured native final-change masks
are disjoint as well: zero emitted overlap and zero changed overlap.

The decisive result is **285/285 and 293/293 source pixels made
observable contributions to the native final Original raster** at this
same guest frame. All are in *actual* 342×224 raster y120–143.
The previous assertion that the unicycles are above an actual 1P y112
player-viewport divider is incorrect. OAM source slot names and
analytic raster-half partitions do not establish gameplay viewport
semantics. Earlier source-empty slots96/97 remain valid negatives.

Preserved machine-readable proof:
[`analysis/data/qa08-native-1p-final-ppu-contributions-2208.json`](../analysis/data/qa08-native-1p-final-ppu-contributions-2208.json).
It contains original/source/removal full-frame SHA256 identities, the
native run/artifact/head, accepted source and guest identity, exact
counts and explicit feature/QA limits. The full uncompacted source
report `ws342_live_1p_final_slots98_99.json` and genuine Original,
source and removed PPU PAMs remain in the referenced native artifact.
No copyright image bytes are copied into the repository.

## Reproduction and engineering consequence

[PR #1324](https://github.com/gamesbyian/UR-Recomp/pull/1324)
provides the exact process wiring, tests and checker:
`tools/check_baldosa_oneplayer_top_final_contributions.py`.
It reuses the pinned AOT guest and authentic `race_1p.txt` twice with
`UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual`,
`UR_RACER_HD_WIDE_REMOVE_FRAME=2208` and precisely one slot selected per
independent run. The checker rejects mutated guest CRCs, false
diagnostic labels, mismatched SHA and changed final pixels outside that
slot's actual source alpha. It admits a source-positive but
delta-negative result as a legitimate negative; this actual run yielded
two fully positive results. There was **no new emulator framework**,
synthetic racer, 4× art, host renderer or guest/ROM/input/WRAM write.

The formerly unknown **specific per-slot final-visible source extent**
at this 1P moving frame is now closed. This is useful groundwork for
future source-accurate Remastered sprites and exact character capture.
It **does not** prove general BG/window/OBJ priority across a moving
race, source pixel ownership at arbitrary other scenes/frames, safe
destructive removal at 342-wide production geometry, authored HD
racer transforms, original-character artistic likeness, physical 4K
Remastered, complete USA event parity or Windows beta acceptance.
The authentic stock Original raster and conservative Original fallback
remain required. The owner-rejected procedural unicycle art is not
restored to artistic/shipping approval by this evidence.
