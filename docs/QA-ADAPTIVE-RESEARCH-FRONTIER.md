# Adaptive research frontier: high-volume discovery and development handoffs

**Classification:** native research only. See [live WORK-QUEUE](WORK-QUEUE.md) for the priority and exclusive implementation owners, [PROJECT-PLAN](PROJECT-PLAN.md) for the definitive original-game technical-reference goal, and [cumulative coordinator](QA-CUMULATIVE-RESEARCH.md) for source-bound evidence. Research runs cannot edit gameplay/original oracles, source-faithful rendering, the Modern product, or the independent release ledger.

This is the first real **discovery** campaign beyond the three endurance cohorts. It answers *what new gameplay states or possible crash boundaries do many legal dual-controller inputs reach?*, not *is the complete remake identical to the original SNES?*

## Ready today: 10,000 genuine compiled-native 2P experiments in one dispatch

[QA adaptive frontier](../.github/workflows/qa-adaptive-frontier.yml) offers **100 / 1,000 / 10,000 exact independent case populations**. It reuses exactly one existing shared native candidate built and source-smoked by \`modern-shared-native-acceptance.yml\`. Each case starts from the **original established two-player controller/movie prefix** and alters only legal post-entry inputs. It captures all standard **16 full 128-KiB guest WRAM source-owned checkpoints**, and three source-mapped *semantic bins* at frames 1740, 2580 and 3420. The player/race/viewport field offsets come from \`summarize_paired_player_slots.py\`, not arbitrary changing stack bytes. Merely changing an unclassified scratch register cannot manufacture coverage.

The matrix distributes work as:

| Whole campaign | Shards | Cases per shard | Max concurrent jobs | Actual native guest processes (if complete) |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 4 | 25 | 4 | 112 |
| 1,000 | 10 | 100 | 4 | 1,120 |
| 10,000 | 40 | 250 | 4 | 11,200 |

**Every 25th case additionally executes three genuine native runs**: identical replay plus independent mute-P1 and mute-P2 interventions. Their pre-intervention full-WRAM hashes must agree, the identical-treatment full-WRAM checkpoints must all agree, and both controller-removal counterfactuals must affect the first post-intervention game state. Thus the 10k option is **10k independent native controller scripts** with **400 deeper deterministic/dual-seat metamorphic checks**, not 10k strict original-SNES comparisons. Source-qualified event acceptance remains **0/45 until the independent original/native gate actually accepts an event**.

The campaign explores five legal-input strategies: balanced, P1-heavy, P2-heavy, alternating seat focus, and rotation/airborne pulses. Per-shard deterministic upper-confidence selection favours strategies that discover *new semantic-state bins* while still exploring every strategy. These normalized bins are **advisory research coverage**, not proof the original emulator produced the same behaviour. Cases are reproducible by source revision, binary SHA, original ROM hash, exact global seed, source script and selected arm. The immutable first dual-seat intervention is preserved.

### Bounded operations and fail-closed evidence

- All matrix case IDs and seed windows are frozen before the native candidate is compiled. A 40-shard matrix uses **at most 4 simultaneously running experiment jobs**. Each shard runs at most 250 cases, with 120-second timeout **per actual guest invocation** and a 180-minute per-job hard limit. No artificial sleeps to fill time budgets. The complete 10k population may take hours of real runner time and is not presumed finished until **40 intact machine receipts** validate.
- No raw ROM, guest WRAM, unbounded output frames or player save files are uploaded. Successful private roots are removed from the runner. Native failures preserve private roots only until its ephemeral job is destroyed; the public receipt records the bounded failure class/seed and any available reproduction evidence.
- The aggregator rejects **missing or partial shards, duplicate inputs or seeds, wrong source/binary/ROM hashes, changed first-entry fixture, forged controller/semantic counts and any false release admission**. A single missing case makes the campaign red, not a dishonest \`9,999/10,000\` pass. The source-specific semantic hashes can be reproduced, compared and investigated, but they're not release evidence.
- Every real successful run produces the compact \`qa-frontier-aggregate\` plus \`handoff.json\` / \`handoff.md\`. Handoffs rank which input strategies were productive and identify bounded novel-state reproduction seeds. They refer findings **to the existing gameplay, QA-08/10, and Modern/QA owners** without automatically creating speculative bugs, approving new HD art or writing gameplay patches.

### Cumulative and automatic versus standalone

To advance the **persistent** evidence ledger, dispatch [Cumulative research campaigns](../.github/workflows/qa-cumulative-research.yml) with \`campaign=frontier\`, \`frontier_cases=100\` first, on \`main\`. On actual success, increase to 1,000 and then 10,000. This is a **manual high-compute promotion**, not a fresh 10k automatic run twice weekly. The general twice-weekly auto rotation (now seven lanes) uses only **100 frontier cases** when it reaches this lane, avoiding GHA concurrency explosions. Each coordinator launch reserves a distinct integer-seed range, records source/run identity and a compact observed strategy/novelty summary, and permanently logs both passes and fails. A direct dispatch is useful for exploratory debugging but does **not** advance the cumulative ledger.

**One-seed reproduction:** download the exact \`qa-frontier-plan\` and use its source SHA to rebuild/retrieve the identical executable, then:

\`\`\`bash
python3 tools/qa_adaptive_frontier.py repro \
  --plan path/to/plan.json \
  --seed 50000019 --arm rotation \
  --exe /path/to/EXACT_NATIVE_BINARY \
  --rom /path/to/verified/Uniracers_USA.sfc \
  --work /unique/private/repro-root \
  --out /path/to/repro.json
\`\`\`

This executes the real candidate again and compares its newly observed semantic signatures with the original receipt. The example seed/arm illustrates syntax only; use the **actual** emitted handoff for evidence-driven reproduction.

## Remaining research frontiers: what must be qualified next

The system can already plan thousands of real **native two-seat state-space** experiments; it is not entitled to call other domains "10,000 correctness tests" when there is no independent truth oracle. Expand one new population only when it can preserve its original source and acceptance boundary.

| Priority / owner | Existing evidence and limitation | What is needed before 10k-case discovery |
| --- | --- | --- |
| **P0 Gameplay / QA-01/07** | Three source-qualified complete-event movies: Zoo, Bowl and Switcher; strict guest-relative result-phase disagreements remain | Resolve first strictly accepted USA event and define a genuine original/native perturbation oracle. Then add multi-seed replay from independent original emulator, with alignment and exact result state unaffected |
| **P0 Graphics / QA-08/10** | OAM/PPU frame2208 top-vs-bottom ambiguity, original alpha/depth history unresolved | Qualify original PPU/OBJ visibility and DMA latch history; then enumerate verified visible sprite/occlusion scenes. Self-vs-self pixels are not source truth |
| **P0 Windows native/Modern** | Native guest, profile, results and storage components exist but true controller-first settled 1P/2P result to fresh-process Records still requires integrated acceptance | Capture an **exact complete real Windows player journey**, then fuzz transitions and lifecycle faults over the observed same candidate and source-backed guest results |
| **Course breadth / technical atlas** | 45 decoded streams and normalized corpus exist, but the course/event acceptance matrix isn't complete | Source-qualify checkpoint/finish/score observers and course-specific original behavior before any 45×N correctness sweep |
| **Performance / CI** | Long native process performance and graphics replay campaigns are already separate cumulative lanes | Reuse their data to form measured hot-path regressions; don't generate wall-clock padding or meaningless pseudo-baselines |

A useful research cycle is **observed novel state → exact reproduction → independent original oracle → causal source/writer hypothesis → focused owning implementation PR → strict regression and coverage refresh**. Repeated cases within an unqualified oracle cannot satisfy that contract, irrespective of scale.

## Named, source-observed feature families for development handoff

The 10,000-input campaign no longer hands off arbitrary lexicographically sorted state hashes alone. Every sampled real 128-KiB guest checkpoint at frames **1740, 2580, and 3420** also supplies a small, closed vocabulary of **raw WRAM-source-slot categories**: both players have nonzero air fields, both have nonzero motion fields, opposite X-speed signs, both rotation candidate fields vary, the split-screen register changes or is nonzero, an offscreen register is nonzero, or the two players' course-progress pointers change. These are observations of existing source-indexed offsets from `tools/summarize_paired_player_slots.py`, *not* visual pixels, exact gameplay semantics or independently accepted original behaviour.

Each real case records a sorted subset of this vocabulary, and the source-bound aggregate counts how often each category occurred plus the **first exact (seed, arm, shard)** witness. The final handoff ranks less common categories first, nominates source-observed dual-air/split/offscreen candidate seeds to the graphics/QA-08 lane, and source checkpoint/rotation/contrasting-motion candidate seeds to the gameplay/QA-01 lane. Both must still capture the matching **independent original USA emulator / PPU** evidence before making fidelity or shipping claims. The signed cumulative ledger preserves per-category counts; missing categories, forged witness seeds, unsupported labels and inconsistent source cohorts fail closed.

This is a practical prioritization mechanism, not an AI automatically editing gameplay code. Production records, actual physical 4K, PPU/OBJ depth and native-to-Records completed events remain the established independent acceptance authorities.

## Exact cumulative observed-fingerprint census (new source-bound runs)

The adaptive source producer already observes all legal native controller cases and derives one normalized 96-bit semantic-state fingerprint per sampled WRAM checkpoint. The prior coordinator discarded the actual fingerprint set after building a HyperLogLog sketch. The exact-census upgrade retains **every** such fingerprint plus a first-seen reproducibility witness (GitHub run ID, deterministic seed, controller strategy and shard) in a sorted, zlib-packed ledger catalog on `research/qa-cumulative-ledger`.

Each completed, coherent **new-style** frontier campaign now reports **exact prior, newly observed and cumulative unique normalized fingerprint counts**, after deduplication against earlier exact-census campaigns. Individual producer aggregates include a complete packed token→witness catalog; the coordinator verifies every witness is in the source-bound seed window, the decoded count exactly matches the reported population, and the existing HLL corresponds to *that precise fingerprint set*. Any discrepancy makes the entire research run red and grants no ledger coverage. The original producer verifies each token against actual native guest checkpoints.

This census covers **exactly the persisted normalized 96-bit fingerprint identities**, not full 128-KiB RAM identity, all possible player states or original-SNES correctness. Truncated hashes have a theoretical collision probability; do not describe this as a proof that all underlying raw states are unique. The semantic extraction epoch is unchanged. A field/quantization/frame change requires a separately reviewed epoch migration; mixed schemas must not be unioned.

**Migration:** previously recorded HLL-only batches are *not* silently reconstructed or counted in the exact union. The new `frontier_exact_coverage` ledger object begins with the first newly executed source producer that exports an exact catalog; its `legacy_sketch_campaigns_excluded: true` marker is mandatory. The older `frontier_coverage` sketch remains available only as legacy trend/compatibility telemetry. Do not compare the exact post-migration count to historic HLL counts as though they were the same population.

**Find the first reproducible witness:** from a trusted checkout of the evidence branch, run

```bash
python3 tools/qa_frontier_exact.py \\
  --ledger path/to/research-evidence/.github/qa-cumulative/ledger.json \\
  --fingerprint <24-character-lowercase-token>
```

The result identifies the first green coordinator GitHub run, original exact source SHA, deterministic seed, arm and shard. Retrieve that run's retained `qa-cumulative-plan` artifact (if still available) and use the documented `qa_adaptive_frontier.py repro` procedure with the **original pinned source and binary**. This witness proves an observed native checkpoint identity only. The long-term source/binary replay recipe must be preserved before expiring CI artifacts are deleted; the exact census itself does not archive complete executables or ROMs.

**Bounded lifecycle:** the packed ledger format currently caps the combined exact corpus at one million normalized fingerprints (26 bytes per entry before compression, including first-source-run witness). This is a safety/resource bound, not a stopping rule for research: before reaching capacity, archive immutable source-qualified catalogs and implement a validated, partitioned exact store. If the bound is hit, fail closed and preserve the reproducible run, rather than revert silently to estimates or fabricate exact counts. The active cumulative coordinator and its original 100/1,000/10,000 case controls remain unchanged.

**Correctness is a separate, higher bar:** no fingerprint novelty grants QA-01/07 event admission, independent PPU correctness, Modern Windows controller-to-Records acceptance or release credit. The exact original/native event matrix and source-qualified comparison rules are authoritative. Route first-seen witnesses to those owners for original-oracle generation, causal debugging and permanent strict regressions. The target research progression is exact witnessed discovery → independent original fixture → strict original/native comparison → causal fix → accepted complete event.

## Cumulative semantic-state saturation (not correctness)

In addition to the exact per-run source-field state fingerprint count, the completed native discovery aggregate now exports a **4,096-register HyperLogLog (HLL)** sketch over its genuinely observed 24-hex-character semantic-state digests. The serialized cumulative coordinator checks the same source-linked disposition, count, planned seed population and claimed release exclusions **before** merging the sketch. Its append-only evidence branch holds `frontier_coverage` with the current extraction epoch, signed/canonical register sketch, running real case count, and **estimated** union cardinality. A red or missing source-run consumes its seed window but never adds invented coverage.

The sketch uses approximately 5.5 KiB of base64 per ledger snapshot, so a 10,000-input campaign does not leave a continuously expanding raw-WRAM or per-frame record corpus. The expected relative standard error is **1.625%**. Identical states across multiple green runs are expected to increase the number of real process journeys without increasing the union cardinality. A new observed state can still register no apparent increase because sketches are approximate. Never call estimated novelty an exact count, release acceptance, a proven defect, or original-SNES state coverage.

A change to field selection, quantization, frame sampling or token semantics requires an explicit `tools/qa_frontier_coverage.py` epoch review before comparing new states with the previous ledger sketch; fail closed rather than silently combining incompatible populations. The `qa_frontier_coverage` tests include duplicate-run union, disjoint populations, bad sketches, epoch mutation and failed coordinator runs. Prior historical 2P endurance receipts remain **uncensused** here: they recorded WRAM determinism but not source-field token catalogs.

Use the estimated *marginal* new-state gain alongside source-meaningful state categories and the existing development gates when deciding whether another 10,000-input batch is worth paying for. This measurement makes prioritization better; it does not itself identify or fix the underlying source/NMI/OAM defect.

## Scientific stopping rules

Do not promote large novelty counts as accepted gameplay. If broad exploration produces no new meaningful semantic categories or only trivial motion variation, shift to the next **qualified question** instead of repeatedly paying for 10k nearly identical states. Revisit inputs after changes to the actual gameplay or source observability. Three non-discriminating source probes should trigger explicit hypothesis revision per the existing project research policy, not a hidden relaxation of the original parity comparator.

**Ownership and risk:** This new tool does not write to \`docs/RELEASE-QUALITY-LEDGER.json\`, the original game, native renderer, Modern frontend, product storage or an art-approval manifest. No automatic issues or code-writing agents are invoked by unreviewed novelty; generated reproducible packets are suitable input for the owner's next autonomous research/development turn.
