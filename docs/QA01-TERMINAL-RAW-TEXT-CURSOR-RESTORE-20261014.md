# QA-01: original result-phase raw `7E:009F` and the direct-page restore boundary

**2026-10-14, source-only original research.** This page is a bounded source contract for QA-01. It neither changes the release ledger nor modifies the original 65816/native gameplay, controller movie, Modern storage, or presentation.

## Why the terminal timestamp is not automatically a scene-transition instruction

Several original/native terminal event observers, including the pending race-relative research PR #1537 (RF-012), identify a `0x84` result-phase signature and subsequent `0x16` restoration by sampling the **raw low byte at WRAM `7E:009F`**. The independent imported RAM catalogue at `reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt` calls the **two-byte** field `7E:009F..00A0` **`wTextPos`**, the DrawText tilemap cursor. This symbol is historical and context-dependent, but makes a single-byte scene/state interpretation unsafe.

The independent Nitrodon bank-80 archive has `80:A18E LDA #$84; 80:A190 STA $9F`. It also has `80:C49E STA $9F` and `80:C432`/`80:C434 INC $9F` in text-layout paths. Thus **0x84 at this address has a real original source text-initialization producer**, and additional writers can change it. This does not prove which producer executed in any of the RF-012 terminal runs; the observed field remains an accurate raw-value *signature* but not a standalone race-result/menu-decision oracle.

## Exact archived SRAM-to-direct-page copy

The Baldosa imported original symbol `83987D Sram_RestoreDirectPage` matches Nitrodon bank 83:

| Original 65816 PC | Archived instruction | Purpose |
| --- | --- | --- |
| `83:987D–987E` | `PHP; REP #$20` | Save status, use 16-bit accumulator |
| `83:9880–9883` | `LDX #$0000; LDY #$00CE` | Initialize source/destination index and inclusive counter |
| `83:9886` | `LDA $770E6B,X` | Read SRAM copy using long addressing |
| `83:988A` | `STA $0000,X` | Write 16-bit destination word to current data bank |
| `83:988D–9890` | `INX; INX; DEY; BPL $9886` | Loop, advancing two bytes, **207** iterations |
| `83:9892–9893` | `PLP; RTL` | Restore status and return |

If the runtime data bank is WRAM, the inclusive `0xCE` counter copies **207 × 2 = 414 bytes**, covering `7E:0000..019D`. The archived absolute-indexed `STA` operand itself does not attest the runtime data-bank register; observing the actual `83:988A` executed source PC with DBR and effective destination is the necessary check.

Critically, `7E:009F` is an **odd** address: the low byte of `wTextPos` is the **upper byte** of the 80th restore `STA` (destination word starts at `009E`), while `7E:00A0` is the **lower byte** of the 81st restore `STA` (destination starts at `00A0`). A CPU/host snapshot at an arbitrary point in the restore cannot be treated as an atomic two-byte `wTextPos` update. It is also unsafe to attribute the observed terminal byte to the copy merely because the source contains this routine: the actual live PC, caller, DBR and preceding writer remain unobserved in RF-012.

The dependency-free `tools/qa01_result_field_restore_contract.py --out <report>.json` reproduces this source mapping from the **preserved original archived instruction bytes and RAM symbol**, with adversarial unit tests that reject missing, duplicated or altered opcodes, changed accumulator width, a changed symbol and out-of-bounds restore byte addresses. The report explicitly encodes **zero** strict event acceptance and **unverified** original/native clock alignment.


## One static direct caller, with a save/video/restore chain

A scan of the retained Nitrodon bank-80 through bank-83 opcode operands finds **one direct** `22 7D 98 83` JSL call to the `83:987D` restore routine, at **`80:9A3F`** in the archived bank-80 `Race_Start` region. This is a static textual direct-target census, not an exhaustive dynamic call graph or proof of a particular terminal-run call.

Its surrounding archived code identifies an immediately relevant **save → reset → restore** sequence:

- `80:9A27`: opcode `22 94 98 83`, calls the **SRAM snapshot routine at `83:9894`** that writes `$770E6B,X` from direct page.
- `80:9A37`: `JSR $A08B`, the original `Menu_InitVideo` initializer already identified by the Zoo CPU witness.
- `80:9A3A`: `JSR $D1FD`, another intervening source call whose effects must be qualified.
- `80:9A3F`: opcode `22 7D 98 83`, the long call to the `83:987D` DP restore loop.
- `80:9A43`: `JSR $98A4`, the post-restore continuation.

The archive sometimes prints `JSR $83987D` for 65816 opcode `22`; the four-byte opcode encodes a **long** call, so the instruction bytes and actual CPU call/return scope govern the provenance. `tools/qa01_result_field_restore_contract.py` and its unit tests now pin this full static sequence. Before asserting an original/native "restore one frame late" root cause, an executed trace should identify whether the matching native guest actually reaches the same **caller, save, video-init, intermediary setup, restore entry and return** boundaries with equivalent state. The original/raw `0x84→0x16` text-position signatures alone do not tell where in this sequence a divergence first begins.

## RF-012 reference-core cross-check and next causal experiment

The pending original/native race-relative PR #1537 uses calibrated original-entry lag 2 for its current native candidate, not unchanged absolute-frame movie bytes; its local terminal outputs are useful provisional behavior evidence, not source-verified strict admission.

The nine Snes9x cases in `analysis/data/frontier-original-native-race-relative-20261014.json` on the PR head all have **34 sampled host frames at raw `0x84`**, while native has **35 frames in eight cases and 36 in one**. The first raw-value change aligns at the same native-normalized host frame in 8/9, one native frame earlier in 1/9. The restoring raw-value change is one native frame later in 7/9, two later in 1/9, and simultaneous in 1/9. A second original core (Beetle-bsnes) for seed `50036056` reports onset 5199 versus native 5198, both restored by native-indexed 5233; the Snes9x original begins at 5198 and restores at 5232. Both source cores nevertheless measure 34 source frames of the raw phase. **Cross-emulator event timing and literal source/native frame clocks are not interchangeable.**

The minimum discriminating original/native experiment is a **short, source-qualified terminal-edge execution trace**, not more seed volume:

1. Preserve a single authentic, independently pinned full guest with identical original/native input provenance, both measured race-entry phases, both-original-core controls, and explicitly distinct host/ICPU/beam clocks.
2. Capture the **actual writers of `7E:009F/00A0`**, their CPU PCs and effective banks, plus distinct reliable race-result/finish, track, lap and menu-controller fields. Associate `80:A190` and the bank-80 layout writers only when they execute.
3. Capture the caller and return around **`83:987D`** with the live DBR, source index, and the 80th/81st `STA` operations. Cross-check the native matching guest path and NMI/save/restore scheduler phase, not only the postframe value.
4. Determine whether original/native first differ in upstream event scheduling, input receipt, renderer/text cursor, actual restore entry or the copy itself. Only a proven difference with equivalent preconditions justifies a gameplay patch. Do not shift the historical movie arbitrarily or reinterpret a partial result as a strict complete event.

**Strict USA complete-event acceptance stays 0/45.** Independent release QA retains sole release-acceptance authority.
