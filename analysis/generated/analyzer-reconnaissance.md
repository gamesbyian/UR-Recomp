# Analyzer reconnaissance — 2026-09-29

Source: GitHub Actions run `36575810121`, head `790f0c98f027b67c0af84ad18743640fa4ea4224`, using the pinned SNESRecomp revision `cd5875cbdaf19f5e324272b1f8051d671fce9215` and canonical USA ROM.

The run generated SNESRecomp's manifest-v3 whole-program analysis successfully and summarized it with the project-owned `tools/summarize_analyzer_recon.py`.

## Static coverage

- analysis roots: **9**
- exact variants: **54**
- AOT-eligible variants: **52**
- LLE-only variants: **2**
- AOT-capable fraction by exact variant: **52/54 = 96.2963%**
- decoded instruction instances across manifest nodes: **1,808**
- transfer edges: **121**
  - direct calls: **110**
  - direct tail calls: **2**
  - unresolved indirect edges: **9**
- exit-mode proofs:
  - exact: **41**
  - multi-mode: **1**

The 9 unresolved-indirect edges are variant-level edges, not nine independent guest instructions. They collapse to **three guest sites**:

- `00:8584` — four M/X variants, `JMP` indirect through operand `$0073`
- `00:8599` — four M/X variants, `JMP` indirect through operand `$0053`
- `80:C3C8` — one M/X variant, `JMP` indirect through operand `$005D`

All nine are classified `lle_dynamic`, so the analyzer keeps them explicit rather than inventing static targets.

## LLE-only variants

Two exact variants remain LLE-only:

1. `80:91DC M1X0` — 119 decoded instructions
   - `truncated_call_continuation`
   - `unproven_call_at_80886D_to_838AF7_m1x0`
   - `unproven_callee_exit`
2. `80:94EB M1X0` — 4 decoded instructions
   - `truncated_call_continuation`
   - `unproven_call_at_8094F4_to_80C3AB_m1x0`
   - `unproven_callee_exit`

These are bounded analyzer-proof gaps with an explicit interpreter path, not unknown code-generation failures.

## Blocker classification

- **Cartridge/configuration:** clear. The canonical ROM probes as standard 2 MiB LoROM, USA region, no coprocessor, 8 KiB SRAM, valid checksum, reset vector `$8858`.
- **Analyzer limitation:** present but bounded. Two exact variants remain LLE-only and three guest indirect-dispatch sites remain dynamically resolved.
- **Runtime/hardware:** no Phase-1 execution blocker identified by this reconnaissance. Subsequent deterministic native bring-up has already reached menus and stock race execution, so the static gaps above are demonstrably survivable under the current interpreter fallback.
- **Unknown:** none currently required to explain analyzer generation or initial execution.

This report does **not** claim that all dynamically executed CPU instructions are AOT. The percentages above describe compile-time exact manifest variants only. Runtime interpreter usage remains a separate measurement question and should be captured on representative deterministic routes if/when reducing fallback cost becomes useful.
