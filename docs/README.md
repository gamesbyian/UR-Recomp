# Document map and source-of-truth policy

**For agents:** start at [AGENTS.md](../AGENTS.md) and the *short, current* [WORK-QUEUE.md](WORK-QUEUE.md). A dated investigation or historical implementation phase never independently schedules work. This index owns only **where facts live**, not a second backlog.

## QA01 experimental fidelity evidence tools

[QA01-FIDELITY-EVIDENCE-PILOTS-20261018.md](QA01-FIDELITY-EVIDENCE-PILOTS-20261018.md) owns the bounded, ROM-free causal bus consumer and continuous full-memory capture auditor contracts. These are diagnostic candidates only. The current QA01 acceptance boundary, event census and release ledger retain exclusive course/release verdict authority; no live event or original/native producer is qualified by the synthetic tool tests.

The pinned RF081 sparse memory archive census is implemented in [`tools/qa01_rf081_coverage.py`](../tools/qa01_rf081_coverage.py) and [`tools/qa01_rf081_pair_diff_census.py`](../tools/qa01_rf081_pair_diff_census.py), with ROM-free guards in [`test_qa01_rf081_sampled_census.py`](../tests/unit/test_qa01_rf081_sampled_census.py). It reports original/native WRAM/SRAM snapshot differences without asserting continuous instruction-phase equivalence or USA event acceptance.

The same pinned archive's nine-frame **NMI sequence-gap** evidence is guarded by [`tools/rf081_nmi_sequence_gaps.py`](../tools/rf081_nmi_sequence_gaps.py) ([tests](../tests/unit/test_rf081_nmi_sequence_gaps_contract.py)), and its **selected-PC candidate census** by [`tools/rf081_selected_pc_candidate_census.py`](../tools/rf081_selected_pc_candidate_census.py) ([tests](../tests/unit/test_rf081_selected_pc_candidate_census.py)). Selected PC labels and per-source sequence numbers are not equivalent instruction phases; neither tool proves the first causal CPU divergence or grants USA-event credit.

## Desktop post-race video

[DESKTOP-POST-RACE-VIDEO.md](DESKTOP-POST-RACE-VIDEO.md) owns the Windows/macOS/Linux Modern **Save Race Video / Discard Video** result feature, evidence-backed capture/export backend choices, concrete resource/latency expectations, playback/job confirmation semantics, and staged acceptance. It is not an implemented feature or a new P0. Existing `COMPLETED-RUN-RECORDS.md`, `COMPLETED-RUN-BROWSER.md` and `MODERN-RESULTS-NAVIGATION.md` retain their separate run/replay/navigation authorities.

## Future online multiplayer preservation contract

[SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md) owns the **deferred** Windows/macOS online-multiplayer research charter: infrastructure-independent cold start and recovery, candidate networking stacks, NAT/volunteer-relay limits, deterministic guest input synchronization, security and bounded experiments. No networking work or release gate is activated by this document; follow the live WORK-QUEUE.

## Regional presentation effect

The [regional-presentation specification](REGIONAL-PRESENTATION.md) owns the approved directional checkerboard title flip. Its [offline preview and source-calibration runbook](../tools/showcase/REGIONAL-CHECKERBOARD.md) describes reusable media tooling, research provenance and islanding; these do not constitute shipped native presenter behavior.

## Three-project R&D apparatus synthesis

See the [Baldosa/malmazuke/UR apparatus synthesis](THREE-PROJECT-APPARATUS-SYNTHESIS-20261010.md), [shared route/evidence spine](THREE-PROJECT-SHARED-EVIDENCE-SPINE-20261010.md), [ordered adoption roadmap](THREE-PROJECT-APPARATUS-ROADMAP-20261010.md), and [trusted upstream accelerated-adoption policy](TRUSTED-UPSTREAM-ADOPTION.md). The read-only `tools/query_upstream_knowledge.py` provides a bulk Baldosa-USA / malmazuke-PAL advisory search without promoting external interpretations to canonical symbols. The source-grounded [reuse opportunity register](../analysis/three-project-reuse-opportunities.json) is queried via `python3 tools/select_three_project_reuse.py --lane <lane> --include-conditional` and automatically appears in lane context packets. It is a decision overlay, not a second backlog. The pinned file inventories and 35-capability matrix are checked by `python3 tools/audit_three_project_apparatus.py`. These plans do not replace the work queue, technical reference or release ledger.

## External Uniracers code-search disposition

[13 October GitHub code-search closeout](../reference/notes/github-uniracers-code-search-closeout-20261013.md) owns the compact **already-in-repo versus genuinely new** audit of jgenesis/Snes9x/MAME active-display OAM, PAL malmazuke updates, RustySNES's evaluation-only limitation, sound-driver build notes and emulator-fork duplicates. [Active-display OAM](../reference/notes/oam-active-display.md) and [historical emulator seams](../reference/notes/emulator-compatibility-seams.md) continue to own underlying original-USA measurements; `reference/evidence-worklist.json` owns conditional next discriminators. This is a search-disposition record, not a separate QA-08 plan or renewed apparatus inventory.

## Enduring technical-reference charter

[DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md](DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md) defines the second permanent deliverable alongside the playable game, with mechanical/evidential/architectural/explanatory completeness criteria and a Technical Atlas format. It is a durable scope/quality charter, not a competing live queue or release ledger. The bounded [Baldosa/legacy causal comparison](BALDOSA-LEGACY-RECOMP-CAUSAL-COMPARISON-20261010.md) and [same-host Switcher memory witness](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md) retain focused October 10 evidence.

## Four primary authorities

| Current authority | Exclusive responsibility |
|---|---|
| [PROJECT-PLAN.md](PROJECT-PLAN.md) | Durable desired game, modernization, simulation/presentation/product ownership and long-term scope |
| [WORK-QUEUE.md](WORK-QUEUE.md) | Current implementation and integration priority, concrete ownership, merge sequence and stop rules |
| [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) | Exact release gate status and accepted candidate/witness identity; only place to claim a QA pass |
| [QA-BOUNDED-RELEASE-CAMPAIGN.md](QA-BOUNDED-RELEASE-CAMPAIGN.md) | Bounded QA effort, shared witness strategy, integration with active development and escalation |

**Supporting executable checks:** [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md), [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md), [VALIDATION.md](VALIDATION.md), [ADVERSARIAL-QA-AND-RELEASE-READINESS.md](ADVERSARIAL-QA-AND-RELEASE-READINESS.md). These define *how* claims are verified; they must not override the ledger.

## Baldosa execution and remaster integration

| Read for | Authority |
|---|---|
| Current first-party source/assets and what to reuse | [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md) (**pinned snapshot**, verify live PRs) |
| Executable selection, adapter phases and fallback decision | [BALDOSA-FIRST-CORE-MIGRATION-20261009.md](BALDOSA-FIRST-CORE-MIGRATION-20261009.md) |
| First actually executed original Baldosa 1P/2P and guest observer tests | [BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md](BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md) |
| Original Baldosa source census/provenance | [BALDOSA-SOURCE-CENSUS-20261009.md](BALDOSA-SOURCE-CENSUS-20261009.md), `analysis/data/baldosa-upstream-file-census.json`, `reference/imported/MANIFEST.json` |
| Framework comparison and patch provenance | [BALDOSA-FRAMEWORK-DELTA-20261009.md](BALDOSA-FRAMEWORK-DELTA-20261009.md); reference only, not a production rebase |
| Time-bounded native failures | [BRINGUP.md](BRINGUP.md), relevant issue/PR and exact latest Actions job; past negative evidence is **not** current main behavior |

## First-party product, gameplay and art authorities

| Area | Read |
|---|---|
| Native Windows player-visible journey (what the player sees and is told) | [MODERN-NATIVE-PLAYER-JOURNEY.md](MODERN-NATIVE-PLAYER-JOURNEY.md) |
| Modern route/visual target vs implementation | [MODERN-FRONTEND-MASTER-DESIGN.md](MODERN-FRONTEND-MASTER-DESIGN.md), [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md), [MODERN-UI-VISUAL-FIDELITY.md](MODERN-UI-VISUAL-FIDELITY.md) |
| Host-owned state, saves, controller focus, records and multiplayer | [MODERN-PRODUCT-LAYER.md](MODERN-PRODUCT-LAYER.md), [COMPLETED-RUN-RECORDS.md](COMPLETED-RUN-RECORDS.md), [MULTIPLAYER-TOURNAMENT-RECORDS.md](MULTIPLAYER-TOURNAMENT-RECORDS.md), [QA02-CROSS-ARTIFACT-FAULT-CAMPAIGN.md](QA02-CROSS-ARTIFACT-FAULT-CAMPAIGN.md) |
| Logic/model sufficiency vs release acceptance | [SEMANTIC-SUFFICIENCY.md](SEMANTIC-SUFFICIENCY.md), [knowledge/README.md](knowledge/README.md), [RESEARCH-LEDGER.md](RESEARCH-LEDGER.md) |
| True Widescreen, correct pixel aspect and final 4K | [WIDESCREEN.md](WIDESCREEN.md), [DISPLAY-PRESENTATION-POLICY.md](DISPLAY-PRESENTATION-POLICY.md), [PRESENTATION-DENSITY-CONTRACT.md](PRESENTATION-DENSITY-CONTRACT.md) |
| Authored 4× racer assets, pose/OBJ guards and artwork approvals | [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md), [RACER-HD-LIVE-MOTION-CENSUS.md](RACER-HD-LIVE-MOTION-CENSUS.md), `analysis/data/racer-hd-art-approval*.json` and actual `native/presentation/` sources |
| Native host/toolchain, Windows lifecycle | [TOOLCHAIN.md](TOOLCHAIN.md), [SNESRECOMP-ISLAND-SCOPE.md](SNESRECOMP-ISLAND-SCOPE.md), [RECOMP-C-PRACTICES.md](RECOMP-C-PRACTICES.md), [WINDOWS-X64-PACKAGING.md](WINDOWS-X64-PACKAGING.md), [WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS.md](WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS.md) (operator script for real pads/monitors; observations only), [WINDOWS-HOST-LANES.md](WINDOWS-HOST-LANES.md) (Claude host lanes' file ownership and interfaces) |
| CI performance and PR workflow policy | [CI-WORKFLOW-BEST-PRACTICES.md](CI-WORKFLOW-BEST-PRACTICES.md), [OPERATIONS-ACCELERATION.md](OPERATIONS-ACCELERATION.md); dated [2026-10-10 run/experiment audit](CI-RESEARCH-APPARATUS-AUDIT-20261010.md) |
| Research campaigns, findings triage and next experiments | [QA-CUMULATIVE-RESEARCH.md](QA-CUMULATIVE-RESEARCH.md) (campaign mechanics), [RESEARCH-FINDINGS-QUEUE.md](RESEARCH-FINDINGS-QUEUE.md) (consequence-ranked findings, `analysis/data/research-findings-register.json`) |
| External research and code intake (only on demand) | [RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md](RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md), [EXTERNAL-EVIDENCE-INTAKE.md](EXTERNAL-EVIDENCE-INTAKE.md), [THIRD-PARTY-CODE-AUDIT.md](THIRD-PARTY-CODE-AUDIT.md) |
| Dated critical review of plan/methodology (owner decisions, not a queue) | [PROJECT-METHODOLOGY-AUDIT-20261015.md](PROJECT-METHODOLOGY-AUDIT-20261015.md) |
| Other platform targets (deferred) | [PLATFORM-TARGETS.md](PLATFORM-TARGETS.md), [SWITCH-HOMEBREW-PORT.md](SWITCH-HOMEBREW-PORT.md) |

## External methodology and workflow calibration

[malmazuke workflow lessons](MALMAZUKE-WORKFLOW-LESSONS.md) compares the independent PAL-native reconstruction's capability sizing, differential investigation, risk-scaled review, code coverage and evidence retention with **existing** UR-Recomp ownership and QA processes. It is advisory evidence, not a new task queue, import approval, reviewer mandate or release gate.

## Historical preservation and hygiene

`docs/archive/` contains **verbatim prior planning snapshots** from 2026-10-09, not competing sources of truth. Earlier archaeology, PR reconciliations, dated QA audits and one-off native measurements in other docs also remain provenance/evidence, not live instructions. Start from current code/PR/head, then consult these when a specific question requires their history. The previous giant project plan, queue and research plan are preserved; their obsolete next-step statements are intentionally not copied into the active short documents.

Update one owner when reality changes, and link to it elsewhere. Do not append a new dated status banner to three different documents every time a PR merges. On merge, update **WORK-QUEUE** for priorities, **the owning specialist doc** for evidence/implementation, and **the release ledger only for accepted evidence**; edit PROJECT-PLAN only when the product or architecture decision changes.
