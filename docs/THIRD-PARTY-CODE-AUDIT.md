# Third-party code audit and adaptation

Imported code is evidence and raw material. Project-owned tooling should be the
best implementation for UR-Recomp's current needs, not a compatibility museum.

## Operating rule

Keep source provenance intact under `references/imported/` when historical
identity matters. Do not preserve defects, emulator-specific APIs, awkward data
models or obsolete constraints in project-owned tools merely because an imported
artifact had them.

For implementation decisions, prefer evidence in roughly this order:

1. canonical-ROM behavior reproduced in the project's deterministic harness;
2. hardware-oriented behavior independently corroborated by modern implementations or hardware research;
3. period source that directly matches bytes/algorithms in the ROM;
4. modern emulator source with a generic hardware model;
5. emulator source with game-specific handling;
6. historical scripts, cheats, achievements and labels;
7. comments, filenames and folklore.

Agreement between multiple emulators is not automatically independent evidence if they share the same historical workaround.

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

Status: useful reference interpreter, but **not independent evidence at the Uniracers OAM seam**.

The pinned newer snapshot still detects the internal title and sets
`SNESGameFixes.Uniracers`; its DMA/HDMA path then applies a named OAM-address
workaround and comments that OAM invalidation is not fully understood. The generated
`analysis/generated/third-party-code-audit.md` pins the exact current source lines.

Consequence: Snes9x 1.43 and the pinned newer Snes9x are two generations of the
same acknowledged game-specific strategy, not two independent votes for the hardware
rule. Use Snes9x as the cheap deterministic interpreter, but corroborate this seam
with generic models, independent cores, and ROM evidence.

### jgenesis sprite implementation

Source: `references/imported/emulators/jgenesis/sprites.rs`.

Status: high-value modern implementation evidence, still to be validated locally.

The code handles active-display/mid-scanline OAM progression generically and
calls out Uniracers as a dependent game rather than branching on the game name.
That is architecturally closer to the model UR-Recomp wants. Its exact timing
and target behavior remain evidence to test, not assumptions to clone blindly.

### MAME SNES PPU snapshot

Source: `references/imported/emulators/mame/snes_ppu.cpp`.

Status: independent PPU implementation reference, explicitly approximate at this seam.

MAME routes the active-display OAM case specially and its source itself calls the
treatment a hack. Use it as an independent discriminator and candidate hardware
model, not as proof that its chosen target is exact hardware behavior.

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

## Toolchain and provenance hardening

The imported evidence corpus and the executable research toolchain have different
policies:

- `references/imported/` preserves evidence bytes. `references/imported/MANIFEST.json`
  classifies every tracked import, pins repository bytes, verifies known upstream
  Git blobs/source hashes, and records review status. CI rejects unclassified additions,
  silent edits and executable-bit drift.
- `.tools/` is disposable build/install space. `tools/toolchain.json` pins exact
  upstream commits and `tools/bootstrap_toolchain.py` validates, resets and cleans
  checkouts before applying any project-owned adaptation and building them.
- build commands are argv vectors, never shell snippets; Python tools use isolated
  per-tool virtual environments; declared executables/shared libraries are verified
  after build.
- small UR-Recomp-specific source adaptations live under `tools/patches/`, are
  SHA-256 pinned, and must pass `git apply --check`.

Concrete adaptations:

- **Flips** builds the CLI target directly instead of dragging GTK into headless CI.
- **Beetle bsnes libretro** is used as a WRAM-capable second libretro oracle; its build
  disables modern glibc fortify wrappers that collide with bundled historical nall
  declarations, without modifying emulator logic.
- **snes2asm** receives a narrow project patch for numeric `--empty-fill` parsing and
  robust malformed/unknown decoder diagnostics.
- **MesenCE** was advanced from the older 2.2.1 pin because later upstream changes
  include SNES mid-scanline PPU behavior and debugger/Lua fixes directly relevant to
  this project.

The integrity audit also caught a real preservation error: the mirrored libretro cheat
file had normalized upstream's literal `&gt;` into `>`. The mirror is restored to
the exact upstream Git blob and now guarded mechanically.

## Tool interoperability

`docs/TOOL-INTEROPERABILITY.md` and `tools/tool_interop.json` own the producer/
consumer graph. The rule is to make durable project artifacts fan out to tools rather
than maintain parallel hand-entered worlds: one fixture grammar, one symbol authority,
one RNC decoder, and explicit adapters where formats differ.

Current high-value chains include:

- shared fixture -> native recomp / Snes9x / independent libretro core -> named WRAM
  checkpoints -> one comparison tool;
- canonical symbols -> snes2asm YAML and da65 info seeds;
- snes2asm -> generated WLA-DX reconstruction project;
- bsnes trace/CDL -> DiztinGUIsh or da65 range/address-mode evidence;
- Mesen/mesen-for-ai -> the same project fixture grammar through
  `tools/run_fixture_mesen.py`;
- RNC packed streams -> project-owned CRC-validated decoder -> structural analyzers.

Do not call two formats compatible merely because they look similar. Mesen CDL to
BSNES/BizHawk-style CDL remains an explicit candidate adapter until its flag semantics
are validated.

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
