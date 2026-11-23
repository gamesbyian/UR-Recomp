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
or owner intervention per experiment retry. The owner's Windows PC, its GitHub integration and Desktop Commander are
available as an **exception-based diagnostic/acceptance station**, never as
routine CI compute. Use hosted Actions by default; escalate only when a
specific interactive Windows, GPU/audio, input, process or filesystem question
is more efficiently or decisively tested on the PC. See the escalation rules
below. Do not make the PC a required dependency for hourly progress.

On a genuinely external dependency, write the **exact source SHA, owning
workstream, attempted commands and GHA run/artifact, observed failure,
blocker owner, next executable command/location, prerequisite and
observable completion condition**. Then work the next independent task.
Repeated identical blockers without an attempted fix are failure of the
development operation.

## Failed tests are owned engineering tasks (2026-11-21)

Both scheduled agents are **explicitly authorized and required** to diagnose,
repair and rerun failing tests, including the tests themselves. Never assume
that a red test means the game is broken or that a green test proves the game
correct. Read the exact failed job, command, first causal error, input
fixtures, actual application behavior and source SHA before changing code.
Choose the correction by evidence:

- **Game defect:** fix runtime behavior; preserve or strengthen the test
  that exposed it. Prove the test fails before and passes after the fix.
- **Test/fixture/driver defect:** fix erroneous expectations, scripts, frame
  clocks, mocks, probes, selectors, test inputs or assertions; establish the
  authoritative intended behavior independently and add a regression that
  would reject the old mistake. Do not modify game physics or progression
  to satisfy a faulty test.
- **Runner/transport/CI defect:** repair the environment or infrastructure
  only as far as necessary to execute the relevant test, then inspect its
  actual game/evidence result. Treat artifact expiry, missing inputs and
  cancelled workflows separately from genuine assertion failures.
- **Unresolved source semantics:** minimize the case and obtain one real
  original/native or product observation distinguishing hypotheses before
  choosing either fix. Avoid speculative controller, clock or renderer edits.

The agent may change, replace or delete obsolete test logic **only with a
specific justification and an equivalent or stronger retained behavioral
assertion**. Never weaken or skip required coverage to get a green check,
change expected values solely to match an incorrect implementation, mask
genuine mismatches, accept an unauthenticated artifact, or claim qualification
from a passing harness. For a revised assertion document the source of
truth (original witness, explicit product contract or independent valid
capture), demonstrate how the prior assertion was wrong, and test both
the valid case and an invalid/tampered case.

The repair is not complete until the relevant exact-head CI is green **and**
the real behavior/evidence has been examined. When red, iterate on the first
causal failure rather than treating failure reports as handoffs. If the exact
test cannot run, record why and use the next executable independent task.
Test repairs count as legitimate engineering progress but are not automatically
player-facing feature delivery or release/course acceptance.

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

## Diagnostic discipline and owner-PC escalation (2026-11-23)

**Pass labels are contracts, not print statements.** Inspect the production
behavior and the assertions that actually caused a workflow to pass. For QA-03
a test claiming `SECOND_GUEST_LEG=PASS` MUST demonstrate a genuinely guest-
raced second fixture, source-bound scored result, a distinct committed fixture
receipt, correct standings and (for complete QA-03) a cold reopen. First-leg
`FIXTURE_COMMITTED`, `ARMED fixture=1`, controller traces and a green
`script_linux` job are **diagnostic-only**. Specifically, run 45259968883
was green because of those weaker assertions while stock `race_state=00`
persisted; no second scored race was established. Fix the assertion/driver,
not the acceptance threshold. Failed assertions are useful evidence.

For every bounded measurement, declare the hypothesis, contrasting possible
outcomes, and the next action each outcome would trigger. After **at most
two consecutive measurement/harness-only sessions on the same question**,
either execute a source-level gameplay repair justified by evidence or switch
to a genuinely different independently executable player journey. A new
timestamp, trace field, script syntax fix or repeat run does not reset that
counter. Do not change native gameplay to silence a faulty fixture; the
existing failed-test root-cause instructions still apply. At the end of
each run, identify actual code changed, source SHA, run/artifact, whether a
second fixture/event actually finished, and whether there was a product fix,
complete journey, decisive difference or evidence-only outcome.

The owner explicitly authorizes GitHub integration on the Windows PC and the
connected Desktop Commander plugin as a **specialist escalation path**.
Use GitHub-hosted runners for build/test loops, then the PC when direct native
Windows execution would resolve a live blocker faster than more scripted
guesswork. Verify device availability/capabilities before use; Desktop
Commander exposes command/process/file tools, but **dedicated GUI clicking,
screenshots and controller injection must not be presumed**. Explore only
safe, bounded supported access. Prefer one targeted batched PowerShell
inspection/repro rather than repeated inventory or hourly polling. Do not
install persistent agents, self-hosted runners, startup services or scheduled
PC jobs, and do not kill unrelated processes, change machine configuration,
delete private files, expose credentials or copy private ROMs to public
artifacts. Use a dedicated repo/test directory and non-destructive actions;
ask the owner only when a disruptive operation is genuinely required. Record
reproducible nonsecret findings/sha in GitHub and validate the eventual
source change via hosted CI. A PC witness must not be called physical
acceptance without the exact actual test and independent criteria.

**Retention CONFIRMED 2026-11-23:** GitHub CLI authenticated on the
owner's Windows PC downloaded original/native Zoo run 44954472753
artifacts 14727143188 and 14726528257 to private local
`%LOCALAPPDATA%\\UR-Recomp\\private-evidence\\zoo-20261121-run-44954472753`.
The resulting 322 files total 49,435,318 bytes; `manifest.json` records
the source SHA, artifact IDs and SHA-256 of each recovered file. The
retrieval process exited 0. **Do not repeatedly redownload** during hourly
agent runs or upload any original ROM/proprietary binaries to public GitHub.
This is private PC preservation, not qualification; verify local availability
before depending on it, and use hosted CI for reproducible game tests.

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
