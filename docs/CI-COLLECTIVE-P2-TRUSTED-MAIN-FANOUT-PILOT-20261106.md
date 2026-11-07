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
- All four real source/EXE/ZIP-bound P2 artifacts were **separately preserved on the owner HP**, without extraction or execution. Exact artifact IDs, ZIP hashes, expiry and a clearly NONRELEASE local path are recorded in the [preservation receipt](#p7-source-bound-preservation-of-qualification-artifacts).
- Continue with actual Windows product, WIDE-07 and first full original/native event priorities rather than building a second fan-out orchestrator. If a naturally justified equivalent **same-SHA/same-13-script** conventional run appears, compare critical path, **all** started job time, setup/build/checkouts/transfers, skip/failure coverage and case identities for 2–3 trials before claiming any improvement or changing workflow defaults. If no such comparison is justified, keep this successful, **manual** bounded route and the existing full bridge.

## P7 source-bound preservation of qualification artifacts

On November 6 UTC, all four ZIP artifacts from trusted-main [run #42198617652](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652) were independently downloaded **again** using the owner HP's existing authenticated GitHub API, compared with the previously checked artifact ZIP SHA-256 values, and saved intact, without extraction or executable launch, under:

\`%USERPROFILE%\Downloads\UR-Recomp-Playtests\Qualification-Evidence\`

Every name starts with **\`P2-NONRELEASE-\`**. The destination is never overwritten if an existing file has a different SHA-256; downloaded temporary files are removed. The local ZIP bytes are source-bound *technical test evidence*, separately identified from the previously [audited October 28 ROM-free physical-playtest package](HP-PLAYTEST-ARTIFACT-PRESERVATION-20261106.md). All four download receipts reported \`preserved and verified\`.

| Exact GitHub Actions artifact | Expires UTC | Local filename after \`P2-NONRELEASE-\` | Outer ZIP SHA-256 |
| --- | --- | --- | --- |
| Producer [#13492983782](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13492983782), **13,033,977 bytes** | **Nov 13 10:00:24** | \`6c57ff4-producer-run42198617652.zip\` | \`8d271b2703b73b39bac0c45b0fe3340d0b9dc541cba7243d2d00580e890addac\` |
| Seed-dependent [#13493053163](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13493053163), 1,094 bytes | Nov 20 10:05:21 | \`6c57ff4-seed-dependent-run42198617652.zip\` | \`ad23894fadab1168a5eb36a6a861b4f316f818fc7be50b077239b0559b657d1d\` |
| Independent [#13494365840](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13494365840), 2,073 bytes | Nov 20 10:06:07 | \`6c57ff4-independent-run42198617652.zip\` | \`be29f42dbf1a8bd87f61d246ed9b6c98d056b565a334419e313cc106ad5e9e7c\` |
| Aggregate [#13493552466](https://github.com/gamesbyian/UR-Recomp/actions/runs/42198617652/artifacts/13493552466), 1,748 bytes | Nov 20 10:06:29 | \`6c57ff4-aggregate-run42198617652.zip\` | \`cea290457e359f072e1fa8ab51c8b557887173698212d7054d1fb7a4a49d2a73\` |

This retains the exact original 13/13 qualification receipts for later A/B or methodological audit after normal GitHub Actions expiry, without another Windows game build. It **does not** prove that a conventional same-SHA comparison was performed, establish a shipping/release gate, permit unmerged PR code on HP, or justify preserving every Actions artifact.


## Next P2 experiment: pre-registered equivalence and stopping contract (November 6)

**Decision first:** no second Windows run is authorized just to generate a favorable speed number. The current 13/13 result already proves this manual route functions. A benchmark is justified only when a separately needed Windows candidate uses the *same immutable source* and all thirteen original journey scripts, or when a reviewer explicitly requests one bounded equivalence experiment. Use the existing workflow paths; do not add a second automatic CI trigger.

Before either arm starts, freeze a single SHA, the original script source and expected index set `0..12`, runner image/toolchain, environment and caching assumptions. Capture those values in the experiment issue/PR as a **pre-registration**. The conventional control is valid only if it builds that exact SHA and executes **exactly the same thirteen scripts with the same assertions, profiles, ROM identity and exit-verdict rules**, without extra acceptance work or suppressed failures. The full Baldosa bridge currently executes *additional* scripts and cannot be used as that control merely by subtracting its timing after the fact. If the existing workflows cannot select an equivalent control without changing acceptance semantics, record **unmatched; experiment deferred** rather than invent a comparison.

For each valid arm, archive these independent dimensions: (1) GitHub run/attempt and checkout SHA; (2) source-bound PE/ZIP/fixture digests and actual script identity plus executed/skipped/failed cases; (3) created-to-final-verdict critical path, with queued versus active job intervals separated; (4) complete started-job interval sum for **all** producer, consumer, coordinator and control jobs, plus available validated step spans with invalid spans explicitly counted; (5) cache/toolchain/runner-label differences and any infrastructure failure. Do not equate job intervals with billed CPU minutes, and do not compare different test populations. All thirteen cases must be genuinely executed in both arms; a skip, duplicate, missing terminal result, moved source or absent aggregate invalidates the pair. A red outcome remains red rather than being excluded from timing.

For a small permitted sample, alternate the arm order across **two independently repeated matched pairs**, permitting at most a third pair if the first two contradict. Never repeat merely to produce a desired direction; stop immediately on source drift, different effective test populations, missing timing evidence, or platform/runner restrictions. Report individual run values, median where appropriate, critical path and aggregate job intervals *separately*, along with uncertainty from queue/cache effects. The pilot's observed **695-second elapsed / 978-second summed job intervals** is a reference observation, not a benchmark control.

**Go/no-go:** leave fan-out manually available and the full bridge authoritative by default. Propose any automation or P4 hourly prompt amendment only after independent source/test review establishes equal coverage and a repeatable meaningful advantage in either wall time or started-job consumption without a reliability regression. Improvements in total job time cannot excuse a slower user-facing verdict without an explicit owner trade-off. Cross-PR frozen candidates remain behind the separate P1 source-admission restriction; no benchmark grants HP PR-code execution, H01–H07, art approval, 1/45 event or 1/12 gate credit.


## Prospective source-shell identity strengthening (engineering-only)

The historical November 6 receipt from run #42198617652 uses **group and aggregate schema 2** and is retained unchanged. A follow-up implementation adds prospective **schema 3** script-body SHA-256 identities to each of the thirteen already-owned source cases and their aggregate. These are calculated from the exact existing Bash commands extracted from the authoritative Windows bridge, then independently checked at receipt aggregation. A case-name match or newly recomputed receipt checksum alone must no longer conceal a changed original shell body. Synthetic unit negative controls cover missing, forged and changed-source script hashes, while keeping the 13 actual scripts, source producer, candidate binary, two Windows groups, artifact topology and release-credit boundary unchanged. At initial publication, schema 3 had no live Windows trial. The subsequent exact-source live trial and independent artifact readback are recorded below; historical schema-2 artifacts remain schema 2 and cannot be relabeled. This is a narrow precondition for later matched P2 comparisons, **not** a conventional same-test benchmark, an automatic workflow trigger or release qualification.


## Completed schema-3 hosted Windows proof and protected receipts (November 6)

**Code and qualification:** [PR #3213](https://github.com/gamesbyian/UR-Recomp/pull/3213), original head `9c8c3c97980bd8b187abc0789ded439e4a004e47`, later **merged into main** as `1b8b2878754af04bc513ac4b607ae96f291d367b`. The unchanged ready-state head passed [full tooling run #42270979715](https://github.com/gamesbyian/UR-Recomp/actions/runs/42270979715): four actual shards, **7,379 tests discovered, 149 skips, all four exits zero**. [Hygiene #42270979776](https://github.com/gamesbyian/UR-Recomp/actions/runs/42270979776) succeeded. Draft-targeted diagnostics independently passed the **25** focused fan-out unit tests. Neither draft skipping nor full-suite recorded skips were counted as executed cases.

**Actual Win32 trial:** [workflow #42271789814](https://github.com/gamesbyian/UR-Recomp/actions/runs/42271789814), manually dispatched on exactly the original PR-head SHA above; the four GitHub-hosted jobs all completed **success**, with source-bound aggregate schema `ur-win32-acceptance-fanout-aggregate/3`. The aggregate contains actual **13/13 passed** Windows script indices `0..12`, 13 distinct valid SHA-256 Bash-body identities, zero issues, zero failed cases, `transport_complete=true`, `release_gate_credit=0`, and `independent_physical_qa=false`. These facts apply to the **tested PR head**, not an asserted post-merge Windows rebuild on a different commit.

A separate read-only authenticated ZIP/JSON audit on the owner's HP independently verified the source-bound v3 aggregate, both group JSON receipts with their canonical SHA-256 self-checks, all 13 real case rows against the combined aggregate, producer `source-commit.txt`, all three hashes in producer `SHA256SUMS`, and the inner ROM-free ZIP CRC. It fetched the **exact source-head bridge workflow Git blob `734e521e6c5ab39d8163305e4505c11f7b7d2051`**, verified its Git blob object identity, and recomputed **13/13 original Bash-body hashes** from the authoritative source, matching the saved case receipts. The artifact audit executes **no game binary, PR source or downloaded script on the HP**. Digest matching and self-checks are not cryptographic signatures or a second execution of the Windows journeys; separate human/physical QA remains outstanding.

### Measured hosted workflow timing (not a matched A/B)

| Job | Started-to-completed interval | Real bounded step |
| --- | ---: | --- |
| Candidate / candidate, `windows-2022` | **405s** | Native compiler stage **102s** |
| Journeys / independent, `windows-2022` | **383s** | Ten-script step **345s** |
| Journeys / seed-dependent, `windows-2022` | **360s** | Three-script step **313s** |
| Aggregate, `ubuntu-latest` | **21s** | Source/case reconciliation |
| **Sum of complete started-job intervals** | **1,169s (19m29s)** | No CPU, billing or net-avoided-work claim |
| **Workflow created to updated (18:33:31–18:47:08 UTC)** | **817s (13m37s)** | Actual end-to-end verdict |

The first schema-2 trial's historical **695s elapsed / 978s job intervals** is retained above. The schema-3 run is **122s longer elapsed** and **191s greater in summed job intervals**, but its source epoch, compiler/cache/runner/queue conditions and receipt implementation differ. There is no equivalent same-SHA/same-test-set conventional arm. **No regression, speedup, avoided runner-minutes or cost saving can be causally inferred from these two observations.** No extra benchmark was launched.

### P7 preservation of the exact schema-3 artifacts

All **four** authenticated GitHub artifact ZIP bytes were re-downloaded into the already established, separately marked **NONRELEASE** `%USERPROFILE%\\Downloads\\UR-Recomp-Playtests\\Qualification-Evidence` folder, with the prefix `P2-NONRELEASE-v3-9c8c3c9-` and suffix `-run42271789814.zip`. Every outer SHA-256 matched the GitHub artifact metadata, all ZIP CRCs passed, and a different existing checksum would have prevented overwrite. The producer archive was inspected as data, **not extracted or executed**.

| Artifact | GitHub ID | Outer ZIP SHA-256 | GitHub expiry UTC |
| --- | --- | --- | --- |
| `producer` (13,034,111 bytes) | [#13530410991](https://github.com/gamesbyian/UR-Recomp/actions/runs/42271789814/artifacts/13530410991) | `b18c5e2784e2e4dc7c2ad62ede42e411991f89370dfd0d218d777bdc6ab3d820` | Nov 13, 18:40 |
| `independent` (2,473 bytes) | [#13532855897](https://github.com/gamesbyian/UR-Recomp/actions/runs/42271789814/artifacts/13532855897) | `7cccb9dcf5d4393ee423db042ff07d55935e7e5fb04356f6a1dfe47757ae2287` | Nov 20, 18:46 |
| `seed-dependent` (1,226 bytes) | [#13531432686](https://github.com/gamesbyian/UR-Recomp/actions/runs/42271789814/artifacts/13531432686) | `071e98105357079681648ba202a69156e62f2aa616eaad825d665c2bf5425d66` | Nov 20, 18:46 |
| `aggregate` (2,231 bytes) | [#13531357812](https://github.com/gamesbyian/UR-Recomp/actions/runs/42271789814/artifacts/13531357812) | `a8f82471f943940cc3f9cf94fffe1fc41e80d5687edb1da071ec61d9e423aa8b` | Nov 20, 18:47 |

**Decision:** preserve the verified v3 integration route as an opt-in hosted source-confidence tool, retain existing full Windows bridge and all release/physical gates, and do not make automatic PR batching or P4 five-task edits until an independently admitted full-tree P1 route and a genuine paired conventional P2 control establish worthwhile impact. Script-body SHA-256 binds each exact Bash body; it **does not** individually fingerprint every invoked Python probe or fixture, which remains protected by the full exact source SHA and separate binary/fixture/package identities. No additional heavyweight orchestration is warranted by this result.

## November 7 Practice course worker reliability and exploratory same-source comparison

**Purpose and boundary.** This is a deliberately narrow test of parallelizing the *ten already-required fresh native Practice course cases* inside the original Bash case #12, without changing its original shell body, original menus/course assertions, per-process user and work roots, one delayed Restart, or two paused-Options processes. [Source PR #3229](https://github.com/gamesbyian/UR-Recomp/pull/3229) remains **unmerged HOLD**. This is neither the complete conventional-vs-fan-out P2 control nor a production CI dispatch change; default worker count remains one.

**Fixed producer and actual source.** Both trial runs used the *same* already successful [Windows build-only #42319534390](https://github.com/gamesbyian/UR-Recomp/actions/runs/42319534390) from source `0362bbb57a66efe1690acf7e2dc3532b91329349`; it ran one 334-second started-job interval, was **not rebuilt** for either trial, and uploaded [artifact #13552457696](https://github.com/gamesbyian/UR-Recomp/actions/runs/42319534390/artifacts/13552457696) (13,034,006 bytes, outer SHA-256 `8f987e835c77907441354886e9872f9fb1fe3a082229392ebd4c2425d31ab7b8`, expiry Nov 14 00:44:56 UTC). Separately verified producer SHA256SUMS: original native EXE `1e77becd4b0a25cfe350304f27db89b5306d6327ecab94a6073b45d38726dc1b`, fixture `306d1647b2b95881331a2d28fafcaf4d447289e19cbdf030955f19e64457cb6f`, inner ROM-free ZIP `5f9cb6e4905c1c3483cf5f92c68764f9e0283bb2f756ba8495d8b7892354f7ce`. The owning original thirteen-script workflow is exact Git blob `734e521e6c5ab39d8163305e4505c11f7b7d2051`, independently compared to the preserved earlier schema-3 source-bound receipt. Source-head [full tooling #42319032603](https://github.com/gamesbyian/UR-Recomp/actions/runs/42319032603) passed **7,419 discovered/162 reported skips across four shards**, hygiene passed, and [real ready-head Windows bridge #42319032706](https://github.com/gamesbyian/UR-Recomp/actions/runs/42319032706) passed 13/13 with default worker one (Practice **386.8s**; different **single-run overlapping** topology).

**Both actual hosted manual fan-outs passed schema-3 aggregate 13/13, with zero issues, zero case failures, and zero physical/release credit.** The job log on the first hosted independent consumer explicitly recorded `UR_PRACTICE_CASE_WORKERS: 2`, versus `1` on the later control. The code at the frozen SHA reads that environment only for the original Practice Python probe. The six compact ZIP receipts were separately downloaded onto the HP **as data only**; their authenticated outer SHA256, ZIP CRCs, group canonical self-hashes, complete 13 indexed cases, exact original Bash-body SHA256 and shared candidate binary/fixture/source identities were independently rechecked. No PR code, Windows executable, ROM or owner profile ran on HP.

| Observed dimension | 2 workers, first [#42328663088](https://github.com/gamesbyian/UR-Recomp/actions/runs/42328663088) | 1 worker, later [#42329344326](https://github.com/gamesbyian/UR-Recomp/actions/runs/42329344326) |
| --- | ---: | ---: |
| Case #12, authentic Practice suite | **258.922s** | **338.829s** |
| Independent group case-step elapsed | **258.953s** | **338.860s** |
| Independent hosted job interval | **301s** | **385s** |
| Seed-dependent group case-step elapsed | **286.641s** | **247.781s** |
| Seed-dependent hosted job interval | **332s** | **294s** |
| Aggregate job interval | **17s** | **20s** |
| Sum of started-job intervals, excluding the shared producer | **650s** | **699s** |
| Created-to-final workflow verdict | **355s** | **412s** |
| Original 13 Bash cases, source/test identities | **13/13 pass** | **13/13 pass** |
| Release gate / independent physical credit | **0 / false** | **0 / false** |

**Source bytes protected on HP, never published as raw guest logs:** All six original individual artifacts and separate audit JSON files were stored in `%USERPROFILE%\\Downloads\\UR-Recomp-Playtests\\Qualification-Evidence` with distinct `P2-NONRELEASE-workers2-0362bbb57a66-*` and `P2-NONRELEASE-workers1-0362bbb57a66-*` filenames, no overwrite or game execution. GitHub outer artifact SHA-256 values:

| Receipt | 2-worker SHA-256 (expires Nov 21) | 1-worker SHA-256 (expires Nov 21) |
| --- | --- | --- |
| Independent | `f8f472633660fb9e3fe070a9f19b3ce286a87396df479ccd4d68efe13e818f27` | `549c2d9b94b8767fa4b14e506b24bfa0c8fa3026a08b81888fd7188fd4a61804` |
| Seed-dependent | `4b92a5b5c657e7c8b6835d6179078eb78c026e5fe1f03a54514400d5eac17700` | `d61b471da999de72fbd01ccedbddbe3ec721066df7aa5d8d29ff2eb361a00321` |
| Aggregate | `a2645537e2c77c23b78834498d899f90d3fdd73c73090e3aa319c57aed0f6e09` | `a8741fdb905e16fd94518b8e4337de3e1d9c36624905a20864c660ef18c4237a` |

**Interpretation and stop decision.** Practice case #12 was **79.907s (23.6%) shorter as observed** with two workers on frozen source; the independent Windows job was 84s shorter, while the unchanged seed group was **38s slower** in that arm. The net started-job interval sum was 49s smaller, and end-to-end workflow verdict was 57s sooner in the two-worker run, but these are **observations from one order (parallel then serial)** rather than the pre-registered counterbalanced formal sequence. Different hosted VMs, system contention and queue/cache variability are not removed; no valid billed-dollar, causal avoided-minute, conventional vs fan-out test equivalence or release progress claim follows. The two-worker fan-out's consumer critical path moved to the 332-second seed-dependent group; further Practice-only optimization would not shorten that measured consumer phase.

No further benchmarking merely for a prettier speed number. Before source PR #3229 is merged, require an *independent agent* to inspect per-process Windows/SDL focus behavior, failure paths, preservation of original menu/save tests, and whether the **selected worker mode must be source-attested in the self-contained receipt**. Current schema-3 receipts bind original Bash bodies and hashes of private output, but do not themselves contain the verified worker mode; the hosted job logs plus frozen code establish what was requested for this experimental observation. A stronger standalone mode receipt would require a separately reviewed source/schema change and requalification, not post hoc decoration. **Keep all release, P1, P4, HP trust and physical QA gates unchanged.**


## November 7 schema-4 original Practice execution-mode provenance qualification

**Scope and source authorization:** The earlier exact-SHA schema-3 2→1 comparison above is frozen historical evidence and remains **neither a matched conventional-vs-fan-out P2 control nor a proven causal saving**. A new [held/draft implementation #3229](https://github.com/gamesbyian/UR-Recomp/pull/3229) at `4701b6a5a254603e02d413d6b89274edca5b51fb` changes the *existing* manual fan-out's receipt contract to `ur-win32-acceptance-fanout/4` and `ur-win32-acceptance-fanout-aggregate/4`, **not** any of its thirteen original Bash scripts, automatic event triggers or shipping gates. It requires source-confirmed selection 1/2 in both Windows consumer groups, forces the seed-dependent group's effective Practice workers to 1, and reads the independent group's original case #12 completed private `report.json`. The source validates selected/reported worker count, exactly ten original menu-qualified cases in original order, same GITHUB_SHA/EXE/USA ROM digest, original clean tier-2 seed, delayed Restart, two paused-Options modes, unchanged saved SRAM/no `.urrun`, no release or physical-pad credit. The compact receipts disclose only selected/reported workers, report case count and its 64-hex SHA-256 digest, never the private report or guest logs. Missing/redirected/tampered/mismatched reports fail closed; a genuine failed case #12 may still preserve a red group receipt without falsely claiming a successful Practice report. Old schema-3 receipts explicitly fail the new schema validation.

**Checks on the exact source:** [focused draft #42345817966](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345817966) **98 directly changed tests passed**, including negative controls for mismatched worker selection, source SHA, EXE, clean seed, missing/redirected/private reports, course inventory and recomputed but contradictory group digest. [Hygiene #42345817936](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345817936) **PASS**. [Manual complete four-shard tooling #42345921135](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345921135) passed **7,425 discovered, 162 recorded skips**, shard exits all zero. This is more than mock success: [actual GitHub-hosted Windows fan-out #42345926890](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345926890), from the exact frozen head, completed **SUCCESS** on **one candidate-build producer plus both actual consumer groups and the aggregate**. All **13 original scripts exited 0** and their Bash-body SHA-256s equal the previously audited source Git blob `734e521e6c5ab39d8163305e4505c11f7b7d2051`. Both group receipts requested worker mode **2**, the independent original Practice `report.json` reported/executed **2**, and the aggregate agrees. Original Practice case #12 took **261.734s**, with the native ten-course, Restart, two paused-Options and source/save assertions unchanged. Actual original Practice report SHA-256 **`e8bbe694f788766e543abe34e9b710bd8a52177e82612595b375de7355fd1193`** is recorded inside the source-bound independent and aggregate receipts.

| Actual schema-4 run element | Hosted started-job interval | Result |
| --- | ---: | --- |
| Candidate / candidate, `windows-2022` | **224s** | One source-pinned successful genuine Win32 build |
| Journeys / independent, `windows-2022` | **301s** | Ten original independent scripts pass; Practice worker mode 2, 261.734s |
| Journeys / seed-dependent, `windows-2022` | **333s** | Three original dependent scripts pass; no false Practice execution claim |
| Aggregate, `ubuntu-latest` | **15s** | Version-4 source/mode/case reconciliation successful |
| **Sum of started-job intervals** | **873s** | Not CPU, billed time or avoided cost |
| **Created-to-updated verdict** | **580s** | Includes newly rebuilt 224s candidate; not comparable with reused-producer 1/2 timing |

**Independently byte-preserved non-release evidence:** GitHub's authenticated actual ZIP metadata, outer SHA-256/byte counts and CRC, producer `source-commit.txt`, three GNU binary-mode `SHA256SUMS` entries, nested ROM-free ZIP CRC, both v4 group receipts' canonical self-digests, group-mode agreement and complete 13-case aggregate reconciliation were recomputed **as data only on the owner's HP**. Four ZIPs plus audit JSON were preserved under `%USERPROFILE%\\Downloads\\UR-Recomp-Playtests\\Qualification-Evidence\\P2-NONRELEASE-v4-PR3229-4701b6a5a254-*`, without extracting or executing any unmerged game or source. **Exact digest evidence:**

| Actual artifact | GitHub ID | Outer SHA-256 |
| --- | --- | --- |
| Five-entry source-pinned producer, 13,033,969 bytes | [#13563633138](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345926890/artifacts/13563633138) | `addded5b9c51f5061c79f6a768e4217b5b5d82423b2ec896046340ebb6995966` |
| Independent v4 group | [#13563449033](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345926890/artifacts/13563449033) | `5ee308b7ce9ee3045d8e2bdc3cd635c1a9dcdf83e842f28e99e4324c9a86c05d` |
| Seed-dependent v4 group | [#13563951236](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345926890/artifacts/13563951236) | `b359acdb599acb325972ef561d1b1df20299538b0f59e414d58cc29487c1bd9f` |
| Combined v4 aggregate | [#13563444324](https://github.com/gamesbyian/UR-Recomp/actions/runs/42345926890/artifacts/13563444324) | `9cb56e1727aab34835f94aac15c007cff13486933139bad36c7394ed69bddc1f` |

Source-bound producer internal SHA-256: original EXE `ef330e6739c80c9faf935a027ce4bd3a3f4af6edb08cd9704a3a3f4c0292dcff`, fixture `28ff077bc0b2ae5580b234b2413c5d3f67acec4aab6af1e5a2b05fb0e28a0154`, ROM-free ZIP `02c77f7bcc5a71f2fe09a0a38a5eaa9e8af828965d53e263c68d240fa94f6b7b`. **Evidentiary limitation:** the ephemeral private original Practice report bytes themselves are not published or retained; the source-frozen hosted **independent Windows consumer** validated the report and published its SHA-256, while the independent archive audit can verify that recorded digest's presence, type and agreement but **cannot recompute it from raw unpublished source bytes**. A self-checking receipt is not a signature or an external physical test.

**Disposition:** The targeted worker-mode provenance gap is closed by this actual hosted **schema-4 experimental implementation**, with all original acceptance assertions and source identity preserved. The underlying observed 2-vs-1 time difference remains exploratory and may reflect Windows VM/queue contention; the schema-4 run is **not** a new comparator or proof of speedup. [PR #3229](https://github.com/gamesbyian/UR-Recomp/pull/3229) remains **DRAFT/HOLD/UNMERGED**, pending a **distinct source reviewer** to inspect Windows SDL concurrency/focus, real-failure receipt semantics, mode tampering, main source drift and whether this modest benefit warrants adoption. No automatic trigger, installed P4 agent prompt, P1 composite admission, HP trust privilege, release-gate credit, physical controller acceptance, 0/12 or 0/45 change. Do not run more benchmark pairs merely to make the improvement look larger.
