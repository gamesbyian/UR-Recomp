# QA-08: title-scoped HDMA first-line Windows renderer candidate (2026-10-14)

**Disposition: implemented Windows build candidate, HOLD FOR INDEPENDENT GRAPHICS VALIDATION.**
This change stages a pixel-visible PPU timing correction in the actual
`UniracersSNESRecomp.exe` candidate *only*. It does not promote upstream
SNESRecomp, change a ROM or guest 65816 opcode, CPU/APU timing, Modern
profiles/options, or the release ledger. The branch must not be merged on
the strength of unit tests or 2P-only source pixels.

## Source provenance and exact original/native observations

The global all-channel first-line HDMA consumed-transfer experiment is
`tools/qa08_patch_hdma_prime_counterfactual.py`. Independently executed
real original Snes9x vs native Baldosa **256×224**, unmasked, same-coordinate
RGB5 comparisons (only Snes9x RGB565 green6→5 reduction, no artificial
shift/crop/scale) gave the following existing results:

| Actual scene | Original Snes9x callback → native guest | Pinned native wrong pixels | All-channel consumed-prime wrong pixels | Independent original/source authority |
| --- | --- | ---: | ---: | --- |
| 2P countdown | 1855 → 1856 | 971 | **0** | [countdown study](QA08-ORIGINAL-COUNTDOWN-VS-NATIVE-PRIME-20261014.md), original run 38630121814 |
| 2P active moving | 2191 → 2192 | 512 | **0** | [moving-source window](QA08-ORIGINAL-2P-MOVING-SOURCE-WINDOW-20261014.md), native run 38665202913 |
| 2P active moving | 2207 → 2208 | 512 | **0** | same source study; separately accepted post-GO control |
| 2P active moving | 2223 → 2224 | 512 | **0** | same source study |

The three post-GO scenes exhibit tens of thousands of differing real original
source pixels across their two viewports. Thus this is **three distinct moving
2P frames**, not three identical static captures. The four independently
executed native variants have **2,473 identical guest CRC records each**.
The original callback pair is the preselected top-scoring candidate among
37 original callbacks for both additional moving scenes. This is a strict
raster registration, **not** a separate executed-65816/camera/inputs parity
witness.

The verified source manifest and SHA-bound per-variant frame identities are
`analysis/data/qa08-real-original-native-postgo-3frame-rgb5-parity-20261014.json`.
In the countdown, selective ch7 and ch5+7 still leave **460** pixels wrong,
so this candidate uses the previously exercised *full* channel advance.
At moving post-GO frames all three first-line-consuming variants agree.
The stock error includes the two-row split brightness seam at output rows
111/113; countdown additionally fixes 459 non-seam contour pixels.

## Implemented graphics correction

`tools/baldosa_uniracers_hdma_firstline_patch.py` first requires:

- Exact `gamesbyian/uniracers-recomp` commit
  `10b864b9d14a7b7416dd909eb7b054c88faef101` and
  SNESRecomp submodule `075fbe4c8e0d97b0013be541795c39cb644a9709`.
- The generated Uniracers guest code exists in the disposable checkout.
- The original known HDMA entry function, A-bus paths, OAM pin, descriptor,
  first-line save/restore and normal-HDMA surrounding source are intact.
- No existing global, ch7-only or ch5+7 experimental transform is installed.

It consumes the first already-applied HDMA line as the channel's own transfer:
`repCount--`, derive `doTransfer`, load the next descriptor if needed.
The C algorithm is compared against the previously executed experimental
transform in negative/idempotence tests. **No new renderer** or second
guest is introduced; the corrected visual pixels flow through the existing
native PPU into the real Windows package.

The `baldosa-windows-native-bridge.yml` build inserts the patch after the
pinned RF-015 DRAM correction and before CMake, and includes the source and
unit test in its PR trigger scope. A dry-run checks all required anchors;
`--apply-candidate` then changes only the disposable game checkout.
The unrelated shared SNESRecomp source checkout/pin and other games' CI builds
are untouched. This does **not** prove that an upstream global change would
be correct: pinned core explicitly documents Gundam Wing's distinct
mid-frame HDMA activation.

Local validation:

```sh
python3 -m unittest tests.unit.test_baldosa_uniracers_hdma_firstline_patch
python3 -m unittest tests.unit.test_qa08_patch_channel57_prime_counterfactual
```

## Acceptance still owed before integration

| Surface | Current evidence | Required independent exit |
| --- | --- | --- |
| 2P countdown | Exact 57,344 RGB5/57,344 experimental global source | Actual corrected packaged Windows raster capture using this build/route |
| Three moving 2P scenes | Three exact experimental source frames, 2,473 identical native guest CRCs | Actual packaged 2P run with source phase/OBJ/window inspection |
| Moving 1P | Original 342×224 & exact native 4× fallback proof, **no first-line A/B original comparison** | Unmodified original/native 1P source pixels, phase, camera and racer evidence |
| 2P transition/terminal results | Not source-accepted | At least one original/native aligned transition and result scene |
| Split raster OBJ ordering/window | Partial slot/alpha and colour writers | Effective per-scanline OAM/window/BG/OBJ ownership at split and moving |
| Widescreen/4× | Existing independent 342→1368 4× source-exact controls | Full candidate 7:6 PAR, untouched 256×224 logic, genuine world margins, no 216-high crop |
| HD racer | Existing 4× procedural art **explicitly aesthetically rejected** | Official reference-registered model/pose study and separate human likeness approval |
| Physical Windows display | No physical pad/display evidence | Source-pinned real-device Original/upscaled fallback and two-pad capture |

**Stop rule:** If candidate Windows compilation or existing 1P/2P functional
journeys regress, or a real independent original/native 1P/transition/raster
comparison finds adverse source pixels, retain the branch as experimental
and do not merge. An exact 2P frame or green Win32 test is not a complete
graphics gate or release acceptance. Do not edit the gameplay/Modern/persistence
authority or try to fix a timing mismatch by deleting/painting sprites.

**Cross-lane handoff:** Gameplay (Agent 1) may use independent guest CRC
and phase receipts, not this candidate as a logic-equivalence oracle.
Modern (Agent 3) should preserve the original renderer and settings seam;
there is no new option exposed here. Integration (Agent 6) should hold the
candidate until an independently sourced graphics disposition is posted.

## Executed Windows candidate and independent post-PPU witness follow-up

**Source-head build before post-PPU capture:** [Windows run 38684927172](https://github.com/gamesbyian/UR-Recomp/actions/runs/38684927172) at graphics head `3ccc5ff55c409e2e95effa5b8ed8da61e0c6ddab` completed **successfully**. The real Windows Clang PE32+ build, import guard, batched eleven native player journeys, ROM-free ZIP and extracted CMD launcher all passed. The opt-in consumed-prime script logged applied=1 before compilation; the script was not just parsed in unit tests. The compiled Windows executable SHA256 is `6f85f32c4f9e973f8e4632888b158abffc24df0bdb506a704852062e4d094db6`, paired with ROM-free payload ZIP SHA256 `dcd6c4290d6bbec12192d004f2e8b04ee9077f27e6c57c1a1618c028ef5f80b3`. **This head does not yet carry the following observer** and those hashes must never be applied to a future observer-enabled binary.

**Additional implementation in this PR:** `tools/baldosa_qa08_windows_original_capture.cpp`, `tools/baldosa_qa08_windows_source_capture_patch.py` and `tools/check_qa08_windows_source_raster.py` attach exactly one read-only `end_sim_frame` callback after the actual Original PPU's `draw_ppu_frame` in the *same existing Windows Modern binary*. The callback is entirely opt-in via an isolated `UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR`; the default player launch neither reads/writes any raster file nor changes a presentation pixel. It writes unaltered full 256×224 RGBA source P7 at genuinely presented guest1856,2192,2208,2224, if those callbacks occur. **No absent frame is synthesized, moved, cropped, substituted or counted.** It never handles `draw_frame`, updates PPU/guest/Modern state, or modifies 7:6 PAR and 4× fallback. Only the disposable pinned Uniracers desktop CMake target receives the source observer; this is not an upstream/core ABI change.

The source checker reuses the existing real 2P Windows process route, checks exactly 2,473 guest CRC samples, authentic source dimensions/format/callback logs, checks observed post-GO frame P7 SHA against *independently archived* corrected native P7 hashes, and identifies a legacy-incorrect hash as negative rather than accepting it. Windows itself reports missing/unsampled frames instead of making a claim about host-presented frame number equivalence. In particular, the already accepted source-sized corrected guest2208 digest is `bf8b4218fb72f94338b19da5c1386bd5ce09c0dc0c767093286e80895fa3353c`.

This one-witness source step runs **against the same new Windows executable**, after the already batched authentic Windows player journeys, with no second compilation and a bounded single 2P source route. Result JSON, native P7 files and log are retained as one separate temporary GHA artifact; if the guest2208 visual callback is absent, the workflow fails closed. No PR/CI status can grant release ledger acceptance, independently certify camera/CPU/inputs, a 1P scene, actual host-filtered 4× frames, or owner-approved Remastered artwork.

## Integrated Windows four-frame contract: exact *short-route* identity (October 16)

Draft graphics head `7069f043` passed complete source-merged Windows 13-journey build [run 38850138288](https://github.com/gamesbyian/UR-Recomp/actions/runs/38850138288). Exact checked-out GitHub PR test commit `0aa1f9906d0265e6cc0928e55bbf4f783b30defe` is a synthetic merge of main `60f3e694` and graphics `7069f043`. The **actual** 19,812,864-byte packaged Windows executable SHA256 `be349d955bb3d4044fc81e66b9a86a23ea153b3c6728a945a51937604ec51aec` matches all three independently downloaded artifacts: four-source observer 12025725844, candidate-binding 12025815332, inner ROM-free candidate ZIP SHA256 `2c5914fdbde48fde76795db35cc630828d531f2dd7ee0783180c5148ad9f080f` from artifact 12024937940. Actual source-size full P7 2P guest frames 1856,2192,2208,2224 each match all four separately source-validated corrected digests; no old-wrong digest survives. The 2,473-frame guest CRC transcript SHA256 is `992dfdc270802e8a0ec1be5a0be6ddc36872edca11c8a91d58367a6235e537cf`.

**Route guard: do not conflate short split-screen and long 2P event.** The short `baldosa/tests/routes/race_2p_split.txt` (2,473 guest frames; actual Windows CRLF checkout SHA256 `4e714899f53c3bbe501bbfcacf91dd549989c9beb7c2cf6265b13eb687142ec6`) uses several short post-GO holds, whereas `race_2p.txt` (5,484 guest frames) holds both players' right direction for 800 frames before distinct trick inputs. The pinned original snesref runner inserts idle frames at command boundaries. Therefore even when original and Windows moving split frames happen to share the same number, these are **different controller histories** and cannot be compared as aligned parity witnesses. Direct byte-level comparison of the 4 latest short-route Windows P7s with the *other* independently archived original Snes9x full-event 2P callbacks (source = native−1) produced 0, **160, 81, 162 wrong RGB5 pixels**, respectively. The three nonzero outcomes are **invalid cross-route original/native candidate comparisons**, *not* evidence of renderer regression. Compare only original/native captures from **the same authenticated route**.

The strengthened one-route checker now requires both the literal short Windows CRLF script SHA and the **entire** 2,473-record native CRC transcript SHA in addition to every pixel and every selected callback. Its unit tests reject forged/different script or CRC while preserving all error images as evidence. The legitimate effect is a stronger bounded title-specific regression, **not** acceptance of the long 2P event, first source instruction phase, race finish/return, effective OBJ/window, physical 7:6, widescreen, 4× or owner-vetoed Remastered likeness. #1641 remains draft HOLD pending separate blackout/results and cursor defects.
