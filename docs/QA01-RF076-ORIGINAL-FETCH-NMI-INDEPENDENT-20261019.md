# QA01/07: original fetched-PC/NMI crosswalk, authentic RF076 fourth epoch

**Independent archived-source decision: HOLD, 0/45 USA courses and 0/12 Windows QA gates.** This evidence extends [QA01 RF076 nine native-NMI qualification](QA01-RF076-NATIVE-NINE-NMI-INDEPENDENT-20261019.md) and the [first-event missing-witness matrix](QA01-FIRST-USA-EVENT-MISSING-WITNESS-MATRIX-20261019.md). It does not retroactively join RF054, RF062 or either earlier RF076 source epoch.

## Exactly which archive was observed

Completed disposable original/native [run 39342841750](https://github.com/gamesbyian/UR-Recomp/actions/runs/39342841750), authentic **case artifact 12231020072** (ZIP SHA256 `402d3ee176307af4415fc24d579b00fb7c763996e02dfefe537f0c698b848b55`, 418 members, CRC-valid), and actual **binary artifact 12229419837** (ZIP SHA256 `713cac1696fdeacd4b079f3b53e768b879f5f7a506c77e2b617cf24e3452188d`, 10 members, CRC-valid). Case checkout `654aa6f7de100ff37f9133ae11039e7471a0456c` refers to **Actions merge execution**, not the branch head. Original source log SHA256 `5940ec4b69f6b41fff4ae0af88925efc84d4b322286adb720cf429e0dfdf6dc7`, native `7f0c65060502ece76780978da19421d598037b17a476ccb2723e389eeec21c4c`. The actual native executable SHA256 is `ca58d0d8020f2b7375dce5aa9f9aa00e7109d76cbdeae2f67dffe3fd2799bbfc`, original Snes9x ELF `91580300bf7b165f1d0b202b66787acbc519d8d05aaf20463ebd9bc8081a49e6`. In-archive and binary-archive `SHA256SUMS` match the actual leaf bytes. This Snes9x binary differs from the *previous RF076 epoch*, so never combine instructions across the two experiments.

The independent [`qa01_rf076_original_fetch_archive.py`](../tools/qa01_rf076_original_fetch_archive.py) checks both immutable ZIPs, exact case/binary identity, original/native source logs, 45,063 contiguous original observer records (45,045 selected **actual original fetched opcodes** and nine each `nmi_pending` / `nmi_before`), and 47,853 native records (45,103 selected AOT decoded-opcode markers, 2,705 stack-read markers, and nine complete native NMI brackets). The original observer has no mixed physical prefix; the native source log still has **75 physically interleaved RF044/RF047 suffix rows** (73 reads, 2 compiled-RTI). These do not prove atomic transport or absence of instrumentation effects.

## Native/source-local crosswalk, *not* cross-guest phase alignment

| Shared **host-frame label** | Actual original first selected fetched PC after NMI | Fetched opcode byte | First selected native AOT opcode PC after native handler | Classification |
| --- | --- | --- | --- | --- |
| 1017 | `82D4F0` | `10` | `82D4EE` | Different |
| 1018 | `82D4EE` | `24` | `82D4EE` | Same selected site |
| 1019 | `82D4F0` | `10` | `82D4EE` | Different |
| 1020 | `82D4EE` | `24` | `82D4EE` | Same selected site |
| 1021 | `82D4F0` | `10` | `82D4EE` | Different |
| 1022 | `82D4EE` | `24` | `82D4EE` | Same selected site |
| 1023 | `82D4F0` | `10` | `82D4EE` | Different |
| 1024 | `82D4EE` | `24` | `82D4EE` | Same selected site |
| 1025 | `82D4EE` | `24` | `82D4EE` | Same selected site |

All nine original NMI wake checks report `WaitingForInterrupt=false` and **no original wake-PC increment** at that observation. The recorded original `nmi_pending` and `nmi_before` are source-local actual events, and its reported fetched opcode bytes occur at the selected original PC. Nine native `deadline_unwind` resume SETs and first selected post-handler AOT markers retain `82D4EE`. This yields **four of nine host-label-only selected-PC mismatches**, not four instruction-equivalent interrupt phase divergences. Different emulators can publish a host frame at different intraframe logical clocks; the instrumented original and native observers do not trace all intervening unselected opcodes or writes. The exact first *consumed differing* byte, genuine guest causality, and full CPU/SPC logic-tick parity remain unqualified.

The matching-source raw Zoo mesh remains **78 unmasked 128-KiB original/native WRAM pairs: 51 byte-identical and 27 unequal with 92 physical byte differences**, concentrated 90 on `7E:01ED..01F1` and two at `7E:0063`; original/native retained SRAM **97/97 equal**, plus next-Bowl sampled +267 progression. These are checkpoint facts, not proof of unsampled frames, published Windows Records or durable on-disk cold-process recovery.

## Fail-closed next decision and source lifetime

The independently verified real case is now consumed by the **existing ROM-free `qa01-authentic-frame-qualification.yml` workflow**, which requires original ELF/source ZIP digests, real contiguous original and native event sequences, the nine-frame crosswalk, physical log interleavings, and the already existing independent raw Zoo memory consumer. The workflow retains both original ZIPs for 90 days **only after** strict admission succeeds. Original provider artifacts expire 2026-10-26; any future duplicate must preserve separately the exact *inner original* ZIP digests and not silently treat a new upload wrapper digest as the source. Full hosted CI success is a source provenance success only.

**Independently authenticated source preservation:** The [source-only QA run 39348841560](https://github.com/gamesbyian/UR-Recomp/actions/runs/39348841560) passed its original/native ZIP re-open, 78 ROM-free tests, exact 78 WRAM memory-pair consumer and HOLD negative. It retained genuine inner research case and ELF ZIP bytes in [artifact 12231814011](https://github.com/gamesbyian/UR-Recomp/actions/runs/39348841560/artifacts/12231814011), 90-day outer wrapper SHA256 `2a334b8ed7a3636c5fa715cf6f513829c52ff9be4cd0e2e94516f8a9cd3543a1`, expiring **2027-01-18**. Independently reopened the wrapper: exactly four CRC-clean members; its nested `genuine-case.zip` and `genuine-binaries.zip` hash to the **original provider artifact SHA256s** `402d3ee...` and `713cac16...`. The existing archive-only workflow verifies wrapper **and** original nested digests before parsing, compares original-provider bytes while present, and only uses exact nested originals if those objects expire after **2026-10-26**. The ordinary equality branch has been exercised; the actual expired-provider fallback remains untested until expiry. This is evidence continuity, not parity or event admission.

**Next actual missing witness:** an instruction/interrupt-phase comparator justified by recorded original/native source-local semantics and genuine first operand reads/writes at those comparable stages. Agent 1 owns any new producer instrumentation. QA owns independent negative-preserving admission. No timing shift, stack mask, solver-made filler or inferred first-consumed byte. Release ledger stays **0/45 USA, 0/12 Windows**.
