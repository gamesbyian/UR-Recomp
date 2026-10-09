# SNESRecomp: exact Baldosa framework delta audit

Compared `gamesbyian/UR-Recomp` pinned `cd5875cbdaf19f5e324272b1f8051d671fce9215` against Ema's `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`, pinned by `baldosa/uniracers-recomp@10b864b9`. [Complete 86-commit/121-file ancestry index](../analysis/data/baldosa-framework-delta-20261009.json), with author, date, subject, changed path, category and churn per file.

**Scope:** `ahead_by=86`, `behind_by=0`. These are commits **since our pinned revision**, not claims of 86 wholly independent new Ema modifications: the ancestry includes upstream merges and broader SNESRecomp changes. This is a large active framework delta, and cherry-picking the fork head wholesale would conflate CPU/PPU fixes, host ownership, netplay and analyzer behavior. Existing UR-Recomp host modifications and offline source island remain authoritative until compatibility is shown.

## Five directly useful patch families

| Priority | Pinned upstream commits | Source modifications | Acceptance experiment |
|---|---|---|---|
| P0 QA-08 | `075fbe4c` | Optional `g_hdma_oamdata_at_10c` game-enabled pin before active HDMA writes to `$2104` in `runner/src/snes/dma.c`; Ema's `src/main.c` sets the flag | Original vs pinned native OAM high-table byte `0x218` at 2P split boundary, lines 0/112; P1/P2 rider visible, no false HD frames, unchanged 1P/VS |
| P1 QA-01/07 | `96b7e9f5` | Clock-driven `$4212` HVBJOY reads in beam-frame driver | Frame-relative title/attract/countdown against original Snes9x; no masked-away race-clock regressions |
| P1 native execution | `5882addc`, `ce196a45` | Opt-in compiled native continuation/interrupt handoff, recorded fallback landings, M/X-specific `[[variant]]` roots | Same ROM/inputs plus exact guest state at boot, menu, 1P/2P, resume, timeout; interpreter cycles and turnaround |
| P1 native temporal parity | `b7b4318f` | `paced_bus` generated guest-memory accesses and updated bus/cycle charging | Frame-aligned or event-relative original/native countdown, collision, lap, input and audio parity; deterministic replay unaffected |
| P2 coverage/ports | `43378981`, `ff993630`, `48748da8`, `eaaa7d9a`, `df5713dc`, `608a6796` | Pad-2 reference scripting, historical profile seeds, web/host input filter, Emscripten, frame pacing | Only if a named existing QA failure/Windows requirement justifies the change; otherwise defer |

The exact game-specific OAM fix has been preserved as an **unapplied** patch in [`analysis/patches/baldosa-oam-address-pin.patch`](../analysis/patches/baldosa-oam-address-pin.patch). Its source is `baldosa/snesrecomp@075fbe4c`; its game-side opt-in is in the already imported `src/main.c`. Avoid blindly patching stock framework headers or editing the submodule on main. A correct port requires both the DMA hook and title-level enablement, with a real visual and OAM regression proving it.

## Dependencies and compatibility traps

1. The `paced_bus` change modifies recompiler CFG parser, generated code and bridge timing. It cannot be evaluated as one isolated C function; reset the generator and record code/output hashes. `HVBJOY` also depends on beam-clock ownership, not just a static 4212 register read.
2. Compiled native handoff modifies interpreted-to-compiled boundaries and return semantics. The original project had known stack under-pop issues in an earlier handoff; Ema's current complete route acceptance is evidence for **their exact stack**, not automatic safety in ours.
3. Their ARM64/web/launcher configuration uses SDL and host code newer than our Windows x64 wrapper. Replacing the framework can silently invalidate Modern input ownership, audio, pause, deterministic replay, widening, profile-root behavior and packaging.
4. Their HLE `MVN` trampoline (`src/gen_stubs.c`, already preserved) should be examined alongside `recomp/bank00.cfg` `hle_func 0199 HleRamBlockMove` and the exact original four WRAM bytes; this title-specific seam may reduce interpreter pressure but requires 8/16-bit index and cycle semantics parity. No standalone guest experiment has yet established it in UR-Recomp.
5. The new browser lockstep input filter bypasses run-ahead and uses a 64-slot, three-frame delay queue. It is valuable independent source but remains a distinct online product, not an urgent Windows acceptance requirement.

**Work boundary:** reserve a fresh native/runtime branch for any actual framework port. QA-08 owns the OAM discriminator, QA-01/07 own original event outcomes, and frontend/persistence lanes must not be disturbed without direct required witness. This document is an engineering selection aid, **not a change to production framework state or an accepted event pass**.
