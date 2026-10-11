# malmazuke PAL reconstruction: pinned research intake and QA handoff (2026-10-10)

**Source:** Mark Feaver, `malmazuke/unirally-reconstruction`; preservation fork `gamesbyian/unirally-reconstruction`. **Immutable source revision:** `42d444594641d23f5d3c15da7b7c454bb5180e43` (not the moving fork branch). **Original research domain:** headerless Europe PAL 2 MiB SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`; his research also pins specific original bsnes revisions and input freezes. See imported `docs/research/R-0001-rom-identity.md`.

**Rights:** Upstream project-owned text/code is MIT-licensed; import includes the unmodified upstream `LICENSE`. The license does not transfer rights to Nintendo/DMA ROM bytes, extracted art or audio. This is a **non-executable research copy** under `reference/imported/reverse-engineering/malmazuke-unirally-reconstruction/`, not another native gameplay backend, bootstrap, build dependency or emulator. No assets, dumps, firmware, native binaries, recorded pictures, build systems, or upstream third-party closure were taken. Every included source blob is identical to its blob at the pinned upstream revision and classified in `reference/imported/MANIFEST.json`.

## Reading the cross-ROM index without hallucinating correspondences

`analysis/data/malmazuke-pal-structural-links-20261010.json` joins Mark's **1,739 address-index items** and **1,873 observed/inferred label entries** to the existing **132 bounded structural-census regions**, *not* a single global PAL/USA relocation. Of the **546 selected domain-relevant PAL ROM addresses**, **151** land in exactly one Europe code interval and receive a strictly *geometric interval-offset candidate*, **2** land in a data interval only, and **393** are explicitly **not covered**. These are hypotheses, not validated byte-level opcode-identity, function-entry, operand, or dynamic execution equivalences. The source label class is kept independently. Zero candidates grant new authority to `docs/SYMBOLS.md` or the USA oracle.

Concrete examples for triage:

| Mark PAL use | PAL address | Candidate USA address | Existing census authority | Interpretation |
| --- | --- | --- | --- | --- |
| `race_progress.cpp:update_checkpoints` | `81:8050` | `81:8050` | `checkpoint-finish/entry_time_prefix` | bounded code-region candidate |
| `race_progress.cpp:cross_start_line` | `81:8139` | `81:8147` | `checkpoint-finish/post_normalization` | offset projection across differing operands; check instruction boundaries |
| `race_update.cpp:lowest_palette` | `81:8B75` | `81:8B95` | `course-surface-sampler/Course_SampleRuntimeSurface` | independent reference to an established USA function family, not equal per-frame behavior |
| `audio_cpu_interrupt.cpp:save_interrupt_caller` | `80:8587` | **unmapped** | bank 80 not covered by bounded census | PAL NMI vector starts one byte before USA `80:8588 I_NMI`, but this separately observed similarity is **not** admitted as a structural-census projection |

For a specific link, go from `entries[*].mark_native` -> local source file and citation -> `correspondence.region` -> `analysis/generated/comparative-structural-census.json` -> inspect exact regional ROM opcodes and operands with existing `tools/compare_europe_usa_snes2asm_homologs.py`, `tools/run_pal_da65_adjudication.py`, and canonical ROMs. **Only** then add any established semantic link to `docs/SYMBOLS.md` with confidence and contrary evidence. The already proven Europe collision marshal `82:89CC` vs USA `82:89B9`, and WRAM `0E9F/0EA1/0F13` vs `0E95/0E97/0F09`, remain owned by `docs/COURSE-PAL-REGISTER-HOMOLOG.md`. Do not globally apply a +10 WRAM or +19 ROM shift.

### Reproduction / audit (offline)

```sh
python3 tools/audit_imported_references.py
python3 tools/validate_external_evidence.py
python3 -m json.tool analysis/data/malmazuke-pal-structural-links-20261010.json >/dev/null
```

Crosswalk producer algorithm: parse the **unchanged** imported `docs/map/static/native-symbols.json` and `labels.json`; select PAL ROM addresses with `src/core/{race_result,lap_result,result_screen,stunt_result,race_progress,race_update,race_state_io,input_timer,race_hud,front_end,front_end_runner,movement,flat_contact,track_sampling,zoom_zoo_movement,hunter_effects,hunter_ending,opponent_ai,presentation,race_windows,audio_cpu_interrupt,audio_cpu_clock_interrupt,audio_driver}.cpp:` users; for each, scan the accepted census `regions[].homologs["europe-retail"]` inclusive `start..end`. No match -> `not-covered`; multiple -> `ambiguous-overlap`; one match -> project the same relative byte offset from `region.usa_start`, classified `structural-interval-candidate` only if `region.kind == "code"`, else `data-interval-only`. Preserve labels as metadata, never require a same-named original function. Avoid run/CI work until the concrete mapping resolves an open defect. The JSON counts and source commit are frozen, not automatically regenerated when upstream changes.

## Priority: Switcher QA-01 NMI / result boundary

Latest USA original-vs-native work already **proves the instruction class**: genuine original Snes9x `PHA 00:858E`, corresponding to USA `80:8588 I_NMI +6`, saves the 16-bit accumulator through stack address `7E:01DD` (original observed byte `42`, CPU frame 5780). Native Baldosa `I_NMI_M1X1` saves the 16-bit accumulator in a genuine `PHA` (logged `A=4004` and `01DD=04`, pre-run frame 5781). Both have `S=01DE→01DC`. Hardware NMI **entry** itself has already been excluded as the writer in the bounded original window. The two observation clocks are *not* yet instruction-aligned. At absolute host 5782, eight WRAM-only differences remain, but both display the genuine MIKE **1:08.81** result at host 5783. The strict guest-entry-relative result onset is still **+4704 original / +4702 native (FAIL)**, USA acceptance **0/45**. These are established in `docs/QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md` and active #1268; **do not redo or preempt that PR**.

Mark's independent **PAL** records isolate *distinct* timing mechanisms which help formulate a USA discriminator:

| Layer | Pinned PAL observation or implementation | Impact on Switcher question |
| --- | --- | --- |
| Race/finish | `R-0012`, `R-0034`: finish flag and result load are separated by a **240-update finish-display interval**; a result can be reached without both riders finishing, depending on winner condition (`R-0053`) | Compare finish display-counter and exact event-phase ownership before assuming a result onset defect |
| Rendering/frontend return | `R-0057`, `race_result.cpp`: return starts with forced blank and **NMI disabled**, long audio reupload, menu-restore, NMI re-enable, then result construction | A host-result picture can match even when guest frame/state phase differs; log transition cause not merely pixels |
| PAL hardware clock model | `audio_cpu_clock_interrupt.cpp`, `audio_cpu_interrupt.cpp`: PAL raster/NMI poll model and save-register wrapper; R-0012 captured NMI-absent frames during PAL result load | Check *actual USA* NMI request/service and `PHA` placement, not PAL vblank count or PAL nominal 50 Hz |
| Clock & result publication | `input_timer.cpp`, `race_progress.cpp`, `race_result.cpp`: race digit advancement, checkpoint/lap, result layout and a separate result-screen lifecycle | Compare CPU accumulator provenance, stack consumer and result flag as independent channels |

**Cheapest new discriminator for QA owner:** On the **same exact fresh stock USA Switcher movie, ROM/SRAM, input and independently calibrated host window**, add a **read-only, 3–5-host-frame original/native trace** around host 5780–5784 capturing: (a) exact NMI request/entry and original `80:8588` handler `PHA` opcode PC; (b) pre-`PHA` A, P/M, X/Y, S and prior instruction/interrupt boundary in both; (c) first post-`PHA` stack read/restore to establish whether `01DD` influences result/progression; (d) actual race finish flag, finish-display count, guest-relative result-transition PC/phase and host-output timestamp. Establish an explicit mapping between **source emulator CPU frames, native pre-run frame and absolute host capture** before subtracting the 2. Distinguish a displaced NMI with valid original stack payload from a genuine earlier guest race-state transition. A pure no-guest-write opcode/interrupt observer and reuse of existing original/native runner is preferable to a novel execution fixture. If this entire trace is too expensive, first extract existing immutable original/native logs at `I_NMI` and adjacent result state, then run **one** bounded probe only if information is absent.

**Stop rule:** no guest/source modification, no input retime, no transplant of PAL timings, no promotion based on identical screen text, no QA-01 acceptance waiver and no new GHA recurring workload. Send narrowed evidence to the owner of #1268 and the current QA lane, without editing their tools or release ledger.

## Distinctive future leads and deduplication register

| Topic | Mark evidence / where to read (source commit pinned) | Disposition against UR-Recomp |
| --- | --- | --- |
| Checkpoint / course sampling | `race_progress.cpp`, `R-0034`, `R-0049`, crosswalk checkpoint/collision regions | **Corroboration + candidate links.** Existing `docs/COURSE-FORMAT.md`, `docs/COURSE-PAL-REGISTER-HOMOLOG.md` and structural census own verified four-ROM truth |
| Finish phase relative to race setup | `R-0049`: `$0304` mod-3 counter resets at race start, not at absolute frame; PAL captures across tracks discriminate it | **High-value original experiment if USA QA finish counter remains unexplained.** Not automatically a USA bug/fix |
| Freeze-before-native reference route | `R-0034`: 21-segment independently frozen Zoom Zoo route; `R-0012`: input-release A/B and full-memory/finish evidence | **Technique / conditional fixture candidate.** UR-Recomp already has deterministic USA source SMV movie, source-only event gate, original/native snapshots. Do not copy PAL controller scripts without demonstrated fresh gap and regional identity |
| Results, score, progression, hidden reset | `R-0057`, `R-0058`, `R-0092`, `race_state_io.cpp` | **Cross-check and new lead:** one-run release/press semantics vs lap immediate press; WIPE RAM hidden menu. Current SRAM and result modules own tests; no guessed product behavior |
| HUNTER, AI, specials, sound, UI, PPU | Other upstream R-0047, R-0052, R-0061, R-0074–0094, `src/core/hunter_effects.cpp`, `opponent_ai.cpp`, `audio_*.cpp`, `presentation.cpp` (left upstream, not duplicated wholesale) | **Indexed upstream leads only.** Existing UR authorities cover these domains; no new local USA execution evidence or regression proven in this intake. Request targeted file at exact commit when a QA observation demands it |

**Negative findings:** Mark's PAL self-contained serialized `URZZ/URDG` state formats are *not* a USA SRAM/WRAM ABI; its independently written frontend is *not* a drop-in Modern UI; a subset of original PAL track fixtures does *not* cover USA Switcher; and its PAL raster model does *not* establish NTSC two-frame causality. No additional game engine, audio framework, emulator core or tests were imported.

## Next independent verification checklist

1. Import audit passes with **265 classified files** (246 prior + 19 new) and all new Git blobs equal pinned source, mode 100644.
2. Open crosswalk and sample-check `81:8139 → 81:8147` against canonical Europe/USA executable bytes and disassembler boundaries; invalidate if it crosses a role/length seam. Explicitly inspect the 393 unmapped items before proposing a new region.
3. QA owner runs bounded, read-only USA NMI accumulator/phase discriminator above on the **same** qualified fresh Switcher result. Record consumer live/dead before any discussion of behavioral changes.
4. Revisit Mark's additional subsystems **on demand**, reducing existing uncertain QA work rather than inventing a parallel roadmap.

**No newly verified USA mechanics are claimed by this intake.** The durable result is an immutable searchable independent PAL primary research set, an explicitly qualified index and a focused next QA experiment.
