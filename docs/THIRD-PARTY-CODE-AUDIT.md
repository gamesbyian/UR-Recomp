# Third-party code audit and adaptation

Imported code is evidence and raw material. Project-owned tooling should be the
best implementation for UR-Recomp's current needs, not a compatibility museum.

## Operating rule

Keep source provenance intact under `references/imported/` when historical
identity matters. Do not preserve defects, emulator-specific APIs, awkward data
models or obsolete constraints in project-owned tools merely because an imported
artifact had them.

Before an imported executable/script/algorithm becomes infrastructure:

1. inspect it for ordinary software defects and silent language/runtime traps;
2. identify version-, emulator- and platform-specific assumptions;
3. verify game-state labels and semantics independently against the canonical ROM;
4. compare later implementations where available, especially where old code used
   a game-specific workaround;
5. extract the useful concept into `tools/`, tests or the native implementation;
6. add a regression test for every imported assumption that becomes an invariant.

## Current audit results

### Dessyreqt 2014 Tabletop bot

Source: `references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`.

Status: useful but not safe to consume as an API.

Confirmed source defects / hazards:

- the player-1 `bytes` table repeats eight named keys; Lua silently keeps the
  later declaration;
- consequently several visually plausible earlier addresses are dead labels in
  the actual running bot;
- `MakeWordSigned()` uses `if word > 32768`, so raw `0x8000` is interpreted
  as +32768 instead of -32768. Correct two's-complement conversion uses
  `>= 0x8000`;
- persistent player-1 pitch is now independently established at `7E:04C7`.
  The bot's effective `7E:0F49` value is current-player scratch state and must
  not be propagated as the canonical persistent pitch slot.

Project response:

- `tools/uniracers_state.py` now owns normalized state fields and signed-word
  conversion;
- `tools/summarize_player_checkpoints.py` and the native Lua replay path consume
  that model rather than independently copying addresses;
- historical aliases remain explicit for old-report compatibility;
- `tools/audit_imported_lua.py` detects duplicate named table keys;
- unit tests lock the `0x8000 -> -32768` boundary and known duplicate-key hazard.

Future adaptation should port policy concepts into state/policy/input layers.
Do not edit the preserved Lua snapshot into becoming the modern implementation.

### Historical Snes9x 1.43

Source: `references/imported/emulators/snes9x-1.43/`.

Status: archaeology/regression inventory, not an implementation template.

The old DMA/HDMA path contains a literal `SNESGameFixes.Uniracers` special
case that forces OAM state. That is strong evidence for the historical
compatibility seam but weak evidence for the correct hardware model.

Project response:

- retain the special case as evidence of the failure shape;
- reproduce the behavior under current runtimes;
- prefer a correct general active-display OAM model over a game-specific branch;
- use the old workaround as a regression discriminator, not as code to port.

### Modern Snes9x snapshot

Source: `references/imported/emulators/snes9x/`.

Status: independent implementation evidence.

This snapshot has substantially different DMA/HDMA machinery and no equivalent
reason to treat old 1.43 internals as authoritative. Use it comparatively,
especially when a historical game-specific fix disappeared after more accurate
general emulation.

### jgenesis sprite implementation

Source: `references/imported/emulators/jgenesis/sprites.rs`.

Status: high-value modern implementation evidence, still to be validated locally.

The code handles active-display/mid-scanline OAM progression generically and
calls out Uniracers as a dependent game rather than branching on the game name.
That is architecturally closer to the model UR-Recomp wants. Its exact timing
and target behavior remain evidence to test, not assumptions to clone blindly.

### MAME SNES PPU snapshot

Source: `references/imported/emulators/mame/snes_ppu.cpp`.

Status: independent PPU implementation reference.

Use as another vote when reducing an observed hardware seam. Do not use source
agreement between emulators as a substitute for a deterministic ROM/runtime test.

### RNC ProPack 2.14

Source: `references/imported/tools/rnc_propack-2.14/`.

Status: authoritative historical format/algorithm evidence, awkward production tool.

The period SNES Method-1 source is extremely useful for decoder signature and
control-flow archaeology. The DOS binaries are not required as the project's
normal decoder.

Project response:

- use project-owned `tools/rnc_method1.py` for analysis;
- validate both packed and unpacked CRCs;
- validate the decoder across all 45 streams in every preserved build;
- bound bitstream reads to the declared packed payload. The decoder previously
  returned synthetic zero bytes after EOF, which was unnecessarily permissive
  even though known-good CRC-checked corpus calls generally hid the problem.

### Historical SMV movies

Source: `references/imported/tas-bots/*.smv`.

Status: data corpus, not trusted semantics.

Use project-owned `tools/extract_smv_input.py` to translate input and embedded
SRAM into neutral deterministic fixtures. Interpret state only after replay
against the canonical ROM and current runtime/reference harnesses.

Audit note: the extractor had a variable-shadowing defect where the original
movie byte buffer name was reused for each integer controller sample; metadata
then called `len()` on the integer. The regression test exposed this and the
buffer/sample variables are now distinct. The associated WRAM trace summarizer
also now rejects non-monotonic frame records instead of silently reconstructing
state across backwards time jumps. The historical replay workflow formerly used
raw `cmp` on generated versus frozen controller files, making harmless comment
header differences look like input divergence; `tools/compare_input_runs.py` now
compares parsed controller intervals instead.

## Promotion checklist

When code moves from "interesting import" to "project dependency", record:

- exact imported source/revision;
- observed bug/assumption review;
- which behavior was independently reproduced;
- normalized project-owned interface;
- regression coverage;
- remaining uncertainty;
- whether the original artifact is still needed after the adaptation exists.

The default answer to "should this old tool become our tool?" is to extract its
knowledge and keep the smaller, testable project-owned descendant.
