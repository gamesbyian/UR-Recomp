# QA-01: USA two-edge VBlank wait and RF-014 provenance (2026-10-14)

**Scope:** Independent gameplay/source interpretation of research PR #1537 (RF-014), using archived USA bank-80 opcode bytes, Baldosa's pinned USA RAM-symbol reference, and pinned upstream framework commits. No emulator was re-executed for this **static** investigation. It does not own #1537, the research queue, a production timing fix or the independent release ledger. Official complete USA event credit: **0/45**.

## Original source-backed mechanism

Verified verbatim by `tools/qa01_vblank_wait_source_contract.py` and fail-closed synthetic tests:

| Original USA PC | Executed operation in archived listing | Exact conditional meaning |
| --- | --- | --- |
| `80:FAC9` | Long call to `82:8035` | Before each first-edge poll |
| `80:FACD` / `80:FAD0` | `LDA $4212` / `BMI $FAC9` | Continue while HVBJOY bit 7 = 1; wait for VBlank **clear** |
| `80:FAD2` | Long call to `82:8035` | Before each second-edge poll |
| `80:FAD6` / `80:FAD9` | `LDA $4212` / `BPL $FAD2` | Continue while bit 7 = 0; wait for next VBlank **set** |
| `80:FADB` | `JSR $FADF` | Run continuation after both observed edges |
| `80:FAE2` / `80:FAE6..FAE8` | `DEC $C6`, reload `$1F` when negative | The 32-state cursor-animation counter |
| `80:FAF2..FAF9` | lookup indexed by `$C6 >> 1`, stores to `$0BDE/$0BFE` | Cursor-animation output, directly downstream of wait |

The imported Baldosa USA RAM map calls `7E:00C6` **`wCursorAnimTimer` (1 byte)**, not a universal game-frame clock. A `$C6` decrement is evidence consistent with executing this particular original wait's continuation. A host interval with fewer decrements is a meaningful *wait-throughput discrepancy*, especially in menus, but it cannot alone distinguish (a) source wait executing less often, (b) unrelated source writes to `$C6` (including the documented direct-page restore), (c) sampling the frame before versus after its write, and (d) true missing simulated gameplay updates. A modulo-32 census with fewer than 32 ticks per sampling interval does **not** detect other legitimate writes that happen to fall in the same modulo residue or change a value without exceeding the host span. The actual writer PC is the discriminator.

The static sequence also contains repeated calls to `82:8035`; whether translated code or tier-down/scheduler boundaries change their cost is an independent implementation question. The listing alone proves neither that those calls were executed in RF-014 nor what time they consume.

## Pinned cross-project reuse preflight

`AGENTS.md` instructs running `select_three_project_reuse.py --lane <lane> --include-conditional`. Its current lane catalog has **no `qa01-gameplay` selector**, so the scoped work uses the `all` registry and filters for the relevant proven entries, without pretending a nonexistent lane ran. Applicable decisions:

- `first-divergence` (P0, now, release-qa): reuse UR's `compare_wram_checkpoints` and `check_framedump_identity` before building another comparator, and consult Baldosa `tools/firstdiff.py` and Malmazuke replay evidence.
- `route-input-identity` (P0, now): preserve exact controller masks, observed consumption and race-entry phase. Original/native absolute frame equality does not imply equivalent race-relative input.
- `reference-multiple-oracles` and `full-event-acceptance` (P0): Snes9x **and** Beetle-bsnes with canonical USA ROM; no partial or source-only release credit.
- `framework-delta-porting` (P1, *conditional*): upstream changes can be selectively piloted **after** a measured runtime defect and before/after independent comparison, never as a global framework upgrade.

Source matrix: `analysis/data/three-project-apparatus-capability-matrix-20261010.json`; pinned Baldosa `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`; UR framework baseline `cd5875cbdaf19f5e324272b1f8051d671fce9215`; malmazuke `unirally-reconstruction@42d444594641d23f5d3c15da7b7c454bb5180e43`.

### Two particularly relevant post-pin Baldosa changes

1. **`96b7e9f50c81f193fddc9d45818790a99c6078d4`**: Clock-driven HVBJOY. The newer beam driver calls `snes_set_beam_clock_driven(true)` each frame. Under that explicit policy, `ReadRegOpenBus(0x4212)` synchronizes to `g_cpu.master_cycles`, while `snes_readReg(0x4212)` avoids the legacy `snes_advance_beam(64)` synthetic tick. Upstream reports its own title countdown previously ran at half speed. **That observation does not establish the present UR transition's smaller deficit or license a direct 64-clock removal**. The old UR pinned framework does not itself contain the later beam-driver source path, so this is **not** a safe three-line cherry-pick.
2. **`b7b4318fba3ad7695e4e37eaf103e9e5c41fc806`**: Opt-in `paced_bus` generated-code mode. Separates opcode/operand fetch clocks, paced guest data accesses and internal cycles, aligning AOT master-clock accounting with interpreter tier in that upstream configuration. Its tests are valuable, but it changes multiple generator/runtime surfaces; isolated beam-policy evidence should precede a broad recompilation experiment.

Existing UR authority already records both candidates: `docs/BALDOSA-FRAMEWORK-DELTA-20261009.md`. These are separate mechanism hypotheses, not two patches to apply simultaneously by default.

## RF-014 discriminating experiment, before any repair

**Decision:** Does native genuinely execute fewer completed `80:FADF` wait routines because of an incorrect beam/poll/scheduler implementation, or do the same guest steps land on different host/sample phases?

**Baselines and population:** Use the *same* exact USA ROM and controller stream for the original Snes9x, independent Beetle-bsnes and both generic / Modern native binaries, with executable and core hashes, source commit, build options, and input SHA. Preserve the original stock 2P host 426–446 transition, a stable menu 20-frame control window, delayed-prefix k=1/k=2 entry routes, and the no-input attract reproduction. The RF-014 773 vs 801/802 and 1311 vs 1326/1327 counts are research's **candidate observations**, not independently re-executed here.

**Minimum observer at the original/source CPU boundary:** Record actual hits at `80:FAC9`, `80:FACD`, `80:FAD0`, `80:FAD2`, `80:FAD6`, `80:FAD9`, `80:FADB` and `80:FAE2`, plus any *other* `7E:00C6` writer with opcode, effective address and DBR. Track `$4212` read values (especially bit 7), CPU PBR:PC, P, S, master cycles, SNES beam line/dot, original NMI entry count and timing, decoded race/scene state, WRAM sample phase, and host-frame entry/exit. Native instrumentation must identify original translated PC/tier-down/helper participation, not merely a C function name. Reuse existing source original opcode/WRAM observation and native trace infrastructure; do not introduce another automated factory. Scope tracing to host **426–446** before collecting large runs.

**Phase and attribution controls:** Original `ICPU.Frame`, native `snes_frame_counter`, guest `$C6`, and host-script `wait/dump` are different clocks. Align actual inputs at their consumed guest phase, record observer capture point relative to NMI and `80:FAE2`, and compare both clocks. A raw `$C6` match does not prove identical executed instruction histories. If any counter changes outside `80:FAE2/FAE8` or the original runtime window uses a different wait, classify it as **not adjudicated**, not "one missed game frame."

**Expected outcomes:**

- Same executed `FAE2` count and source-state progression across corresponding phases, shifted host observation => **observer/scheduler phase**; preserve simulator code.
- Fewer native `FAE2` hits, with original/native `$4212` read transitions or master-clock advancement demonstrably unequal at the **first** missing edge => candidate **beam/poll timing defect**, narrow A/B against the pinned upstream behavior and validate NMI/2P/attract/terminal regression before any port.
- Same `$4212` edges but native extra tier-down, instruction-cycle/host scheduling stalls and delayed continuation => **scheduler or AOT cost**; investigate call `82:8035` and paced bus timing before changing beam semantics.
- `$C6` value differs while actual `FAE2` counts do not, or a restore writes it => **counter aliasing**, not proved missing guest work.
- Results agree at race-relative gameplay checkpoints but terminal source state diverges => preserve specific terminal event oracle failure pending result caller.

**Stop:** Capture the earliest source-backed differential instruction/event and its consuming lifecycle impact. If unchanged source-bounded trace supports only a different host phase or source wait frequency, report that limit without patching or certifying full-event parity. A repair requires a pre-patch failing exact witness, post-patch corrected exact witness, and no regression across two independent original cores.

## Second priority: closest complete-event witness

**USA Zoom Zoo Circuit** is the best-documented complete-scored candidate, not an accepted event. Both original and native reach lap zero and the exact displayed MIKE/BRONSEN results; native reaches the intermediate restore and result transition roughly one guest-relative frame early, with transient post-result WRAM/PPU differences. Source `$009F` is the **two-byte `wTextPos` field**, so its raw values cannot independently define race phases (#1543). The executed original transition is localized around guest-relative +5155..+5163. Once the transition-frame cause is assessed, replay the **unchanged** Zoo input through genuine result, menu restoration and persistence, and have the independent QA owner certify or reject one exact candidate. Switcher Race B's real MIKE 1:08.81 result likewise still fails strict guest-relative terminal timing despite same-host text.

This source contract changes no native gameplay, Modern/graphics code, research scheduling, comparison thresholds, ROM, SRAM or release-quality ledger.

## Additional original-source chain: sound queue service inside both VBlank loops

The calls at `80:FAC9` and `80:FAD2` both enter original bank-82 `82:8035`, a conditional SPC700 sound-command queue service. It runs before **each** `$4212` read. The source byte and symbol contract is now pinned by the same fail-closed test.

| Original source PC | Role |
| --- | --- |
| `82:803C LDA $2142` / `82:803F CMP $7E2004` | Read APU acknowledgement and compare command toggle |
| `82:8043 BNE $8077` | Skip transmit path when handshake mismatches |
| `82:8046 LDA $7E2000` / `82:804A CMP $7E2002` | Compare sound queue read and write indices |
| `82:804E BEQ $8077` | Skip transmit path for empty queue |
| `82:8051 LDA $7E2006,X` / `82:805D ORA $7E2016,X` | Read queued sound-command low/high data |
| `82:8059 STA $7E2004` / `82:8066 STA $7E2000` | Update toggle and queue read index |
| `82:806D STA $2142` | Transmit command through APU I/O |

Baldosa's imported USA RAM map calls the fields `wSndQueueRead`, `wSndQueueWrite`, `wSndApuToggle`, `wSndQueueLo`, and `wSndQueueHi`. **A shared VBlank wait can therefore take different 65816 instruction paths depending on sound-queue state and APU acknowledgement.** RF-012 reports an early original/native WRAM difference at `7E:2000`; this overlaps the source queue read index. It is a meaningful competing/common-cause hypothesis for both terminal and screen-transition offsets, not an execution-time or causality verdict. The helper does not itself implement an indefinite APU acknowledgement wait, so a claim of an APU *stall* would also be premature.

In the bounded host 426–446 and terminal 5193–5198 experiments, add original and translated-PC receipts for `82:803C/8043/804E/8059/8066/806D`, actual `$2142` reads/writes, queue bytes, consumed CPU master clocks and the next `$4212` poll edge. Distinguish (1) different sound branch/cycle costs, (2) different beam advancement at the same CPU instant, (3) NMI/scheduler phase differences, and (4) silent writes/restores before attributing a missing simulation frame. The original `82:8035` path can be a decisive experiment without changing sound or game behaviour.

## RF-014 follow-up: source-qualified first-load CPU/VRAM stores and pinned Baldosa contrast

**New 2026-10-14 research candidate (PR #1537, head `aed51dc`):** A no-input Baldosa guest built from `gamesbyian/uniracers-recomp@10b864b9` reports **1,327** completed cursor-wait continuations, equal to Beetle-bsnes 1,327 (Snes9x 1,326); the older UR native framework (`cd5875c`) reports **1,311**. The independent source audit here has **not replayed** these emulator observations. Research also reports first black-load reference host frames 248–276 versus old native 248–278, with later offset accumulating; the newer Baldosa guest agrees with the references to one host frame on all five attract loads. This narrows the suspected RF-014 timing problem to the old legacy SNESRecomp runtime or generated clock model. **It does not prove one specific upstream patch caused the improvement**, nor does it certify a complete Modern Windows event.

**Effective dependency identity matters:** Querying the pinned game's Git tree at `baldosa/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101` returns submodule `snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`. The checked-in `framework_pins.txt` text instead names `77867082...` and should not silently override the actual gitlink. UR main's own active `snesrecomp` gitlink remains `cd5875cbdaf19f5e324272b1f8051d671fce9215`. The imported Baldosa `recomp/bank00.cfg` explicitly enables global `paced_bus`; `recomp/bank81.cfg` independently labels `81:CD07` as `Hud_InitRace_FastRom` and `81:BB89` as `Decomp_ToVram`. A patch attribution must record which codegen directive was actually enabled.

**New ROM-free source evidence:** `tools/qa01_attract_cpu_vram_source_contract.py` checks the original USA bank-81 `81:CD70..D09C` region and reports **29 distinct `STA $2118` instruction sites** and **28 distinct address-register `STA/STY $2116` instruction sites**. They are CPU PPU-port stores, not a claim about how many times each executes per host frame. The original separate decompressor `81:BB89` contains byte-wide long stores `81:BCEE STA $002119` and `81:BCF4 STA $002118`. The archived listing includes branches and width flag changes, so actual executed PC, accumulator width and repeated visits must come from dynamic receipts, not from multiplying static store-site counts by a guessed word size. This source contract deliberately does **not** certify research's candidate 738 guest VRAM words/frame, per-frame execution of `81:CD70`, or source-synchronized CPU/NMI and beam clocks.

**Next narrow causal discriminator:** Reuse the original/native first-load host 248–278 trace. Count actual executed original `81:CD70..D09C` and `81:BB89..BD47` VRAM-store instructions, record M width and store address/value, VBlank/NMI and CPU master-clock deltas, and compare against old native `cd5875c` and newer Baldosa `075fbe4` with **exact executable+config+ROM+input hashes**. Independently classify CPU time spent in (1) ROM opcode/operand fetch, (2) I/O register writes, (3) other memory/stack, and (4) host scheduler/wait. Only if the **same executed source operations** cost too many master clocks in the old compiled guest should `paced_bus` cycle charging be the isolated candidate A/B; if the discrepancy is in `$4212` beam-status sampling, use the separate HVBJOY control. Do not apply the two upstream patches together as an untestable bundle.

**Shipping boundary:** The newer Baldosa fork's no-input attract match is promising, but the current Modern route still needs an exact nominated executable built from that fork and independently verified through a complete original/native course, finish/result/progression and post-race restore. The legacy executable remains a rollback and its RF-014 mismatch cannot be redefined away. QA-01 strict USA denominator remains **0/45**.

## Conditional instruction master-clock discriminator (QA-01 source preflight)

The newer Baldosa `recompiler/snes_cycles.py::region_speed` maps bank-81 high-ROM instruction fetch to **8 master clocks per byte when MEMSEL=0** and **6 when MEMSEL=1**. The destination CPU PPU register range `$2100–3FFF` costs **6 clocks per bus access** independently of MEMSEL. The old emitter's relevant static path charges all CPU cycles at the code-region speed, while Baldosa `paced_bus` charges opcode fetches at code-region speed and guest data transfers at their own memory-region speed. For a single source `STA/STY absolute` with three fetched instruction bytes, these are the conditional costs:

| Source register write | MEMSEL=0 legacy / paced | MEMSEL=1 legacy / paced |
| --- | ---: | ---: |
| One data byte (M/X=8-bit, 4 CPU cycles) | 32 / 30 master clocks | 24 / 24 |
| Two data bytes (M/X=16-bit, 5 CPU cycles) | 40 / 36 master clocks | 30 / 30 |

These cases are reproduced by the read-only `conditional_abs_store_master_clocks` model and unit-tested for all four legitimate inputs plus invalid widths/MEMSEL. Thus, **if the executed bank-81 store uses slow ROM (MEMSEL=0)**, the legacy model overcharges this individual I/O store by 2 or 4 master clocks. **If MEMSEL=1**, this particular PPU port-store cost cannot account for any difference between the implementations. This does **not** include surrounding guest fetch/data/stack instructions, NMI time, PPU register side effects, calls, loops, or scheduler behavior; it is not evidence that 2–4 clocks accumulated into a host-frame skip. Another regional-memory change could have the opposite sign.

The critical next receipt is therefore actual `$420D` MEMSEL at the **first executed** `81:CD70..D09C` store, actual M/X widths and source-PC hit counts, plus CPU master-clock deltas and vblank boundaries for *the same* original/native work. With MEMSEL=1, discard the proposed PPU-store clock-overcharge mechanism for these instructions immediately and investigate the first differing neighboring operation. Never patch or shift frames on the strength of this conditional model; compare separately against the exact newer Baldosa execution that already matches the no-input attract reference.

### Original MEMSEL writers that distinguish the two models

The same source contract now independently pins **four explicit bank-80/bank-83 `$420D` writer instructions** in the USA archive:

| Source instruction | Nearby original bytes | Static possible effect |
| --- | --- | --- |
| `80:91EA STA $420D` | `80:91E8 LDA #$01` | Reset/boot initialization selects FastROM (set 1) |
| `80:92E8 STZ $420D` | Later linear init, followed by `80:9311 JMP $885B` | Boot setup subsequently clears MEMSEL (0) |
| `83:CC6F STA $420D` | `83:CC6D LDA #$01` | Another game-path set to FastROM |
| `83:FA39 STZ $420D` | Original bank-83 setup/reset sequence | Another path clears MEMSEL |

These are *static direct operands*, not a complete runtime writer history or proof of the exact order at host 248. The potential FastROM set at `83:CC6F` means the simple "boot cleared `$420D`" deduction cannot establish the mode during the relevant first-load CPU writer. An actual original register write/PC receipt for `$420D` and a sampled native `g_memsel` at the first `81:CD70` execution are the cheapest discriminators. The test deliberately refuses to set `first_load_memsel_value_proven` or infer unobserved indirect writers.

## Static direct caller qualification for the candidate bank-81 first-load writer

A bounded original USA direct xref adds a possible **attribution trap** to the RF-014 first-load candidate. The 29 bank-81 `81:CD70..D09C` VRAM-data store sites belong to the decomp/Baldosa source-labelled **`Hud_InitRace_FastRom`** family. The archived original direct wrapper is `81:CCE6 JSR $CD07; 81:CCE9 RTL`, and the visible long caller is `82:DC1A` (`22 E6 CC 81`). The preceding source code at `82:DBF7/DBFA` stores P1/P2 lap counts (`$0EF1/$0EF3`), at `82:DC13` calls race-event-queue initialization, and at `82:DC17` calls the associated video setup. This is a strongly **race-setup-shaped** call chain, not by itself an identified title-loading routine.

Research PR #1537 assigns candidate executed CPU VRAM work in this bank-81 region to the first black attract load at host 248–276, whereas the same research places the first no-input attract **race** much later (around 1423). There may be valid repeated or indirect entry paths, or the CPU observer may be attributing different VRAM activity; static evidence alone cannot resolve it. The new `hud_direct_caller_source_contract` fails closed on all identified opcode/operand changes but explicitly marks actual host-248 execution and exhaustiveness over indirect calls as **unproven**. The cheapest live discriminator is now simply to capture actual original executing PBR:PC for `$2118` writes in host 248–278, then label whether each write came from `81:CD70..D09C`, `81:BB89..BD47`, or another original code path. Only after this attribution should the conditional MEMSEL/master-clock charge model be applied to the relevant observed instruction family.

Do not relabel a named HUD routine as the first-load decompressor solely because its static bytes contain PPU-port stores. Conversely do not discard a valid original executed CPU PC just because its recovered source name sounds improbable. **Executed evidence decides.** This is not a graphical OAM/PPU implementation or QA-08 result, and the USA complete-course release count stays **0/45**.

## Stronger first-load original source route: title/logo upload is not race-HUD upload

An additional bounded original USA cross-reference, captured as `attract_upload_direct_source_contract`, identifies source paths much closer to the black attract/title loads than the race-specific `81:CD70..D09C` HUD initializer.

- In original `80:93FB Attract_Main`, `80:9402 STA $2100` engages forced blank, followed by `80:941B JSL $82B1D8` with immediate `A=#4E` and `80:9424 JSL $82B1D8` with `A=#48`. These are *static source call sites*, not dynamically observed host frame 248.
- The original logo setup separately calls `82:B1D8` at `80:B0A6` (`A=#50`) and `80:B0AF` (`A=#4A`), then executes a `JSR $FAC9` cursor/VBlank wait inside `80:B0C3` and its countdown. These show another plausible first-load family without equating attract screen and logo loading.
- In source `82:B1D8`, `82:B1DB SEP #$20` makes accumulator 8-bit, `82:B1DD STX $2116` sets VRAM address and `82:B1ED BEQ $B208` selects an alternate compressed path if `$4D == $80`. On the ordinary path, the loop `82:B1F2` fetches a byte, `82:B1F5 STA $002118` stores it, `82:B1F9` fetches the next byte, `82:B1FC STA $002119` stores it, and `82:B200/B201 DEX/DEX; 82:B202 BNE $B1F2` repeats. On the alternate path, `82:B216 JSL $81BB89` enters `Decomp_ToVram`, which has other byte-wide PPU writes at `81:BCEE` and `81:BCF4`. Neither route is DMA; both explicitly use original CPU I/O instructions.
- This offers a *plausible* family for the research-reported approximately 738 VRAM words/frame. The true executed PC distribution, branch selection, word count, timing and source stage at host frames 248–278 remain **unmeasured by this contract**. In particular, do not promote 29 static HUD `STA $2118` sites to 738 dynamic first-load writes.

The source is an exact direct-call/branch-byte contract with adversarial mutated-opcode, duplicate-PC and swapped-VRAM-byte-write tests. It does not assert which source path is the actual host-248 black load. The first useful **dynamic** receipt is an original opcode/PPU writer log for one dense first-load host window: count `82:B1F5` and `82:B1FC`, `81:BCEE` and `81:BCF4`, `81:CD70..D09C`, and any as-yet-unknown PBR:PC; record the original `82:B1ED` branch result, guest `$420D` and M-width, observed VRAM address/data, CPU clocks, NMI and VBlank edges. The same trace should be collected for the old UR native `cd5875c` and newer Baldosa `075fbe4` binaries with exact input/ROM/config IDs. Keep one named earliest source divergence as the target rather than extrapolating the accumulated 17-frame attract drift.

For each `STA long` to `$002118/$002119`, the original source contains a **four-byte instruction fetch plus a byte of PPU I/O data**. Under the pinned conditional emitter-region model, with MEMSEL=0, the older uniform-code-speed model charges 40 master clocks per 8-bit store versus 38 with Baldosa's region-paced bus; a two-store low/high loop pair would thus differ by 4 clocks *if executed and if these modes apply*. Under MEMSEL=1, both compute 30 clocks per 8-bit store, no such excess. Under M=0, the hypothetical one-instruction difference is 4 instead of 2; `82:B1DB SEP #$20` specifically selects M=1 in its direct upload path. Do not treat any of these *conditional microcosts* as proof of a multi-frame delay without the actual executed path and integrated CPU/beam timing. A hardware-compatible source flow cannot be repaired by trimming guest code or inserting arbitrary timing shifts.

**Three-project reuse choice:** keep the existing UR original/native frame/oracle harness and source opcode crosswalk; reuse the imported Baldosa original labels, generated-clock methodology and existing fail-closed QA-01 tests, and consult Malmazuke's replay/original-identity discipline. No new emulator, new recurring workflow, guest-engine rewrite or graphics/Modern ownership required. **Strict USA event credit remains 0/45.**

## Actual 2026-10-14 Windows/Modern framework identity boundary

The distinct no-input attract outcomes cannot be generalized across different native executables. A read-only current-source preflight in `tools/qa01_native_framework_lineage.py` checks the effective original-recompiler lineage of *three* build/packaging paths:

| Build path in current repo | Effective configured framework | What this does **not** establish |
| --- | --- | --- |
| `.github/workflows/modern-shared-native-acceptance.yml` with `canonical_candidate != true` | `tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only` → repository-owned `tools/toolchain.json` / `tools/toolchain-entries/snesrecomp.json` pin `RetroPortingToolKit/snesrecomp@cd5875cbdaf19f5e324272b1f8051d671fce9215`, then Modern guest recompilation | Not the newer Baldosa guest, no reference-matched attract claim |
| `.github/workflows/modern-native-heavy-router.yml` canonical Modern Linux build | Same pinned original UR `cd5875c` staged from `.tools/src/snesrecomp`; its `modern-native-canonical-candidate` can be consumed by Shared Modern acceptance when `canonical_candidate == true` | A borrowed canonical artifact is *not* identified by the borrowing workflow alone; inspect its producer/ZIP checksum |
| `.github/workflows/windows-native-smoke.yml` portable Windows x64 ZIP | Same `tools/bootstrap_toolchain.py` staged old UR `cd5875c` plus project patch stack, with `assemble_windows_package.py` | Source manifest alone cannot attest a downloaded exact executable/ZIP, runtime CPU parity or a physical release test |
| `.github/workflows/baldosa-windows-native-bridge.yml` independent Baldosa Windows title | Checks out `gamesbyian/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101` and asserts its **actual** submodule `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709` before native build | A different Windows executable, not automatically the one packed by `windows-native-smoke.yml` |

The separate new Baldosa guest's **1,327** no-input attract VBlank-wait passes versus reference Beetle's **1,327** (Snes9x 1,326) are encouraging bounded original-native research observations. The older UR executable's **1,311** passes remain an observed discrepancy, including on the ordinary default Modern and portable Windows *framework lineage*. That does **not** establish the same *number* of missing waits in a freshly nominated packaged Windows ZIP, as candidate state, version, exact binary and output must still be independently replayed.

The static framework lineage checker and adversarial unit tests fail closed on changed canonical pin, removed clone/build steps, unqualified shared-candidate reuse and changed Baldosa source gitlink. The checker deliberately says **downloaded ZIP exact SHA provenance not proven**, **two Windows binaries not identical**, and **release credit 0**. This is gameplay-source QA evidence classification. The independent release-quality ledger remains exclusively owned by QA-02/12 and is unchanged; the Modern product implementation, package or workflow remain untouched.

For a true shipping-candidate resolution: first nominate exact Windows ZIP/executable with a retained source+framework pin and SHA; then capture that binary's same-input no-input attract and first-load PBR:PC/beam traces against both original cores and the distinct Baldosa fork, before admitting any gameplay or event timing result. The original sequence and controller masks must remain unchanged; no targeted byte/clock patches without a falsified earliest cause. **USA strict completed events still 0/45.**
