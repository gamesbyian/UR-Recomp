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

Regional-switch checkerboard **offline preview** (synthetic-only until menu measurement): `python3 tools/showcase/regional_checkerboard_wipe.py --synthetic-demo --outdir /tmp/ur-checker-demo`; calibration and island/reuse policy: [`tools/showcase/REGIONAL-CHECKERBOARD.md`](showcase/REGIONAL-CHECKERBOARD.md). Tests: `python3 -m unittest tests.unit.test_regional_checkerboard_wipe`. No runtime integration, new bootstrap dependency, or CI workflow.

Pinned Baldosa/malmazuke/UR apparatus audit (file-level inventory and 35 grounded capability decisions):

```bash
python3 tools/audit_three_project_apparatus.py
python3 -m unittest tests.unit.test_audit_three_project_apparatus
```

An inventoried tool is not a verified original-game or native-execution feature; consult the [three-project synthesis](../docs/THREE-PROJECT-APPARATUS-SYNTHESIS-20261010.md) before adoption.

Upscaling/scaler research trial provenance (no image model installed and no asset approval):

```bash
python3 tools/art/validate_upscale_trials.py path/to/trial.json --report /tmp/trial-summary.json
python3 -m unittest tests.unit.test_validate_upscale_trials
```

The schema/example and controlled model/shader comparison steps are in [HD-UPSCALING-EXPERIMENT-PLAN.md](../docs/HD-UPSCALING-EXPERIMENT-PLAN.md). Output reports cannot mark art shipping-ready.

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

Opt-in archived Snes9x 1.43 DMA entry provenance, inspired by malmazuke's DMA channel inventory:

```bash
# Run on a temporary, private working copy of archived Snes9x 1.43 dma.cpp.
python3 tools/instrument_snes9x143_dma_entry.py /tmp/snes9x143/dma.cpp
# Compile and run the appropriately pinned/reference emulator fixture separately.
python3 tools/report_snes9x_dma_entry_provenance.py /tmp/dma-capture.log --from-frame 2208 --to-frame 2210 --json-out /tmp/dma-summary.json
python3 -m unittest tests.unit.test_snes9x_dma_entry_provenance
```

The instrument records DMA **entry descriptor fields**, source A-bus address and B-bus data port, but no transfer completion, HDMA, VMADD/OAMADD/CGADD latch, PPU pixel ownership or verified USA result. A ROM/original executable trace is **not yet captured** by this pilot. No repo-tracked emulator sources or release artifacts are modified by this opt-in instrument. Do not claim full DMA-to-visible-pixel lineage without separately observing relevant PPU register writes and completing an independent original/native comparison.

Baldosa native-interpreter coverage triage (read-only, no AOT promotion):

```bash
# Each report must come from the pinned Baldosa SNESRecomp
# tools/tier2_ingest.py --json, retaining the original capture identity.
python3 tools/report_baldosa_tier2_route_coverage.py \
  --route race_1p=/tmp/captures/race_1p.ingest.json \
  --route race_2p=/tmp/captures/race_2p.ingest.json \
  --top 12 --json-out /tmp/baldosa-interpreter-work.json
python3 -m unittest tests.unit.test_report_baldosa_tier2_route_coverage
```

The tool hashes the **unchanged pinned Baldosa route scripts and input reports**, but the route-to-capture association remains *caller-supplied and unverified* by Tier-2 identity; it preserves per-route ROM/program/build/module identities, orders exclusive interpreted CPU PC costs and M/X variants, and adds independent Baldosa source-name *leads*. Different builds are never silently pooled. Reports with incomplete identity are rejected; incomplete captures carry warnings. This is performance-investigation evidence **only**, not a safe-root list, original/native end-to-end oracle, evidence of a full course result, or permission to edit generated code. The upstream Tier-2 capture still must be run separately on the appropriate pinned emulator/backend; no capture or emulator build is performed by this command.

## Compact CI and experiment result reporting

- `tools/summarize_unittest_ci.py`: publishes the timing-balanced (per-vCPU, max 4) shard tooling unit-test outcome, bounded failures, observed test totals and hashed raw-log receipts to `ci-tooling-unit-result.json` and `GITHUB_STEP_SUMMARY`. Missing or incomplete shard evidence is never a pass. The original failing test step retains its failure verdict; full logs are uploaded only when necessary.
- `tools/partition_unit_tests.py` + `tools/unit_test_timings.json`: deterministic, timing-balanced partition of `tests/unit/test_*.py` into CI shards (every module in exactly one shard; unknown modules get a default weight). Refresh the timings occasionally; they only affect balance.
- `tools/ci_compile_cache.py`: PATH shim (`g++`/`gcc`/`clang++`/... symlinks, enabled by `UR_COMPILE_CACHE_DIR`) that caches per-source objects of combined compile-and-link commands by preprocessed source + flags. Used only by `tooling-unit-tests.yml`; unknown flags pass through to the real compiler.
- `tools/publish_experiment_result.py`: small transport receipt for manual or maintained research runs. Requires a real primary JSON object and every declared input; records exact SHA-256/byte counts, source-run identity, question and a domain-provided readable summary. Its `produced_not_adjudicated` status explicitly does not certify original-game fidelity. Example: `.github/workflows/one-shot-execution-coverage-ab.yml`.

Results valuable after Actions artifact expiry must be promoted into the **existing** research ledger/compact `analysis/data` with actual conclusions, provenance and reproduction commands by a reviewed commit. Never schedule more CI or copy large captures into Git just to make a report. See `docs/CI-RESEARCH-APPARATUS-AUDIT-20261010.md`.
