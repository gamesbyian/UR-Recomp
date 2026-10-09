# Resource collection and development research: bounded support

**Status (2026-10-09):** **Support only for a named Baldosa incorporation or adversarial-QA blocker.** This file owns *when to obtain external information*, not project priority or product architecture. Those are [WORK-QUEUE.md](WORK-QUEUE.md) and [PROJECT-PLAN.md](PROJECT-PLAN.md). The complete prior historical resource-hunting and multi-analyzer plan is preserved in [archive/RESOURCE-RESEARCH-PLAN-THROUGH-20261009.md](archive/RESOURCE-RESEARCH-PLAN-THROUGH-20261009.md); its dated priority ladder is not current.

## Intake state and reuse

- Baldosa's pinned repo has already been exhaustively inventoried (210 Git entries, 85 retained useful maintained inputs) in [BALDOSA-SOURCE-CENSUS-20261009.md](BALDOSA-SOURCE-CENSUS-20261009.md) and [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md). Do not duplicate generated C, restart source acquisition, or mistake upstream tests for accepted full events.
- The archive includes Nitrodon maps/disassembly/trace notes, Dessyreqt maps, Snes9x/SMV/TAS bot leads, multiple ROMs, RNC course data, sprite/OAM and audio references; source catalog: `reference/catalog.yml`, `reference/imported/MANIFEST.json`, `docs/RESEARCH-LEDGER.md`. Check existing evidence **before outreach or web search**.
- Historical original Snes9x Zoom Zoo and scored Bowl playthroughs are especially useful *input sources* for the existing QA-01/07 transplant, not native result acceptance. The 45-course identity and paired-event denominator remain with [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md).
- Existing ROM/prototype homolog, M/X variant, graphics atlas, APU/SPC and source-preparation studies are retained and accessible on demand. They need not all be complete to ship a correct host Modern front end.

## Research trigger and stopping rule

For every new archaeology/tool/source request, name (1) the exact Windows gameplay, visible presentation, guest/host compatibility or data-integrity decision it unblocks, (2) the hypothesis and cheapest discriminator, (3) the existing test or source owner, and (4) the stopping condition. Prefer reuse of a proven upstream routine or a one-run breakpoint/PPU/state observation. If an experiment finds a defect, fix it at the owning layer and add the smallest regression to existing scripts. If results do not alter the integration/QA decision, stop and document that negative in the specialist evidence file.

Never launch an independent broad disassembly campaign, multiplayer network stack, source download sweep, extra generalized QA system or alternate platform path solely to increase knowledge coverage while a known Modern/Baldosa vertical slice is incomplete. Where independent original validation is essential, preserved Snes9x and current exact ROM/hash are still required.

## Provenance and external work

Pin commit/URL, observed dates, byte hashes, source platform and relevant build identity. Separate original evidence, inference and speculative working hypotheses. Preserve third-party artifacts only when they actually enable a named implementation or test, with exact source provenance; keep large reproducible outputs out of Git. For source intake rules use [EXTERNAL-EVIDENCE-INTAKE.md](EXTERNAL-EVIDENCE-INTAKE.md) and [THIRD-PARTY-CODE-AUDIT.md](THIRD-PARTY-CODE-AUDIT.md). For practical tools use [TOOLCHAIN.md](TOOLCHAIN.md) and [TOOL-INTEROPERABILITY.md](TOOL-INTEROPERABILITY.md).

If future project direction makes general archaeology or editor support active again, update the live work queue first, then selectively reactivate archived plans instead of letting them reappear as an undocumented second priority.
