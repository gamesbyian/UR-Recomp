# Tool Interoperability and Chaining

The toolchain is more useful as a graph than as a shelf of executables. This document records which artifacts can move between tools, which chains are already exercised, and where a small adapter can eliminate repeated manual work.

The machine-readable authority is `tools/tool_interop.json`. Its handoffs use three statuses: **verified** means the repository exercises the seam; **supported** means the native formats and documented contracts line up but the full chain is not yet a regression; **candidate** means an adapter or semantic validation is still required.

## Current high-value chains

| Chain | Flow | Current value |
|---|---|---|
| Deterministic differential | canonical ROM + one fixture script → native recomp + `snesref`/Snes9x → named WRAM dumps → `compare_wram_checkpoints.py` | One input script drives both engines, so state disagreement is directly comparable instead of being contaminated by different replay logic. |
| Independent emulator cross-check | same ROM/fixture → Snes9x core + Beetle/bsnes-derived core through `snesref` → same dump format | Separates recomp divergence from Snes9x-specific behavior, especially important because Snes9x contains named Uniracers handling. Beetle currently has a known post-quit teardown abort; completed checkpoints remain usable and the workflow gates that exception narrowly. |
| Reassemblable static project | canonical symbols → generated `snes2asm` YAML → `snes2asm` → WLA-DX project/source/assets → WLA-DX rebuild | Known names flow into the generated project automatically; a rebuilt project can become a byte-diff or controlled-mutation oracle. |
| Trace-assisted DiztinGUIsh | bsnes-plus trace/usage map → DiztinGUIsh → annotated project → asar-oriented assembly | Dynamic M/X, DB/DP and code/data evidence reduces 65816 desynchronization and keeps annotations collaborative. |
| Trace-assisted da65 | bsnes-plus log/CDL → cc65 `parse-bsnes-log.awk` → da65 RANGE/ADDRMODE info → bank-local disassembly | Dynamic M/X state is exactly the information da65 needs for reliable 65816 operand widths. Project labels can now be layered into the same info files. |
| Graphics archaeology | extracted native SNES palette/tile/map bytes ↔ SuperFamiconv ↔ PNG/JSON/native bytes | Gives visual inspection and controlled round trips without writing another tile converter. Exact Uniracers layout still needs per-asset classification before edits are considered lossless. |
| Patch experiment loop | original ROM + IPS/BPS ↔ Flips → derived ROM → ROM verifier → deterministic execution/differential | Makes ROM mutations reproducible and keeps the patch separate from the canonical input. |
| RNC archaeology | ROM → project RNC scanner/Method-1 decoder → CRC-verified decoded bytes → payload/course analyzers | The period compression format, game corpus and project analyzers already form a working pipeline. |

## UI state atlas chain

The frontend mapping work uses the same fixture-first interoperability rule as gameplay validation. Controller-only scripts drive the native runtime; SNESRecomp's existing `dump <tag>` facility emits framebuffer BMPs alongside WRAM, VRAM, CGRAM, OAM, registers and metadata; `analysis/ui-capture-manifest.json` states which tags correspond to conceptual UI states; and `tools/build_ui_atlas.py` reduces those raw bundles to compact JSON/Markdown evidence.

This chain is **verified** at the producer/consumer seam: the native smoke invokes the atlas builder over the generated dump directories, while unit coverage checks successful discovery, strict mismatch handling and optional missing captures. `analysis/ui-menu-index.json` plus `tools/query_ui_state.py` provide the reverse lookup path from an observed `7E:009F` menu byte back to the conceptual state model without loading the full UI documentation.

Keep raw screenshot/state bundles ephemeral unless a particular capture has durable evidence value. The compact manifest, state graph, reverse index, fixtures and reports are the reusable interfaces.

## Canonical symbol fan-out

`docs/SYMBOLS.md` remains human-owned. `tools/export_symbols.py` generates `analysis/generated/symbols.json`, and `tools/export_symbol_adapters.py` now projects that authority into tool-specific seeds:

| Output | Consumer | What is deliberately included |
|---|---|---|
| `analysis/generated/snes2asm-symbols.yml` | `snes2asm -c` | Known ROM function labels as LoROM file offsets plus known RAM symbols as 24-bit addresses. |
| `analysis/generated/da65-symbols-bank-XX.info` | da65 | Bank-local function labels and 65816/start-address boilerplate. |

The da65 export intentionally does **not** invent RANGE or ADDRMODE entries. 65816 M/X state should come from an execution trace or CDL source. This lets static names and dynamic execution facts be composed rather than conflated.

The same symbol authority should eventually feed Ghidra and Mesen label formats once those import contracts are pinned. Do not maintain parallel hand-edited label lists.

## Where formats already align

`snes2asm` generates a Makefile and source/assets intended to be reassembled with WLA-DX, so this is a native producer/consumer relationship rather than an adapter project. Its graphics, palette, tilemap and BRR decoders also expose native SNES payloads that can be inspected by project scripts and, where layout matches, SuperFamiconv.

SuperFamiconv is especially useful in both directions. It emits native SNES palette/tile/map bytes, PNG previews and JSON representations, and its tile/map subcommands can also consume native data. For reverse engineering, prefer **native bytes → preview/JSON** first. Only use PNG → native bytes as a replacement pipeline after an exact round-trip test proves palette ordering, tile deduplication, flipping, map width/order and base offsets.

Flips produces ordinary derived ROMs and IPS/BPS patches. A derived ROM is therefore immediately consumable by every ROM-facing analyzer/emulator, but it must be treated as a distinct fingerprinted experimental input rather than allowed to masquerade as the canonical ROM.

`snesref` normalizes multiple libretro cores behind one fixture/dump interface. That is a major interoperability asset: Snes9x and a WRAM-capable independent core can be swapped without rewriting the test workload.

## Pinned malmazuke research lookup

The local [malmazuke symbol query](../tools/README.md) is a read-only join from the audited imported `native-symbols.json` and `labels.json` to the bounded `analysis/data/malmazuke-pal-structural-links-20261010.json` index. It reports original PAL cited source, observed/inferred/data/unknown classification, permanent upstream research-record links and optional **unverified** USA structural candidates. The catalog registers a *supported* transport chain, not a verified function-semantic correspondence or gameplay acceptance. Use the actual canonical USA ROM and original/runtime oracle before promoting claims. This is an extension of the existing cross-build research atlas, not a rival symbol authority.

## Useful chains that still need adapters

### Mesen CDL → disassembly evidence

`mesen-for-ai` can export Mesen's byte-level Code/Data Logger data. DiztinGUIsh already imports BSNES/BizHawk usage/CDL information, and cc65 ships a BSNES-log helper that generates da65 RANGE/ADDRMODE sections. These are adjacent formats, not yet the same format.

A project-owned `mesen-cdl-adapter` should map Mesen's SNES code/data flags into a verified compatibility representation. Before routine use, validate the mapping against a deterministic scene where known executed code and known data reads are independently established. Once proven, one headless Mesen run could feed both DiztinGUIsh and da65 instead of maintaining a separate manual trace session.

### Shared fixture script → Mesen

The existing `tests/input/*.script` grammar already drives native recompilation and `snesref`. `mesen-for-ai` has frame stepping and latched input, so an adapter can replay the same project fixture in Mesen. This is preferable to creating a third hand-authored input format. The adapter should preserve exact frame-boundary semantics and named checkpoints.

### Historical SMV → neutral replay → multiple engines

The historical P1 chain is already **verified**, not aspirational. `tools/extract_smv_input.py` converts Snes9x SMV movies into the project-neutral controller stream, emits provenance metadata, and recovers embedded reset-anchored SRAM where present. `tools/compare_input_runs.py` compares parsed intervals rather than comments.

The neutral stream is now explicitly dual-player and backward compatible:

```text
start:duration:p1-mask[:p2-mask]
```

Historical three-field output remains unchanged and means P2 idle. `tools/controller_input.py` is the parser authority for new project adapters.

The same artifact can now move in three directions:

- `snesref`/libretro consumes it through `SNESREF_INPUT_FILE`; the project applies `tools/patches/snesrecomp-dual-controller-input.patch` to the pinned reference frontend when P2 input is required;
- the native runtime consumes it through `tools/replay_input_via_lua.py`, which writes both controller 1 and controller 2;
- Mesen consumes it through `tools/replay_input_mesen.py`, which writes ports 0 and 1 through the existing mesen-for-ai bridge.

ROM-free unit tests verify the shared parser and both project-owned writers. The dual-player CI lane also requires the pinned `snesref` patch to apply and compile. A canonical-ROM three-engine 2P replay is still the promotion gate from **supported** to **verified** for the new P2 path.

The reference WRAM trace is normalized by `tools/summarize_wram_trace_checkpoints.py`, while native snapshots use the project-owned state model. The 2008 Dragster workflow already compares P1 semantics from the same historical input corpus. This remains the template for future external input formats: convert once to a neutral project artifact, then replay everywhere.

### Dynamic trace → canonical symbols

Dynamic tools can discover call targets, RAM writers and execution ranges. Their findings should not remain trapped in trace files or GUI databases. Confirmed names/addresses should flow back through `docs/SYMBOLS.md`, after which all symbol adapters regenerate automatically.

## Efficiency rules

Prefer one durable artifact that many tools consume over several tool-specific copies. In particular: one fixture script should drive every execution engine; one canonical symbol map should seed every static/debugger tool; one decoded RNC implementation should feed all payload analyses; and one patch should define a ROM mutation that every execution/analyzer can replay.

When two tools overlap, use them as independent checks or consecutive stages rather than running both mechanically. Snes9x plus Beetle is useful because disagreement is informative. `snes2asm`, da65 and DiztinGUIsh should not all produce giant disassemblies by default; choose the one whose inputs best match the evidence available, then cross-check only the seams that matter.

Do not write an adapter merely because two files can be coerced into similar shapes. A valid handoff must preserve semantics that matter to the consumer: CPU bank and M/X state for 65816 disassembly, palette/index ordering for graphics, frame timing for input replay, and address-space identity for memory/CDL data.

## Next interoperability work

The highest-return additions are, in order: complete an end-to-end shared-fixture run through Mesen; validate a Mesen-CDL compatibility adapter for DiztinGUIsh/da65; add Ghidra/Mesen symbol exporters; and create exact native-graphics round-trip fixtures once the relevant Uniracers asset regions are identified. SMV controller/SRAM extraction is already a verified neutral-input chain and should be extended rather than reinvented.

Keep those as adapters around project-owned canonical artifacts. Avoid converting the repository into a chain of opaque third-party databases.
