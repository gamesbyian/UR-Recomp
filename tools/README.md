# Project tools

Project-owned scripts live here. External tools are not vendored into this directory; their exact sources/revisions are registered in `toolchain.json` and installed into ignored `.tools/` by `bootstrap_toolchain.py`.

Before adding another script, check whether an existing project tool or a pinned external tool already owns the operation.

Key commands:

```bash
python3 tools/check_repo_hygiene.py
python3 tools/bootstrap_toolchain.py --list
python3 tools/bootstrap_toolchain.py
python3 tools/validate_tool_interop.py
python3 tools/export_symbol_adapters.py --check
```

See `docs/TOOLCHAIN.md` for selection guidance, `docs/TOOL-INTEROPERABILITY.md` for producer/consumer chains, and `AGENTS.md` for task routing.

UI-state helpers:

```bash
python3 tools/query_ui_state.py --menu-id 0x99
python3 tools/query_ui_state.py --state MAIN_MENU
python3 tools/build_ui_atlas.py --help
```

Pinned external research symbol lookup (read-only; PAL source is a lead, not USA oracle):

```bash
python3 tools/query_malmazuke_symbols.py --pal 81:8050
python3 tools/query_malmazuke_symbols.py --usa-candidate 81:8050
python3 tools/query_malmazuke_symbols.py --grep 'race_progress|hunter' --limit 20
python3 -m unittest tests.unit.test_query_malmazuke_symbols
```

The lookup also joins the pinned malmazuke original-code labels to their upstream research records (using immutable source links). For example, `--grep 'R-0038'` locates cited addresses from a particular research document. Source records not copied into UR-Recomp still point to the pinned upstream commit.

The lookup consumes the audited selected malmazuke native-symbol index and the existing bounded structural candidate JSON. A USA candidate is **not** a verified function correspondence; use the canonical USA ROM and PAL/USA analysis tools to adjudicate it. No core, ROM loader, network access or gameplay code is added.

Structural PAL/USA mapping gap report (derived only from the existing pinned candidate index):

```bash
python3 tools/report_malmazuke_mapping_gaps.py --domain result --limit 15
python3 tools/report_malmazuke_mapping_gaps.py --domain frontend --json-out /tmp/frontend-gap.json
python3 -m unittest tests.unit.test_report_malmazuke_mapping_gaps
```

This report distinguishes **not covered by the current structural interval index** from unimplemented code, untested gameplay, or a proved USA/PAL difference. The worklist is ordered by upstream original-code evidence class and address, not product urgency. Domain counts overlap and must not be summed.

Bounded CPU-direct PPU register-write provenance (inspired by malmazuke's register-order provenance):

```bash
python3 tools/report_ppu_direct_write_provenance.py reference-trace.log --from-frame 1005 --to-frame 1010 --json-out /tmp/ppu-direct.json
python3 -m unittest tests.unit.test_report_ppu_direct_write_provenance
```

This **only** consumes existing original Snes9x `PPUPCTRACE` lines from `tools/instrument_snesref_ppu_pc_trace.py`. It retains ordered CPU PCs and $2116–$2119 register writes, and accepts contiguous four-write sequences; absent $2115 state, DMA/HDMA observations, interleaved writes and final PPU priority are **not inferred**. Malformed events or reversed timestamps fail nonzero. Do not use this as source-OBJ/2P correctness proof or a substitute for original/native QA gates.
