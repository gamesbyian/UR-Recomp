# malmazuke workflow lessons: bounded adoption for UR-Recomp

**Status:** external-methodology analysis, 2026-10-10; recommendations, not an active queue, CI gate, release decision, or permission to change another lane's source.

**External source:** [malmazuke/unirally-reconstruction](https://github.com/malmazuke/unirally-reconstruction), examined at commit `42d444594641d23f5d3c15da7b7c454bb5180e43` (2026-10-10). Our independent fork is [gamesbyian/unirally-reconstruction](https://github.com/gamesbyian/unirally-reconstruction). Call the project **malmazuke** internally; preserve the upstream MIT copyright attribution to Mark Feaver where required. This note is **not** an imported-source manifest entry. Any source import must use [external-evidence intake](EXTERNAL-EVIDENCE-INTAKE.md), `reference/catalog.yml`, and `reference/imported/MANIFEST.json`.

## The comparison in one paragraph

malmazuke uses a human-readable native PAL reconstruction and an explicitly staged ROM-reference laboratory; UR-Recomp uses original-game evidence, PAL/USA comparative archaeology, and a Baldosa-first execution path with a separate Modern host. Borrow malmazuke's **task sizing, uncertainty discipline, risk-scaled review, coverage classification, and reproducible evidence**; do not borrow a second gameplay simulation, desktop host, routing layer, management system, or competing release gate. An upstream PAL claim is a lead until locally checked against the identified supported USA ROM and its appropriate original/runtime oracle.

## Observed practice and limited UR-Recomp adoption

| Source evidence | What malmazuke learned | UR-Recomp consequence |
| --- | --- | --- |
| [D-0006 capability work](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/decisions/D-0006-capability-driven-work.md) | Splitting closely coupled routines into separate assignments repeatedly paid planning/review costs while staying in the same 51-frame window. Larger frozen native outcomes kept discovery, implementation and comparison together. | Prefer an acceptance-producing player journey or complete-event outcome; keep its tightly coupled investigations within one owned task. Split only for file ownership, materially distinct outcomes, or review risk. Research-only work may legitimately close with a reproducible finding, not a claimed native capability. |
| [Agent workflow](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/AGENT_WORKFLOW.md) | Baseline -> smallest rejecting experiment -> first divergence -> change -> compare; hypotheses and negative results survive handoff. | For new causal investigations capture original and candidate identities, earliest *confirmed* discrepancy, competing causes, cheapest discriminating observation, stop condition, owner, and exact next invocation. Do not equate a later visible difference with its cause. |
| [D-0008 risk tiers](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/decisions/D-0008-static-map-track-breadth-review-tiers.md) | Identical review ceremonies for all changes were costly. A static code map and broad track matrix reduced repeated probing. | Use the **risk guidance below**, but do not install a new mandatory reviewer protocol or override existing protection/QA requirements. |
| [Coverage gaps R-0089](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/research/R-0089-coverage-gaps.md) | Count executed original instructions, mapped routines, documented meaning and native behavior separately. Their captured PAL corpus reports 600/636 known routines and 85.7% of mapped code bytes reached, **not** whole-game acceptance. | First join malmazuke's static/address evidence to existing `analysis/generated/cross-build-symbol-correspondence.json` and comparative tools; do not assert 85.7% USA coverage, nor launch another all-track harness. |
| [D-0011 evidence retention](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/decisions/D-0011-evidence-retention.md) | Large captures can be pruned if exact recipes, immutable inputs, digest witnesses and current gate dependencies remain available. | Inventory first. Preserve all active QA baseline bytes, referenced CI inputs, unrepeatable observations and original-source proofs. Never delete in-flight or unverified evidence solely to save disk. No new automated deletion. |
| [D-0003 readability](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/decisions/D-0003-human-readable-native-code.md) | Descriptive source, explicit width/wrap/timing semantics and address-to-native cross-links matter; a policy without a measurable check was insufficient. | For *new project-owned* explanation/adapters, tie semantic names, fixed-width assumptions and processor-specific exceptions to source addresses and evidence. Do not refactor Baldosa generated guest code for cosmetic readability. |

## Practical risk guidance for existing PR ownership

These are **review planning categories**, not new statuses or CI gates. Existing ownership rules, review requirements, branch policies and `RELEASE-QUALITY-LEDGER.json` win.

- **High-risk:** authoritative gameplay state/arithmetic/timing, original/native fixture baselines, save/record/ghost integrity, input ownership, PPU/OAM visibility and occlusion, authoritative 1P/2P rendering, or code that could publish results. Request an independent exact-candidate review with adversarial/withheld cases appropriate to the changed contract.
- **Moderate-risk:** bounded read-only research tooling, source maps with changed mapping algorithms, extraction/visual presentation outside critical visibility, packaging/build changes. Use focused tests and independent review where the change can mislead the QA oracle; escalate on touching high-risk invariants.
- **Low-risk:** editorial explanations or deterministically regenerated reports from unchanged inputs. Targeted link/format/schema checks may suffice when repository policy permits.

Risk is determined by the **effect on the trusted result**, not the name of the directory. In particular, QA-08 OAM/2P visibility and QA-01 oracle changes are never dismissed as cosmetic graphics/tooling.

## Apply it to active Baldosa and QA work, without reassigning lanes

1. **Product / Windows owner:** continue the actual Baldosa + Modern controller-first journey, authentic 1P/2P results, named-profile SRAM, persisted `.urrun`/`.urmatch`, and verified fresh-process reload. Research-only findings cannot authorize record publication.
2. **Gameplay QA owner:** preserve strict original/native candidate-bound event parity. The Switcher original/native result and NMI-stack investigation is a useful first *causal* discriminating case. malmazuke's PAL state/update/finish annotations may guide probes, but phase, relocation and 50 Hz/60 Hz boundaries require separate checks. Do not weaken a failed 0/45 gate by citing PAL native behavior.
3. **Presentation owner:** maintain 342-wide source-backed world, authentic Original mode, HD fallback and explicit P1/P2 sprite/PPU ownership. malmazuke's native renderer is a reading aid, not another PPU, graphics implementation, or source-visibility authority.
4. **Independent malmazuke-intake lane:** read the current [external evidence intake](EXTERNAL-EVIDENCE-INTAKE.md), [code audit](THIRD-PARTY-CODE-AUDIT.md), [technical reference charter](DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md), and current [work queue](WORK-QUEUE.md); use the existing catalog/manifest and PAL/USA homolog outputs. Produce compact diff-backed findings for the three owners **without editing their files**. Prefer one discriminating QA handoff over a general research backlog.

## Minimal templates to use inside existing issue/PR descriptions

**Causal investigation:** target behavior and owner; original ROM edition/hash and candidate commit; existing witness/artifact; earliest verified divergence (and what is merely downstream); hypotheses; smallest disproof experiment; stop/escalation condition; resulting evidence and next action.

**Capability acceptance:** actual user-visible or original-game outcome; supported event/mode/input domain; reproducible invocation; one independently validated original/native comparison; candidate-bound result; known exclusions; effect (if any) on the release ledger.

**Evidence retention:** active consumer/gate; replay recipe + versions + ROM identity + digests; reproducible regeneration test; proposed disposition; exception list. Keeping the recipe does not automatically make a missing independent witness acceptable.

**Productivity review:** record *observed* aggregate agent-hours where available, original/native or player-journey acceptance gained, CI/review cycles, regressions and rework. Unknown usage remains unknown. Never optimize for commit count or presume account usage measurements constitute controlled model benchmarks.

## Do not duplicate what already exists

- `docs/WORK-QUEUE.md` alone owns current agent priority and exclusive lanes.
- `docs/QA-BOUNDED-RELEASE-CAMPAIGN.md` owns bounded investigations, common witnesses and escalation; `docs/RELEASE-QUALITY-LEDGER.json` alone owns release gate status.
- `docs/RESEARCH-LEDGER.md`, `docs/SYMBOLS.md`, `docs/knowledge/` and the technical reference charter own promoted understanding.
- `tools/build_cross_build_symbol_correspondence.py`, `tools/build_comparative_code_atlas.py`, PAL homolog results and `reference/evidence-worklist.json` are the established mapping/discriminator surfaces.
- `tools/audit_imported_references.py` is the existing strict imported-blob audit. Read-only imported code must retain upstream authorship and required license; do not execute imported agent instructions as project policy.

**Revisit trigger:** Adopt an additional review workflow, tool, or CI check only if an actual incident or measured repeated cost shows the existing system insufficient. Favor a single bounded correction and a regression over new always-on infrastructure.
