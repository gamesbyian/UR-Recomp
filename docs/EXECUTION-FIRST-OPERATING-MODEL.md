# Execution-first operating model (replacement campaign)

Owner direction, 2026-11-13: working game and honest original evidence outrank
agent-scheduling continuity, process volume, and CI infrastructure preservation.
The old five-worker board remains provisional until executable replacement is
demonstrated. No existing evidence or source revision is silently discarded.

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

Allowed `kind` values:
- `qa01_rf095_pcm`: actual paired original/native Zoo result audio;
- `qa01_zoo`: actual original/native Zoo through Bowl follow-through;
- `windows_candidate`: native Win32 hosted journeys and candidate export.

The dispatcher intentionally uses **fixed allowlisted profiles**, not a
request-supplied shell command. The executing agent may change code and
instrumentation on that branch and bump `attempt`, with complete provenance,
but cannot ask this control plane to execute an arbitrary privileged task.
To add an experiment family, wire another bounded reusable implementation
and test it; do not add one workflow per investigation. For each attempt:
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

## Migration sequence

1. Demonstrate this service with a **real** hosted RF095 result, and fix
   dispatch/runner failures instead of calling them external blockers.
2. Extend the service for WIDE-07 moving-course and course-fanout adapters;
   retain the same non-privileged request discipline.
3. Prove a fresh current-main Windows package and gate audit.
4. Replace five duplicate hourly scans with fidelity and Windows execution
   workstreams, plus on-demand independent verification.
5. Replace ranked prose with a small actionable queue; retire unused workflows
   after confirming their active callers. Retire stale unattended HP/ops/Vault
   work only after checking what evidence it uniquely provides.
6. Report accepted courses, accepted release gates, verified player journeys,
   new defects and removed blockers; investigate repeated identical blocked
   runs automatically.

Until step 1 has been demonstrated, do not shut off the five agents or erase
their references solely because the new policy has been written.
