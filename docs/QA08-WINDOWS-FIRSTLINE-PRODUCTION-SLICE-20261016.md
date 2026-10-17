# QA-08: narrow Windows first-line HDMA production slice (2026-10-16)

**Disposition: draft integration candidate, NOT QA-08/10 acceptance or approved renderer/art.** This source-only extraction from the held experimental graphics PR #1641 is deliberately smaller than its 37-file branch, and #1649 remains independent research. It changes only the pinned disposable `gamesbyian/uniracers-recomp` source used to compile the existing Windows Uniracers PE. No global SNESRecomp checkout, CPU/APU clock, source guest, Modern persistence, game logic, or release ledger is modified.

## Decision and provenance

The original first-line HDMA implementation primes the first source byte(s), then restores the descriptor, so the first visible-line HDMA path reuses an already-transferred table entry. `tools/baldosa_uniracers_hdma_firstline_patch.py` advances the primed channel's table/descriptor, `repCount` and `doTransfer` through the existing transfer path. The change is ALL channels, source-pinned to title `10b864b9d14a7b7416dd909eb7b054c88faef101` and core `075fbe4c8e0d97b0013be541795c39cb644a9709`, plus the generated Uniracers guest. Fail closed on drift, partial patches, another title, or competing HDMA transforms. The test compares its transformation byte-for-byte with the independently exercised earlier all-channel experiment, including idempotence and negative cases.

Existing independently executed original/native *256×224* RGB5 witnesses from #1614/#1641:
- 2P countdown original callback 1855 ↔ native guest 1856: stock 971 wrong pixels, consumed-prime 0;
- three distinct genuine moving 2P original callbacks 2191/2207/2223 ↔ native 2192/2208/2224: stock 512 wrong each, consumed-prime 0 each;
- 2,473 complete guest-WRAM CRC records identical across four tested native experimental variants.

These are **source-qualified bounded raster results**, not real-device acceptance. Draft #1641 subsequently checked selected moving 1P/2P actual compiled Windows frames, but included *additional* V0 and 2014-reference brightness changes: its later 203/263 exact moving/result comparison must **not** be credited to this first-line-only extraction. Exact source-built CI and independent comparative capture remain required for this new head.

## Actual product staging

`.github/workflows/baldosa-windows-native-bridge.yml` retains current-main RF-015 and merged #1744 RF-017 generated-source verifier, exact Clang v1.0.14, `SOURCE_DATE_EPOCH`/PE timestamp evidence, and all present Windows Modern journeys. It dry-runs then stages this one HDMA transform **after immutable title/framework pins and successful USA RF-017 regeneration, before the real PE build**. The workflow explicitly includes new source/test invalidation paths. No opt-in raster research farm or heavy trace workflow is made automatic.

This is a reviewable integration candidate; CI passing means the source-guard, native compile and existing product journeys passed. It does not certify source-exact Original at transitions/results without an independently produced exact-PE raster.

## Open original/native visual causality, not safe to patch here

- Premature guest4016 unblank: historical original callbacks 4015–4016 are forced-black with `INIDISP=$80`; real Windows already has `$2100=02` at native 4016 (54,709 RGB5 errors). Determine originating CPU writer/NMI/beam and host replay field ownership before changing visible timing.
- Four-phase result CGRAM/source-clock cycle: 318,775 RGB5 errors in the verified 2P 263-field partition. Reconcile original `$2121/$2122` register writes, native guest VRAM/CGRAM and completed visible field before any palette/host-buffer adjustment.
- Medal pixels: original full 544-byte OAM at original host4032/4176 matches native incoming DMA host4030/4174. Native incoming 70/70 sampled sprite records match its effective raster. At the same five sampled medal pixels, two original and native BG1/OBJ winners differ although slot position/palette/priority coincide; tile delta is +2/0/−2 by slot group, not globally. Obtain source-WRAM at DMA trigger and first divergence instruction/beam from CPU/APU owner. No universal sprite-index or 2-frame frame shift.
- Two isolated finish pixels: both independent engines select BG3 main + OBJ sub, full addition at brightness7, with identical operand CGRAM. The 2014 Snes9x reference brightens before full add while native does after. This isolated historical-emulator-vs-native RGB5 difference must **not** authorize changing SNES physical DAC stage order, nor softening a raw comparator.
- Cursor RGB deltas similarly implicate 2014 brightness/math ordering rather than a blanket recolour.

The full historical 2P source corpus still reports **203/263 exact fields and 385,373 raw wrong RGB5 pixels** *on the broader held graphics candidate*, with no masking. Both drafts #1641/#1649 remain HOLD MERGE.

## Presentation and visual exit

Separate contracts and owners remain: genuine `256×224` stock source raster; `342×224` expanded *world*, not stretched 4:3; full-height `7:6` source pixel aspect; `512/513` 16:9 fit; selectable `1×–4×` nearest Original fallback. Existing native logical and physical **3840×2160** tests in `docs/WIDESCREEN.md` are valid for their exact sources but do **not** establish this newly extracted Windows PE's actual panel output, odd drawable behavior, P1/P2 source-visible racer identity or any authored 342-wide Remastered OBJ admission. Preserve centre pixels, both split bands, title/menu/finish transitions and HUD without crops or painting.

The project owner has separately **rejected the current procedural 4× racer likeness**. This patch supplies no HD graphics approval. Before any replacement art claim, present an official-reference/stock gameplay/old technical baseline/new model 4-column, perspective-registered side+expressive-pose study, both enlarged and at real 1P/2P gameplay scale, with numerical normalized landmarks and human likeness sign-off.

**Stop / handoff:** If an exact source-bound Windows compare exposes a regression or changes a previously exact scene, hold this PR and identify the first source-effective divergence. CPU/APU owner supplies source-DMA and `$2100/$2122` clock/beam equivalence, without a graphics agent changing CPU clocks. Independent QA owns any release-ledger update and physical display acceptance. Do not merge huge draft branches to resolve this small integration slice.

## Independent actual Windows source evidence: diagnostic versus clean production (October 17)

The separately compiled **diagnostic** graphics head `9b311887` in held PR #1745 produced four authentic 256×224 P7 images from the exact Windows Uniracers process on the 2,473-guest-frame short controller script. [Runner #39000100984](https://github.com/gamesbyian/UR-Recomp/actions/runs/39000100984), [artifact 12088668732](https://github.com/gamesbyian/UR-Recomp/actions/runs/39000100984/artifacts/12088668732), archived artifact digest `sha256:3d8bca597c8109744ceef07b8b63d590d6610b9922b585c70fb8ff5edc3f5f87`. All four full P7 SHA hashes **exactly matched** separately archived first-line corrected native source P7s; previous original/native RGB5 comparisons on the corrected variant showed zero incorrect source pixels. The two consecutive real 2P moving pairs changed 35,505 and 36,155 actual RGBA pixels, in both split-screen bands. No image matching an old incorrect native P7 remained.

The **complete native guest** digest is NOT legacy equivalent: actual current RF-017 Windows 2,473-CRC transcript `d1fb659fe3c23d37329cd78624d46fdcbf1445a09b812105905d7c0ca0e5a348` versus archived older pre-RF-017 `992dfdc270802e8a0ec1be5a0be6ddc36872edca11c8a91d58367a6235e537cf`. Both use controller-script SHA `4e714899f53c3bbe501bbfcacf91dd549989c9beb7c2cf6265b13eb687142ec6`. This difference remains evidence, not a waived guard or proven CPU root cause. Graphics #1745 adds a second real RF-017 Windows guest with the P7 observer disabled to independently measure full current-core repeatability. CPU/APU owns any causal pre-/post-RF-017 source-clock first difference.

**This PR stages the clean implementation only.** No observer source, checker, instrumented hook, brightness LUT, V0 override, emulator shim, source APU/CPU clock change or broad #1641/#1649 code. The newly compiled clean Windows executable has its **own** source and PE SHA, so the diagnostic P7 identity is supporting prior evidence rather than an acceptance receipt for this different binary. Even fully green product CI is insufficient for 1P/results, 7:6 physical 4K, owner-vetoed HD art or QA-08 release certification. Keep draft until independent source/owner review.
