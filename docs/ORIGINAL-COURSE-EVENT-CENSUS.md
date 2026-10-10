> **Fixed-frame terminal discriminator (2026-10-09, merged #1098):** The latest [original/native guest run 38005782923](https://github.com/gamesbyian/UR-Recomp/actions/runs/38005782923) removes `until 009F == BC` polling entirely and samples 18 **identical guest-relative frames +5158..+5175** from the same independently observed active Zoo entry and unchanged 2014 button stream. The **one-frame native lead is real in sampled guest state**, not merely script polling: `7E:0313` first leaves active race at **+5161 Baldosa vs +5162 Snes9x**, and actual result `7E:009F = BC` appears **+5162 Baldosa vs +5163 Snes9x**. Both P1 and P2 have **zero laps, checkpoint 1 and gate 1** before the transition, and **both ultimately print identical settled times and best laps**. The previously suspicious saved P1/P2 contacts differ transiently between **+5170..+5172**, but **converge to the same values by +5173**, so a result-only sample 8 frames after independently observed result onset is not comparable as though it were the same guest-result phase. Raw DP `C6/C8` already have a one-step phase difference at +5158, of **unknown cause and gameplay meaning**. Precise [durable observed boundary evidence](../analysis/data/zoo-original-baldosa-fixed-result-boundary.json) and [source WRAM/PPU captures](https://github.com/gamesbyian/UR-Recomp/actions/runs/38005782923/artifacts/11650174888). The next narrow producer adds pre-result samples (+4700..+5157) to locate the onset of the transient phase slip without globally shifting inputs. This is a real guest-transition frame discrepancy, **still 0/45 independently accepted USA complete pairs**. No rules or controller workaround authorized.

> **Controller-latch falsification (2026-10-09, merged #1093):** A single pinned Baldosa guest build replayed the same original 2014 Zoo input at native scene-origin offsets **-1, 0, +1** against the **same independent Snes9x reference**, with original controller masks/durations unchanged. **Only phase 0** completed Circuit and matched the displayed original result; both shifted variants **first visibly disagreed in P1 course position/contact/checkpoint at scene-relative +604**, missed the second lap credit at +1721 (**native 3 remaining vs original 2**), still had **3 laps remaining** at +4700 (original **1**), and never reached Circuit result by relative +5900. This rules out a **simple whole-input ±1 frame rebase** as a correction for the remaining **one-frame result-menu observation delta**. It does **not** prove whether the residual one-frame offset is a host `until` polling convention or a genuine result-transition timing difference. Durable [three-phase original/native evidence](../analysis/data/zoo-original-baldosa-latch-phase-discriminator.json), [CI run 38004850276](https://github.com/gamesbyian/UR-Recomp/actions/runs/38004850276) and [raw phase captures](https://github.com/gamesbyian/UR-Recomp/actions/runs/38004850276/artifacts/11650877148). Official course acceptance stays **0/45**. Next: **fixed scene-relative boundary captures +5158 through +5173 in both guests**, requiring causal frame-level distinction rather than adding per-course offsets.

> **Latest original/Baldosa completed-Circuit candidate (2026-10-09, PR #1091):** Both independently booted guests play the unchanged 2014 Zoom Zoo controller scene through a genuine **lap-zero stable result**. Their canonical USA stream-2 50,665-byte course payload is resident at **all 7/7 active checkpoints on each guest**, and **all 14 named semantic fields agree** at all seven active samples (positions, both stored contacts, checkpoint, finish gate, laps and stopwatch included). The native and original settled *displayed* results are byte-for-byte equal as decoded PPU text: **MIKE 1:16.46, best lap 0:25.10; BRONSEN 1:20.07, best lap 0:26.45**, with LAPS ON ZOOM ZOO. Both result-onset WRAM samples have P1 laps=0, contact words=0 and result menu 0xBC. Remaining discrepancies: guest-relative result onset **+5163 original vs +5162 Baldosa** (one frame), and **only at the eight-frame-later result-stable observation** P1 contact 0 vs 10240 and P2 contact 0 vs 512. Non-semantic WRAM differences also occur at some active frames; **3/9 full 128-KiB snapshot pairs** match exactly. Durable compact [independent native/reference evidence](../analysis/data/zoo-original-baldosa-completed-circuit-candidate.json) preserves source/ROM/build provenance, matching PPU rows, per-sample lap/contact progression, raw WRAM differences, and the two unresolved gates. CI evidence: [run 38003554403](https://github.com/gamesbyian/UR-Recomp/actions/runs/38003554403), [captured original/native artifacts](https://github.com/gamesbyian/UR-Recomp/actions/runs/38003554403/artifacts/11650466437) (retained for 7 days), unmodified reference input and ROM. This eliminates the earlier *unverified PPU result* gap and localizes observed contact disagreement to post-transition, but does not yet decide a one-frame controller/host-latch phase or prove post-result contact fields semantically irrelevant. **Official QA-01 acceptance remains 0/45 USA** pending decisive phase/terminal-difference adjudication and reviewed reproducibility; this is a high-value complete-Circuit **candidate**, not an admitted release case.

> **2026-10-09 integrated original/Baldosa QA rule:** This file owns the exact 45 USA event denominator and the independent original-native settled-result admission protocol. The Baldosa source runs and merged 2P/window/pause/CRC bridges are valuable **test inputs**, not complete-event passes. Merged #1079 owns the completed original+native Zoo scene transplant; its result-state semantic difference needs investigation; build the first genuine Race/Circuit/45s Stunt result pair from existing runners before broad automation. The release ledger currently reports **0/45 complete**; do not promote from menu return or WRAM equality. Shared candidate and current implementation owner: [WORK-QUEUE.md](WORK-QUEUE.md).

> **External route lead, 2026-10-09:** `baldosa/uniracers-recomp` at `10b864b9` has a scripted Zoom Zoo (Circuit A) route, now preserved byte-exact under `reference/imported/reverse-engineering/baldosa-uniracers-recomp/tests/routes/zoomzoo_1p.txt`. Its reported menu return is not an original/native terminal-result pair. `tests/input/qa01-baldosa-zoo-candidate.script` adapts the drive policy for our own runner, with a stronger result-state gate, but has not been executed here. Try this before inventing another circuit controller; preserve **0/45 complete** pending independently admitted evidence. See `docs/BALDOSA-RECOMP-CROSSPROJECT-INTEGRATION.md`.

# QA-01 / QA-07: original course and expert-event acceptance census

**Status (2026-10-08): bounded L2 investigation, no L4 course/event completion pass.**
Release authority remains `docs/RELEASE-QUALITY-LEDGER.json`; this file
owns the denominator and the protocol for admitting a complete course result.

## Authoritative Zoo result lifecycle observations for Windows integration

The executed independent original-native CI comparison above establishes **USA 7E:009F = 0xBC** as the actual *Circuit result menu*; **7E:0313 = 0x3D** at settled result is **not** an active-race boolean. Canonical USA track ID **7E:00CE = 1** denotes Zoom Zoo. P1 7E:0EF1 (laps remaining) is **zero** at result onset, and 7E:1199 / 7E:119D are **1/1** for P1 checkpoint / finish gate in both original and Baldosa. Result state raw stopwatch 0E0F/0E13/0E17/0E1B/0E1F is **15/15/15/15/10** at both guests' onset and stable observations, a non-time sentinel: **derive published elapsed time and best lap from the decoded guest result presentation and validated clock lifecycle**, not these post-result raw bytes. The observed result text for P1 is **MIKE 1:16.46 / 0:25.10**. P2 is **BRONSEN 1:20.07 / 0:26.45**. These fields are useful read-only guest lifecycle inputs to the existing Modern product, **not authorization to synthesize persistence/records or to alter the guest clock/scoring**.

Source scene-entry frames were **1604 original** and **1606 Baldosa**; observed result menu onset was **6767 original** and **6768 Baldosa**. Compare elapsed *guest-relative* frames (**5163 vs 5162**), never absolute host frame numbers. The retained original/native observations distinguish active-course contact from post-result residue: 0E95/0E97 match in all seven active captures and at both result onsets, but differ at the stable result eight frames later. Exact instrumented writer and controller-latch phase remain unresolved. The bounded ±1 native-only source input intervention (merged #1093) changes real physics/contact and fails to finish. Fixed-frame independent result-window evidence (merged #1098) now proves a genuine one-frame guest result-transition lead on native, with contacts converging two frames later. The latest discriminator searches backward before relative +5158 to identify the earliest clock/transition phase slip. Do not assume a global controller offset or change gameplay rules. No per-course workaround is authorized.

## Exact denominator and observation classification

`analysis/data/course-corpus.json` has 45 canonical USA stream-indexed
course identities, nine tours, and nine occurrences of each event slot:
Race A, Circuit A, timed Stunt, Race B and Circuit B. This is **ROM
content/identity evidence**, not a statement that an executable playthrough
has passed. The nine timed stunt courses have decoded `45` at header byte
2 and omit resource `0x24`; the other 36 courses contain that reusable
checkpoint/finish *resource family*. These facts do not identify a unique
contact cell, number of laps, gate order, finish plane or final result.

The primary Windows-original course release gate covers **45 USA-retail
cases**. A broader comparative matrix separately tracks **90 reference
cases** from Europe retail and the 1994-11-29 PAL prototype. Together
this is **135 course/build cases** (108 race/circuit and 27 timed stunt),
with 27 cases for each event-slot family across all three builds. The
comparison variants identify regional divergences; completing every
prototype case is not an automatic Windows shipping requirement. The
historical legacy beta is a separate archival build. A complete `passed` entry must include the
original route and start, event-specific contact/checkpoint/lap/finish
(or stunt score/timer) and result, matched against a pinned Snes9x or
MesenCE run from an independently named native run, on a fresh process,
with exact ROM and candidate provenance.

The primary-USA baseline is **0/45 complete event passes**, **4/45
partial observations**, **41/45 unverified**. Across all three builds,
**0/135 complete**, **4/135 partial**, **131/135 unverified**, as encoded in
`analysis/data/course-event-runtime-evidence.json`. Specifically:

- **USA Dragster (course 01), partial:** the seven-frame native WRAM
  progression witness observes the postframe checkpoint/lap/finish gate
  transition, but does not capture the instruction-time dispatcher value
  or demonstrate original/native all-event/result parity.
- **USA Zoom Zoo (course 02), partial:** the original pinned 2014
  Snes9x 5,000-frame WRAM write trace has an actual Crawler circuit
  entry at movie frame **3190**, both racers at **(9200,1489)** versus
  identical ROM header pairs **(9200,1488)**, and five verified
  P1 checkpoint/finish-gate/lap transitions at **3408, 3794, 4031,
  4722, 4911**. P1 laps remaining drops **4→3** and later **3→2**;
  the separate archived Snes9x result-screen proof reaches a settled
  Circuit result (`0xBC`) at movie frame **8353**, MIKE total 1:16.46
  and best lap 0:25.10. These were originally separate **original-only** observations, but
  the later independently booted original/native 2014 scene transplant in
  merged #1091 and source-phase refinements through #1114 now demonstrate
  matching completed Zoom Zoo lap/checkpoint/contact samples and actual
  settled Circuit PPU times. The native menu 0x84→0x16 transition and final
  result 0xBC occur one independently measured scene-relative frame before
  original; original CPU scope 83:988A and native generated function
  Sram_RestoreDirectPage_FastRom both write the same restored menu/track
  fields. This is a paired **candidate**, not independent complete-event
  acceptance. The precise remaining causal uncertainty and artifact identifiers
  live in [the source-owner crosswalk](../analysis/data/zoo-original-native-sram-restore-source-owner-20261009.json).
  **Still partial, 0/45 complete.**
  Reduced write provenance: `analysis/data/zoo-original-2014-live-progression.json`.
  Original terminal evidence: `analysis/generated/result-screens-probe.json`.
- **USA Bowl (course 03), partial:** the archived original 2014 Snes9x
  movie reaches a legitimate scored 45-second Stunt result. The source
  reports tally `0x2F` at frame **11915** and settled result `0x18` at
  **11985**, with MIKE score **764**. This is an authentic **original-only
  source completion**, not an independently matched fresh native Stunt
  run. Provenance: `analysis/generated/result-screens-probe.json`.
- **USA Jumpover (course 20), partial:** six bounded input-only
  original/native stunt landing-reward thresholds match **on a circuit B
  course**, but no complete circuit lap/finish/result or 45-second stunt
  event is established on Jumpover. **No timed-Stunt identity has
  an accepted fresh original/native complete-event pair**, including Bowl.

Every Europe-retail and PAL-prototype case remains unverified at comparative L4.
No paired-ROM payload CRC, native unit test, static course-cell match,
or success on Dragster can be counted as a substitute.

Recompute the matrix and deny a forged/incomplete pass:

```sh
python3 tools/audit_original_course_event_coverage.py
python3 tools/audit_original_course_event_coverage.py --check
python3 -m unittest discover -s tests/unit -p 'test_audit_original_course_event_coverage.py'
```

The report is generated at `analysis/generated/course-event-qa-census.json`.
The observation register is intentionally small and must change only when
new original/native evidence is retained. The validator checks
completeness and source categories, **not** whether a witness is truthful;
reviewers still admit each candidate and exact trace.

The retained ROM-side evidence separates 42 nonzero numerical matches
between the optimizer's unused startX constants and header A.x×16, one
nonzero disagreement (Zoom Zoo), and two zero-value annotations whose
runtime interpretation is unknown (Jumps, Hill Climb). The source script
never reads startX when performing calculations. Numeric coincidence
is useful for track-identity reconciliation, **not** a dynamic spawn witness.

## Measured USA checkpoint-family cell census (2026-10-09)

The full-ROM placement job (`tools/audit_all_course_checkpoint_placements.py`,
unit log `QA01-45-COURSE-PLACED-CELLS`, PR #1014) confirms all **36/36
Race/Circuit** courses contain *placed* `0x24` cells, and all nine timed
Stunt courses are negative controls. There are **zero** Race/Circuit
courses which list `0x24` but have no placed 16×16 cell. This closes the
specific hypothesis that shipped races are missing the entire checkpoint
resource family.

However, **34/36** courses have *no candidate world cell in the exact
X column* of the historical optimizer's hand-entered finish-X number.
This is primarily evidence that the handwritten coordinate is not an
authoritative event predicate. It does not mean 34 courses are missing
their finish! ROM-static nearest horizontal gaps were 95 units for
**Zoom Zoo**, 30 for **Two Loops**, 28 for **To and Fro**, 27 for
**Hairpin Hill** and 26 for **Flat Fun** and **123 Jump**. Historical
positions are world X only and omit the Y component, racer collision
footprint, entry direction and checkpoint order.

The paired archived **original** Zoom Zoo movie preserves P1 world XY
at guest frames 3400/3800/4200/4600/5000 while still racing. The
follow-on `tools/correlate_zoo_original_positions_with_cells.py` uses
those exact Snes9x samples and all decoded candidate 16×16 rectangles
to report the nearest *two-dimensional* gap and candidate C000 slot
for each sample. This tests whether the historical 95-X-unit anomaly
survives comparison against actual executed world positions rather than
another handwritten coordinate. A geometric zero gap is NOT an
observed contact, handler instruction or lap/finish event: original
instruction-time `0F09` and previous-frame contact remain the required
causal witness. This work does not raise the 0/45 complete-event count.

The first canonical-ROM/source-pinned 2D witness has **784**
Zoom Zoo checkpoint-family candidate world cells. The nearest
candidate cell center-to-rectangle separations at original Snes9x
movie frames **3400, 3800, 4200, 4600, 5000** are respectively
**(91,0), (54,0), (2568,0), (1778,0), (893,258)** world units on
(X,Y). The nearest C000 slot IDs are 195, 193, 200, 200 and 200.
**None of those five rider centers is inside a candidate cell**.
The exact per-frame position, nearest 16×16 world rectangle and slot are
preserved in `analysis/data/zoo-original-2014-spatial-witness.json`.
A canonical-ROM unit test now recomputes every value and rejects drift.

This sharply narrows the *sampled* observations but does not claim the
rider never touched a checkpoint between the 400-frame-spaced archived
snapshots. A useful next original-Snes9x trace should sample the
vicinity of frames 3400 and 3800 densely, record
`7E:0E95` (previous stored contact), `7E:0F09` (dispatched
contact), `7E:1199` (next checkpoint), `7E:119D` (finish gate),
`7E:0EF1` (laps remaining) and the actual `81:8050`
handler entry. Observe PC order before inferring active cell or finish.

```sh
python3 tools/correlate_zoo_original_positions_with_cells.py \
  --json-out /tmp/qa01-zoo-real-2d-cells.json
python3 -m unittest discover -s tests/unit \
  -p 'test_correlate_zoo_original_positions_with_cells.py'
```

## Actual Snes9x Zoom Zoo spawn, checkpoint and lap chronology

**Recovered from authentic original execution, 2026-10-09.**
Historical workflow run `37184022134` artifact `11296685866`
retained a 35,428,252-byte original Snes9x JSONL WRAM write trace
(`669,690` records, guest frames 1..5000, source SHA-256
`5fc0e88c89d2dc35b945a2c1f37f522fe8ba3090ea64a0efe50e1748b39f93ab`).
That **raw** trace was reconstructed frame-by-frame, not inferred from
the movie's sparse reference output or the out-of-phase native screenshots.

At the original Zoom Zoo race entry **frame 3190**, guest track ID is 1,
`inRace=1`, P1 and P2 are both **(9200,1489)**. The two identical
header coordinate pairs are **(575,93)** ×16 = **(9200,1488)**.
Thus the header's X is a live start-position match, with the first
active-frame Y one unit lower. The historical unused
`magicnumber.lua startX=8961` is **not** the actual start position,
resolving that earlier static interpretation question without guessing
whether the Y unit came from gravity or postframe ordering.
Because both header pairs are identical, their P1/P2 assignment
remains intrinsically uninformative.

| Snes9x guest frame | P1 world X/Y | Checkpoint index | Finish gate | P1 laps remaining | Previous stored P1 contact → new postframe |
|---|---|---|---|---|---|
| 3190 | 9200, 1489 | 0 | 0 | 4 | first active frame |
| 3408 | 8943, 1568 | 0→1 | 0→1 | **4→3** | `2304` (slot 194) → `2308` (196) |
| 3794 | 8478, 2907 | 1→2 | 1 | 3 | `2704` (194) → `0706` (195) |
| 4031 | 11931, 3568 | 2→3 | 1→0 | 3 | `2B04` (194) → `0B06` (195) |
| 4722 | 11852, 1073 | 3→0 | 0 | 3 | `0F20` (200) → `0F20` (200) |
| 4911 | 8961, 1568 | 0→1 | 0→1 | **3→2** | `0306` (195) → `2304` (194) |

At the first observed lap-counter decrement, the original timer bytes
`0E0F/0E13/0E17/0E1B/0E1F` read `0/0/0/2/1`,
approximately **0.2 seconds** elapsed. At the second decrement they
read `0/2/5/2/4`, approximately **25.2 seconds**. Thus the first
`4→3` is an initial start-line crossing shortly after the start,
not evidence of a completed 25-second lap; the 1,503 guest frames
between the two observed decrements provide the stronger bounded
original circuit traversal. Intermediate checkpoint changes have
their raw stopwatch bytes retained in the fixture for timing or
region-cadence comparisons.

The Snes9x trace records **low WRAM 7E writes only**. It does not
dump or verify the full resident `7F:0000` course decompression
buffer. ROM-static resource-0x24 slot membership is a separate
evidence source, and same-frame original live C000/handler execution
remains to be observed before attributing geometry causally.

The Snes9x trace records the **direct writes** to `0EF1`
(laps), `1199` (checkpoint), and `119D` (finish gate) in
those same frames. The second observed lap decrement is **1,503
original frames** after the first; intervening checkpoint order
is **1→2→3→0→1**.

**Distinct original lap-semantic counterexample:** checkpoint **3→0**
at frame **4722** does **not** decrement laps (`3` remains `3`)
or set the finish gate (`0` remains `0`). Only **189 original guest
frames later**, at frame **4911**, does checkpoint **0→1** accompany
a gate `0→1` and lap `3→2`. A reconstructed circuit that awards
a lap on checkpoint-index wrap is therefore inconsistent with this
original Zoom Zoo sequence. The direct event-write regression
`test_checkpoint_wrap_is_not_a_lap_decrement_in_the_original_game`
now pins that distinction. It is an original-game semantic invariant
for this observed course sequence, not yet evidence that the native
guest violates it. Although the P1 X at the second decrement happens
to equal the optimizer's unused `8961`, that coincidence does not
retroactively identify the recorded historical X as a spawn or
authoritative finish plane.

**Original within-frame write order challenges a blanket one-frame
dispatch explanation.** The original Snes9x trace retains an ordered
series of actual changed `7E` WRAM writes for each guest frame.
For the first observed lap decrement at frame **3408**, the
low-byte P1 persisted contact `0E95` changes at **zero-based write
index 88**, followed by the lap decrement `0EF1` at index **91**
and checkpoint/gate `1199/119D` at **107/108**. At the second
lap decrement **4911**, the order is P1 contact index **107**,
lap **113**, checkpoint/gate **141/142**. The original first
non-lap checkpoint changes at **3794** and **4031** also follow
a persisted P1-contact low-byte change earlier in the same labeled
frame. At **4722**, checkpoint 3→0 is observed with no changed
P1 `0E95` byte that frame.

This is not an instruction-PC trace: unchanged writes and other
register/7F activity may be absent, the emulator's `f` boundary
is external to a CPU call frame, and more than one sampling/dispatch
bracket may occur. Therefore **do not assert** that either the
prior postframe word or the same-frame newly stored contact word
was consumed by the finish handler. The ROM-authoritative bank-83
call order (dispatch before later sampler in the identified main
path) remains valid, but its simple one-guest-frame causal application
is underdetermined by the original execution chronology.
The source-reconstruction verifier now checks exact in-frame
contact/progression write indices against the reduced fixture.
The decisive next witness remains instruction-time 82:8C32,
81:82ED/805D, 81:8DF3 with a frame counter.

These original contact words are **postframe** P1 stored values from
`7E:0E95`; their decoded C000 slots are candidates, not a
per-instruction cell/collision assertion. USA ROM call order dispatches
course objects before sampling new contact, and 0F09 frame-end scratch
belongs to the most recently updated player. **Do not assign the new
same-frame postframe contact word as the cause of the lap transition.**
At frames 3408 and 4911 the *previous* stored words/slots differ,
yet both progression transitions have checkpoint/gate/lap patterns
`0/0/n → 1/1/n−1`. An instruction-time P1 dispatch trace is required
to establish whether both select the same gate/class.

**Coverage disposition:** this is the third primary-USA `partial`
case, not a full `passed` case. It establishes real original-start
and bounded circuit checkpoint/lap semantics over frames 3190..5000,
but no finished circuit result, no independently synchronized native
replay, and no assertion about the other 44 course events. The primary
full-event release denominator remains **0/45**. For future recovery,
download workflow run `37184022134` artifact `11296685866` and
reconstruct its `_temp/dessyreqt-first-race-trace.jsonl`;
the reduced evidence fixture is retained in the repository even after
the workflow artifact expires.

The retained `tools/verify_original_zoo_2014_reference_trace.py`
reprocessor can re-read that exact **raw** zipped JSONL, verify the
35MB source hash and **669,690** source records, reconstruct original
postframe P1/P2 state from changed bytes, and reproduce **all five**
checkpoint/gate/lap intervals, preceding/succeeding stored P1 contact
words, raw stopwatch bytes and the exact intra-frame progression write
order. It refuses a modified full source, missing sampled frames, or
changed reference event values. Example after downloading the
historical run artifact:

```sh
python3 tools/verify_original_zoo_2014_reference_trace.py \
  --artifact-zip /path/to/dessyreqt-4250-first-race-replay.zip \
  --json-out /tmp/original-zoo-wram-witness.json
python3 -m unittest discover -s tests/unit \
  -p 'test_verify_original_zoo_2014_reference_trace.py'
```

The latter tests source parser behavior with synthetic WRAM writes;
they do not claim a fresh original emulator execution. The full
artifact SHA-verified reconstruction is a separate, reproducible
confirmation of the original run already executed in 2014-movie
workflow `37184022134`.

## Historical complete-original results versus pending fresh native pairing (2026-10-09)

The archived, anchored 2014 original Snes9x movie already has **settled
original-only** Crawler results: Dragster race menu `99` at movie frame 2874;
Zoom Zoo circuit `BC` at 8353 with MIKE total 1:16.46, best lap 0:25.10;
Bowl scored 45-second stunt with tally `2F` at 11915, final `18` at
11985 and MIKE score 764. The source is
`analysis/generated/result-screens-probe.json`, created by
`tools/probe_result_screens.py` on the original Snes9x reference.
This is meaningful **original event-complete source evidence**, but is
**not** a new USA release-course acceptance: it is not an independent,
scene-rebased native/authentic comparison and does not establish matching
native result or contact/lap semantics.

`tools/probe_original_event_complete.py` (implementation PR #1055;
[bounded execution plan](QA01-2014-COMPLETE-EVENT-TRANSPLANT.md)) now
attempts a genuine original/native pairing: pin original SMV SRAM, discover
course entry and result from independently executed source movie, calibrate
fresh guest entries through stock menus, transplant the exact original input
relative to each entry, and compare scene samples plus actual guest PPU
result text and score. It fails closed for a missing original course/result
source, missing non-Dragster finish time, unmatched result, zero-score stunt
or circuit lacking two sampled lap decrements. Crawler Switcher is the
first non-Dragster Race candidate; its complete original source result
has not yet been confirmed and is an **explicit unresolved producer
dependency**, not a successful replay. No binary pairing was executed
as part of #1055's initial tool-only contribution, so the census
remains **0/45 USA complete; 4 partial; 41 unverified** and the release
ledger stays **in_progress**.

**Next actual discriminator:** execute Zoo and Bowl on prepared pinned
Snes9x plus native Authentic binaries, verify source-entry state,
controller latch phase and result fidelity; independently find an actual
Switcher finish in original source or select another completed
non-Dragster Race. Only promote a reviewed, fresh-process exact-identity
witness to the 45-row machine-readable census. The disputed Dragster
frame-2903 consumed contact remains unresolved absent instruction-PC
evidence of an actual result divergence.

## Non-Dragster counterexample priorities

1. **Zoom Zoo, USA circuit A (02):** historical hand-entered start X
   `8961` disagrees with `header.spawn_or_landmark_a[0] * 16`
   (`575 * 16 = 9200`). Treat this as a *static interpretation
   discrepancy*, not a proven wrong spawn. First correlate the live course
   load and guest start state with historical position, then collect a
   full lap/checkpoint/gate/result sequence. Test reverse approaches,
   repeated finish-plane contact and lap wraparound.
2. **Jumps, USA timed stunt (13):** the external optimizer hardcodes
   start X `0`, versus header candidate `262 * 16`. Its startX constant
   is never consumed by that script, so the zero is an **unqualified
   historical lead**, not demonstrated incorrect spawn geometry. The
   header has two distinct coordinate tuples and the stunt family
   deliberately has no ordinary `0x24` resource. Confirm runtime track,
   timer, scoring and two-player spawn before claiming any mismatch.
   Do not apply an ordinary lap/finish contract to a timed stunt.
3. **Regional course deltas:** Europe-retail course streams 4, 16, 20,
   26, 27, 35 and 36 differ from USA. The PAL prototype's 45 unpacked
   streams match USA but its live contact register operands relocate.
   Inspect actual runtime entry, decoded-cell activation and parity on
   representative *modified* Europe courses, especially Switcher (04)
   and Jumpover (20), before extrapolating.
4. **Expert-event discriminators:** L-shoulder flips, borderline
   landing contact, held-input combinations, repeated imperfect
   landings, boosts while airborne/offscreen, ground/side collisions
   and narrow pass/finish windows. Pin before/after exact guest-frame
   state and independently compare reference/native; distinguish
   transient progress, queued message IDs, pop-time reward and final
   result. Existing R-hold (22–25) and A-hold (4–5) cases are useful
   threshold seeds, not coverage of these other classes.

**Entry-probe measurement correction, 2026-10-09:** The original/native
first-64-frame comparison now also observes **P1 and P2 checkpoint,
finish gate and lap words**, plus P2 velocities. Previously, equal
positions and stored contacts could conceal early phantom finish/gate
credit or an erroneous P2 lap decrement. The synthetic fail-first
regression is documented in
[QA01-NONDRAGSTER-ENTRY-PROGRESSION.md](QA01-NONDRAGSTER-ENTRY-PROGRESSION.md).
No fresh engine execution was performed for this change; it is a
measurement-coverage correction and retains the **0/45** USA complete
event denominator, **3** partial cases and **0/135** broader complete
event count.

## Executable non-Dragster entry discriminator (QA-01 step 1)

`tools/probe_original_non_dragster_course_entry.py` now supplies two
**bounded original-menu input-only** reference/native probes:

- `--case zoom-zoo`: Crawler tour, second track, canonical USA stream 2,
  guest track ID 1, circuit A. Candidate for live spawn and repeated lap
  progression investigations.
- `--case jumps`: Shuffler tour, third track, canonical USA stream 13,
  guest track ID 12, timed Stunt. Candidate for 45-second score/timer
  acceptance. This must not be mislabeled a race/finish event.

Both drives use a recovered-SRAM fresh boot, the existing scripted original
menu state labels, and Snes9x vs native Authentic. They admit a snapshot
**only** if guest course ID, active-race state and entire decompressed stream
match the exact canonical USA ROM at `7F:0000` except the established
loader-mutated cursor bytes. They compare WRAM racer positions, velocities,
contact words, lap and boost fields, plus original-ROM timer digits at eight fixed relative
frames (0/1/2/4/8/16/32/64), including early P1/P2 candidate-header
spawn assignment.
There are no WRAM pokes. Any first discrepancy retains its frame and field
values, but capture-phase differences require a writer/phase diagnosis
before claiming guest semantics differ.

Example (use locally built Snes9x reference driver, core and native target):

```sh
python3 tools/probe_original_non_dragster_course_entry.py \
  --case zoom-zoo --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-zoo \
  --json-out /tmp/qa01-zoo.json
python3 tools/probe_original_non_dragster_course_entry.py \
  --case jumps --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-jumps \
  --json-out /tmp/qa01-jumps.json
```

Self-check without ROM or emulator:
`python3 -m unittest discover -s tests/unit -p 'test_probe_original_non_dragster_course_entry.py'`.

**Acceptance boundary:** these are runnable investigative probes,
**not successful guest executions in the retained corpus yet**.
Even a matching 64-frame window proves entry/start and initial timer semantics only.
Neither course may become a fully `passed` event/candidate row until
full checkpoint/laps/result (Zoom Zoo) or scoring/timer/result (Jumps) is
captured from each engine. Do not adjust the 0/45 release denominator on
the strength of a test fixture's existence.

## Archived expert-input route to first real timed Stunt result

The imported reset-anchored 2014 `dessyreqt-4250-submission.smv` contains
over 8.7 million original input samples. Its pre-existing first-race replay
`analysis/generated/historical-2014-first-race-replay.json` demonstrates
that **absolute frame-zero native playback is not aligned to the original
reference**: the original first-race entry is frame 794, while the native
screen at that same frame was still in menu flow. Those differences are
timing/phase counterexamples; assigning them to physics would be invalid.
Repeatedly increasing absolute-replay duration would not repair the
starting condition.

`tools/extract_historical_smv_scene_window.py` now selects a bounded
scene-relative input window (up to 24,000 samples) from the pinned original
SMV or its single-file ZIP wrapper. It validates the original movie UID,
sample count, P1 controller bit, NTSC/reset anchor, ROM CRC, controller
offset, reserved joypad bits and absence of reset markers *in the selected
window*. It outputs original input-run lengths and hash/provenance. When
given a **caller-measured** target race-entry frame it can rebase the
exact input masks to a fresh reference/native session. It intentionally
does not infer the actual movie's race-entry frame.

**Prospective expert-play experiment (not yet performed):**

1. First trace the Snes9x archive replay on the **original** core beyond the
   verified first-race window, sampling current track `7E:00CE`,
   active-race `0313`, current menu `009F`, five stunt timer bytes,
   boost and stunt-message ring. Source reconnaissance reports an active
   historical Bowl stunt run ending around movie frame 11867; treat that
   frame as a **search lead**, not a verified event timestamp.
2. Only after observing the exact first original Bowl (`course:03`,
   track ID 2) **race-entry** frame, extract enough of its original input
   timeline to cover scored gameplay, expiry and the actual Stunt results
   transition. Example with *illustrative* frame values:
   ```sh
   python3 tools/extract_historical_smv_scene_window.py \
     --first-movie-frame <verified-original-bowl-entry> \
     --frames <verified-bounded-stunt-window> \
     --json-out /tmp/bowl-original-input.json
   ```
3. Boot both original Snes9x and native Authentic into Bowl through the
   same scene-keyed menu route using the identical original SRAM. Measure
   their own `race-entered` guest frames and independently rebase the
   preserved controller input window to each; do not reuse the movie's
   absolute frame as a native timestamp or transplant a Snes9x freeze.
4. Compare scored-stunt message enqueues, queue-pop and actual reward,
   original clock countdown, results transition and final outcome. Classify
   first divergence at **event-relative guest frames**, with clear
   attribution of reset/host phase and score/physics differences.

The existing idle `ui-stunt-result-route.script` did **not** produce a
result at timer zero in either original or native Bowl. This hypothesis
tests whether *active archived stunt play* reaches results and whether
actual scoring/timeout handling agrees. The scene-window tool is an
input extraction seam only; **no full timed Stunt acceptance row is
promoted** until that paired run has executed and retained its outcome.

## Event-specific mismatch diagnostics without motion masking

The 2014 Zoom Zoo paired replay now captures both a raw first field
difference **and** `event_state_diagnostics` that compare progression,
persisted contact and boost as separate channels. An entry-phase or
movement discrepancy may occur before a later *different*
checkpoint/gate/lap state, which must not be hidden or misclassified.
Every original/native progression change interval retains both
postframe contact words and the exact guest-frame spacing. Only
consecutive frames support a one-frame interval; sparse matches do
not prove the absence of transient progress between them.

The event-state extractor does not reinterpret contact as a same-frame
trigger: the original USA dispatch invokes the course handler **before**
the later contact sampler. It retains the prior contact word as a
candidate input and requires instruction-PC evidence before asserting
a specific cell caused a checkpoint or finish. The raw and event
results are different observations, not competing verdicts.
No new full-event pass is admitted merely by running this tool.

## Frame-2903 causal exclusion

The native artifact `analysis/data/dragster-finish-contact-transition.json`
observes P1 postframe word `2024` / C000 slot 10 at 2902, then
postframe `2020` / slot 8 with progression `3/0/1 -> 1/1/0` at
2903. Both select runtime object code `0x14` and both mask to the same
handler control class. The ROM-backed USA main-loop order dispatches
bank-82 course objects **before** bank-81 samples new contact. Thus
the preceding slot-10 word is the stronger **candidate** for the
frame-2903 dispatch input. No instruction-time capture yet proves
that value was consumed, and no 16x16 cell is definitively assigned
by the postframe snapshots.

The phase-correlation tool now refuses backward gate transitions or
multi-lap discontinuities and builds its explanation from the actual
frame and words rather than a hardcoded frame-2903 sentence. This
hardens **evidence interpretation**, not the guest's physics or lap
behavior. Next decisive trace: break at USA `82:8C32` (P1 object call),
`81:82ED` (shared word read), and `81:805D` (handler control class),
record `0F09`, `0E95`, `0EF1`, `119D`, per-player identity and guest
frame before and after; retain executed-PC chronology. PAL needs its
independently identified `0F0D` / `0F13` shared words and corresponding
instruction sites, not USA addresses blindly applied to relocated code.

## Admission / stopping rules

A static placement probe establishes only plausible cells. An L2 native
trace establishes only what that specific native run did. A paired
original/native state window establishes event-relative parity for that
window. A full L4 acceptance row requires an **actual** original-menu
launch, start, contacted course events in causal order, terminal result
and independently paired execution, with candidate/ROM hashes and
fresh-process reproducibility. Missing references remain `unverified`
or `blocked`, never `passed`. Where a failure is reproduced, preserve
input sequence, first divergent guest frame and exact WRAM/PC evidence
before modifying the authoritative game.
