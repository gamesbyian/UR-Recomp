# UR-Recomp agent operating contract

**Owner direction, November 13, 2026:** the project operates as **two execution
workstreams** with a verifier on demand, not five board-checking generalists.
The sole operating authority for scheduling and next jobs is
[the execution-first model](docs/EXECUTION-FIRST-OPERATING-MODEL.md) together
with [the executable queue](docs/EXECUTION-QUEUE.json). Read fresh GitHub
`main`, current Actions/PRs and actual evidence before deciding an action.
Do not spend a run rediscovering historical blockers or rewriting the board.

## Required outcome of every run

Advance **Fidelity** (first fully accepted original-USA course; 0/45) or
**Windows** (first independently accepted exact-candidate release-quality gate;
0/12), prioritizing an actual game experiment, executable repair, source-bound
player journey or independently testable missing witness. Verifier is on
demand, not an hourly third auditor. Never award acceptance based solely on
a CI green, a test of a harness, similar waveforms, provisional process
evidence or a self-approval under a shared GitHub identity.

**A missing executable dependency is an engineering task.** If the emulator,
library, runner, script, sample or build is unavailable, install/build/repair
the needed hosted execution route and retry. The standing nonprivileged
`.github/workflows/agent-bounded-experiments.yml` executes source-controlled
`experiments/request.json` on `experiments/*` branches. New bounded Linux
experiments use `kind=script_linux` and `experiments/run.sh`; specialized
original/native and Windows profiles are also available. No new PR, workflow
or owner intervention per experiment retry. The owner's physical HP PC and
Desktop Commander are not ordinary CI compute; do not use either to avoid
normal hosted development.

On a genuinely external dependency, write the **exact source SHA, owning
workstream, attempted commands and GHA run/artifact, observed failure,
blocker owner, next executable command/location, prerequisite and
observable completion condition**. Then work the next independent task.
Repeated identical blockers without an attempted fix are failure of the
development operation.

## Delivery-first selection rule (2026-11-18)

The Nov 11–13 versus Nov 14–16 comparison showed **2 versus 15 merges**
and the new experiment service working, but **zero completed USA courses,
zero complete Windows release gates, and no merged player-facing runtime
implementation in the latest 72-hour window**. Optimize the next 72 hours
for **working game source and independently exercised player journeys**, not
another increase in CI or evidence documents.

At the beginning of each invocation, choose the smallest *player-observable*
missing or defective behavior supported by current evidence. The order is:

1. **Fix a reproduced game defect** in `native/product/`, `native/title/`,
   or the relevant runtime sources; add a test that fails on the prior
   behavior, execute a genuine run, then merge a qualified PR.
2. **Finish a real player journey or complete a release/course criterion**
   using already existing compiled games, scripts and original witnesses.
   If it fails, trace the first causal product defect and return to (1).
3. **Make one bounded original/native discriminator** only when a concrete
   implementation decision still depends on it. State beforehand which
   result would cause which source change; inspect real output before retry.
4. **Repair essential tooling** only if (1)–(3) cannot run because of the
   named defect. Stop when the dependency works; do not keep polishing it.

After **two consecutive sessions on the same question** that produce only
measurement, documentation or harness changes without a new source fix,
new player behavior or formal qualification, switch to the smallest
reproducible game-level test or another ready independent gameplay target.
Exceptions are allowed for an objectively necessary original-data or
security discriminator; explicitly state what remains unknown and the
exact pass/fail test, rather than reporting another general investigation.
Never introduce an unjustified renderer or physics modification just to
satisfy a quota. Unknown original/native phase differences are reasons to
measure first, not to alter working gameplay speculatively.

A `green` Action is a completed execution, **not a completed feature**.
At each stop classify the actual result as (a) merged product/runtime fix,
(b) genuine verified player journey or accepted gate, (c) independently
observed source divergence that changes a concrete next edit, or
(d) infrastructure/evidence-only. Report (d) plainly; do not call it
product delivery. Prioritize (a) and (b) in subsequent runs. Do not add
another scorecard, workflow or meeting merely to report these categories.

Windows: **prioritize QA-03 multi-leg tournament gameplay now**.
Exercise real guest/controller legs 2/3, standings and cross-process
persistence; fix the first reproduced game-source defect and test it on
Windows. Preserve [draft #3372](https://github.com/gamesbyian/UR-Recomp/pull/3372)
as an unmerged C04 test prototype. Its attempt 35 (Actions run 44875961788)
failed before the profile chooser opened, so no real exit-86/cold-restart
witness exists. Do not start further C04 iterations until a minimal F2
event-to-chooser test is demonstrated and QA-03 has received direct game
execution. Source/CI artifacts remain available; never call C04 accepted. Fidelity: compare authentic
adjacent original/native WIDE-07 frames against the same native phase,
resolve source clock alignment, and fix the first demonstrated compositor
or game defect. If no defect is proved, advance authentic Zoo complete-event
behavior. 3D racer model recreation remains on owner hold.

## Current known positive executable evidence

- Real source-bound Zoo original/native RF095 PCM: GHA
  [43532930092](https://github.com/gamesbyian/UR-Recomp/actions/runs/43532930092).
  Strong aligned waveform correlation is not yet audio parity.
- Real original Snes9x and native WIDE-07 experiments: GHA
  [43539425650](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650)
  and [43540488054](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054).
  Merged [#3359](https://github.com/gamesbyian/UR-Recomp/pull/3359) reconstructs
  both BG1/BG2 layers from original source and finds all **38,528/38,528**
  widened margin RGB5 pixels match at two authentic checkpoints. The
  transient blue arrow, additional moving frames and whole-course acceptance
  remain open.
- Fresh ROM-free Windows x64 candidate with hosted player journeys and real
  Win32 NTFS evidence: GHA
  [43545814590](https://github.com/gamesbyian/UR-Recomp/actions/runs/43545814590).
  This is an experiment-branch source with only the experiment request added,
  **not** an independently accepted exact-main physical release.

**Do not re-run these identical experiments** without a new falsifiable
question or materially different source. Take the next discriminator from
[the queue](docs/EXECUTION-QUEUE.json).

## Ground rules and sources

Build a faithful, enjoyable, eventually multiplayer Windows x64 remaster;
portable builds should be ROM-free. A valid owner-supplied original USA ROM is
necessary for genuine original/native differential observations. Source ROM
risk policy: [owner direction](docs/OWNER-ROM-RESEARCH-RISK-PRIORITY.md).
Owner willingness to tolerate discoverability never grants third-party
redistribution rights, permission to leak secrets or bypass platform refusals.
Hosted experiments run least privilege, ephemeral, with no repository-write
credentials, owner's private machine or unbounded external access.

Game intent: [project plan](docs/PROJECT-PLAN.md).
Acceptance: [release ledger](docs/RELEASE-QUALITY-LEDGER.json);
specific original comparison: [QA01](docs/QA01-EVENT-CAMPAIGN.md);
Windows build and release: [BRINGUP](docs/BRINGUP.md),
[validation](docs/VALIDATION.md);
graphics and widescreen: [WIDESCREEN](docs/WIDESCREEN.md).
Other dated documentation, historical work board, five-agent schedules,
CI optimization plans and legacy PRs are **reference material**, not
execution policy. Use [doc map](docs/README.md) only for the needed subsystem.

Consult original executable evidence and directly useful pinned
Baldosa/Malmazuke/redcomp-dream observations before implementing a duplicate
tool, but transfer only rights-compatible verified behavior or methods.
Human-made 3D racer modelling is currently paused pending collaborators;
do not divert Fidelity or Windows execution sessions into speculative 3D.

Make substantive fixes in the repo with source-bound tests and inspected
Actions results. Prefer one coherent PR, integrate after relevant actual CI
passes, update the active queue as soon as a discriminator changes, and
publish a concise final handoff: code/evidence, actual observed behavior,
accepted counters, one runnable next action, and whether your job is done
or needs more work. Don't need repeated "go on" messages to resume an
obvious executable job.
