# Project tools

Project-owned scripts live here. External tools are not vendored into this directory; their exact sources/revisions are registered in `toolchain.json` and installed into ignored `.tools/` by `bootstrap_toolchain.py`.

Before adding another script, check whether an existing project tool or a pinned external tool already owns the operation.

Key commands:

```bash
python3 tools/check_repo_hygiene.py
python3 tools/bootstrap_toolchain.py --list
python3 tools/bootstrap_toolchain.py\npython3 tools/validate_tool_interop.py\npython3 tools/export_symbol_adapters.py --check\n```

See `docs/TOOLCHAIN.md` for selection guidance, `docs/TOOL-INTEROPERABILITY.md` for producer/consumer chains, and `AGENTS.md` for task routing.
