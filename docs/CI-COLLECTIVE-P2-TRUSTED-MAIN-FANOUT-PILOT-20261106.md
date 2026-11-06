# P2: one verified Windows x64 producer, two hosted acceptance groups

**Evidence date:** November 6, 2026 UTC. **Scope:** manually nominated, already-merged trusted `main` source, GitHub-hosted Windows x64 only. This is an existing one-build acceptance *subset*, not new CI infrastructure, an admitted composite PR source, Windows release evidence or a matched build savings benchmark. The [November 4 CI infrastructure plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md) remains the authority for P1/P2 and release/HP trust.

## Existing source architecture, recovered rather than reinvented

- [#2557](https://github.com/gamesbyian/UR-Recomp/pull/2557) introduced the two-group fan-out over a single exact Windows export. [#2561](https://github.com/gamesbyian/UR-Recomp/pull/2561) created the shorter **build-only** source-pinned producer, retaining the five unchanged native build/stage steps from the full [Baldosa Windows bridge](../.github/workflows/baldosa-windows-native-bridge.yml). [#2565](https://github.com/gamesbyian/UR-Recomp/pull/2565) connected one manual dispatch to that producer and both consumers. No production PR/push trigger or new runner needed.
- Producer: [`.github/workflows/windows-exact-build-only.yml`](../.github/workflows/windows-exact-build-only.yml), reusable `workflow_call` on `windows-2022`, with pinned `gamesbyian/uniracers-recomp` source `10b864b9d14a7b7416dd909eb7b054c88faef101`, exact submodule and toolchain requirements, ROM/source checks, Clang 22.1.8, source-time-derived PE timestamp, one ROM-free ZIP and `qa-baldosa-native-export` artifact. The build-only route performs **no acceptance journeys**.
- Source drift guard: [`tools/check_windows_build_source_reuse.py`](../tools/check_windows_build_source_reuse.py) compares the shell bodies of five critical build stages verbatim with the full bridge, failing if they diverge. The produced artifact includes actual executable, profile fixture, ROM-free package, source SHA and `SHA256SUMS`.
- Consumers: [`.github/workflows/windows-acceptance-fanout-pilot.yml`](../.github/workflows/windows-acceptance-fanout-pilot.yml) runs **two hosted Windows** matrix groups after producer success, downloading its *same-run* artifact. The `seed-dependent` group serially executes original script indices **0–2** (the first creates the private SRAM baseline); `independent` executes original indices **3–12** with two local worker threads and separate writable state. No native recompile occurs in either consumer.
- The consumer validates `source-commit.txt == GITHUB_SHA`, all `SHA256SUMS`, the original ROM identity and candidate binding; each group emits source/EXE/fixture/ZIP digests and only bounded log/summary hashes. The Ubuntu aggregate requires **exactly 13 distinct original script indices**, exit-zero real group receipts and identical source/package identities. An absent, failed or duplicated case does not receive credit. Receipts explicitly set `release_gate_credit=0` and `independent_physical_qa=false`.
- Historic first [one-build trial #40167815138](https://github.com/gamesbyian/UR-Recomp/actions/runs/40167815138) completed the 13 journeys in **9m57s** on October 25; a distinct later historical [PR trial #40222618116](https://github.com/gamesbyian/UR-Recomp/actions/runs/40222618116) retained an exact aggregate with 13/13 cases and no gate credit. These source epochs differ from the new trusted-main run. The approximately **16m47s** historic full bridge also ran many other CMD, display, fault and acceptance cases; its elapsed time is **not an equivalent A/B baseline**.

## New trusted-main trial, exact immutable source

| Property | Source-verified value |
| --- | --- |
| Hosted workflow | [run #42198617652](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652), manual `workflow_dispatch`, input `build_only=true` |
| Run source HEAD | `6c57ff4f4ef68c7f4f2a038df6a39a17675890f3` (then-merged `main`, no PR composite) |
| Run created → updated UTC | `2026-11-06T09:54:57Z` → `10:06:32Z` |
| Workflow conclusion | **success**, four jobs completed successfully |
| Exactly 13 original player journeys | **13/13**, indices `0..12`, all exit-zero, `transport_complete=true`, zero issues/failed cases |
| Release and physical acceptance | **0 gates credited**, physical QA explicitly false; formal 0/12 Windows and 0/45 original/native event admissions unchanged |
| Executable SHA-256 | `ec6406f801cead75d074291d7897ef7422458fb8ca955539f1a55ba818553f03` |
| Profile-fixture SHA-256 | `aa9e3b9950af633ec9de50da12cd752bad472e62061848b7be4bc5a7e50d2f3e` |
| Inner ROM-free ZIP SHA-256 | `cec9f64663f4065ebcfe88598c5b5f16e6342cd365dbcdb6a6f007755cbb87fe` |

The [producer artifact #13492983782](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13492983782), 13,033,977 compressed bytes, was independently downloaded for an actual ZIP CRC and manifest/hash audit. Its `source-commit.txt` matched the exact run SHA; the three SHA-256 values in `SHA256SUMS` matched the downloaded bytes; the nested ROM-free ZIP had four expected files, passed CRC verification, and its executable was **byte-identical** to the separately exported executable. No ROM, SRAM or personal save payload was found. These checks confirm source integrity of this candidate, not malware safety or final release suitability.

Both small group artifacts were independently opened and checked for valid ZIP structure, self-consistent receipt SHA, correct group indexes, zero exits and the same producer source/EXE/fixture/ZIP identities. The final [aggregate artifact #13493552466](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13493552466) was independently parsed: schema `ur-win32-acceptance-fanout-aggregate/2`, `expected_cases=observed_cases=13`, all indices unique and sorted, `transport_complete=true`, `failed_cases=[]`, `issues=[]`, `release_gate_credit=0`, and `independent_physical_qa=false`. Evidence is source-bound, but generated receipt hashes are **not cryptographic signatures or independent re-execution**.

## Observed time, not inferred savings

| Hosted job | Job interval | Actual journey/build substep | Notes |
| --- | ---: | ---: | --- |
| Candidate / candidate | **333s** | Native compile **128s** | Checkout steps 43s; verified native stage 76s; source/ROM/guest checks 50s; toolchain fetch 20s; artifact upload 4s |
| Journeys / seed-dependent | **292s** | Recorded original journeys **248.344s** | Serial indices 0–2, same candidate SHA |
| Journeys / independent | **336s** | Recorded original journeys **294.625s** | Indices 3–12, two workers, independent private output |
| Aggregate | **17s** | Receipt/cardinality reconciliation | Hosted Ubuntu; no product run |
| **Summed started-job intervals** | **978s (16m18s)** | Windows jobs 961s; Ubuntu 17s | Not billable CPU or hypothetical alternative time |
| **Created-to-finished workflow** | **695s (11m35s)** | Both consumer jobs overlapped | End-to-end actionable verdict for this source and limited suite |

Job timing came from a complete, four-row authenticated GitHub run-job API inventory. It includes reported job intervals and orchestration semantics, not metered CPU. The full conventional bridge has **additional acceptance cases**; neither its historical 16m47s result nor the October 25 fan-out's 9m57s is an exact same-SHA/same-test-set performance control. The first current-main trial therefore proves working source-bound fan-out but **no numerical compute savings, cash savings, speedup ratio or production replacement decision**. Standard hosted runners in this public repo should not be assigned fictitious per-minute charges.

## Trust, retention and next decision

- This invocation ran **only an already-merged `main` SHA on hosted `windows-2022`/Ubuntu**. The workflow itself is manually dispatchable with a supplied ref; a future **cross-PR composite** still requires the unpublished stronger P1 full-tree source verifier, an independently approved source admission procedure and full per-PR integration gates. Do not send unreviewed PR code to the owner HP.
- The producer export currently expires **2026-11-13T10:00:24Z** (seven-day retention); independent group and aggregate receipts expire **November 20** (14-day retention). Retain source/run/artifact identifiers in this document; neither temporary artifact replaces the preserved, independently audited October 28 physical playtest package.
- Continue with actual Windows product, WIDE-07 and first full original/native event priorities rather than building a second fan-out orchestrator. If a naturally justified equivalent **same-SHA/same-13-script** conventional run appears, compare critical path, **all** started job time, setup/build/checkouts/transfers, skip/failure coverage and case identities for 2–3 trials before claiming any improvement or changing workflow defaults. If no such comparison is justified, keep this successful, **manual** bounded route and the existing full bridge.
