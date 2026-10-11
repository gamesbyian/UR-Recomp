# Trusted upstream: fast adoption without invented fidelity

**Operational policy, 2026-10-10.** This is an implementation policy for existing
UR-Recomp owners, not another work queue or release gate. The current
[three-project apparatus synthesis](THREE-PROJECT-APPARATUS-SYNTHESIS-20261010.md),
[work queue](WORK-QUEUE.md), [project charter](PROJECT-PLAN.md), and sole
[release ledger](RELEASE-QUALITY-LEDGER.json) retain their existing authority.

## The time-saving rule

**A pinned, maintained upstream subsystem may be a trusted engineering input
before its full game-fidelity certification.** Stop treating every upstream
function, descriptive name, or general-purpose algorithm as a research question
that must be independently rediscovered before it can be used.

Treat trust as specific to an *operation* and *evidence domain*, not to an
author or repository in the abstract:

| Tier | Permission after its entry checks | Not authorized |
| --- | --- | --- |
| **U0 preserved** | Search and quote an exact imported source snapshot with attribution | Executing imports, changing canonical claims |
| **U1 research-ready** | Bulk-query upstream names, hypotheses, disassembly and static maps; use them to select experiments and annotate draft research | Promoting PAL/USA matches or external symbols as original USA fact |
| **U2 engineering-qualified** | Vendor/link a coherent licensed tool or backend, exercise its existing tests, add a narrow UR input/output contract and pinned rollback; allow dependent feature development | Waiving independent original behavior checks or storing fabricated game results |
| **U3 integrated** | Use the component in an exact host candidate after representative real-domain interface, lifecycle, failure and data tests pass | Claiming whole-game correctness or distribution readiness |
| **U4 certified for stated scope** | Claim only the precise original/native or release behavior independently accepted in the release ledger | Extending the scope to unplayed courses, untested hardware or modes |

Upstream evidence is often sufficient for U1 and can be sufficient for a U2
starting point. Independent downstream acceptance is required when a use crosses
an irreversible save/result boundary, directly determines original-game
mechanics, changes authoritative reference behavior, or decides final PPU/OBJ
visibility. A U2 component can unblock an internal alpha even if U4 remains
0/45 for complete USA event comparison, so long as its limitations are visible.

## Default dispositions for the existing pinned sources

- **Baldosa USA native guest**: use the existing integrated core as the
  implementation dependency, with a single host-owned Modern input/profile/
  persistence authority. Preserve the old backend as rollback. Trust its
  internals provisionally; test our exact interface and independently certify
  complete original game events. Do not restart a second recompiler or hand-edit
  generated game C. Current imported source is
  `baldosa/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101`.
- **Baldosa USA decomp and symbols**: expose all imported names and RAM
  descriptions at U1 without individual review. Use source-address matches
  as pointers for investigation, not automatic additions to
  `docs/SYMBOLS.md`. Recomp M/X or framework changes receive component
  regression before U2/U3 promotion.
- **malmazuke PAL labels, native-to-ROM index and research**: bulk-search at U1.
  The index covers many more entries than the 546 specifically classified
  PAL/USA structural candidates. Projected offsets are *candidates*, including
  when spellings or addresses happen to match; do not interpolate global region
  shifts. Snapshot:
  `malmazuke/unirally-reconstruction@42d444594641d23f5d3c15da7b7c454bb5180e43`.
- **malmazuke MIT tools**: favor one cohesive module plus its transitive
  dependencies/tests over algorithm-by-algorithm rewrites when a current task
  actually benefits. Candidate families: effective-address decoding, replay
  first-difference, content provenance, static coverage and dependency-closure
  gate identity. Qualify U2 with synthetic negatives and an authentic
  representative input; defer enabling an expensive QA gate cache until changing
  an actual transitive dependency provably forces the check to run.
- **malmazuke PAL native C++ mechanics**: a richly documented U1 reference
  for the technical atlas, future tooling/editors and targeted causal probes,
  not a second active Windows game simulation or a USA release oracle.
- **UR Modern app, saves/records, 342-wide graphics and release QA**: retain
  first-party ownership; whole external frontends are not automatically a fit
  merely because their core plays the original game.

## One bulk-discovery interface, no symbol promotion

The upstream-preserved Baldosa labels and malmazuke PAL native map/labels are
now searchable together without copying observations into `docs/SYMBOLS.md`:

```sh
python3 tools/query_upstream_knowledge.py --summary
python3 tools/query_upstream_knowledge.py --match 'finish|checkpoint' --limit 30
python3 tools/query_upstream_knowledge.py --address 81:8050 --json
python3 tools/query_upstream_knowledge.py --usa-address 81:8147 --json
python3 tools/query_upstream_knowledge.py --match 'race_progress.cpp' --source malmazuke
python3 -m unittest tests.unit.test_query_upstream_knowledge
```

The `--address` flag looks up a **literal address** within each named ROM
region, with PAL and USA results kept distinct. The `--usa-address` flag
adds only precomputed *code-region interval candidates* from the frozen
PAL/USA index alongside exact USA results; these are never validated homologs.
Malformed/stale map schema or duplicate correspondence entries fail closed.
The output reports original upstream source commits and is advisory. It
does not edit any preserved imports, the canonical symbol list, generated
code, host state, QA fixtures, or release decisions.

For actual canonical promotion, consult ROM/opcode boundaries, original
instruction/state evidence, and the appropriate PAL/USA homolog analysis.
One verified concept may fan out to multiple downstream tools at once;
do not demand a separate rediscovery for each consumer.

## Fast dependency qualification: one packet, not N separate studies

Before admitting a **new executable upstream module** at U2:

1. Pin the exact source commit, file hashes, transitive dependencies,
   applicable license, authorship and asset/ROM exclusions. Do not silently
   refresh a moving branch or copy private/proprietary game content.
2. Run its upstream tests and a short local adversarial suite on invalid
   inputs, deterministic output, and file/process safety. Record skipped
   prerequisites as skipped. Scan for network, environment and write effects.
3. Define a single project-owned input/output adapter and rollback route.
   Do not establish rival profile, game simulation, fixture or symbol authority.
4. Run one representative real ROM-independent or legitimate original-ROM
   fixture. Reuse an existing shared capture when possible, and bind it to the
   precise tool version/input; failures stop promotion but need not stop U1 use.
5. Record the qualified scope once in the owning tool/subsystem documentation.
   Downstream callers reuse that qualification until the module or transitive
   inputs change. Critical game, PPU and persistence gates remain separate.

A coherent upstream update can contain multiple tightly coupled patches.
Test the group in one isolated candidate and keep one rollback, rather than
needlessly porting every patch as a separate PR. Split only where unrelated
risk or failure diagnosis requires it. Retain original independent oracles and
do not weaken mismatching checkpoints to get a green CI result.

**Risk and rights**: Baldosa uses PolyForm Noncommercial and malmazuke's own
code is MIT. Follow their actual terms and preserve notices. Neither grants
rights to Nintendo/DMA ROMs or game-derived assets; a linked binary may inherit
Baldosa's noncommercial restrictions. Repository/public release exposure is a
separate owner decision. The [apparatus roadmap](THREE-PROJECT-APPARATUS-ROADMAP-20261010.md)
records an outstanding public-ROM-history concern; this policy does not
authorize deletion, history rewriting, distribution or commercial licensing.

## Measure outcomes, not ceremony

Report qualified module families, agents/teams using each shared research
fact, accepted player journeys, minutes of duplicated capture avoided and
actual regressions found. U1/U2 reuse is permitted immediately; a component's
U3/U4 status must only advance with recorded candidate-bound evidence. Never
upgrade the release ledger based merely on upstream reputation or source volume.
