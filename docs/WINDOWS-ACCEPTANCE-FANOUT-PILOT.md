# Windows acceptance: manual exact-candidate fan-out pilot

Status: opt-in engineering pilot, not a release-gate producer or a physical Windows acceptance claim. The existing Baldosa Windows native bridge is still authoritative for its complete set of packaging, startup, storage, CMD, fault and UI checks.

## Run

1. On the exact current main source, manually run baldosa-windows-native-bridge.yml with export_campaign_inputs=true. This retains the same single source-bound executable, profile fixture and ROM-free ZIP under qa-baldosa-native-export (seven-day retention). Preserve the run ID and verify that all bridge checks passed.
2. On the **identical repository SHA**, manually dispatch windows-acceptance-fanout-pilot.yml with candidate_run_id set to that successful bridge run. The workflow refuses earlier source commits, non-successful runs and wrong workflow producer names. It never recompiles the candidate.
3. Its two isolated hosted Windows jobs verify SHA256SUMS, the actual ZIP's embedded manifest/executable hash using the existing binder, the approved original ROM hash, and exactly the current 13 original Win32 player-journey shell command bodies extracted by run_baldosa_parallel_windows_journeys.py.

Group seed-dependent runs the original baseline first, checks its actual newly produced 8192-byte SRAM seed, then runs the two existing Records cases. Group independent runs only the ten source-asserted baseline-independent original routes with at most two workers inside the second Windows job. A fresh output parent is created but no baseline save is fabricated or shared. Independent output roots and private logs stay on the ephemeral Windows jobs; only per-group JSON receipts are uploaded.

The Ubuntu aggregate validates both SHA256-bound receipts, their shared source/EXE/fixture/ZIP identity, all original 13 case indices and step names, every exit code, missingness, duplicate coverage and any attempted release credit. It fails closed on missing group or mismatch, but never writes RELEASE-QUALITY-LEDGER.json.

## Why this pilot has intentionally limited scope

The existing native Windows bridge already has a two/three-process on-runner journey parallelism pilot and four-cohort independent reliability fan-out. This additional workflow validates whether **two separate GHA Windows jobs** provide a worthwhile wall-time/runner-minute tradeoff using one pre-built candidate. It is not a new gameplay oracle. The bridge still executes many additional source-bounded CMD, process-crash, save, extracted-ZIP and other regressions; these are not silently replaced. A passing aggregate can assist independent QA but cannot mark any Windows release gate as passed, and physical controllers/displays are not available through hosted Windows evidence.

Measure identical candidate sequential/2-process versus this exact fan-out before adopting it beyond opt-in. If the relative GHA setup and artifact transfer costs outweigh gains, retain the old route. Avoid broad scheduled dispatches.

ROM-free contract tests: python3 -m unittest tests.unit.test_qa_windows_acceptance_fanout
