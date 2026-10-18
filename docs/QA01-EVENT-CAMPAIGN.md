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

## Original 2014 post-result movie continuation (optional; QA-07)

The standard full-event producer stops at the independently observed stable
result +6 frames, so it does not yet observe subsequent result-screen
continuity, any returned menu, next course or persistence. The **existing**
`qa01-event-campaign.yml` now offers a default-off boolean
`source_followthrough` for *only the three already source-qualified cases*,
Zoo Circuit, Bowl timed Stunt, and Switcher Race B. It changes neither case
selection nor candidate or release acceptance.

The default producer retains its archived SMV source controller window
through **original result +40 frames**. Only when explicitly opted in, extend
that *same, unchanged movie* through result **+80**. No new buttons, durations,
ghost route, savestate or victory state are fabricated. The original
full-horizon WRAM trace identifies the independently observed 2014 result
onset and reads `track`, `menu` and `in_race` at movie result
**+8, +16, +24, +32, +64 and +72**. This covers the independently observed
original Switcher `0x99` screen through movie frame **17087** (result
17030 +57), instead of ending the experiment before its return-menu phase.
Missing source frames fail closed. The independently booted Snes9x/native
replays then collect full real **128 KiB WRAM snapshots** at those same
offsets measured from **each guest's separately observed fresh result
onset**. Script log receipts must prove each precise host frame (an exit code
or arbitrary dump filename is insufficient). Native and original event entries
continue to be calibrated independently, and input timing is unchanged.

The opt-in report lives under `source_terminal_followthrough` in the
existing `producer-report.json`. Every sampled row retains the three
different clock axes: original archived movie absolute frame, fresh original
host frame, and fresh native host frame. It includes source/original/native
named state, both fresh guests' laps/checkpoint/finish gate, SHA-256 of genuine
full-WRAM images, field-level disagreements and exact sample/dump provenance.
Raw guest bytes remain local to the CI case workspace and are **not**
uploaded. Version 2 of the optional compact report records six sample rows,
with `all_followthrough_named_pairs_equal` and
`all_followthrough_full_wram_pairs_equal` reporting distinct semantic and
bytewise outcomes. The primary strict `paired_event_candidate`, event comparator,
campaign `strict_divergence` classification and `release_admissions: 0`
are unchanged. This report cannot prove SRAM persistence, final menu
restoration, valid next-event selection or independent PC/APU correctness.
An equal result-relative state is **not automatically** equal race-relative
gameplay, particularly with the already observed Zoo +5163/+5162, Bowl
+3365/+3364 and Switcher +4704/+4702 terminal differences.

The decision is bounded: determine whether the authentic post-result
controller continuation remains on the result, enters another state, or
diverges between original/native. If it changes, isolate the earliest
+8…+72 sampled mismatch and perform a narrow verified source input /
actual consumer trace. If all agree semantically, that supports only
continuation for those 72 source-result-relative frames; it does not erase
the earlier strict result phase mismatch or justify increasing 0/45.
To execute, manually choose `selected=zoom-zoo` and
`source_followthrough=true` on the existing campaign. Repeat for Bowl or
Switcher only if the first case changes the next decision, or choose
`selected=all` when a justified comparative campaign is required.
The optional observation and tests do **not** produce a newly executed real
SNES witness merely by merging; real results require a separately checked
workflow run.

**Three-project reuse:** UR's source-qualified 2014 SMV extractor, Snes9x
reference, full guest dump recorder and strict event comparator are reused
unchanged; Baldosa's pinned native research guest remains a separate
execution oracle, while malmazuke's PAL replay/source knowledge remains a
qualified lead only. No new workflow, new CI trigger, replacement emulator,
guest logic, CPU/APU runtime correction or second 45-course denominator
was introduced.

## Independent primary-artifact receipt audit (2026-10-18)

The manual campaign's aggregate rechecks the derived `case-result.json`
assertions but does not itself reopen the source `producer-report.json`.
A complete-looking derived receipt can therefore outlive an altered or
missing primary source JSON. The aggregate job now runs the ROM-free,
read-only `tools/qa01_event_primary_artifact_audit.py` on its already-downloaded
case artifacts, with no extra emulator build, workflow trigger or runner.
It checks the exact producer bytes against their recorded SHA-256,
requires the **original shared build's three-line SHA256SUMS** in each case
archive, checks original/native producer executable digests against that
already-verified manifest and checks the manifest identity across case
shards. It retains the third staged `snesref` digest for build provenance
without claiming the manifest by itself proves emulator execution.
The checker additionally requires the full advertised original/native
sampled-frame population,
reconstructs the first sampled named-field divergence and fresh-entry
equivalence from raw observation rows, reclassifies each case from the
primary report and compares the entire derived receipt. It also recomputes the published aggregate and rejects
unexpected case directories. The audit's separate JSON and job summary
explicitly distinguish **verified transport only** from acceptance.

For local inspection of downloaded plan, cases and aggregate:

```bash
python3 tools/qa01_event_primary_artifact_audit.py \
  --plan qa01-plan.json --results-dir cases/ \
  --campaign-result campaign-result.json \
  --out qa01-primary-artifact-audit.json
```

Any missing primary report or SHA256SUMS, changed producer bytes,
different case manifest, mismatched executable digest, forged case summary,
aggregate disagreement or producer failure is an incomplete/invalid audit;
it cannot be promoted as source-authentic coverage. The checker does
**not** authenticate original emulator execution independently of the
producer, verify original ROM bytes from an archive, decide causal CPU/APU
equivalence, or grant event/release credit. It stays a second transport
integrity check; QA-01/07 and the census retain full admission authority.

### Controller replay identity and completeness

The existing event producer already constructs the actual Snes9x and pinned
Baldosa injected-input files after independently calibrating both guest
entry frames. The manual case artifact now also retains its
\`work/<case>/replay/ref.input\`, \`pinned-baldosa.input\`, \`complete.script\`,
and optional exact Switcher original-only supplementary script. The same
read-only primary-artifact auditor checks all nonzero masks, durations and
ordinal order against the **exact observed native frame shift**, checks the
SHA256 of the executed reference/native script against the original producer
hashes, and requires every advertised sparse sample's dump command, terminal
onset, and settled result. Each case retains both original input-file digests
in the compact audit receipt. Missing or mismatched routes are invalid
transport, not gameplay divergence.

The files are *supplied controller events* generated from the original SMV,
not an independently measured consumed-button bus trace. Matching input
files do not prove the original/native engines latched each mask on the
same CPU phase, nor that unsampled game frames agree. Retain guest input
execution evidence and independent QA-01/07 authority. No original 2014 movie, ROM or native executable is added to the retained case archive. **New opt-in raw Zoo full-memory guest captures** are separately retained and independently rechecked as described below; these are real Snes9x/Baldosa WRAM and SRAM images, never synthesized gameplay states.

### Original/native result-gate claim reconstruction

A second source-only check, \`tools/qa01_event_result_gate_audit.py\`,
independently recalculates the existing producer's eight raw result claims
from retained guest observations. It verifies actual onset/stable result
menu, original versus native final/intermediate PPU text, the archived
MIKE/P1 positive time or stunt score, observed Circuit lap decrements,
the final zero-lap state and non-active terminal race bytes. Both positive
and negative claims must agree with these raw source records. The
existing first sampled-field comparison, source-entry flags, source/native
relative terminal clocks, source-progression and SRAM witnesses remain
separate checks.

This validator deliberately mirrors the **existing** original event
producer's rules without changing the producer or independently
declaring a complete-event pass. It rejects a self-consistent set of
reported booleans when the underlying observed guest result disagrees.
It does not reconstruct decoded text directly from original PPU binary
bytes (the producer owns that capture), prove unsampled laps/frames, or
establish input-consumer timing. No additional emulator execution,
release ledger write or 45-event credit is introduced.

### Original/raw Zoo checkpoint and earned SRAM bytes (2026-10-18)

Earlier RF054 Zoo research [run 39161563837](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837) genuinely executed **78 original/native full-WRAM checkpoint comparisons**, observed result +5163 and next Bowl +267, and reported 11 matching earned full-SRAM handoff snapshots, but its original 18-member case ZIP did **not** retain the actual 128KiB/8KiB guest images. [The independently rehashed original four-artifact review](../analysis/data/qa01-rf054-independently-rehashed-four-artifact-bundle-20261018.json) can validate source, genuine ELF/core bytes, logs and producer arithmetic, **not recompute those 78+11 memory pairs** from unavailable historical bytes. No retroactive parity claim is permitted.

The existing **manual-only** campaign now retains only the **already-generated original/native `*.wram.bin` and `*.sram.bin` images** under `work/<case>/replay/{ref,native}/` alongside its original producer, binary SHA manifest, input and execution logs, within the existing 7-day case artifact. This may increase ZIP size but adds **zero** new guest simulation, separate build, recurring workflow or artificial evidence. No game ROM, movie, savestate or compiled research ELF is copied into the case artifact.

For `selected=zoom-zoo` with **all three** `zoo_race_mesh=true`, `zoo_dp_window=true`, `zoo_next_bowl=true`, the successful existing case job runs `tools/qa01_zoo_raw_archive_audit.py`. The verifier reopens **every byte** in the 78 original/native 128-KiB WRAM checkpoint pairs and the 11 Zoo→Bowl full WRAM/8-KiB SRAM pairs, requires unique correct logged dump host frames, checks all SHA-256/count/first-byte/changed-page producer claims, recalculates the earned 2510-centisecond Zoo rank and complete record-table checksum, and refuses truncated, missing or inconsistent raw images **even if the producer summary says passed**. Its exact additional receipt is `qa01-zoo-independent-raw-audit.json`; the signed source/gameplay acceptance obligations are **unchanged**.

To recheck a downloaded and extracted authentic original case artifact containing these raw files:

```bash
python3 tools/qa01_zoo_raw_archive_audit.py \
  --artifact-root /path/to/extracted/qa01-campaign-case-zoom-zoo \
  --out /tmp/qa01-zoo-independent-raw-audit.json
```

An observed nonmatching byte is a **verified bounded difference**, not an invalid artifact. A missing/tampered raw image, contradictory digest/count/host clock or fabricated positive **is** invalid evidence. Even full exact 78+11 raw-memory agreement would not prove every unsampled game frame, CPU/SPC instruction causality, the shipping Windows PE, source-consumed gamepad input or disk/power-cut persistence. The read-only audit **always holds accepted USA events at 0**, leaving independent QA-01/07 and the 45-event census sole authority. Its unit tests are synthesized ROM-free byte fixtures and cannot stand in for a real guest run.

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

## Original executed APU read → acknowledgement branch provenance (2026-10-14)

RF-015 is the highest-value shared result-handoff discriminator: on the
separately executed two-seat seed `50036056`, Baldosa's 33-frame `0x84`
result prelude is shorter than the original 34-frame reference, and the
first observed difference is the `7E:2000` sound-command queue before a
`7E:00C6` vblank-wait pass. **This is not itself a proved APU cause.**
The existing **manual**, opt-in `qa01_apu_phase` source observer for historical
Zoo is available to collect a different genuine original 1P event. Its
output must never be merged numerically with seed `50036056` as though
the two controller movies or APU histories were the same.

The existing `tools/qa01_apu_phase_report.py` now also reports
`original_ack_read_branch_pairs_count`,
`original_ack_read_branch_pairs_sample` (up to 16), and explicit unpaired
read/branch counts. It associates an executed original **`82:803C`
`LDA $2142`** with the immediately following *logged* **`82:8043`
`BNE`** only when the sparse executed-PC stream and original frame
boundary support the association. Each reported pair contains the returned
low A byte, effective I/O-mapped data bank, branch **actual next PC**,
queue indices/toggle and original-frame receipts. An intervening logged
opcode, missing read, or unexplained frame gap produces **unpaired evidence**
rather than a fabricated queue decision. Synthetic adversarial tests cover
these failure modes.

**Do not infer BNE from the stored `Registers.PL` zero bit.** Snes9x can
maintain effective flags lazily; a captured pre-op `PL` is not automatically
the executed branch predicate. The next PC is the observed outcome. The new
pairing does not match any native AOT read to that original branch, correlate
CPU/APU master clocks, establish `$4212` wait equivalence, rewrite result
timing, or waive the strict original/native event comparator. It is a
**read-only analysis improvement**, with `release_gate_credit: 0`.

**Smallest decision-bearing follow-up:** dispatch only a deliberate
`selected=zoom-zoo`, `qa01_apu_phase=true` campaign with pinned original
movie, ROM/core/native executable and independent entry receipts. Inspect
unpaired counts *first* and the source-local read/branch outcomes around
the +5156…+5163 result boundary. Compare corresponding native `$2142`
reads and queue snapshots only after establishing a valid clock and input
identity mapping. If APU acknowledgement is demonstrably earlier, hand the
exact original CPU PC/beam, native port-clock and `$4212` wait receipts to
the separate CPU/APU timing owner; this gameplay lane must not implement its
runtime fix. If no causal difference exists, return to the documented
upstream Zoo +5156/+5157 restore transition and source finish-decision
owner. The 2014 Zoo source and the 2P finish seed are **separate experiments**.

Three-project reuse preflight: UR already owns the full-event source probe
and first-difference machinery; Baldosa's imported route/firstdiff tools and
malmazuke's pinned replay/finish analysis remain research aids, not alternate
USA oracles. No new runner, recompiler, comparator, CI trigger or gate owner
was introduced. The retained three-event source matrix still records Zoo
+5163/+5162, Bowl +3365/+3364, Switcher +4704/+4702 guest-relative
results, all strict mismatches. **Accepted USA events remain 0/45.**

## 2026-10-15: close the Zoo postframe observation gap before further theory

The optional original/native `--zoo-terminal-phase` probe previously captured **+5156..+5173** consecutively. It stopped *before* RF-015's observed Zoom Zoo result-screen return difference at **+5179 native / +5180 original**, while the separate source follow-through samples only +8, +16, +24, +32, +64 and +72 from each result onset. The first mismatch among those six observations (+16) cannot be promoted to the actual first divergent guest frame.

The owned producer now extends the existing **independent fixed guest race-entry-relative postframe observer to +5156..+5186** (31 consecutive original and native snapshots; same archived input). No new guest, runner, event acceptance rule or CI workflow is created. In addition to the existing same-relative and same-absolute-host comparisons, it reports a `contiguous_post_result_observation` covering the overlapping post-onset range with separately named **first observed** differences in (a) named fields, (b) gameplay fields, (c) raw `7E:009F` text cursor, and (d) whole-WRAM digests. The last three are *different evidence classes*: cursor/raw WRAM changes alone cannot establish a differing event decision, and no postframe alone locates a divergent source CPU instruction. The report explicitly denies CPU writer proof, cold-process SRAM persistence and release-event credit. Unit fixtures create a corrected-onset (+5163/+5163), return-edge (+5179/+5180) negative example; they are not original-emulator observations.

**Next execution, scoped to one decision:** manually run the *existing* `qa01-event-campaign.yml` with `selected=zoom-zoo`, `baldosa_refresh_beam_rate=true`, `zoo_terminal_phase=true` and `source_followthrough=true` on the reviewed SHA. Preserve exact native ELF and original core/ROM/movie hashes, original and native entry-frame receipts and the fixed-frame `reference.log`/`native.log`. Verify the first differing **source-qualified observed postframe** against the original source movie and distinguish same-guest-relative from same-host comparisons. Only if it identifies a genuine timing/logic difference should Agent 5 receive a bounded CPU/beam/PC handoff. If the original/native first changed field is only `wTextPos` or free-running scratch, locate its live reader and upstream instruction before calling it a gameplay defect. Stop if the next observation cannot change the strict decision; do not run a 45-course breadth sweep.

**Current execution status:** this instrument change carries no new executed original/native receipt and no corrected full-event admission. Pending an actual matching full source/result/return/progression and cold-process persistence witness, the authoritative ledger remains **0/45 complete USA events**. The existing `strict_candidate` is an onset-level investigative label and cannot be expanded by this diagnostic.


## Executed Zoo-to-Bowl raw-memory residual audit (2026-10-16)

The genuine 2014 original movie, fresh original emulator and Baldosa research
guest were independently re-examined from **three archived original/native case
ZIPs**, not re-emulated. The SHA-bound
[three-case review](../analysis/data/qa01-archived-zoo-bowl-raw-wram-3run-review-20261016.json)
retains actual producer-report digests, all eleven result-relative
+259/+263/+264/+265/+266/+267/+268/+269/+272/+276/+280 sample counts and
guest-entry provenance. The RF-015+017 controls are Actions runs
[38847972295](https://github.com/gamesbyian/UR-Recomp/actions/runs/38847972295)
and [38848262320](https://github.com/gamesbyian/UR-Recomp/actions/runs/38848262320);
the RF-018-only treatment is
[38861174758](https://github.com/gamesbyian/UR-Recomp/actions/runs/38861174758).

| Bounded source-original/native handoff fact | RF-018 off, both independently repeated controls | RF-018 on |
| --- | ---: | ---: |
| Source/fresh-original/native next-Bowl entry relative to Zoo result | +267 / +267 / +267 | +267 / +267 / **+265** |
| Named gameplay triplet matching source in eleven samples | 11 | 9 |
| Matching complete 8 KiB original/native SRAM samples | 11 | 0 |
| Matching complete 128 KiB original/native WRAM samples | **8** | 0 |
| Total unmasked WRAM differing-byte *occurrences*, all eleven pairs | **12** | **2,203** |

The control WRAM differences are limited to **four bytes each at +266, +267
and +280**. They concern stack addresses `7E:01ED–01F0`, and at +267
also `7E:2000/2004` (sound-command queue). There is no evidence-based waiver:
matching visible/named states, authentic +267 entry and complete SRAM do **not**
establish raw 128 KiB WRAM parity, equal CPU PC, or continuous-frame parity.

The independent campaign's bounded `next_bowl_bounded` classification therefore
retains its established semantics: `bounded_source_handoff_agreement` means
the observed named/source entry, earned record/checksum and 8 KiB SRAM contract
passed. It **does not mean all sampled WRAM bytes agree**. The report now
separately preserves `all_sampled_full_wram_pairs_equal`,
`raw_wram_differing_sample_offsets` and
`raw_wram_differing_byte_occurrences`, and its aggregate exposes how many
case reports have unmasked next-Bowl residuals. A real RF-018 +265 progression
difference remains `sampled_progression_divergence`; missing or contradictory
WRAM/source/guest receipt claims are producer errors. Neither scientific
outcome changes the primary result-only `strict_candidate` label or authorizes
course release credit. **USA acceptance: 0/45**.

This audit reused the existing original/native emitter, Baldosa research
bridge and source-movie input identities. It introduced no extra emulator run,
original controller rephase, Windows build, altered byte mask, automatic CI
factory or release-ledger write. See source-owner
[CPU/APU #1689](https://github.com/gamesbyian/UR-Recomp/issues/1689)
for executed clock/instruction attribution; [#1686](https://github.com/gamesbyian/UR-Recomp/issues/1686)
remains the separate actual Windows RF-017 shipping-source mismatch.
