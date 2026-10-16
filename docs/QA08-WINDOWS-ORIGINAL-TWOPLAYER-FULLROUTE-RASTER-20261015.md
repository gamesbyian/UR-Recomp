# QA-08: actual Windows 2P complete-route original raster adjudication (2026-10-15)

**Independent disposition: 190/263 sampled source pixels exactly match. 73 scenes are still divergent. Graphics release gate remains HOLD.**

The previously approved Windows 2P countdown and three post-GO moving source-pixel frames were **not extrapolated** to the full event. This experiment independently executed the same real USA retail `race_2p.txt` script with the original Snes9x core and with the actual brightness+HDMA-corrected Windows x64 Uniracers executable. Both original and native scripts terminated at **guest frame 5484**. The original core preserved the exact stock original actions except removing `turbo on`; Windows used its Git-for-Windows CRLF encoding of that same source script. Input and state snapshots across runtimes are not independently accepted merely from this video alignment.

## Immutable actual-source witnesses

- Original pinned Snes9x: [run 38781958316](https://github.com/gamesbyian/UR-Recomp/actions/runs/38781958316), artifact `11996107746`, original ZIP SHA-256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`. **263 unmasked 256×224 BGRX callbacks**, original callback range `1279..5471 step16`; **242 distinct images**.
- The actual Windows game: [run 38783232271](https://github.com/gamesbyian/UR-Recomp/actions/runs/38783232271), artifact `11997485920`, ZIP SHA-256 `b2a84f182b70b6bc5bc70338a602a7d979fd0d133c80217b70a682d69bea7c71`. Real corrected `UniracersSNESRecomp.exe` SHA-256 `9107fe4e5e6515f161f4f3e666349def7f4b2f242a1837db32ac09c70d1c1ac9`. **263 same-sized unmodified PPU P7 source frames**, native guest `1280..5472 step16`, complete **5484 native guest CRCs** (transcript SHA-256 `c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876`).
- The **independently implemented** full-source comparator `tools/qa08_compare_windows_original_twoplayer_sparse.py` ran again on archived sources in [Actions 38790782686](https://github.com/gamesbyian/UR-Recomp/actions/runs/38790782686), **success**, artifact `11999783198`, ZIP SHA-256 `d1bc6772bee78ba00883d42f78d41630cefe0141e0dfc3951370e3077c8a3ebd`. Exact route, source frame numbering, every source SHA, all 263 genuine source images, and full 57,344 unmasked RGB5 pixels per frame are checked. Only Snes9x original RGB565's sixth green bit is reduced to native RGB5. Zero pixel shifting, 216-high cropping, spatial alignment, temporal search, masked HUD, replacement screenshot or inferred presentation is accepted.

The full strict comparison covers **15,081,472 original/native source pixels**:

| Scene window | Original/native RGB5 exact | Divergent frames | Wrong RGB5 pixels |
|---|---:|---:|---:|
| Menu and countdown | 23/46 | 23 | 4,487 |
| Moving split-screen, finish transition and late results | 149/195 | 46 | 707,828 |
| Results/menu return | 18/22 | 4 | 74,032 |
| **Entire 2P source sample** | **190/263** | **73** | **786,347** |

**The first pixel difference** occurs in a small selection-arrow sprite at native 1280 (**245 incorrect pixels**). During countdown and earlier moving 2P gameplay, genuine full-source frames are exact. The first **large** difference occurs at guest **3648**, after source-exact scene 3584, with **27,136** wrong pixels. The original 2P finish screen is darkened and the Windows scene remains fully lit. In the subsequent finish sequence the actual original/global brightness differs while geometrical composition remains recognizable. At native **4016**, Snes9x is black and Windows displays an approximately 1–4 level dim results screen (**54,709 wrong pixels**).

The results checkerboard has a separate remarkably regular error: native frames **4064, 4176, 4288, …, 5408** (112-frame cadence) produce a checkerboard grayscale disagreement on approximately 24,000 pixels, usually interspersed with almost-exact source frames. At 4064 the original/native four grayscale RGB8 mappings are **132→123**, **165→140**, **123→165**, **140→132**. The text and scores remain aligned. A brute-force whole-field translation does not improve that frame over zero shift, while frames 4032 and 4080 are source-exact except for **296** small sprite pixels. This suggests a palette/CGRAM animation phase or compositor state defect, **not proved** as an isolated PPU algorithm error: compare original/Windows register and guest-phase evidence before changing rendering or game timing. Preserve source frames and the exact 112-frame periodicity as independent discriminators.

The remaining small menu arrow/rider/result icon colour disagreements often differ by one 5-bit channel unit and warrant separate OBJ/palette-colour-math inspection. Do not generalize a cursor fix across all colors. Current Windows 1P source benchmark remains **162/261** exact and **99.66%** fewer wrong pixels after active legacy brightness correction, with **no regressions** in those sampled scenes.

## Next bounded graphics engineering

1. Instrument **read-only** original/native `INIDISP` brightness (`$2100`), CGRAM writes/palette, colour-math `$2130/$2131`, and HDMA line/beam phase for exactly the first divergent finish window 3620–3888, blackout around 4016 and one pair of results checkerboard intervals 4032/4064/4080. Record actual guest and callback index. Prefer an existing pinned Snes9x PPU write-log witness rather than creating speculative guest patches.
2. If brightness registers and color-math line writes are identical, repair the earliest proven *graphics raster* mismatch with failing full-source pixel tests. If registers or timing differ, hand off exact source/phase evidence to gameplay Agent 1 or CPU/APU agent; **do not change their files** or paper over timing errors with sprite filtering.
3. Preserve the existing completed, tested original Snes9x and corrected Windows artifacts. Research-only comparator CI automatically reuses them; the expensive emulator producers are manual-only after acceptance. Avoid another automatic high-volume campaign.
4. Repeat distinct 1P/2P real Windows Original capture and player journey checks on any source correction; do not alter 256×224 logic, the authentic 7:6 pixel-aspect or 4×/widescreen extra-world contracts. A 216-high picture is not acceptable. Remastered character likeness and pose remain **unapproved** pending user aesthetic review.

**What this does not prove:** continuous event phase/instruction equivalence, physical SNES accuracy, effective per-scanline OBJ window ownership, correct host wide-world composition or HD character identity, or any release-quality ledger success. Keep the Windows graphics candidate #1641 **draft** until these gates are independently accepted. Machine-readable abbreviated source and hashes: `analysis/data/qa08-verified-windows-two-player-raster-fullroute-20261015.json`.


## Independent early cursor colour discrepancy in both original modes (October 16)

A fresh **archive-only** full-pixel cross-check of actual independently executed source samples compared Snes9x and the compiled Windows Original PPU in both 1P and 2P. Four historical ZIPs were byte-for-byte SHA256 authenticated, and each mode covered **25 preselected complete 256×224 frames** (guest 1280–1664 every 16; original callback = guest − 1), **2,867,200 unmasked RGB5 pixels** total. The original Snes9x RGB565 green6→5 conversion was the only colour normalization; there was no coordinate shift or pixel mask. Machine receipt: `analysis/data/qa08-early-cursor-crossmode-source-20261016.json`; unit guard: `tests/unit/test_qa08_early_cursor_crossmode_source.py`.

The **first divergence is a menu-selection arrow** in both modes. In 1P guest1280, **254** different pixels lie within x54–85/y193–210; in 2P guest1280, **245** lie within x32–63/y65–80. Across the bounded 25-frame window the wrong pixels are **1,050 in 1P and 4,487 in 2P**, with only the first six 1P scenes and first 23 2P scenes nonzero. The 2P frame1648 and all later previously captured pre-GO frames are exact. The *same independent pixel substitution* original expanded RGB5 `[90,74,82]` versus Windows `[90,66,74]` occurs **480 times in 1P** and **3,035 times in 2P**. This isolates a repeatable **colour/PPU-provenance discrepancy** within the arrow without requiring a guessed camera or renderer-wide timing fix.

**Not yet adjudicated:** whether the particular colour difference originates from CPU CGRAM palette entries, OBJ palette selection, active colour math, subscreen or host raster ordering. The preserved final pixels alone do not establish CGRAM words or effective priority. Do **not** remap those colours globally, infer that sprite OAM geometry decides final colour, or change instruction timing. Compare original/native CGRAM/CGADSUB and final pixel ownership on the earliest arrow scene before any narrowly scoped correction. The separately source-proven 2P blackout and cyclic result palette defects remain open. No release, widescreen, 4×, HD character likeness or QA-08/10 approval.


## Complete sampled original/native RGB5 residual partition (October 16)

Independently re-reading four unchanged SHA-pinned 2014 Snes9x and compiled Windows source-image archives gives a **complete accounting of every remaining incorrect pixel** in **261 sampled 1P and 263 sampled 2P** original-size full 256×224 RGB5 frames. Original callback=f−1 to native guest=f, no optimized frame search; original Snes9x green6→5 is the only colour normalization. Machine source identities and exact cohort arithmetic: `analysis/data/qa08-original-native-rgb5-residual-partition-20261016.json`, tested by `tests/unit/test_qa08_original_native_rgb5_residual_partition.py`.

**1P (162/261 exact, 19,153 wrong):** All 99 divergent frames have their *entire* mismatch bounding box at most **32px wide ×18px high**, moving with menu/result cursor positions. Six opening-menu arrow scenes account for **1,050** pixels; three finish-to-results scenes (guests 3968,3984,4000) account for **520**; 90 subsequent results/menu-return samples for **17,583**. Every sampled moving-race PPU image is exact. This does not accept continuous original/native CPU/camera/OBJ parity in intervening unsampled fields.

**2P (203/263 exact, 385,373 wrong):** The prior independent register/byte chronology accounts for **54,709** original blackout frame4016 pixels and **318,775** four-grey CGRAM-cycle pixels in 13 results frames. **All remaining 11,889** are: **4,487** pixels in 23 opening-menu cursor frames, **two one-pixel finish residues** at guests3792/3872, and **7,400** pixels in result-medal colour areas. The medal group contains **21** non-grey result samples with the *exact same 296-pixel XY mismatch mask* at x202..227/y91..153 (**6,216 pixels**). Independently source-classified grey-phase scenes add four further 296-pixel residual medal areas (**1,184 pixels**); together **25×296 = 7,400**. Original/native images show three small medal-shaped result icons in that region. These masks alone do not establish CGRAM provenance, OBJ priority or final pixel arithmetic.

This partition is exhaustive **only for the 524 sampled frames** and does not grant all-event, physical display, Widescreen/7:6, 4×, release or owner-vetoed character-likeness approval. Source-admission work next requires original/native effective CGRAM, $2130/$2131/$2132 colour maths and per-scanline OBJ/BG/window ownership for **one cursor** and **one medal** region, while CPU/APU and gameplay independently reconcile the earlier native results brightness/palette writes. No speculative global palette fix.


## Recomputable whole-raster source comparator (October 16)

`tools/qa08_verify_full_raster_residual_partition.py` **recalculates all 261 sampled 1P and 263 sampled 2P original/native RGB5 source differences directly from authentic frame bytes**, instead of trusting a summary. Four immutable 2014 Snes9x / real compiled Windows Actions archives, all full-ZIP SHA256 pinned:

| Source | Actions artifact | ZIP SHA256 |
| --- | ---: | --- |
| Original 1P | 11956993823 | `1b2fb01338380dc7e4d093ccbb0a5778bd04388945ee0bc7eb5b910d4de3ca59` |
| Windows 1P | 12009006895 | `db0dc0aacde50503aee0cdbe8047dc22ef1550233afd83c4c69fa27099f1d005` |
| Original 2P | 11996107746 | `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e` |
| Windows 2P | 12014896975 | `f01ab5a4888c227f306a0b9cd89e67710a4b41cad4c22867072280a17811fa82` |

It checks entire archive and every frame SHA, independent source manifests and USA ROM, preselected original callback `native_guest−1`, real full 256×224 P7 header and 57,344 RGB5 pixels per frame. No omitted regions, shifted registration, global colour remapping or invented frames. It independently recomputes **162/261 and 203/263 exact**, **19,153 and 385,373 wrong RGB5 pixels**. On genuine byte comparison, 21 non-grey results frames share an identical **296-pixel medal discrepancy footprint**. Four separate grey-phase result frames have that exact same 296-pixel non-grey footprint, after subtracting the recognized grey pixels. Whole-frame mask SHA256: `8b83bed21e2ff70ca279f993f4256e1edd64ad8f1edb657ee87554527e0594be`.

Reproduce with downloaded ZIPs:

```sh
python tools/qa08_verify_full_raster_residual_partition.py \
  --original-1p /path/to/qa08-1p-original-2014.zip \
  --windows-1p /path/to/qa08-1p-postv0-windows.zip \
  --original-2p /path/to/qa08-2p-original-2014.zip \
  --windows-2p /path/to/qa08-2p-win-current.zip \
  --out /tmp/qa08-source-partition.json
python -m unittest tests.unit.test_qa08_verify_full_raster_residual_partition
```

The recalculated result is preserved as `analysis/data/qa08-source-verified-full-partition-20261016.json`. Adversarial tests fail on forged archives, truncated pixels, false RGB5 green conversion and invalid mismatch classification. This bounded archive-only verifier **does not approve** complete original/native executed game phase, real effective OBJ/BG/window ownership, 7:6 PAR or Remastered likeness. Source-register and per-pixel priority witnesses, not recolouring, are required before a graphics fix.


## Distinct pixel causes: cursor palette-like, medals disprove RGB-only LUT (October 16)

Reanalysing the identical four SHA-pinned source ZIPs **per original/native full 256×224 pixel**, the very first 1P/2P menu-arrow scene permits a *single-valued mapping* for its **wrong pixels only**, but this does not prove a palette correction: **233/254** 1P and **196/245** 2P wrong source-colour pixels share an original RGB5 that also renders correctly elsewhere within that same source frame. A universal original-RGB5 → corrected-Windows-RGB5 lookup would therefore regress already exact pixels. The original/native effective CGRAM and $2130/$2131/$2132 remain unexamined for these arrow lines.

For the results medals, all **21** separately authenticated nongray result frames exhibit an invariant **296-pixel** erroneous footprint. The stronger negative is mathematical: **28 distinct original colours in each medal frame produce multiple divergent Windows colours for the same source RGB5**. In **16 frames, 294/296** bad medal pixels cannot be represented by a single-valued RGB5→RGB5 remap of wrong pixels, and in the other **5 frames 290/296** cannot. In every frame, **267/296** wrong source-colour pixels also occur as exact elsewhere in the same frame. The largest original-colour equivalence class reaches **eight distinct wrong Windows RGB5 outputs**. These facts **disprove a single global output RGB lookup or image-wide palette-remapping repair** of the medal pixels. They do **not** identify OBJ versus BG layer, prove sprite geometry, exclude per-tile palette-index state differences or diagnose final colour math. Pixel position and per-layer priority/palette provenance still require independently observed original/native PPU registers.

These measured negatives are computed from the independently SHA-verified source frames by `tools/qa08_verify_full_raster_residual_partition.py`, stored in `analysis/data/qa08-source-verified-full-partition-20261016.json`, and defended by `tests/unit/test_qa08_verify_full_raster_residual_partition.py`. There is **no pixel recolour or renderer adjustment**. Do not merge the HDMA candidate on this basis; the blackout/CGRAM CPU-phase blockers remain separate.


## Original OAM result medal source slot candidates, independently triangulated (October 16)

From actual original Snes9x archived OAM/PPU register captures [source run 38822737039](https://github.com/gamesbyian/UR-Recomp/actions/runs/38822737039), artifact **12013432991**, ZIP SHA256 `d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8`, retained original 544-byte OAM snapshots at Snes9x fields **5183 and 5184** are SHA256 `a9384c981763b175c9286fc06cd49f5cc183a5fdd6fd5f7920819f3d1300b5df` and `0107b6bde5aa41a234dc99fd24f9fae3de4ff718d757994bfbee996c88b6ff33`. Those two **complete OAM memories differ in 8 bytes**, but the seven specific candidate sprite records and their high-OAM size/X bits are unchanged. Original register snapshot: OBJSEL=$63, size select 3, first sprite 0; all seven are nominal **16×16 small OBJ, priority 1**:

| Original OAM slot | X | Y | Tile | OBJ palette | Spatial role |
| ---: | ---: | ---: | ---: | ---: | --- |
| 112 | 200 | 91 | $A2 | 5 | Top medal rectangle |
| 113 | 200 | 115 | $A4 | 6 | Middle medal rectangle |
| 114 | 200 | 139 | $A6 | 7 | Bottom medal rectangle |
| 96, 98 | 219 | 112 | $CC, $E6 | 5 | Adjacent right-side upper/middle OBJ |
| 97, 99 | 219 | 88 | $CC, $E6 | 5 | Adjacent right-side top OBJ |

Independently compare the actual archived compiled Windows and original Snes9x 2P guest 4032 and **all other 20** previously source-qualified nongray result frames; each has precisely **296** wrong full-PPU RGB5 pixels, original callback = native guest −1, identical real source XY mask. For every one of these 21 frames, **278** of those 296 wrong pixels lie inside the nominal x200..215 medal OAM rectangles, **18** lie inside the x219..234 adjacent slot-96..99 rectangles, and **zero** lie outside the union or in the space separating them. The 18 split into nine wrong pixels in the top band and nine in the middle band; none in the bottom. These are source-determined *spatial candidate rectangles*, not effective rendered pixel provenance.

The new `tools/qa08_verify_original_medal_oam_candidates.py` refuses altered original OAM, original/native producer ZIPs, any changed per-frame SHA or a single mask pixel not represented by exactly one candidate family. Machine evidence: `analysis/data/qa08-original-medal-static-OAM-candidates-20261016.json`; adversarial tests: `tests/unit/test_qa08_verify_original_medal_oam_candidates.py`. Reproducer with three independently archived ZIPs:

```sh
python tools/qa08_verify_original_medal_oam_candidates.py \
  --original-oam /path/to/qa08-original-register-writes.zip \
  --original-2p /path/to/qa08-2p-original-2014.zip \
  --windows-2p /path/to/qa08-2p-win-current.zip \
  --out /tmp/qa08-medal-oam-candidates.json
```

**Critical no-merge boundary:** original Snes9x OAM fields 5183/5184 are *not* the same frame as genuine Windows guest 4032, and even same-frame OAM end-snapshots do not necessarily reflect the **effective** OAM values at lines 91–153. The split-screen title rewrites high-OAM with HDMA, and priority/OBJ shade depends on the active line's buffer and BG/window/colour maths. This is a concrete **seven-slot, three-band** target for a subsequently independently matched original/native scanline capture, **not proof** that those seven objects are final pixel owners or a rationale for OAM slot remapping. Source CPU/beam parity, forced blank and results CGRAM phase remain independently unaccepted, along with 7:6, 4× and HD likeness.


## Live Win32 source provenance isolates two-tile medal OAM candidate (October 16)

The exact-head graphics candidate (Windows run [38862296865](https://github.com/gamesbyian/UR-Recomp/actions/runs/38862296865), all **30** enabled steps successful) now has a genuine opt-in **legacy renderer** per-pixel source observer at 11 already independently original/native-wrong pixels. Source-only original/native reference geometry: full 256×224, original callback=f−1. Bound Windows source ZIP artifact **12030148116**, outer SHA256 `002c95a44f3539652760609c6f6d7376c82e6014f2481cc60bbb1f8990b3b970`. Its native actual 5,484-frame 2P CRC SHA256 remains `c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876` and actual source executable SHA256 is `bb96e2cabc045244b6ad8c2c3bca90db25080759192666e895a602ed04018fff`.

**Native PPU final-pixel ownership is now observed, not guessed from screenshot geometry.** At guest1280 cursor (55,65), the original expanded RGB5 is [90,74,82] and native is [90,66,74]; native main resolver layer0 (BG1) and subscreen layer4 (OBJ) are both active with math, main pre-math RGB5 [15,15,15] and sub [9,4,6], actual CGADSUB=$7F and CGWSEL=$02. For result guest4032, the native top-medal wrong pixel (207,91) resolves **BG1 main / backdrop sub**, OBJ buffer empty at that position, so it cannot be fixed by a global palette remap. The middle (205,115), bottom (205,139) and adjacent (225,96)/(225,120) wrong pixels resolve **OBJ layer4** on both screens with live OBJ CGRAM indices E4, F6, DE respectively and source-exact native outputs. The same five pixel-layer/OBJ samples are repeated unchanged in guest4176 despite the separate gray-phase issue.

The **per-scanline live native OAM source** provides a narrower discriminator. Across each of the five actual sampled native lines at guest4032 and again at 4176, OAM slot 112 has tile/attr `1BA0`, slot113 `1DA2`, slot114 `1FA4`. The separately original Snes9x archived results at frames 5183/5184 identify the exact same three slots, coordinates and palettes but tile/attr `1BA2`, `1DA4`, `1FA6`. Native slots96/97 use `1BCE`, whereas that later original end-OAM uses `1BCC`; slots98/99 may differ between the two observed native result frames. Thus the medal candidates exhibit an **exact two-tile index discrepancy**, not merely an image colour transform. However the original OAM reference is at frame5184, **not original callback4031/4175**, so this is still an observed cross-time difference, not an independently assigned graphics-vs-guest cause. Importantly, selected original object palettes 5/6/7 map into OBJ CGRAM $D0–$FF, separate from rotating result gray indices $6C–$6F.

Research-only matching original-source programme: `tools/qa08_snesref_original_medal_fields_patch.py` adds three read-only host `do_dump` callbacks at **original 1279,4031,4175**, after executing the exact original input; `tools/qa08_verify_original_medal_endfields.py` checks their true frame numbers, original full BGRX framebuffer SHA against the already independently captured 263-frame Snes9x source, registered sprite bytes, all 256 CGRAM words and PPU port-ring/host metadata. `.github/workflows/qa08-original-medal-matching-source.yml` runs only on this research PR or a manual dispatch, reuses the existing pinned 2014 Snes9x debug library and full USA input, rejects changes to any of 263 original frames, and retains only bounded OAM/CGRAM register evidence. **Original end-of-field snapshots do not prove the effective scanline OAM.** No original/native CPU/beam phase or per-pixel OBJ authority, full game, physical 7:6/4×/HD appearance, or QA-08/10/release acceptance follows from matching snapshots alone. Never shift tiles or recolour the medal until source-matched evidence assigns OAM production, tile VRAM, sprite priority and color math to the correct owner.


## Matched-number original/native OAM experiment adjudicated (October 16)

The one-shot original 2014 Snes9x source run [38864201582](https://github.com/gamesbyian/UR-Recomp/actions/runs/38864201582) **executed successfully through the unmodified full 2P route** and archived source artifact **12030581890**, ZIP SHA256 `7a506cfc5f44bd8cc6aaba8482f42140b51618ba14aedec8f9bc7558417ad4b2`. The independent `qa08_original_results_port_chronology.py` stage **accepted all 263/263 video callbacks byte-exact**, unchanged controls and original CRC-side reference before the newly added checker rejected the *different* snesref end-of-field screenshot. Separate native full-2P Windows successful capture: [38862296865](https://github.com/gamesbyian/UR-Recomp/actions/runs/38862296865) artifact 12030148116, ZIP SHA256 `002c95a44f3539652760609c6f6d7376c82e6014f2481cc60bbb1f8990b3b970`, actual **5,484 guest CRC** entries source-hash unchanged and 70 native live scanline OAM slot records.

**The real original Snes9x OAM snapshots are now at original corresponding fields 4031/4175, preselected callback=f−1 for native guest4032/4176.** Independently byte-read original complete 544-byte endfield OAM; slots 112,113,114 in **both** fields contain sprite tiles `$A2,$A4,$A6` at x200/y91,115,139, palettes5,6,7 and priority1. The native PPU's **actual 5 sampled raster lines per result field** record the same positions/attributes, yet those three tiles are `$A0,$A2,$A4` in both guest fields: **−2 native**. Original slots96/97 both carry `$CC`; native carries `$CE`: **+2 native**. Crucially, slots98/99 are **identical** original/native (`$E6` in 4031/4032 and `$E2` in 4175/4176), ruling out a universal sprite-tile offset. Fourteen independently source-anchored slot×field comparisons have the same result. The actual Windows pixel-layer witness includes one wrong top-medal sample where native main resolves BG1 with no OBJ, while three other tested medal/adjacent source pixels resolve OBJ. The registration is source-evidence for a **specific OAM tile selection disparity**, not yet its CPU-vs-renderer origin.

**Important producer nuance that initially failed the new checker:** `snesref`'s original completed-field *host screenshot* is not identical to the already authenticated video callback with the same numeric field. For original 1279,4031,4175, mismatches are respectively **216**, **778**, **766** entire pixels of 57,344. Both original image producers' complete 256×224 raw bytes and individual SHA256 are preserved; neither is masked, cropped, shifted or silently relabelled. The original **263 callback images remained byte-exact**, which is independent of this host screenshot disagreement. The corrected original-source `tools/qa08_verify_original_medal_endfields.py` pins the separately observed host screenshot SHA and its exact discrepancy counts, compares original reference pixels **only to original video callback bytes**, and checks original OAM/CGRAM/PPU metadata from the genuine completed-field observer. Negative tests preserve this separation.

All three genuine source archives are independently paired in the archive-only, SHA-pinned `tools/qa08_verify_matched_original_native_medal_oam.py`. Its output authority `analysis/data/qa08-original-native-matched-medal-tile-discriminator-20261016.json` records all 14 paired slot deltas, 70 native OAM line samples, all frame-identity caveats and exact upstream source SHA identifiers. Its adversarial test is `tests/unit/test_qa08_verify_matched_original_native_medal_oam.py`.

The original-emulator workflow `qa08-original-medal-matching-source.yml` is **retired to manual-only** now the source producer and its archived proof exist; documentation changes need not incur another costly Snes9x build. The broken initial post-capture checker was an overly strong equivalence assumption between host screenshot and video callback, not evidence of a guest/raster mutation.

**HOLD:** Matching *numbered* fields and two completed-end OAM dumps are not Snes9x *scanline-effective* OAM or proven equivalent 65816/NMI/beam phase. Original PPU sprite tile data (VRAM), true OBJ-vs-BG/window priority, and guest CPU production of those tile words remain separate decision gates. Do **not** patch all sprite tile numbers by ±2, recolour medal pixels, merge graphics #1641 or accept physical 7:6/4×/HD likeness/QA-08/10/release quality on this evidence alone.


## Original 2014 PPU OAMDMA byte-source proof (October 16)

An additional independent read of **the same already archived original Snes9x producer bytes** settles whether the original OAM snapshot could simply have been a post-frame OAM rewrite unrelated to on-screen sprites. For original 1279, 4031 and 4175, their corresponding `.ppuw.tsv` debug journals (SHA256 respectively `d35f96e06ccfb136ee6540cb170b9653e8dcd65585cfe1ca7d88bc4649afbb9e`, `2ad83b28ebd60707e712c29735c5ab0d7dbcfb95b66b147274fc2f36bb83e530`, `ea2624b4225e860732624ec664899a75c8da838ab2fd6671a1f9003242b67384`) record **exactly 544 $2104/OAMDATA writes per original field**. Every write is tagged **DMA**, and all occur during VBlank (frame1279 V229–232, frame4031 V226–230, frame4175 V227–230), with **zero recorded active-visible scanline OAMDATA writes**.

Most importantly, the **entire ordered sequence** of those 544 observed actual $2104 data bytes is **byte-for-byte identical to the complete 512-byte low OAM + 32-byte high OAM snapshot** in each field. The original medal slot tile bytes were therefore genuinely DMA-written before the 0–223 visible raster lines, not merely misread after the fact. Within complete recorded PPU-port writes, there is no later active-line OAMDATA write that could replace them. At source4031/4175, byte offsets `450,454,458` (slot112/113/114 tile entries) are `A2,A4,A6`, while offsets `386,390` (slot96/97) are `CC,CC`. Original slot98/99 offsets `394,398` are `E6/E6` and `E2/E2` at the two source fields.

The archive-only `tools/qa08_verify_matched_original_native_medal_oam.py` now requires exact 544-write original source journals, **all bytes** reproducing OAM, every source tag being DMA, VBlank-only beam positions, exact journal SHA and chronological ordering. The adversarial test rejects fabricated writer tags, visible-scanline writes, truncation and changed tile payloads. This strengthens *original-side OAM source provenance*, but still is not direct same-scanline original OBJ priority/colour math or original/native 65816 instruction-phase parity. The native OAM discrepancies and separate INIDISP/CGRAM-phase defects remain unresolved. No tile edit, palette replacement or graphics merge is authorized.


## Critical correction: original snesref frame-counter registration (October 16)

**The earlier claim of exact source-time matched OAM is withdrawn.** The original `snesref/frontend.cpp` labels raw video callback using pre-increment `g_frame`, while `capture_frame` saves `g_fb_frame=g_frame+1`, and host `do_dump` runs after increment. Consequently, host OAM dumps labelled **4031/4175** accompanied raw original callbacks **4030/4174**, not 4031/4175 as the comparison assumed. The 216/778/766 pixel differences were a **one-frame registration error**, not independent image producers of identical-numbered original frames. The 544 original VBlank DMA writes are genuine and byte-exact for their captured fields, but comparisons with native guest4032/4176 **cannot establish the claimed −2/+2 OAM tile discrepancy**. Research workflow targets are corrected to host dump **1280/4032/4176** for original raw callbacks **1279/4031/4175**. Prior archive-only comparator is disabled as an acceptance gate until the newly aligned OAM evidence is captured, and neither a sprite patch nor graphics PR merge is authorized.
