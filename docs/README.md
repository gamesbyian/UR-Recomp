# Document map and source-of-truth policy

**For agents:** start at [AGENTS.md](../AGENTS.md) and the *short, current* [WORK-QUEUE.md](WORK-QUEUE.md). A dated investigation or historical implementation phase never independently schedules work. This index owns only **where facts live**, not a second backlog.

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
| Modern route/visual target vs implementation | [MODERN-FRONTEND-MASTER-DESIGN.md](MODERN-FRONTEND-MASTER-DESIGN.md), [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md), [MODERN-UI-VISUAL-FIDELITY.md](MODERN-UI-VISUAL-FIDELITY.md) |
| Host-owned state, saves, controller focus, records and multiplayer | [MODERN-PRODUCT-LAYER.md](MODERN-PRODUCT-LAYER.md), [COMPLETED-RUN-RECORDS.md](COMPLETED-RUN-RECORDS.md), [MULTIPLAYER-TOURNAMENT-RECORDS.md](MULTIPLAYER-TOURNAMENT-RECORDS.md), [QA02-CROSS-ARTIFACT-FAULT-CAMPAIGN.md](QA02-CROSS-ARTIFACT-FAULT-CAMPAIGN.md) |
| Logic/model sufficiency vs release acceptance | [SEMANTIC-SUFFICIENCY.md](SEMANTIC-SUFFICIENCY.md), [knowledge/README.md](knowledge/README.md), [RESEARCH-LEDGER.md](RESEARCH-LEDGER.md) |
| True Widescreen, correct pixel aspect and final 4K | [WIDESCREEN.md](WIDESCREEN.md), [DISPLAY-PRESENTATION-POLICY.md](DISPLAY-PRESENTATION-POLICY.md), [PRESENTATION-DENSITY-CONTRACT.md](PRESENTATION-DENSITY-CONTRACT.md) |
| Authored 4× racer assets, pose/OBJ guards and artwork approvals | [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md), [RACER-HD-LIVE-MOTION-CENSUS.md](RACER-HD-LIVE-MOTION-CENSUS.md), `analysis/data/racer-hd-art-approval*.json` and actual `native/presentation/` sources |
| Native host/toolchain, Windows lifecycle | [TOOLCHAIN.md](TOOLCHAIN.md), [SNESRECOMP-ISLAND-SCOPE.md](SNESRECOMP-ISLAND-SCOPE.md), [RECOMP-C-PRACTICES.md](RECOMP-C-PRACTICES.md), [WINDOWS-X64-PACKAGING.md](WINDOWS-X64-PACKAGING.md) |
| CI performance and PR workflow policy | [CI-WORKFLOW-BEST-PRACTICES.md](CI-WORKFLOW-BEST-PRACTICES.md), [OPERATIONS-ACCELERATION.md](OPERATIONS-ACCELERATION.md) |
| External research and code intake (only on demand) | [RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md](RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md), [EXTERNAL-EVIDENCE-INTAKE.md](EXTERNAL-EVIDENCE-INTAKE.md), [THIRD-PARTY-CODE-AUDIT.md](THIRD-PARTY-CODE-AUDIT.md) |
| Other platform targets (deferred) | [PLATFORM-TARGETS.md](PLATFORM-TARGETS.md), [SWITCH-HOMEBREW-PORT.md](SWITCH-HOMEBREW-PORT.md) |

## External methodology and workflow calibration

[malmazuke workflow lessons](MALMAZUKE-WORKFLOW-LESSONS.md) compares the independent PAL-native reconstruction's capability sizing, differential investigation, risk-scaled review, code coverage and evidence retention with **existing** UR-Recomp ownership and QA processes. It is advisory evidence, not a new task queue, import approval, reviewer mandate or release gate.

## Historical preservation and hygiene

`docs/archive/` contains **verbatim prior planning snapshots** from 2026-10-09, not competing sources of truth. Earlier archaeology, PR reconciliations, dated QA audits and one-off native measurements in other docs also remain provenance/evidence, not live instructions. Start from current code/PR/head, then consult these when a specific question requires their history. The previous giant project plan, queue and research plan are preserved; their obsolete next-step statements are intentionally not copied into the active short documents.

Update one owner when reality changes, and link to it elsewhere. Do not append a new dated status banner to three different documents every time a PR merges. On merge, update **WORK-QUEUE** for priorities, **the owning specialist doc** for evidence/implementation, and **the release ledger only for accepted evidence**; edit PROJECT-PLAN only when the product or architecture decision changes.
