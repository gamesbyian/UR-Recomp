# QA08 + Modern: independently replayed real Windows combined candidate
18 October 2026 | **source-only integration evidence, no release admission**

**Outcome:** The clean HDMA first-line and V0-before-HDMA graphics correction
[#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780)
was composed on disposable source from Modern native SRAM/crash recovery
[#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713)
without touching a single Modern persistence implementation line.
The original 1330-line Modern Windows workflow was preserved verbatim
and in order, with only fourteen graphics-trigger/unit/staging lines.
This was draft diagnostic [#1827](https://github.com/gamesbyian/UR-Recomp/pull/1827),
**not** a silent product merge.

**Exact source:** CI source/merge revision
`5c5c992ecdc156f638c13a0d6d6c20a3331c52d6`, verified in the
GitHub commit graph with **first parent**
Modern `b9165d23437316dbfce0701f9ce5a237ad03bed0`,
**second parent** graphics integration
`93fc81f9b73002df23b18d8b98f98d53b1e41eed`.
This branch in turn contains only the scoped PPU patch from clean graphics
`4cfede2f04d9ad48c6e6cd5e74fc31922a5a6280`.
It excludes experimental premath #1807, read-only original
source observers and unapproved art #1826.

**Actual Windows run:** [39108666637](https://github.com/gamesbyian/UR-Recomp/actions/runs/39108666637),
SUCCESS across native Windows PE/journeys, repository unit suite and hygiene.
Real PE32+ AMD64 20,332,544 bytes SHA-256
`1786c474399b245305ba6ab22ff816653ad762ea36d4ac6a4667ec6a74e7ef53`;
ROM-free 6,057,064-byte portable ZIP SHA-256
`fdd53e041772459e2df3b78275a959d81ca379c1cec48ffc41fa5c2991a122eb`.
GitHub artifact IDs: package **12129726985**, independently bound receipt
**12130090206**. Outer archive SHA values
`5e30ecef730d90b14390edba0cb0ff3b17b7d0ea34fadbbe52978dd00268f98f`
and
`e3eb5b38118a236deb1fd33c90300e2d945b911d511f821b82d66f22a25c1384`.
The real archives were separately downloaded and inspected byte for byte:
the binding JSON, embedded package manifest, original launcher/readme hashes,
actual Windows binary, PE32+ AMD64 header and all four archive members
agree with the exact original SHA-bound product receipt. No ROM or named
profile is bundled.

The ordinary Windows source-qualified journeys include original/native
2473-frame 2P guest CRC, native 1P/2P Modern profile startup, controls,
records, original SRAM first/second process and cold boots, typed/raw
save and manual recovery/rollback options. The actual Windows console
Q/R/T/S path, OS sharing-denial test, source-typed recovery and malformed
intent tests also succeeded. These are **automated real Windows tests,
not personally operated physical UI, pulled power, full-volume
fault injection, clean-machine owner acceptance or hardware 4K**.

**Strict bounds:** The previous archived clean PPU image census
[#1822](https://github.com/gamesbyian/UR-Recomp/pull/1822)
still leaves 890,205 wrong original/native RGB5 pixels in 263
sampled 256×224 images. This newly combined product PE was
**not** separately full-263 original-source captured and must not
inherit that PE's image/CRC receipts by source-name coincidence.
Forced unblank at guest4016, original CGRAM phase and medal
effective pixel ownership remain unresolved. Guest original
CPU/APU 45-event completion remains unaccepted. Original 342×224
world, 7:6 PAR, 512/513 fit, full 3840×2160 and nearest-density
Original fallback retain their independent prior evidence; this
build has not newly established physical UHD acceptance.
Owner's veto of existing procedural 4× racer art is unchanged.

**Reproduce the independent binary identity test:** download both
unexpired workflow artifacts, then invoke the stdlib-only verifier:

```sh
python tools/qa08_verify_modern_graphics_combined_candidate.py \
  --binding-archive /private/baldosa-win32-candidate-binding.zip \
  --package-archive /private/baldosa-modern-windows-x64-romless-candidate.zip \
  --out /private/qa08-verified-combined.json
```

The verifier requires the exact outer ZIPs, immutable binding JSON,
inner ZIP hash and sidecar, source/ROM identities, binary PE header,
manifest membership, file sizes and SHA-256s, and explicit no-release
claims; it neither runs a game nor edits product state. The separate
one-shot experiment PR should remain unmerged, while Modern and
graphics production owners decide their separate merges and
independent QA eventually qualifies a final cross-lane candidate.
No changes to `docs/RELEASE-QUALITY-LEDGER.json`.
