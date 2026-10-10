# QA-08: independent native stock-centre parity in the 342-wide field

**Status: accepted bounded native Original PPU observation**, merged #1210. The exact native AOT run `38083079741` passed; artifact `11681138053` contains both independent raw PAMs, full CRC witnesses and `ws342_original_center_parity_1856.json`. This is not a release certificate or a replacement for moving-rider visual review.

## Question

At one genuine moving 2P guest frame (1856), does the 256×224 PPU image
from an independent **fixed-width** native guest process equal the exact
centre crop [43, 299) of a separately executed **342×224** Original PPU
image, in both top and bottom split views?

The existing wide margin probes show live course pixels in the extra 43
columns per side. They do not establish that the original centre, HUD,
split boundary or moving OAM colours survive the widened presenter
unchanged. A source-derived alignment discrepancy could remain hidden
behind a plausible full-frame screenshot.

## Reused evidence and execution

- Fixed Original source run: the already-required `race_2p_split_ur_fixed_source_1x`, capturing guest frame **400** for the accepted fixed 4K witness. It now additionally captures **1856** through a separate, strictly parsed read-only environment selector. **No extra native process**.
- Wide Original source: the existing full 342×224 guest-frame-1856 PAM from `race_2p_split_ur_ws342`.
- Both images are real independently rendered native PPU outputs, require exact guest-frame filenames, and require the complete independent **2,473-frame guest CRC streams** to agree.
- `tools/check_baldosa_original_center_parity.py` examines **all 57,344 centre pixels**, preserving their full RGBA bytes. It emits exact stock and wide SHA256s, top/bottom changed-pixel counts, changed rows and the first twenty positional/RGBA differences.
- Machine-readable report and both native PAMs are retained in the existing Baldosa artifact; the existing 4K host and wider-world checks remain unchanged.

## Measured native result

At guest frame **1856**, all **57,344 RGBA source-centre pixels** matched: **0 top-band differences, 0 bottom-band differences**. Independently executed fixed Original and widened Original guest CRC sequences agreed for all **2,473** guest frames. The fixed PPU pixel SHA256 and recovered centre SHA256 both equal `6b907da3f91cf81cd31dfa6a4f781a879942e6a63efee42ecbe4e9113d11f689`. The actual full-width 342×224 PPU SHA256 is `0e956fac212cb7413a32ee2a0de318540e58cfd5f2b7610472c2573ab6719dd9`.

## Interpretation

`center-exact` is a strong same-frame Original centre-parity observation,
but not evidence of authored 342-wide HD, game-state equivalence, menu
transitions, all-course 1P/2P acceptance or hardware scan-out.
`center-delta-observed` is valid evidence, not a false unit-test success
or an automatic defect label. The differences must be classified by
screen region, camera/scroll, BG, HUD, OBJ, window and actual PPU source
priority before assigning a player-facing bug. Either status explicitly
withholds release HUD certification and HD replacement permission.

Zero synthetic/reconstructed frames enter native admission. Adversarial
unit fixtures exist only to prove that the comparator cannot ignore
small top-band/bottom-band changes or accept unequal guest CRCs.

## Next actionable graphical work

With exact centre parity established for this 2P frame, prioritize independent
wide-edge OBJ source visibility, later HUD/camera transitions and authored Remastered
racer coverage. The merged #1211 follow-up captures actual post-GO 2P source-wide
racing at frame 2208; neither test grants 342-wide HD source substitution.
