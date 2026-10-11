# QA-01 bounded original/native event campaign

Status: **manual research infrastructure; not a release gate**. Owns orchestration
only. The existing original/native event producer and strict comparator remain
authoritative. For current delivery priorities read [WORK-QUEUE.md](WORK-QUEUE.md);
for CI policy read [CI-WORKFLOW-BEST-PRACTICES.md](CI-WORKFLOW-BEST-PRACTICES.md).

## Why this exists

Agents repeatedly invoke source-qualified original/native event probes and then
inspect large job logs one event at a time. The campaign runs only the **three
already source-qualified historical scenes** in one deliberate invocation,
compiles the pinned original reference and historical Baldosa research guest once,
fans out independent case execution, and gives a single identity-bound summary
with explicit missingness. It is a reusable *transport baseline* for later
coverage, not a new 45-course runner.

The first population is:

| Case | USA course | Existing producer | Expected current evidence status |
| --- | --- | --- | --- |
| zoom-zoo | course:02, Circuit | \`probe_original_event_complete.py --case zoom-zoo\` | Strict guest-relative result phase unresolved |
| bowl | course:03, scored Stunt | \`--case bowl\` | Strict one-frame result-phase discrepancy unresolved |
| switcher | course:04, Race B | \`--case switcher\` | Strict guest-relative result-phase discrepancy unresolved |

The event producer requires the original archived movie to show a genuine
complete event; it then executes matched historical controller inputs from
stock, independently observed guest entries. A report with matching result
text but misaligned terminal guest frames remains **strict_divergence**. Even a
\`strict_candidate\` is still *investigative* until reviewed against the full
QA-01 admission protocol.

**Important scope boundary:** the native input in this pilot is the exact
pinned historical Baldosa QA guest already used by the existing original/native
event probes, **not the current integrated Modern Windows product executable**.
This campaign therefore checks the historical original/native event research
baseline and the quality of its evidence apparatus. It does not clear
end-to-end current-Baldosa shipping fidelity, player journeys, or any L4/L5
release gate. A later production-candidate adapter must preserve full
original-source independence and be separately validated before reuse.

## Running it

1. In GitHub Actions, open **QA-01 bounded original/native event campaign**.
2. Choose a branch/ref containing the workflow. Use the \`selected\` menu
   to run \`all\` or one existing source-qualified event.
3. Inspect the run's **plan** and **aggregate** job summaries first. Only
   download per-case artifacts and logs for named ambiguities or failures.

There is **no** PR, push, schedule or downstream workflow trigger. Multiple
manual runs on the same ref are serialized (never automatically cancelled).
The three cases may run on up to two independent Ubuntu 22.04 runners.
One producer compiles Snes9x, snesref and the native research guest once.
Each case uses its own pristine process/work root. Case jobs have 90-minute
hard timeouts and an inner 75-minute producer cap; build and aggregator have
separate bounds. This is a deliberately limited population, not a
CPU-unbounded overnight fuzz campaign. Expand only for an accepted,
decision-bearing case family, and consider its marginal evidentiary value first.

Execution is deterministic for fixed ROM/movie/source/toolchains/inputs,
subject to the existing original-emulator implementation and host timing
limitations. Before changing run flags, compare with the owning historical
workflow and reverify original/native admission invariants.

## Artifacts and contract

- \`qa01-campaign-plan\`: \`qa01-plan.json\`, exact checked-out source
  SHA and selected case manifest with stable SHA-256.
- \`qa01-campaign-reference-and-native-binaries\`: three checked binaries
  and a verified \`SHA256SUMS\` file; shared by case jobs. Retained 7 days.
- \`qa01-campaign-case-<id>\`: classification \`case-result.json\`,
  original producer JSON and bounded diagnostic logs, retained 7 days.
- \`qa01-campaign-aggregate\`: \`campaign-result.json\`, retained 14 days.
  The aggregate's Markdown is also written to the Actions Job Summary.

The deterministic entrypoint is \`tools/qa01_event_campaign.py\` with
\`plan\`, \`classify\` and \`aggregate\` subcommands. \`tests/unit/
test_qa01_event_campaign.py\` validates selection, provenance, no-credit
policy, bad/missing evidence, aggregate exits and workflow trigger boundaries.
The producer remains \`tools/probe_original_event_complete.py\`.

Known dispositions:

| Disposition | Meaning | Campaign green? | QA-01 admission |
| --- | --- | --- | --- |
| \`strict_candidate\` | Producer says paired event met its current strict candidate assertions | Yes, if all case receipts complete | **No automatic credit** |
| \`strict_divergence\` | Authentic original/native result observed but strict paired comparison negative | Yes, scientific negative and complete transport | **No credit** |
| \`producer_error\` | Producer died/timed out, report missing/invalid or provenance inconsistent | No | No credit |
| \`missing_evidence\` | Expected case receipt absent or modified, e.g. cancelled runner | No | No credit |

A green **campaign means complete, coherent experiment transport**, not that
the remake passed fidelity. A strict divergence is an expected scientifically
useful negative, so it must not be silently converted to pass, nor misreported
as an infrastructure crash. The aggregator checks that *all planned* cases
supplied valid matching receipts, rejects unexpected case directories and
reports exact missingness. It always sets \`release_admissions: 0\`. It never
modifies \`RELEASE-QUALITY-LEDGER.json\` or checks into \`main\`.

Raw ROMs, historical controller movie bytes, guest dumps, user data and complete
compiled build trees must not be uploaded as case artifacts. The reference
and native binaries are ephemeral CI build inputs; redistribute no ROM bytes.
Only promote small durable, reviewed decision-bearing evidence to \`analysis/
data/\` or the owning QA document. Run artifacts expire.

## First full-run correction (2026-10-11)

The first real dispatch, [run 38169094991](https://github.com/gamesbyian/UR-Recomp/actions/runs/38169094991), completed the shared build and all three case *jobs*, but **none produced a completed paired-event JSON**. Its aggregate was correctly red with three `producer_error` receipts, not three actual strict gameplay divergences:

- Both Bowl and Switcher native calibration processes failed to load `libOpenGL.so.0` on the slimmer case runners. Case runners now install the required ELF runtime libraries and reject missing `ldd` dependencies before invoking any producer.
- Zoom Zoo's independent 2014 original movie revealed the genuine 34-active-frame temporary course-ID=0 result handoff at source frames 8314–8347, restoring track 1 at 8348–8351 and entering the settled Circuit result at 8353. Its source selector previously permitted the equivalent narrowly attested terminal handoffs for Switcher and Bowl but rejected Zoom Zoo. The new *original-only* qualifier checks each exact boundary and stable `0xBC` result, with negative tests for shifts, foreign courses, bad return, prior active courses and unstable results. This does not alter native timing or the strict comparator.
- Failed producers now fail the individual case job as well as the aggregate, with a bounded root-cause excerpt in each case receipt and summary. A genuine strict negative still means successfully completed research transport, not QA-01 acceptance.

Run completion or green transport must not be inferred from three green job wrappers. A future dispatch is necessary to prove these repairs against real original/native binaries; do not claim that the failed first dispatch provided any complete paired-event evidence.

## Zoo boundary discriminator (manual, optional)

The successful three-case [run 38171397687](https://github.com/gamesbyian/UR-Recomp/actions/runs/38171397687)
confirms **3/3 coherent completed transports, 3 strict scientific divergences,
zero native/reference producer errors and zero release admissions**. Zoo source
and fresh guests match entry signatures and all 43 sparsely sampled gameplay
states, with identical settled PPU result but a genuine *guest-relative* 1-frame
result-onset delta (+5163 original vs +5162 native). The prior executed input
latch experiment ruled out a blanket +/-1 input-stream correction. Existing
[original event census](ORIGINAL-COURSE-EVENT-CENSUS.md) identifies the
remaining decision: whether host polling or gameplay phase first separates
during the authentic +5158..+5173 Zoo result boundary.

**Cheapest new discriminator:** manually dispatch this *existing* workflow
with **selected=zoom-zoo** and **zoo_terminal_phase=true**. The opt-in causes
one separate fresh original/native pair, using the same pinned ROM/movie,
SRAM, reference core and research Baldosa binary, and identical controller
stream and real independently calibrated entries. It captures full actual
128-KiB guest WRAM (not synthetic result state) at fixed relative offsets
+5156..+5173. Its auxiliary script uses waits and dumps, *not* a terminal
"until" poll, patch, altered game rules or input rebase. The primary strict
replay still runs and determines the scientific disposition, unchanged.

The optional result is in the existing producer JSON under
"zoo_terminal_host_phase". It provides independently observed host frame
for each snapshot, first four-frame-stable Circuit result for each guest,
offset from that guest's original primary "until"-observed result,
named field and full WRAM-hash equality on **both** distinct alignment axes,
the script SHA-256 and 0 release credit. Aux logs are uploaded; raw guest
memory is not published. A missing dump, invalid 128-KiB capture,
unexpected course, changed entry or forged host/guest relation fails closed.

**Interpretation:** first compare the fixed-frame onset to each primary
"until" result. If one is offset, investigate that core/script polling
boundary before touching game logic. If first fixed result transitions
really disagree, inspect same-host versus same-relative menu/track/race
and lap/clock progression at the first differing frame to select a targeted
writer/reader or scheduler experiment. Never call equal named-field hashes
CPU/interrupt parity; never globally add a frame or admit a course.
The experiment intentionally does **not** resolve Switcher's actively
owned NMI/stack work or the already executed Bowl 8-frame tally phase.

**Stop:** one source-qualified diagnostic is enough to choose which
clock boundary needs causal tracing. If it cannot distinguish them,
record that inability; do not commission another unbounded replay batch.

## Failure triage and extension

When infrastructure is red, use the aggregate's first missing/invalid case,
then the corresponding case result, then its bounded producer log. Do not
open unrelated CI jobs or repeat a successful case blindly. If a scientific
negative is new, compare its source/ROM/core/movie hashes and earliest
divergence with prior proof, then commission one bounded hypothesis test in
the owning gameplay lane.

To add a course/event later, first obtain **an independently demonstrated
complete original event** and valid fresh-entry native producer. Then update
the existing semantic event runner's allowlisted cases, this campaign's
bounded case registry, and synthetic tests. Never generate 45 selections from
\`course-corpus.json\` merely because 45 RNC streams are known. Confirm the
new cohort's expected wall cost and extend the selected campaign only when
the same observer, input and source-admission contract applies.

For long-running future storage and graphics campaigns, reuse the manifest,
shared-candidate, isolated work-root, compact receipt and aggregation
pattern, but keep their own existing semantic validators, QA owners,
physical-evidence requirements and minimal discriminators. Do not create
a second generalized test oracle or automatically trigger hours-long work.
