# Windows acceptance: manual exact-candidate fan-out pilot

Status: opt-in engineering pilot, not a release-gate producer or a physical Windows acceptance claim. The existing Baldosa Windows native bridge is still authoritative for its complete set of packaging, startup, storage, CMD, fault and UI checks.

## Single-dispatch quick route (verified October 25)

Manually dispatch windows-acceptance-fanout-pilot.yml with build_only=true (the default). This invokes the independently guarded exact-build-only reusable Windows producer from #2561 once, then starts two isolated Windows consumer jobs with one exact hash-checked exported candidate from the same run. No external run ID required.

The [real build-only qualification run #40167815138](https://github.com/gamesbyian/UR-Recomp/actions/runs/40167815138) completed **all original 13 Windows journeys** in 9m57s total elapsed, with a SHA-consistent, zero-issue aggregate and zero release credits. The two original Windows groups took 233.672 seconds and 253.328 seconds respectively. This is bounded gameplay and storage journey testing, not a substitute for the full bridge's additional fault, display, CMD, packaging and independent hardware QA.

To reuse an earlier successful bridge or build-only producer run rather than rebuilding, explicitly choose build_only=false and provide candidate_run_id. That run must have the identical source commit, be successful, have the accepted producer workflow name and expose the existing five-file SHA manifest. All 13 original source shell scripts and fail-closed case aggregation remain unchanged; no PR or push event can launch this route.

## Run

1. On the exact current main source, manually run baldosa-windows-native-bridge.yml with export_campaign_inputs=true. This retains the same single source-bound executable, profile fixture and ROM-free ZIP under qa-baldosa-native-export (seven-day retention). Preserve the run ID and verify that all bridge checks passed.
2. On the **identical repository SHA**, manually dispatch windows-acceptance-fanout-pilot.yml with candidate_run_id set to that successful bridge run. The workflow refuses earlier source commits, non-successful runs and wrong workflow producer names. It never recompiles the candidate.
3. Its two isolated hosted Windows jobs verify SHA256SUMS, the actual ZIP's embedded manifest/executable hash using the existing binder, the approved original ROM hash, and exactly the current 13 original Win32 player-journey shell command bodies extracted by run_baldosa_parallel_windows_journeys.py.

Group seed-dependent runs the original baseline first, checks its actual newly produced 8192-byte SRAM seed, then runs the two existing Records cases. Group independent runs only the ten source-asserted baseline-independent original routes with at most two workers inside the second Windows job. A fresh output parent is created but no baseline save is fabricated or shared. Independent output roots and private logs stay on the ephemeral Windows jobs; only per-group JSON receipts are uploaded.

The Ubuntu aggregate validates both SHA256-bound receipts, their shared source/EXE/fixture/ZIP identity, all original 13 case indices and step names, every exit code, missingness, duplicate coverage and any attempted release credit. It fails closed on missing group or mismatch, but never writes RELEASE-QUALITY-LEDGER.json.

### Private original-script output fingerprints

Each original Win32 script's combined stdout/stderr log stays on the ephemeral Windows worker. The producer records a SHA-256 and byte length for each actual log and (when present) its optional Markdown summary, using strict fixed filenames. Missing or symlinked logs fail closed. A missing optional summary is represented as `summary_sha256: null` and `summary_bytes: 0`, not invented evidence. All 13 fingerprints flow into the aggregate receipt without uploading private logs, user paths, ROM or SRAM.

These digests bind the output to a future separately authorized inspection, but **are not signatures or independent guest acceptance evidence by themselves**. Historic #40167815138 ran before this provenance addition and cannot be described as having these case-level hashes.


## Why this pilot has intentionally limited scope

The existing native Windows bridge already has a two/three-process on-runner journey parallelism pilot and four-cohort independent reliability fan-out. This additional workflow validates whether **two separate GHA Windows jobs** provide a worthwhile wall-time/runner-minute tradeoff using one pre-built candidate. It is not a new gameplay oracle. The bridge still executes many additional source-bounded CMD, process-crash, save, extracted-ZIP and other regressions; these are not silently replaced. A passing aggregate can assist independent QA but cannot mark any Windows release gate as passed, and physical controllers/displays are not available through hosted Windows evidence.

Measure identical candidate sequential/2-process versus this exact fan-out before adopting it beyond opt-in. If the relative GHA setup and artifact transfer costs outweigh gains, retain the old route. Avoid broad scheduled dispatches.

ROM-free contract tests: python3 -m unittest tests.unit.test_qa_windows_acceptance_fanout
