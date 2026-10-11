# Project tools

Project-owned scripts live here. External tools are not vendored into this directory; their exact sources/revisions are registered in `toolchain.json` and installed into ignored `.tools/` by `bootstrap_toolchain.py`.

Before adding another script, check whether an existing project tool or a pinned external tool already owns the operation.

Key commands:

```bash
python3 tools/check_repo_hygiene.py
python3 tools/bootstrap_toolchain.py --list
python3 tools/bootstrap_toolchain.py\npython3 tools/validate_tool_interop.py\npython3 tools/export_symbol_adapters.py --check\n```

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

The lookup consumes the audited selected malmazuke native-symbol index and the existing bounded structural candidate JSON. A USA candidate is **not** a verified function correspondence; use the canonical USA ROM and PAL/USA analysis tools to adjudicate it. No core, ROM loader, network access or gameplay code is added.
