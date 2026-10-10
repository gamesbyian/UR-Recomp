# QA-01: representative complete-event adjudication, 2026-10-10

**Status:** bounded, source-backed research plan, **not an accepted release gate or a demonstrated Windows candidate pass**. This report separates three independently executed **matching settled-result candidates** from unresolved guest-relative transition timing. It does not change `docs/RELEASE-QUALITY-LEDGER.json` or the 45-USA denominator. Consult current `main` before execution.

## Three event families already have independent original/native results

| USA event | Original and Baldosa settled presentation | Residual issue | Source witness | Disposition |
| --- | --- | --- | --- | --- |
| Switcher Race B | MIKE **1:08.81**, both show result at absolute host 5783 | Original active entry at host 1079 and native at 1081; guest-relative terminal +4704/+4702; strict comparator red | `analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json`; `docs/QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md`; workflow 38078429375 | Candidate, not admitted |
| Zoom Zoo Circuit | MIKE **1:16.46** (best lap 0:25.10), BRONSEN **1:20.07** (best lap 0:26.45); laps/checkpoints and settled PPU agree | Native result 0xBC at guest-relative +5162, original at +5163; known transient contact fields converge; scheduling/source boundary unresolved | `analysis/data/zoo-original-baldosa-completed-circuit-candidate.json`; `analysis/data/zoo-original-native-sram-restore-source-owner-20261009.json` | Candidate, not admitted |
| Bowl scored Stunt | MIKE **764**, qualification **68**; 28/28 sampled active semantic states and settled PPU agree; both result at absolute host 4349 | Guest-relative onset +3365 original / +3364 native; phase not adjudicated | `analysis/data/bowl-original-baldosa-scored-stunt-candidate-20261009.json`; workflow 38021981513 | Candidate, not admitted |

The three results are **not three admitted course passes**. The official ledger remains **0/45** USA independent completed-event admissions (four partial, 41 unverified in the current census). Correct visible output at a single time does not establish all-frame equivalence, and guest-relative terminal disparity cannot be silently ignored.

## Switcher restoration boundary: already executed, not a pending experiment

**Important correction to the earlier plan:** the identical-host restoration experiment was already completed by one-shot PR #1175 / original-native run **38073881560**, and preserved in [the exact evidence record](../analysis/data/switcher-original-native-restoration-same-host-20261010.json). **Do not rerun +4699..+4701 merely to satisfy this document.**

Reference first enters temporary course 0/menu 0x84 at **host 5744** and native at **host 5745**. Despite the differing entry-relative transition labels, both original and Baldosa restore course 3/menu 0x16 at **the same absolute host 5778**. Three sampled same-absolute-host restoration frames **5778, 5779 and 5780** show all recorded named state fields equal. Both guests emit the Race B result at **host 5783**. This establishes a genuine same-host menu/track restoration match, not identical CPU timing, all-memory equality, or continuous event parity.

The existing strict guest-relative comparator still observes entry at original **1079** / native **1081**, terminal +4704/+4702, and fails appropriately. The earlier paired report's relative-frame conflicts at +4664/+4697/+4698 compare differing **absolute** host frames. Do not infer a guest instruction defect from those sparse contrasts alone, but do not normalize them away without an independently validated frame-owner model.

**Disposition:** the three-frame host-5778 restoration investigation is closed by existing evidence. The remaining actionable source questions are (a) original/native instruction and hardware phase at the genuine host-frame result boundary and (b) whether their low-WRAM differences are read by result/progression-critical code. Either question should be pursued only with a bounded writer/consumer trace or demonstrated player impact.

## Follow-on discriminator: Switcher host 5782 → 5783

After the restoration window above has been classified, the completed opt-in independent original/native observation at **the same absolute host frame 5782**, immediately before **both** genuine MIKE 1:08.81 results, found identical VRAM (65,536 bytes) and CGRAM (512 bytes), equal values for 21 sampled named state fields, and **eight** differing bytes in the entire 131,072-byte WRAM. Their WRAM offsets are:

`001DD 001E6 001E7 001EF 001F0 001F1 001F2 001F3`.

Do not infer that these eight bytes are cosmetic, uninitialized, CPU scratch or player-impacting without proving their writers and read sites. Do **not** claim CPU/interrupt/host scheduler equivalence from this observation. The 197,120-byte combined state is **not** identical.

1. **Use existing exact original/native movie and opt-in diagnostics only if instruction-time evidence remains necessary.** Pin ROM, original emulator build, Baldosa commit/build, unchanged controller masks, guest entry and exact host frame. Do not create another broad workflow, rebase input or adjust thresholds.
2. **If still needed, discriminate output from timing at fixed host frames 5781, 5782, 5783, 5784** using both guests on the same host-frame definition. Record before/after guest-frame boundary, PC/PB, NMI/VBlank/DMA or CPU scheduling phase (if existing probes expose them), result menu and original PPU text, input latch, guest game-mode and track. Different guest entry frames must remain explicit; report both host-relative and entry-relative coordinates.
3. **Writer/read crosswalk for eight offsets.** For each byte, supply original bank:PC write(s), instruction-time call context and state/phase; determine whether any read controls physics, scoring, winner, persistence, display or progression. Group contiguous fields only after demonstrating actual instruction access width and semantics. Distinguish writes before host 5782, writes on host 5783, and differences due solely to boundary capture phase.
4. **One causal test, only if necessary:** capture immediately on both sides of the identified original and native instruction boundary using existing source/native observer hooks, with unchanged input. A controlled comparison of corresponding instruction lifecycle points is preferable to globally shifting frame labels.
5. **Stop condition:** either demonstrate that the terminal offset is a measurement/host-boundary convention with independently equivalent original-defined event/result and subsequent transition, or locate the earliest original/native player-relevant state transition and show its causal writer. If the available probes cannot decide, log precisely which register/boundary is missing, leave course partial, and switch to the next family.

### Eight-offset classification template

| Offset group | Proven original writer (bank:PC) | Original readers and semantic consumer | Earliest differing phase | Impacts result/progression? | Confidence |
| --- | --- | --- | --- | --- | --- |
| 7E:01DD | unverified | unverified | no earlier-than-5782 proof | unknown | unclassified |
| 7E:01E6–01E7 | unverified | unverified | no earlier-than-5782 proof | unknown | unclassified |
| 7E:01EF–01F3 | unverified | unverified | no earlier-than-5782 proof | unknown | unclassified |

**Addressing note:** these are linear WRAM offsets (SNES WRAM base `7E:0000`), not original source PC addresses. The table deliberately makes no speculative claims about field widths or meaning.

## Cross-event offset overlap: independent Bowl scored-Stunt observation

The independently captured **Bowl** scored-Stunt eight-frame tally residue record is [`analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json`](../analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json), run **38025090532**. Its source original and native guests both reach authentic PPU score **MIKE 764** / qualifier **68**. Every Bowl sample reports a complete, non-truncated WRAM offset list (cap 128; maximum sample 50 differences).

Comparing the eight **Switcher host-5782** WRAM-difference addresses against the union of Bowl's eight original/native snapshots produces this exact cross-event intersection:

| Switcher offset | Also differed in Bowl, absolute host frames |
| --- | --- |
| `7E:01DD` | 4333, 4343, 4344, 4345, 4346, 4347 |
| `7E:01E6` | 4343, 4344, 4347 |
| `7E:01E7` | 4343, 4344, 4347 |
| `7E:01EF` | 4343 |
| `7E:01F0` | 4343, 4347 |
| `7E:01F3` | 4348 |
| `7E:01F1`, `7E:01F2` | **not observed** in Bowl's eight sampled frames |

The **six-of-eight overlap** is an observed cross-event correspondence, not evidence of simultaneous equal phase, ongoing differences at every frame or a particular field purpose. All eight Switcher offsets fall in the *unlabelled* `7E:01D8..01F3` cluster of the pinned [imported RAM label catalogue](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt). No entry covers these addresses. A shared transient workspace is a **hypothesis**; writer PC, readers and consumer impact remain unproved. The Bowl offset-union contains 57 distinct WRAM addresses, 25 in this cluster. Its two early six-byte samples share only `7E:01E3`; there is no all-eight-frame persistent offset.

**Bounded discriminating work:** trace *one* high-frequency intersection address (`7E:01DD`) to original PC/writer and reader at an event handoff. Include `7E:01F1` as a negative cross-event control. If the writer and reader are identified, expand to `01E6/01E7` only if they share an instruction access width or a result/progression consumer. Do not treat lack of a catalogue name as proof of an unused byte or suppress it from comparison.

## Admission protocol for one representative event per family

Preserve all raw comparisons, including negative outcomes. A course enters the official 45-USA completed census only after an independently booted original/reference and native execution have provenance-pinned **valid entry**, unchanged authentic controller stream, course identity, real event mechanics (Race finish/checkpoints; Circuit laps/checkpoints; 45-second Stunt timer/scoring), same authoritative winner/time/score/result, and independently checked **post-result progression and next event entry**, with the strict comparator either passing or a narrowly justified, source-proved measurement normalization independently reviewed. Do not waive a real gameplay discrepancy merely because settled PPU text agrees.

**Shared Windows candidate:** subsequent J-01/J-03/J-09/J-17 evidence must name the same pinned merged Baldosa Windows executable and portable ZIP SHA-256 as the product and presentation lanes. A Snes9x/native command-line witness can support course semantics, but it cannot itself establish a controller-first shipped Windows UI, records, fresh-process SRAM, audio, physical display, accessibility or sustained-use pass. Treat absent product routes as **not yet testable**, not player-facing failures unless an actual candidate demonstrates one. Do not put a candidate SHA or ZIP hash into the release ledger until independently verified.

**Classification boundary:** demonstrated wrong physics, scoring, winner, next-event progression or destroyed/corrupt valid data is an actual P0. Unresolved frame-phase research without demonstrated player impact is an unadmitted QA-01 evidence gap, not automatically a P0 product defect. Unimplemented required player journey blocks a polished beta regardless of whether source-game execution is faithful. Alpha readiness, external polished beta and final certification use distinct standards in `docs/QA-BOUNDED-RELEASE-CAMPAIGN.md`.

## Coordination and resource control

- Reuse already archived Switcher/Zoo/Bowl results and their exact CI artifacts rather than rerunning three long independent movies without a changed discriminator.
- Owner: QA-01/QA-07 original/native comparison. Product/packaging owner supplies exact Windows candidate and handles profile/records behavior; renderer owner supplies graphical source-visible witnesses. QA remains independent for gate admission.
- No additional triggered workflow or general-purpose instrumentation unless the bounded existing probe cannot observe the named boundary and a specific original-source question justifies expansion.
- On next completed run: record exact candidate/head, emulator, input/ROM hashes, original/native chronology, expected/actual, earliest meaningful difference, provenance and explicit pass/fail/unverified status. Update the census only if the course admission criteria are actually satisfied; update the release ledger only when the candidate-bound release gate qualifies.

## Sources

- [Switcher same-host pre-result eight-byte report](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md)
- [45-course census, provenance and partial candidates](ORIGINAL-COURSE-EVENT-CENSUS.md)
- [Shared witness and bounded stopping rules](QA-BOUNDED-RELEASE-CAMPAIGN.md)
- [Player journeys and candidate evidence](QA-PLAYER-JOURNEYS.md)
- [Dual technical reference/product objective](DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md)
