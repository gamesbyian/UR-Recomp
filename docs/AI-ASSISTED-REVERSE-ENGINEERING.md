# AI-Assisted Reverse Engineering Practices

Last reviewed: 2026-09-30

This document records reusable workflow lessons from AI/LLM-assisted ROM hacking and binary reverse-engineering projects. It is a **method guide**, not a second work queue and not an argument to adopt every external tool.

The project should import techniques when they improve evidence quality, agent efficiency, or semantic compounding. External AI output is never authority: deterministic ROM/runtime evidence remains the oracle.

## Sources reviewed

The 2026-09-30 pass inspected these especially relevant projects and workflow documents:

- `monteslu/romdev` — agent-facing retro ROM development/reverse-engineering toolkit and ROM-hacking playbook: https://github.com/monteslu/romdev
- `paulomanrique/mesen-for-ai` — MCP/headless Mesen bridge and debugger skills: https://github.com/paulomanrique/mesen-for-ai
- `vgrichina/re-skill` — Claude Code retro-game RE skill with persistent labels, verification gates, and dead-end tracking: https://github.com/vgrichina/re-skill
- `cellebrite-labs/ghidra-rpc` — persistent agentic Ghidra workflow with structured query/mutation surfaces: https://github.com/cellebrite-labs/ghidra-rpc
- `bethington/ghidra-mcp` — battle-tested Ghidra AI workflows, including type-first documentation, batching, completeness checks, and falsification: https://github.com/bethington/ghidra-mcp

These are technique sources, not implementation authorities for Uniracers or SNES behavior.

## What UR-Recomp already does well

The external material strongly validates practices already present in this repository:

- deterministic controller replay through multiple engines;
- state/checkpoint comparison rather than visual intuition alone;
- targeted write tracing and first-divergence localization;
- canonical symbols that feed multiple analysis surfaces;
- separation of observation, interpretation, confidence and provenance;
- controlled mutation/counterfactual experiments;
- cross-emulator corroboration for hardware-sensitive claims;
- value-of-information and stopping rules;
- compact generated evidence rather than committing giant traces/dumps;
- external claims treated as leads until reproduced locally.

Do not create parallel infrastructure merely because another project has a similar feature.

## Practices worth importing explicitly

### 1. The mechanical oracle decides

An LLM may propose a semantic label, routine interpretation, structure layout, patch or reconstructed implementation. Completion requires an external discriminator wherever one is available.

Preferred oracles include:

- exact ROM bytes / disassembly facts;
- deterministic input replay;
- state or write-history checkpoints;
- controlled ROM mutation;
- cross-build structural correspondence;
- emulator/hardware behavior;
- compiler/assembler byte diff for reconstructed code;
- a minimal falsification test targeted at the claim.

A documentation score, confident explanation, decompiler output or model consensus does not establish truth.

### 2. Keep the hypothesis-test loop short

Prefer experiments that let the agent form a hypothesis, execute one bounded test, inspect the result and revise within the same working episode.

If an experiment requires a giant capture before it can answer anything, look for a cheaper discriminator first. A good loop often looks like:

1. name one uncertainty;
2. identify the smallest observable that separates plausible explanations;
3. run one deterministic experiment;
4. record the result immediately in the owning authority;
5. either promote the result or choose the next discriminator.

This is the AI-specific version of the repository's existing value-of-information rule: short feedback loops reduce hallucinated narratives and stale assumptions.

### 3. Build compact context packets, not binary dumps

When asking an agent to interpret an opaque routine or state transition, provide the smallest connected semantic neighborhood that makes the question answerable.

A useful context packet may include:

- function/range and current symbol/confidence;
- direct callers and callees;
- direct ROM/WRAM/PPU references;
- known sibling/parallel functions or structures;
- relevant cross-build matches;
- whether the routine executes in the fixture being studied;
- a bounded dynamic trace/write history around the event;
- competing interpretations and what would distinguish them.

Do not dump whole banks, giant decompiler listings or full traces into context by default. Expand only when the current packet cannot discriminate the hypotheses.

### 4. Use the narrow debugger primitive first

The `mesen-for-ai` workflow usefully formalizes a practical ordering:

- "who wrote this?" → write watch;
- "did this code run?" → execution breakpoint;
- "what code/data participated?" → CDL/coverage;
- "what happened around this small interval?" → bounded trace;
- full instruction tracing only when smaller instruments fail.

For UR-Recomp, reuse existing project-owned adapters and trace clients rather than copying this API literally.

### 5. Treat execution-coverage deltas as a semantic search tool

CDL/coverage should not be only disassembler input.

For a controlled A/B action:

- execute the same baseline fixture twice;
- change one action/state variable;
- compare executed ROM ranges/basic blocks;
- identify code newly reached or no longer reached;
- intersect that delta with known symbols/xrefs and dynamic writers.

Examples: neutral vs jump, clean landing vs failed landing, no stunt vs tabletop, P1-only vs P2-only input, checkpoint contact vs non-contact.

A small coverage delta can locate behavior more cheaply than scanning every reader/writer of a broad state region.

### 6. Preserve dead ends with retry conditions

Repeated agent sessions can rediscover the same failed route. Record a dead end when a materially bounded approach has failed enough times that repetition is likely.

The entry should say:

- question/task;
- approaches tried;
- why they failed or remained non-discriminating;
- what new evidence or capability would justify retrying;
- better next decomposition if known;
- date/session/commit or evidence reference.

Prefer the existing research ledger or owning specialist document when the dead end concerns a substantive claim. Create a separate dead-end artifact only if repetition becomes common enough to justify it.

A useful trigger is approximately ten fruitless tool calls on one narrow task, or two to three materially different failed approaches without uncertainty reduction. Do not log trivial mistakes.

### 7. Persist semantic improvements into tool-visible state

Knowledge should compound across agents. Stable discoveries should flow into machine-consumable surfaces where possible:

- `docs/SYMBOLS.md` → generated symbol adapters;
- state/fixture manifests;
- comparative-code-atlas metadata;
- parsers and typed structures;
- regression assertions;
- queryable knowledge pages.

Avoid leaving important semantics only in prose summaries, PR descriptions, chat transcripts, Ghidra workspaces or raw traces.

### 8. For decompiler work, stabilize types/structure before prose

The Ghidra agent workflows repeatedly hit a failure mode where commentary and names are written against unstable inferred types, then re-analysis invalidates them.

For any future Ghidra-heavy lane:

1. establish function boundaries and processor context;
2. resolve calling convention/signature and useful data types;
3. identify structures/field offsets where evidence supports them;
4. then rename locals/functions and add explanatory comments;
5. finish with a mechanical contradiction/falsification pass.

Do not import another project's naming convention merely because its workflow uses one.

### 9. Use cross-binary matching as leverage, not decoration

AI-assisted Ghidra projects make heavy use of function hashes/signatures to transfer work across versions. UR-Recomp's four-ROM comparative atlas is already pursuing the stronger version of this idea.

Continue favoring fingerprints that survive relocation where possible: normalized instruction shape, CFG, callers/callees, ROM/WRAM/PPU accesses, table relationships and bounded byte signatures.

A label propagated across builds still inherits the evidence/confidence of the match. Do not turn similarity into semantic certainty.

### 10. Bound tool output for model consumption

Agent-oriented RE tools deliberately cap watch events, paginate functions and batch edits. Apply the same principle to project-owned tools:

- return the few highest-value events by default;
- expose filters/ranges/checkpoints;
- summarize large datasets mechanically;
- preserve raw artifacts only when reproducibility needs them;
- let the agent request expansion deliberately.

This is both a context-efficiency rule and an epistemic one: the important event should not be buried under 50,000 irrelevant lines.

## Near-term UR-Recomp applications

These are **supporting accelerants**, not new gates that outrank the shipping critical path.

1. **Verify controller polling semantics once.** Determine the relevant SNES controller-read cadence/boundary for the canonical game and whether any current fixture assumptions can shift under lag/multiple polls. Promote only whatever invariant is needed for reliable replay alignment.
2. **Prototype fixture-to-fixture execution-coverage deltas.** Use the existing Mesen/CDL lane or another already-owned coverage source. Start with one known causal pair and ask whether the delta materially narrows routine discovery. Keep it only if the information gain is real.
3. **Add bounded perturbation experiments when a semantic routine remains opaque.** Sweep a small domain of one state/input variable from a shared checkpoint, cluster outcomes/first divergences, and use the partition to infer behavior. Do not brute-force state space without a concrete hypothesis.
4. **Use compact context packets for stubborn semantic work.** Before broad source/disassembly reading, assemble callers/callees/xrefs/dynamic participation/current hypotheses into a small artifact or query output. Automate this only after repeated manual use proves a stable contract.
5. **Escalate hardware questions through existing test ROMs first.** If an uncertainty concerns SNES behavior rather than Uniracers logic, search emulator test suites / consoledev test ROMs before writing a bespoke experiment. Write the smallest synthetic test ROM only when existing tests do not discriminate the behavior.

## Adoption rule

Do not add a new dependency merely because its documentation contains a good idea.

Prefer this order:

1. steal the technique;
2. express it using existing UR-Recomp tools/data;
3. add a small adapter if needed;
4. adopt/vendor a new tool only when the adapter/tool provides recurring measured value that existing surfaces cannot provide cheaply.

The desired result is not "AI-powered reverse engineering" as a separate subsystem. It is a repository whose evidence surfaces, task decomposition and feedback loops make agents less likely to hallucinate, repeat work, or spend expensive effort on low-information experiments.
