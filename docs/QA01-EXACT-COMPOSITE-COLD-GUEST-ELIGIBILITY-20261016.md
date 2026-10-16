# QA-01: qualify exact composite Zoo source replay for the existing cold-guest record test

**2026-10-16, source-verifier correction only. No new original/native run, no full-event admission; USA remains 0/45.** Owner: gameplay QA-01/07 and CPU/APU research, **not** Modern persistence or independent Windows release QA.

## Concrete blocked experiment

The already executed exact research guest [run 38884542449](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449), permanent [case receipt](../analysis/data/qa01-composite-exact-elf-zoo-handoff-20261016.json), and [source review](QA01-COMPOSITE-EXACT-ELF-ZOO-HANDOFF-20261016.md) include a complete source-authentic result +5163, Bowl continuation +267, 11/11 sampled in-memory SRAM pairs, and a 78-sample unmasked WRAM mesh. The authentic **expanded** replay script is SHA-256 `1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52`; the shorter three-event script SHA `04ad1c2d…` is *not* interchangeable. Original ROM, 2014 movie, and movie input segment policy were unchanged.

The separate existing `tools/qa01_cold_result_record.py` previously accepted only the short script or the ordinary +280 next-Bowl script `414cb0b1…`. An independent *cold guest* check against the exact composite receipt consequently failed before running any guest, despite the source movie and existing SRAM images being authentic. That is a **source-validation eligibility defect**, not evidence that the game itself failed a cold restart.

## Small reversible correction

The verifier now recognizes **only** the independently reported exact expanded controller-script SHA, additionally requiring:
- The existing exact source original USA ROM/movie and extended movie-window digest `7b03f40e…`, unchanged complete Zoo +5163 frame clocks, source vs fresh Bowl +267, equal sampled source-earned SRAM and zero false release credit.
- The distinct exact-reference-script SHA matching the expanded digest, all **78** source-relative mesh ticks in canonical order (using the existing producer's `sample_frames`), their separately measured original and native host clocks, all 128 KiB compared per pair, **zero excluded/masked bytes**, and explicitly no claimed every-frame equality.
- The bounded **13 consecutive** original/native SPC direct-page frames +5034..+5046, zero masked WRAM bytes and no event-credit claim.
- The original/native **captured** result+72 SRAM image SHA and real earned 2510-centisecond best lap, original table checksum and reloaded ranked records under genuinely restarted guest processes, as already required by the cold verifier.

Negative deterministic tests reject a substituted source-window digest, missing mesh sample, altered host frame, excluded byte, missing SPC frame, regression to the +265 Bowl handoff, or a synthetic event pass. The old, independently qualified short and ordinary next-Bowl scripts remain accepted with their preexisting source contracts. This fix creates no second runner, new copy of a ROM, or acceptance override.

## Exact existing sources and unproven acceptance gates

- Research checkout `d9134a6e5da87145f1ad38e02382cce067fe6ec3` (**non-main**), exact native ELF SHA-256 `9a3bd17afd8377a4c83e76c05cd57dfdae2488e498aa4bea1b90a2baa018bb48`.
- Original Snes9x core SHA-256 `ec4ce30d80e0b2c22b5d700aec01d601bd85db452ccb8e2b32fa75e9fe63554a`; original `snesref` SHA-256 `5fb3cca1f51d13762e7b82e736133cdab702aafbca07b9164d568139a3bcc18a`.
- Original USA retail ROM `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; 2014 SMV `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442`; original SRAM seed `a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828`.
- Fresh original/native Zoo entry host **1017/1017**, result +5163/+5163, next Bowl at Zoo result +267/+267, next Bowl host **6447/6447**. Bowl Stunt score **764** and Switcher MIKE **1:08.81** remain only separate result candidates, with Switcher's original movie +4703 vs fresh original/native +4704.
- Residual Zoo +5040/+5045 sound-data pointer (original/native hex `73/74`, `B3/B4`); 13/13 +5034..5046 sound-transfer counters equal. Residual next-Bowl +266/+280 four stack bytes each at `7E:01ED–01F0`. **51/78** Zoo WRAM image pairs exact and **27/78** different, 92 unmasked differing byte occurrences.
- Genuine original/native SPC `$2140..43` start handshake and stack read consumers at the divergent sample instants, all intervening instruction/frame clocks, actual Windows RF-017 shipping source identity ([#1686](https://github.com/gamesbyian/UR-Recomp/issues/1686)), host autosave publication/OS cold durability, and independent player journey QA remain unproven. The separate local SPC trace reported in [RF-028](RF028-INTERRUPT-ENTRY-COST-20261016.md) is a **lead**, not independent hosted original/native instruction-PC admission proof.

**Next evidence-producing step:** independently rerun the **existing** `qa01_cold_result_record.py` against the SHA-verified source-composite producer archive's unmodified postresult +72 images and exact original/native ELF/core, in clean separate guest processes. If the artifact lacks a complete source `replay/ref` and `replay/native` tree, reproduce exactly one Zoo-only combined binary/source observer and perform the existing cold reload in that same case; fail rather than replace it with manually invented SRAM. Do not use a different script SHA to pass a guard. Next, only if this bounded cold-guest check passes, obtain the original/native executed `$2140` and SPC `$F4` handshake phase and stack read/write consumers at +266/+280. Source-owner [#1689](https://github.com/gamesbyian/UR-Recomp/issues/1689) covers CPU/APU; independent product QA covers cold disk and ledger.

**Admission: 0/45.** This improves the ability to *run* a missing verification; it does not claim that verification already ran or eliminate an actual gameplay discrepancy.
