# Execution-first operating model (replacement campaign)

Owner direction, 2026-11-13: working game and honest original evidence outrank
agent-scheduling continuity, process volume, and CI infrastructure preservation.
The two scheduled execution workstreams are active; the former five-worker
shared-pool board is retired as dispatch authority. Hosted specialized and
general source-controlled experiment execution have both been demonstrated
against real original/native game data. No existing evidence or source revision
is silently discarded.

## What a worker does

Choose one of two independent outcomes: **first fully accepted USA course**
(0/45) or **next independently accepted Windows release gate** (0/12).
The fidelity stream owns original/native behavior, audio, timing and the
course campaign. The Windows stream owns a genuinely playable candidate,
controllers, saves, multiplayer and release gates. A verifier checks concrete
results on demand and alone may recommend formal ledger changes.

Each development run MUST attempt a game-related executable observation or
repair. If blocked by a missing tool, runner, dependency, fixture or script,
**removing that blocker is the task**, provided it needs no unavailable external
authority or physical device. Install/build/repair or extend an execution
route, then retry. A failed attempt with a fresh, source-bound reproduction
is a result; repeatedly reporting the same obstacle without attempting a new
route is a coordination-system fault. If one route is truly impossible, work
the next independent ready task.

An incomplete task hands off:
- exact source SHA and workstream;
- question, previous attempted commands/run IDs, and actual observed outcome;
- blocker owner, executable next command, execution location and prerequisite;
- observable pass/fail discriminator and whether another task can proceed.

Do not write a narrative instead of doing the next available experiment.

## Standing hosted experiment service

The source file `.github/workflows/agent-bounded-experiments.yml` is a
standing GHA runner dispatcher. It uses GitHub-hosted ephemeral runners,
`contents: read`, no OIDC/secrets, no self-hosted runner and no PC.
Each job is bounded by the existing reusable workflow's own timeouts and
has a separate serial concurrency group per experiment branch.

An execution agent creates a branch named `experiments/<work-id>` **from
current main**, writes `experiments/request.json` with this schema, and
pushes. Each updated request commit automatically starts a new run on that
exact source revision, with the record retained in the
`agent-experiment-request` artifact. No PR approval, manual workflow
dispatch or merge is required for a retry.

```json
{
  "schema": "ur-agent-experiment-request/1",
  "kind": "qa01_rf095_pcm",
  "question": "Does actual original/native stereo PCM agree at the USA Zoo result?",
  "expected": "Obtain exact frame-bound PCM from both engines, or isolate a producer failure.",
  "owner": "fidelity",
  "attempt": 1
}
```

Allowed \`kind\` values:
- \`qa01_rf095_pcm\`: actual paired original/native Zoo result audio;
- \`qa01_zoo\`: actual original/native Zoo through Bowl follow-through;
- \`windows_candidate\`: native Win32 hosted journeys and candidate export;
- \`script_linux\`: **general-purpose source-controlled experiment recipe**,
  edited and rerun entirely by the agent without a workflow edit, PR,
  merge or owner intervention per attempt.

For \`script_linux\`, supply \`experiments/run.sh\` on that experiment branch
alongside \`experiments/request.json\`. The JSON uses the same exact six
fields shown above, with \`kind\` set to \`script_linux\`. The shell file must
begin with \`#!/usr/bin/env bash\`, be a regular file under 256 KiB, and be
in the same exact source revision as the request. Each new attempt modifies
the script or product sources as needed, increments \`attempt\`, commits
\`experiments/request.json\` and pushes the branch. That request change is
the only automatic trigger. Do not try to dispatch by editing the workflow.

The hosted worker executes \`bash experiments/run.sh\` after stripping the
Actions environment down to an explicit allowlist. It has no inherited
\`GH_TOKEN\`, GitHub App credential, OIDC token or repository write scope; its
checkout has no persisted Git credential. No self-hosted/HP runner, owner PC
or private environment is available. Install missing packages or compile
emulators and native binaries on that ephemeral Ubuntu runner as needed.
A 30-minute script limit plus the job timeout bounds execution. Put useful
machine-readable outputs, logs and bounded evidence in
\`$UR_EXPERIMENT_OUTPUT_DIR\` (64 MiB uploaded-evidence limit);
\`$UR_EXPERIMENT_SOURCE_SHA\` identifies the exact checkout.
The automatically retained receipt records source SHA, script/request hashes
and the execution step outcome. A failed experiment retains whatever bounded
evidence it produced; the next agent inspects that output and **repairs the
recipe, toolchain or product**, rather than restating the failure.

The three specialized profiles remain available for lengthy already-proven
original/native and Windows pipelines. \`script_linux\` is the normal route
for a new bounded Linux-side question, including WIDE-07 instrumentation,
new audio alignment experiments, and independent code reproduction.
Do not treat an agent-supplied script as an authorization to access secrets,
the owner's PC, proprietary external services, or another system. Even a
successful hosted experiment does not grant a USA course or release gate.

For each attempt:
open Actions > Agent bounded experiment execution > branch run, inspect all
failed jobs and download their artifacts before changing source/request.
Use the failed command and its exact output as the next question.

The initial service is a **real-compute capability**, not an automatic
research conclusion. A dispatched experiment does not qualify a course or
release gate. Evidence must be compared, reproduced when needed and judged
against behaviorally relevant, explicit acceptance criteria. Internal-state
differences are causal leads rather than automatic vetoes or automatic waivers.

## Work selection and actual delivery

Priority A: execute RF095 stereo PCM on a source-pinned original/native
USA Zoom Zoo case, fix instrument/producer faults, determine behavioral
effect, finish one complete course, then replicate the course procedure.

Priority B: produce a fresh tested Windows ROM-free candidate, audit all
12 existing gate conditions against current sources and actual evidence,
and close the least expensive independently satisfied gate. Physical tests
are owner-supplied when unavoidable; hosted tests must not impersonate them.

WIDE-07 requires its own moving-course adapter if no current reusable
workflow produces the demanded evidence. Do not misidentify draft PR #2873
as WIDE-07: it is an independent native voice-7 audio extractor. Keep its
experiment distinct from RF095's paired stereo output.

Do not claim metric movement for a tool test, source-only fixture, receipt,
synthetic-only Windows test or absence of a reproduced failure. The 0/45
and 0/12 counters change only upon evidence-backed qualification.

## Verified migration status, 2026-11-13

1. **Hosted service operational:** Specialized actual original/native stereo PCM
   run [43532930092](https://github.com/gamesbyian/UR-Recomp/actions/runs/43532930092)
   and real source-controlled `script_linux` WIDE-07 original Snes9x
   run [43539425650](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650)
   and native real state run
   [43540488054](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054)
   prove the general hosted execution route can build and run original/native
   experiments. Retry through updated request scripts; do not establish another
   execution platform as an answer to a successfully solved dependency.
2. **Original-USA-derived WIDE-07 pixels:** Merged
   [#3359](https://github.com/gamesbyian/UR-Recomp/pull/3359)
   independently predicts all 38,528 left/right 342-wide margin RGB5 samples
   at two real moving-course checkpoints from original source BG1/BG2,
   all 38,528 matching the actual native framebuffer. It does not prove other
   moving frames, true 342-pixel original-SNES rendering, sprite/HDMA
   interactions, matched absolute guest clocks or full WIDE-07/course acceptance.
   A transient 1-pixel original/native blue-arrow boundary remains to isolate.
3. **Playable Windows candidate operational:** Hosted source-controlled request
   [run 43545814590](https://github.com/gamesbyian/UR-Recomp/actions/runs/43545814590)
   succeeded against a branch from main differing only in the experiment
   request, emitted ROM-free native x64 candidate artifact 14094547287,
   controller journeys and genuine NTFS recovery evidence. Its actual
   experiment SHA is `513bc5ad42f52c790a028eb2e20a9a3d51d9c065`,
   not the `main` source SHA. Independently verify before physical playtest
   and nominate an exact-source release candidate separately when required.
4. **Coordination replacement active:** Fidelity and Windows hourly execution
   workstreams replace the five redundant shared-pool agents; the on-demand
   independent verifier remains distinct. Recurring noncritical HP/Vault/ops
   scans were retired or converted to manual. Six dormant operations/CI
   proposals (#3295, #3302, #3281, #3274, #3258, #3229) were closed with
   recoverable branches instead of remaining active reviews. Old ranked board,
   211 historical workflows and dated deep-research documents are not mandates
   to preserve process overhead. Retire a specific remaining workflow only
   after checking actual build and evidence consumers.
5. **Next actual targets:** first fully independent USA course qualification,
   then 44 more; first fully independent Windows QA gate, then 11 more.
   `docs/EXECUTION-QUEUE.json` carries exact next actions, owner,
   execution location, source runs and completion discriminators. Reuse evidence
   already captured; pursue causal first failures or additional distinct
   moving frames rather than re-observing the same source traces.

**Formal acceptance remains 0/45 USA courses and 0/12 Windows release gates**
until complete evidence-backed independent evaluation. A file count, workflow
success, correlation, two-frame positive image, hosted candidate or self-review
must not increment either counter.
