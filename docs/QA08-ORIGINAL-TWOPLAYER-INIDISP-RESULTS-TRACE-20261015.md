# QA-08 source-certified 2P finish and results PPU register trace (2026-10-15)

**Actual original Snes9x register witness, not a Windows correction or a CPU-phase acceptance.**

The full-route original 2P source was previously captured from pinned 2014
Snes9x as **263 full-size 256×224 BGRX callbacks**, all ending at original
script frame **5484**. That source has been independently compared against
the corrected playable Windows executable: **190/263 exact**, **73
divergent**, **786,347 incorrect RGB5 pixels**, with the large divergences
concentrated in the finish fade and results-screen checkerboard animation.
The reference images were not discarded or replaced with screenshots.

The original harness already provides a patched `snesref_debug` register
export and exact `$2100–$2133` per-frame PPU write journal. Rather than
guess native brightness from screenshots or alter the original guest, I
introduced **only three additional zero-frame `dump` instructions** at
natural input-script command boundaries. The analyser proves that removing
those three commands returns exactly the stock original script minus its
`turbo on` acceleration directive, byte for byte. It re-executed all
**263 original frame callback captures and verified that every raw image
SHA-256 equals the untouched prior original source**. The original input
sequence, CPU execution, PPU imagery and frame count were therefore not
perturbed by the diagnostic observations.

Original PPU source: [run 38791934542](https://github.com/gamesbyian/UR-Recomp/actions/runs/38791934542), artifact `12000438001`,
whole ZIP SHA256
`d5e08ad76137c86125f64d52b6d0dc689352375ab536f4c430238f3bc6d6908e`.
The read-only source script SHA256 is
`bddfb15fedbaba3fcb0e95e628f11e1506fd210d93f4be67c6e9855c705dd3db`.
Diagnostic original `snes9x_libretro.so` binary SHA256 is
`11cd574e85e003986ad4633b47ce126f8c1867d54912e18c7aa6b84e074f3975`.
It is **not bitwise identical** to the earlier original-source compiled
binary, but exact 263/263 source-image replay establishes the narrow
reproducibility requirement of this register experiment. This does not
resolve independent toolchain binary reproducibility.

| True original scene | Snes9x frame | `$2100` V0 / V111 / V113 HDMA | Final brightness | `$2131` | CGRAM 512-byte FNV1a |
| --- | ---: | --- | ---: | --- | --- |
| Before finish | 3622 | 0F / 00 / 0F | 15 | 04 | `fe405bb5` |
| Finish fading | 3683 | **07 / 00 / 07** | **7** | 04 | `e79794a9` |
| Results | 5184 | No `$2100` writes in sampled frame | 14 | 7F | `e8cdbe60` |

Both the pre-finish and fading scenes also contain CPU `$2100=80`
forced-blank writes during V225 and restoration to `0F` near V242–243.
The early visible line's effective brightness is then independently
replaced by HDMA at V0. This establishes the original dual-camera
**three-band source behaviour**, including a true zero-brightness split
line and two equal upper/lower bands. It is consistent with the earlier
source-qualified brightness-seam correction and says exactly what the
native PPU register stream must accomplish.

The results screen instead uses mode 3, colour-math `7F`, brightness
`0E` and animated grayscale background. A checkerboard image mismatch
repeats at native frames 4064, 4176, …, 5408 (112-frame cycle), while
other nearby frame samples are source-exact apart from a small OBJ
colour difference. The registered source images and pixel-mask analysis
do not support shifting/cropping the whole image to repair it.

## Independent comparator handoff and gate

A separate graphics-owned **opt-in read-only native Windows PPU probe** is
now staged on draft PR #1641. It logs the active legacy PPU's INIDISP
brightness/forced-blank, CGADSUB, CGWSEL, fixed colour, and full CGRAM
FNV1a at the same bounded finish and results intervals. It does **not**
write guest code, DMA buffers, OAM, registers, Modern state or render
pixels, and is disabled in ordinary player sessions.

Once the Windows PPU probe completes, require:

1. **Same 263/263 native RGBA P7 source hashes** as the previously accepted
   full-route Windows capture, and unchanged native 5484-frame CRC receipt;
   otherwise the observer experiment is invalid.
2. Compare original and Windows register states at source-qualified
   frame boundaries and effective scanlines, taking account of source
   `retro_run` callback/guest numbering and HDMA V-counter semantics.
3. If native `$2100` is wrong at the finish, pass an exact register/beam
   timing witness to the owning CPU/guest/HDMA lane before altering
   timing or guest state. If registers are equal but source pixels
   differ, localize the raster/compositor error in this graphics lane.
4. For the result checkerboard, establish whether CGRAM and native
   scrolling/tile register state really match before changing colours
   or inventing an animation-phase fix.

Machine-readable register provenance:
`analysis/data/qa08-2p-original-INIDISP-HDMA-colormath-trace-20261015.json`.
The archive includes actual `*.regs.json`, `*.ppuw.tsv`,
`*.cgram.bin`, `*.oam.bin` and `*.info.json` files, not only a prose
interpretation. The original SNES logical frame is **256×224** with
authentic 7:6 display pixel aspect; no 216-line crop, HD racer replacement
or source-masked acceptance is permitted. The 4× Remastered
character likeness is still artistically unapproved, and **no release
ledger gate has been admitted by this experiment**.

## Rejected input-splitting probe and read-only host correction (October 15)

A proposed diagnostic split the existing original `press right+p2:right 1500` into consecutive holds of `1499` and `1` with one new zero-frame `dump` between them. Actual original 2014 Snes9x hosted run [38821308874](https://github.com/gamesbyian/UR-Recomp/actions/runs/38821308874) executed the candidate and **failed the mandatory whole-raster control at original callback 5215**. Its failed original artifact `12013131778` remains the negative witness. No CGRAM phase or original/native equivalence was admitted.

The specific cause is now source-read, not guessed: the pinned `baldosa/snesrecomp/tools/snesref/frontend.cpp` `script_tick()` inserts **one idle frame after each hold-type command**. Two syntactically consecutive holds are therefore not the same real input history as one continuous hold. Keeping nominal button-mask counts equal does not repair that difference. Reject this input-splitting method permanently for fidelity work.

The corrected discriminator keeps the historical source 2P script **byte-identical** to the already authenticated three-dump variant and instead stages an opt-in **host-only** `do_dump("qa08_results_previous")` immediately after `p_retro_run(); g_frame++` at actual completed frame 5183. It reuses the pinned debug core/ring and unchanged original source-image verifier; no guest code, CPU timing, raster state, menus or native Windows renderer is patched. This follows the existing read-only debug export semantics and still requires 263/263 original raw frames byte-exact, original 5184 register proof and source phase logs before accepting a chronology finding. The new automatic research trigger is temporary and must return to manual-only after the exact result is classified; independent actual Windows 1P/2P evidence still decides promotion.

## Exact adjacent-CGRAM result and bounded 112-frame follow-up

The *corrected* opt-in original-host 5183 snapshot passed [source run 38822001530](https://github.com/gamesbyian/UR-Recomp/actions/runs/38822001530), artifact `12013971294`, ZIP SHA256 `c547a38e64cc71a5c7041ea6126d10a0eb030ace08a2870716d3a0b91dcc5efc`. All 263 source images were **byte-identical** to independent uninstrumented original 2P. The stock three-dump input script SHA256 stayed `bddfb15fedbaba3fcb0e95e628f11e1506fd210d93f4be67c6e9855c705dd3db`, and script quit stayed 5484. Exact original CGRAM at frame **5183 and 5184** is `e8cdbe60` for both; **zero changed CGRAM words** and **zero $2121/$2122 records in either 5183/5184 journal**. An update in the single interval 5183→5184 is therefore ruled out. Native Windows CGRAM at 5184 still differs (`898ece20`); no native timing or raster correction is admitted.

The next bounded experiment uses the **same source-qualified original host and unchanged script**. Its opt-in read-only `snesref_dbg_ppuw_*` ring scan retrieves only $2121/$2122 actual writes for **5072..5184**, exactly one 112-frame result animation cycle ending at the discrepant frame. It must validate ring coverage, source frame/readout identity and the same 263 video frames. The output is a compact raw TSV with true register write beam phase, not 113 new per-frame screenshots or a global frame search. Record a negative zero-write result if that is what the machine reports. A native guest/PPU same-clock write witness is still required before changing original rendering.

## Resolved original data-port chronology: four-state palette phase (October 15)

**Source-only measurement completed.** [Run 38822737039](https://github.com/gamesbyian/UR-Recomp/actions/runs/38822737039) passed the exact pinned USA ROM/guest script and **all 263 original 256×224 BGRX callback hashes unchanged** against independently captured Snes9x. Its original diagnostic host/core binary SHA-256 is `39b70cd547420db5a920bd31d52bff19e9114af9d7ae69d156a110f9ce66221e`; artifact `12013432991`, entire artifact ZIP SHA-256 `d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8`. The historical original route remains byte-exact; the host-only capture does not modify CPU/APU, renderer, input, or game data. All tooling-unit and hygiene checks passed on exact graphics head `86d14efe74acde70328a62a381775ea59ba6158d`.

**Actual $2121/$2122 chronology:** the PPU's existing original write ring contains **192 CPU palette-port writes**, organized as exactly **12 writes every 7 frames**, over source frames 5073, 5080, …, 5178. Each update writes exactly four grayscale CGRAM slots `$6C–$6F` (one $2121 address plus two $2122 data bytes per slot) during V225–226. Every other slot is unchanged by these writes. The four 15-bit original colors `4210, 4631, 4A52, 56B5` rotate among those same four slots. The source updates repeat the exact four configurations every **28 frames**, including no palette writes in source frames 5183 or 5184. The visible source uses brightness 14 and Snes9x 5-bit multiplication, yielding grayscale values **123, 132, 140, 165**.

**Independent source reconstruction:** freeze the actual 512-byte source CGRAM at original frame 5184 (`e8cdbe60` FNV1a), replace **only** those four slots with their actual source port-write values from one of the last four update frames, and recompute the entire 512-byte FNV1a. This deterministically yields:

| Last original update | Full source-derived CGRAM FNV1a |
| --- | --- |
| 5157 | **`898ece20`** |
| 5164 | `6d363000` |
| 5171 | `2a904be8` |
| 5178 (observed original at 5184) | **`e8cdbe60`** |

The **previously independent real Windows source observer** recorded `898ece20` at native frame 5184, precisely one of these original-source reconstructions. Relative to current original frame 5184, that is one *future* seven-frame palette phase **modulo four**, equivalently three preceding updates, and correctly predicts every one of the earlier native→original visible grayscale replacements (`123→132, 132→140, 140→165, 165→123`). This is now a strongly source-qualified **palette phase classification**, but checksum equality is weaker than comparing all **512 native CGRAM bytes** and does not itself prove the native CPU performed the four writes at the wrong beam/guest phase.

**Sampling cadence correction:** the existing sparse source comparator samples every **16 frames**. The observed recurring mismatch every **112 sampled-game frames** can follow from aliasing a **28-frame four-state original palette cycle** with the 16-frame sample interval: LCM(28,16)=112. Do not attribute a standalone 112-frame animation to the original game without further proof.

**Next discriminator, no speculated fix:** on the same Windows original-mode candidate, read only native live palette **slots $6C–$6F** and preferably the entire 512 bytes plus the preceding native $2121/$2122 port chronology, with guest frame and beam/callback phase bound to the unmodified source frame. Compare actual words and their writers, not only the FNV checksum or already presented pixels. If native CPU/port updates are ahead, coordinate with gameplay CPU/APU writer authority; if phase-matched registers still render differently, localize the PPU snapshot/materialization ownership. Neither case authorizes a global gray remap, native-clock adjustment, instant source correction, release gate, or Remastered HD character approval.

Reproducer: `tools/qa08_classify_results_cgram_phase.py --source-archive <downloaded archived ZIP> --output <receipt.json>`, fail-closed on exact archive, PPU TSV, source CGRAM and 263-frame source receipt hashes. Machine evidence is `analysis/data/qa08-original-results-four-state-cgram-20261015.json`. The completed original research workflow is now **manual-only**; no temporary PR research fanout remains.
