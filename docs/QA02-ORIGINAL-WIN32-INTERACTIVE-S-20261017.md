# Independent actual Windows packaged S-choice: three-profile byte isolation, 2026-10-17

**Bounded hosted Win32 S acceptance only, no QA-02/03 release gate.** A human never typed the choice, no real physical gamepads/audio/UHD were witnessed, no actual disk-full/partial write or electrical interruption occurred, and this tested PR-merge Windows ZIP is **not** the older nominated owner ZIP nor a final integrated Modern+graphics merged-main candidate.

## Exact current Windows source and artifacts

- Modern product draft [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713), exact head `c42f1f4ab44aeab44e1ab914a0e353194b7ea356`; real green native [Windows run 39068318622](https://github.com/gamesbyian/UR-Recomp/actions/runs/39068318622). Source actually compiled/tested is PR-merge `503464180dad14bb0275e9fea03f1902c1b5c861`, parents then-main `b80ad58ee98ddbeed5fb530d1e4d9114e44a9450` and that exact Modern head. Later `main` commits must not be silently substituted.
- Original GitHub Actions S evidence wrapper artifact **12114188428**, externally verified SHA256 `38e096e4a377a4f1ec564cae231fdb8d43b494434d8ede168f552775e1085aef`: precisely **36 ZIP entries**, CRC clean, bounded/unique/safe; **29 original byte streams** verified individually against source SHA256/length receipts. No copyrighted ROM or original personal player data.
- Original portable candidate wrapper artifact **12114487315**, SHA256 `f1833f9b3b45662df75faff69cd545a7fdae383dca1669ab566c3fa4d590142d`: complete **four-file ROM-free ZIP** SHA256 `33eb094ef5a9c2c959f79b03823e434f8f036ff05bf00fa3cb98bd96fd6bc596`, actual **20,327,424-byte PE32+ AMD64** SHA256 `2dfef82712ab6eae160d5b2962bcf828d604c03ac0630e287771b6a36388673b`, original packaged CMD SHA256 `b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3`; all manifest immutable files individually hashed and ROM/user-profile absence checked. Separate original binding artifact **12114019652**, SHA256 `d738472a3ed41d26c4c128392c8a230c18772ebb125fceac572fb033bb8e95b5`, matched exact source revision/PE/ZIP/CMD.
- Source console logged an actual packaged no-argument `S` key and the exact literal registered healthy profile ID `native-ci-second` via **two separate real Win32 console injectors** (`interactive-S.key.log` and `interactive-S.profile.log`, each `exit=0`). Original startup refused damaged A once, published the healthy next-boot selector once and booted genuine B to first frame. Two separate fresh original Windows CMD/game processes again loaded B to first frame without prompting for recovery.

## Independently recomputed source bytes

- Original named A (`native-ci-rider`) full 8-KiB raw SHA256 **`fa566cc413f0e5bca8cd4014a05ac1ae76e603567eb74c5745e259547a710a08`**; its original exact typed `stock_sram` decoded to a valid full 8 KiB, with **exactly one source-created mismatch** at offset `0x0711` (XOR `0x35`). Damaged raw and its committed typed file did not change on S or either cold boot.
- Distinct healthy named B (`native-ci-second`) raw SHA256 **`c7db68306d7c44253263b1957cfae71f89888e813f140c0c91f32a802063fef9`**, equal to typed stock SRAM, remained byte-identical throughout repair and both cold boots.
- Unrelated C (`native-ci-third`) raw SHA256 **`0ceadd6ffcde64e977826e94e5016e528cf76dd32841dbc9e5b43e350353fea3`**, equal to the independently retained *original* typed C snapshot from **before the fixture intentionally removed C's on-disk typed file**. Source product verifies C remains missing; the archived original byte set directly verifies unchanged C raw and preserved pre-deletion typed receipt. Absence of the live on-disk typed C on each later stage is **producer-asserted**, not independently reconstructible from a 29-byte-stream export without a separate filesystem inventory.
- Original canonical catalog still registered A, B and C in that order, including broken unrelated C, but **did not change a byte** through S and both cold boots. Original selector changed from A SHA256 `eb0d0bd6c37dfa57766faff9e70f57d1730cabca36426d2863553256bbe87956` to B SHA256 `9db71c0e82a02b0f2514fb4711d3476a2438099be2682cdba622cb34b4a4cc4b`, where the *sole actual data change* was replacing `profile=native-ci-rider\n` with `profile=native-ci-second\n`. Both later actual cold snapshots matched the complete after-S seven-file canonical snapshot **byte-for-byte**. No raw/typed/catalog promotion, no fabricated Records or archive authority observed in retained canonical byte snapshots.

## Reuse and acceptance boundary

```sh
python tools/check_qa02_win32_interactive_s_original.py \
  --zip original-artifact-12114188428.zip \
  --sha256 38e096e4a377a4f1ec564cae231fdb8d43b494434d8ede168f552775e1085aef \
  --cmd-sha256 b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3
```

Independent QA [PR #1790](https://github.com/gamesbyian/UR-Recomp/pull/1790) maintains this read-only original GitHub ZIP checker, positive/negative ROM-free tests, exact-source profile and byte equality checks, and **both** injector receipts. It does not alter the Modern player data implementation or execute the game itself. Hosted R/T/Q have separately qualified source-bound artifacts through merged [#1783](https://github.com/gamesbyian/UR-Recomp/pull/1783) and [#1786](https://github.com/gamesbyian/UR-Recomp/pull/1786). Real user-operated menu/actual full or partial NTFS write failures/process interruption, joined integrated graphics candidate and physical pads/audio/UHD are not covered.

**Do not update the release ledger:** the immutable original owner source `11501a15dea38fa912335cfc63103ce3a7208001` / ZIP `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` remains a distinct older build. Release **0/12**, complete USA events **0/45**.
