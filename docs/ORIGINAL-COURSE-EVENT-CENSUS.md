> **Fresh independent original/raw Bowl byte review (same date, 0/45):** Downloaded and locally rehashed [run 39168164480, artifact 12151357791](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480/artifacts/12151357791), exact source `9ee3b8cb876f630d259882dde62da07ba6217c8d`, **ZIP SHA256 `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`**. Reopened all 24 original/native 128-KiB WRAM plus 24 8-KiB SRAM images and checked their individual SHA-256, source-guest log clocks, scored rank0 764 and full table checksum against the original producer: **3,041 unmasked different WRAM byte occurrences, 0/12 equal full WRAM pairs, 0/12 equal full SRAM pairs**. The exact **same three SRAM bytes** differ at all 12 offsets (`0EF6` 01/00, `0F31` 01/00, `0F33` 05/04), none affecting the earned Bowl record. At source-relative Bowl result **+334/+338/+339**, only two WRAM menu-animation counters `7E:00C6/00C8` differ. At **+340**, still before either observed next-race entry, WRAM divergence expands to **33 bytes** including source-labelled NMI flag, stack, rival setup and sound queue. Fresh original enters the next race at **+341**; native at **+344**, with **666/688/671** differing bytes at +341/+342/+343. **First differing byte is not first *causally relevant* writer**: imported Baldosa labels are unverified runtime hypotheses; CPU/APU owner should qualify the first actual consumed +339→+340 state writer/reader, not mask or rephase the 3-frame transition. [Machine byte census and precise witness scope](../analysis/data/qa01-bowl-independent-raw-byte-review-20261018.json). No Windows disk proof, full instruction parity or accepted USA event. 

> **Current independent USA event decision, 2026-10-18 (0/45):** Real source-pinned [Bowl result→Switcher run 39165986390](https://github.com/gamesbyian/UR-Recomp/actions/runs/39165986390), exact PR source `c634918f541a7c1d33e5bd51ae75c4d7b5506532`, reached scored Bowl result **MIKE 764**, but the genuine 2014 movie enters the next Switcher at Bowl result **+342**, fresh Snes9x at **+341** (host 4690), and native at **+344** (host 4693). These are independently printed guest clocks, **not** a three-way pass. The actual diagnostic job returned green for its one-frame Bowl *diagnostic* despite the strict progression negative: **12/12 unmasked 128-KiB WRAM handoff pairs unequal and at least one 8-KiB SRAM pair unequal**. A separate [genuine cold-reload run 39167303557](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167303557), source `255886a0bf9d9415109c3b43d862306efcc61e48`, recovered source-earned **764** with consistent record words/holders/checksum in **two fresh guest processes** at startup +300/+420. This is a bounded guest cold positive, **not** full-event, Windows disk/power-cut or source/native clock parity. Exact run IDs/producer outcomes are [PR #1844's machine receipts](https://github.com/gamesbyian/UR-Recomp/blob/9ee3b8cb876f630d259882dde62da07ba6217c8d/analysis/data/qa01-bowl-cold-guest-executed-20261018.json), which are not independently rehashed archive ZIPs. Independent [raw-byte verifier](../tools/qa01_bowl_handoff_raw_archive_audit.py) merged in #1848; first two archives lacked the raw handoff guest memory images and cannot be retrospectively called independently byte-rehashed. **Disposition: Bowl strict progression FAIL, no course admission.** Keep original/native clock differences visible and send semantic CPU/SPC causes to their owner; do not shift controller frames, waive SRAM/WRAM, label a diagnostic exit 0 as acceptance, or repeat the identical negative to harvest a green result. Latest Zoo remains the better first-event candidate via [bounded source-based independent review](QA01-INDEPENDENT-FIRST-USA-EVENT-ACCEPTANCE-20261018.md); still no complete causal parity or exact Windows shipping acceptance. **USA accepted 0/45; release QA gates 0/12.**

> **RF-043 exact earliest Zoo stack witness window (2026-10-17; 0/45):** Re-audited immutable genuine [RF041 control case](https://github.com/gamesbyian/UR-Recomp/actions/runs/39069703970/artifacts/12115251490) (ZIP SHA256 `1c21481a...`, all 78 unmasked whole-WRAM pairs). Independent original/native host entry **1017 (+0)** is byte-exact; **first real four-byte mismatch at host1018 (+1)** in `01ED–01F0`, persists sampled +2/+4, full-WRAM equal again +8/host1025. Across entire sampled course **20 four-byte stack windows (80)**, **five two-byte stack `01EE/01F1` windows (10)**, **two `0063` sound windows (2)** = **92 unmasked byte occurrences**. Source-original movie clock entry3190 remains separate from fresh guest host1017. [Executable fail-closed RF043 checkpoint auditor](../tools/qa01_rf043_zoo_first_stack_window.py) and [first-writer/NMI protocol](RF043-ZOO-STACK-FIRST-DIVERGENCE-20261017.md) pin the next **host1017..1025 original/native opcode/interrupt actual read/write witness**; this *does not* prove writer provenance, safe masking, complete-event parity or release credit.

> **RF-042 rejected equal-age native SPC queue A/B (2026-10-17; 0/45):** Genuine original/native [run 39072151377](https://github.com/gamesbyian/UR-Recomp/actions/runs/39072151377), immutable source `8be9337d`, built and executed Zoo (producer exit0); case step failed absent native IPL witness. Independently SHA-verified [14-file artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/39072151377/artifacts/12115434806) `1fc55834...` against RF041 control: **all 78 original-source full-WRAM sample hashes identical**, while original/native exact whole-WRAM pairs **51→46**, unmasked byte differences **92→106**, seven new native sound-DP changes frames +5040..+5046 at `0063/0064/0069`. Target native `82B4` writer and `QA01RF042TIE` marker missing; IPL 117→0. Zoo result +5163, Bowl +267, whole SRAM/cold record checks remain bounded. **Equal-age after-opcode queue trial is rejected, no shipping correction or event credit.** [Negative source findings](RF042-REJECTED-EQUAL-AGE-SPC-QUEUE-20261017.md), [SHA/byte machine receipt](../analysis/data/rf042-rejected-equal-age-native-ab-20261017.json), [historical unmerged trial #1795](https://github.com/gamesbyian/UR-Recomp/pull/1795).

> **RF-041 source-executed CPU↔SPC opcode-debt tie resolution (2026-10-17; 0/45):** [Genuine V2 Zoo run 39069703970](https://github.com/gamesbyian/UR-Recomp/actions/runs/39069703970), frozen staging source `54c3660b`, independently SHA-256 rehashed 18-file case `1c21481a...`, observes original CPU-port2=24 Snes9x SMP sync from local age **103919447 to 103919450** with *zero* source SMP debt, actual F6 PC154F opcode 7E cycle2 reading old23 **before** same-local-age CPU port publication, then new24 at local age103919457. Native applies queued 24 before same-local-age F6 PC154F consumes new24 at native age103919434 with **cpuCyclesLeft=0**. Thus nonzero SMP/deferred-cycle debt does not explain this particular local ordering disagreement. **Do not equate absolute SPC clock axes, insert artificial CPU polls or globally shift queue**; only an architecture-grounded instruction-atomic equal-target visibility A/B could justify smallest correction. All 78 full-WRAM pair observations, 13 dense sound DP, Zoo +5163, Bowl +267, 11 full earned SRAM and two guest cold reload controls remain byte-identical to RF040; 51/78 whole WRAM pairs exact, all 92 unmasked residual byte-occurrences remain, **0/45 complete USA events**. [Actual source/debt and native queue receipt](../analysis/data/rf041-v2-executed-zoo-smp-debt-boundary-20261017.json), [RF041 report](RF041-ZOO-SMP-OPCODE-DEBT-20261017.md). Next independent Zoo stack last writer/next reader/NMI provenance.

> **RF-040 executed CPU-visible echo-return proof (2026-10-17; 0/45):** [Genuine USA Zoo one-shot 39066224227](https://github.com/gamesbyian/UR-Recomp/actions/runs/39066224227), source f28fa3168fa39fb160910fd647050b7fa62d0cf, [18-file SHA-verified case archive](https://github.com/gamesbyian/UR-Recomp/actions/runs/39066224227/artifacts/12113836860), confirms source-original six genuine CPU CMP $2142 returns **23,23,23,23,23,24**, native three genuinely paced read returns **23,23,24** (raw=post-filter). Actual source SPC PC1555 output echo24 occurs at original local SPC age103919466 between fifth and sixth CPU polls; native SPC PC1555 echo24 at native local age103919443 between second and third CPU polls. Original/source SPC incoming-new24 read→echo takes 9 local ticks; native takes 9; source original CPU publication→echo takes 16 local ticks and native queued apply→echo 9, *without any equivalence of absolute clocks or a qualified fix*. All 78 paired raw full-WRAM observation records, 13 sound DP samples, result +5163, Bowl +267, 11 SRAM and cold record outcomes are **identical to RF039**; 51/78 unmasked pair equality, 92 real stack/sound residual byte-occurrences and 0/45 unchanged. [Exact receipt](../analysis/data/rf040-executed-cpu-echo-20261017.json), [full report](RF040-CPU-ECHO-SPC-OUTPUT-PROTOCOL-20261017.md), [source-only PR #1787](https://github.com/gamesbyian/UR-Recomp/pull/1787). Next source SPC opcode clock-debt/apply boundary, no blind shift, stack masking, Windows shipping QA or USA event admission.

> **RF-039 executed target sound receiver order, source-qualified (2026-10-17; 0/45):** In real USA Zoo [run 39064227716](https://github.com/gamesbyian/UR-Recomp/actions/runs/39064227716), source `a8a82f53...`, independently SHA-256 verified case artifact `4fb6ea55...`, original SPC F6 at **source age103919450/PC154F reads old 23 before same-age CPU port2 publishes 24**, then reads 24 at **103919457**. Native exact queue apply of port2 24 at its independently measured **SPC age103919434 occurs before the same-age PC154F F6 read sees new 24**. Subsequent original/native F6/F7 PC/value recipient sequence matches at six tracked landmarks with recorded age offsets 22–23 cycles; this does not equate the absolute axes. Native **1289/1289** host6091 CPU port2/3 publications have exactly ordered queue schedule values; 219 targeted original SPC reads and 4535 native queue/receiver events with no truncation. All 78 full-WRAM sample records are **bit-identical to RF038 V2 source/control**, 51/78 original/native pairs exact and 92 residual byte-occurrences remain unmasked; true Zoo +5163, next Bowl +267, 11 full earned SRAM pairs and cold guest ranked record agree. Research `strict_candidate`, **0/45** complete USA events. [Exact machine receipt](../analysis/data/rf039-executed-zoo-spc-receiver-order-20261017.json), [source execution and next discriminator](RF039-TARGET-SPC-RECEIVER-PROTOCOL-20261017.md), [draft #1781](https://github.com/gamesbyian/UR-Recomp/pull/1781). Next: actual CPU port2 echo-return values, SPC output publication and instruction-atomic queue boundary; only then narrow A/B, never a global tick shift or stack mask.

> **RF-038 executed 6:3 polling discriminator (2026-10-17; 0/45):** Corrected [genuine USA Zoo V2 run](https://github.com/gamesbyian/UR-Recomp/actions/runs/39019821122), source `7ce5e2cb`, independently SHA-256 verified 18-file case artifact 12096114331 (`70da829b...`), brackets original CPU frame6091/V116 writes `82:82F6 STA $2142` at H442 and `82:82F2 STA $2143` at H972. **Six** source executed `82:8301 CMP $2142` polls versus **three** native `cpu_read8_paced($80:2142)` polls at master 2176886940/6992/7044 (52-clock spacing); exact port writer intervals **530 versus 374 = +156**. This narrows discrepancy to the *observed CPU poll loops*, not a demonstrated SPC queue defect. Source SPC F6/F7 read versus native queue schedule/apply/receiver still missing. 51/78 unmasked full-WRAM paired images exact, source Zoo +5163/Bowl +267, 11 earned whole SRAM pairs, cold guest result unchanged; independent complete USA acceptance **0/45**. [Report](RF038-EXECUTED-SOUND-WRITER-INTERVAL-20261017.md), [machine receipt](../analysis/data/rf038-v2-executed-source-native-poll-count-20261017.json). No timing patch, stack masking, release-ledger or Windows-shipping claim.

> **RF-037 source-executed sound-payload equivalence completed and merged (2026-10-17; no USA admission):** [Merged #1756](https://github.com/gamesbyian/UR-Recomp/pull/1756) replays the unchanged real USA Zoo with independently pinned [V4](https://github.com/gamesbyian/UR-Recomp/actions/runs/39006650922) and [V5](https://github.com/gamesbyian/UR-Recomp/actions/runs/39010683041) guests. The original CPU genuinely publishes **45,645** port2/3 values; the native publishes **56,041** over a longer host window, whose first **45,645 port/value pairs match the entire original prefix byte-for-byte** after resolving *only three source-SPC-age-tied two-write order ambiguities* (SHA-256 for both 91,290-byte streams `ca1db861be56cabef9152f950be39a8d179722bb5cdb890e1ae23f9b7260f084`). This is payload equivalence, **not** exact SPC recipient phase or within-age source bus order. The unmasked **78 full 128-KiB WRAM** sample pairs still show **51 exact**; **90 of 92** unequal byte occurrences are in stack-page `01ED–01F1`, two are live sound pointer `$63`, and zero are elsewhere among these samples. Source/fresh-original/native result **+5163**, Bowl **+267**, 11 entire SRAM pairs and cold ranked record unchanged; no timing patch and **USA 0/45**. [Source report](RF037-SOUND-TRANSACTION-20261017.md), [exact port receipt](../analysis/data/rf037-v5-exact-source-native-port-stream-20261017.json), [Zoo stack census](QA01-ZOO-STACK-RESIDUAL-CENSUS-20261017.md). Next source-validated discriminator: original SPC F6/F7 true reads vs native queue schedule/apply/reader on separately calibrated clocks, plus genuine Zoo stack writer/reader/NMI instruction provenance. RF-036 global-phase negatives still prohibit blind shifts, masking and QA-ledger edits.

> **RF-036 executed negative, RF-037 source consumer handoff (2026-10-17; 0/45):** Authentic [IPL timing A](https://github.com/gamesbyian/UR-Recomp/actions/runs/38998740919) and [in-flight timing B](https://github.com/gamesbyian/UR-Recomp/actions/runs/38999611814) demonstrably published first CC *after* the genuine SPC comparator, yet original/native full unmasked 128-KiB WRAM equality **regressed from 51/78 to 46/78 and 0/78**, respectively. First B disagreement appears at **Zoo +0, 7E:01D6**; sound counter and stack residuals worsen. True Zoo +5163, Bowl +267, 11 whole earned SRAM matches and cold guest ranked-record reload cannot waive those regressions. Rehashed [machine receipt](../analysis/data/rf036-executed-ipl-boundary-negative-20261017.json), [full falsification report](RF036-IPL-PORT-ORDER-NEGATIVES-20261017.md). The literal IPL fix draft #1747 was closed **unmerged**; do not repeat global/special-case phase shifts. **RF-037** next proves real $63 pointer consumer → CPU $2143/$2142 writer → SPC recipient in both +5040 and +5045 windows with calibrated clocks. Shipping Windows event and all-frame CPU parity still unproven. **0/45.**

> **RF-035 source-executed reader liveness, no event admitted (2026-10-16):** [One exact original/native source Zoo run 38999341435](https://github.com/gamesbyian/UR-Recomp/actions/runs/38999341435) with [machine receipt](../analysis/data/rf035-source-executed-live-sound-consumer-20261016.json) and [executed report](RF035-EXECUTED-LIVE-SOUND-CONSUMER-20261016.md) proves the original bank-82 sound LDA/STA/port compare opcodes execute and native sound pointer `$63` is truly consumed (last frame6056 word `C773` in `Snd_IncDataPtr`, first frame6057 `C774` in `Snd_UploadBlock_80D1`, matching native +5040 `74` vs original `73`). Both source traces explicitly **truncate** before a symmetric +5040/+5045 original/native port-value chain can be established. SHA-verified RF034 controls stay invariant **78/78 original, 78/78 native full WRAM hashes**, 51/78 pairwise exact, 92 unmasked residual byte occurrences, Zoo +5163, next Bowl +267 and 11 full earned SRAM pairs. RF037 needs bounded frame-scoped real reader/writer/port receipt. **No shipping fix, no independent Windows equivalence and 0/45 acceptance.**

> **RF-035 consumer-liveness experiment prepared (2026-10-16; not executed; 0/45):** [Read-only opcode/WRAM helper observer and fail-closed protocol](RF035-SOUND-CONSUMER-LIVENESS-PROTOCOL-20261016.md) target the original executed $02:82F0/82F2/82F6/8301 upload instructions and native actual $63/$64/$69 read helpers during the +5040/+5045 sound residual. Require a live consumed value to downstream $2142/$2143 transaction before changing RF-034 first-CC ordering; direct AOT helper bypass must stay an explicit coverage gap. Retain all 78 full-WRAM, 13 sound, 11 earned SRAM, Zoo +5163/Bowl +267 and exact Windows source gates. No executable replay was conducted under RF-035 and no correction or event is claimed. **0/45.**

> **CPU/Windows source identity corrected on main (2026-10-16; not a complete-event admission):** Merged [#1744](https://github.com/gamesbyian/UR-Recomp/pull/1744) (`a1621b7e`) stages source-qualified RF-015 + RF-017 in-order CPU I/O clock generation in the one existing native Windows bridge, regenerating from the pinned USA ROM and requiring **89 generated banks / 15,484 in-order charges** with preserved block clock totals before linking. Exact integrated PR head `a7968317` passed compiled real Windows guest, **13/13 scripted journeys**, ROM-free candidate binding and independent unit/hygiene workflows ([Windows run 38996071005](https://github.com/gamesbyian/UR-Recomp/actions/runs/38996071005)). This removes the RF-015-only build source blocker [#1686](https://github.com/gamesbyian/UR-Recomp/issues/1686) but **does not** establish fresh Windows original/native +5163/+267 clock/input equivalence, full WRAM parity, SPC/stack liveness, cold publication or physical release QA. Earlier original/native research results remain research-specific. The nominated pre-change ZIP is immutable; **0/45 events and 0/12 release witnesses admitted**.

> **QA-01 exact composite ELF independently restarted original/native guests with source-earned Zoo record (2026-10-16; no Windows disk/power-cut proof; 0/45):** [Hosted run 38959452580](https://github.com/gamesbyian/UR-Recomp/actions/runs/38959452580) reused exact native ELF SHA-256 `9a3bd17a…` and original Snes9x SHA-256 `ec4ce30d…` from the original combined-stage candidate after code-only correction of the exact extended script SHA `1eb3e841…` preflight. ROM and 2014 source movie hashes were independently enforced. Genuine Zoo `+5163/+5163`, source/fresh-original/native Bowl `+267/+267/+267`, 78 real unmasked Zoo WRAM mesh captures, 13 consecutive +5034..+5046 sound DP frames and **11/11 full SRAM handoff pairs** again passed. Unlike prior in-process-only evidence, the unmodified real result+72 images were staged into **distinct new original/native guest processes**, and each recovered MIKE's earned **2510-centisecond lap**, ranked-record table/holders and valid checksum at cold startup frames **300 and 420**. [Bounded machine envelope](../analysis/data/qa01-composite-exact-elf-cold-reload-hosted-20261016.json), [witness artifact 12071918268](https://github.com/gamesbyian/UR-Recomp/actions/runs/38959452580/artifacts/12071918268) SHA-256 `0da1db998a22caadd869e444e699eff0bdfdd54ec24d944743506c6096833fd5` (expires 2026-10-23 20:09 UTC). This closes **research native guest-level cold ranked-record load only**; no shipping Windows autosave publish, disk hard-kill/transaction test, all-frame CPU/SPC liveness, handoff stack-reader proof or independent QA admission. Source-owner [decision and next clocks](QA01-EXACT-COMPOSITE-COLD-GUEST-ELIGIBILITY-20261016.md). **0/45 remains.**

> **RF-029 executed negative, not admitted (2026-10-16):** The opt-in IPL SPC `CMP $F4,#$CC` read moved from opcode cycle 5 to cycle 4 (temporary source `1c59ae63...`), an actual original/native [one-shot run 38961077234](https://github.com/gamesbyian/UR-Recomp/actions/runs/38961077234) and independently rehashed case artifact `12073346907` compared against exact composite ELF [run 38884542449](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449). All **78 original** 128-KiB WRAM image hashes match across runs; **only 7 native frames +5040..+5046 changed**. Original/native full-WRAM equality **regressed 51/78 → 46/78**, with differing-byte occurrences **92 → 104**; the sound-pointer `$63` and sound-counter `$69` now both differ at seven frames, rather than only two pointer differences with 13/13 equal counters. Genuine Zoo source/fresh-original/native result **+5163**, Bowl continuation **+267**, earned ranked MIKE record and **11/11 full SRAM pairs** remain matched. RF-029 intervention and temporary workflow retired without production promotion; low-stack +266/+280 byte residuals and executed SPC/CPU consumer clocks still unresolved. [Permanent detailed technical result](RF029-IPLCMP-BUS-PHASE-20261016.md) and [machine A/B receipt](../analysis/data/rf029-zoo-iplcmp-negative-ab-20261016.json). **0/45 accepted.**

> **QA-01 exact same research binary now passes bounded authentic Zoo-to-Bowl progression (2026-10-16; 0/45):** Independent read-only [run 38884542449](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449) re-used SHA-exact ELF `9a3bd17a…` from combined three-event [run 38879846733](https://github.com/gamesbyian/UR-Recomp/actions/runs/38879846733) and original core `ec4ce30d…`, without recompilation or controller rephase. Genuine USA Zoo source/fresh-original/native result +5163/+5163/+5163 and next Bowl from Zoo result **+267/+267/+267**; 11/11 full 8KiB SRAM pairs and all named states equal, 9/11 full 128KiB WRAM pairs equal with **eight** unmasked stack-byte occurrences at +266/+280. The 78-checkpoint Zoo full-WRAM mesh has **51 exact, 27 different**, 92 differing-byte occurrences. Across +5034..+5046, `$69` audio counter agrees **13/13** and `$63` sound pointer differs by **one count only** at +5040 and +5045, much improved over earlier research guests. The one-shot job's final red status is an **incorrect shorter-source-script SHA guard** after a genuine successful producer and `strict_candidate` classification; the expanded original script hash matches all older full-window controls. [Permanent SHA-verified exact-ELF QA report](QA01-COMPOSITE-EXACT-ELF-ZOO-HANDOFF-20261016.md), [machine receipt](../analysis/data/qa01-composite-exact-elf-zoo-handoff-20261016.json); temporary PR #1706 was closed without merge. Sampled progression is stronger but unsampled frames, sound writers/SPC handshake, Windows product identity and cold disk persistence remain **unaccepted**. **0/45 complete USA courses admitted.**

> **QA-01 latest source-original/native event research (2026-10-16; 0/45 admission):** Independently rehashed actual [campaign 38879846733](https://github.com/gamesbyian/UR-Recomp/actions/runs/38879846733) on exploratory **non-main** RF-015..019 plus SPC/interrupt-stage native build. Zoo, Bowl and Switcher all reached `strict_candidate` with matching fresh original/native relative result **+5163/+5163**, **+3365/+3365**, **+4704/+4704** and genuine rendered text; six paired full 8192-byte SRAM snapshots and three-way named states also match per event. **All 18 paired full WRAM samples are non-byte-exact**. Switcher's archived original movie result duration is **+4703**, not fresh original/native **+4704**; distinct source-clock delta is now explicitly recorded, not rephased or promoted to source equivalence. The Zoo +267 next-Bowl lifecycle and +5040 audio pointer mesh were **not observed** on this exploratory binary. Permanent [source-pinned QA review](QA01-EXPLORATORY-SPC-THREE-EVENT-REVIEW-20261016.md) and [three-event machine receipt](../analysis/data/qa01-combined-spc-three-source-event-review-20261016.json). **0/45 complete original/native USA event passes, no Windows release credit.**

> **QA-01 archived native NMI sequence census (2026-10-10):** Without another emulator run, hash-verified [artifact recovery run 38098340646](https://github.com/gamesbyian/UR-Recomp/actions/runs/38098340646) found **four fully captured and register-verified `I_NMI_M1X1` PHB/PHD/PHX/PHY/PHA16/PHA8 stacks** in the original native run's limited WRAM write log: native frames **5781, 5786, 5787, 5788**, full A words **`4004, 4040, 4004, 4004`**. SP before→after was **`01DE→01DC`** at 5781 (word at 01DD) and **`01E3→01E1`** for the other three. [Exact source witness](../analysis/data/switcher-native-nmi-complete-stack-prologues-20261010.json); [full original five-frame A comparison](../analysis/data/switcher-original-nmi-pha-full-accumulator-executed-20261010.json). Source Snes9x `ICPU.Frame` **is not aligned** with native `snes_frame_counter`; incomplete/unlogged bursts cannot be called absent. The original actual result and text match at host 5783, but guest-relative **+4704/+4702 fails**; USA **0/45** unchanged.

> **QA-01 original NMI full-A research executed (2026-10-10):** Real original/native [run 38097707477](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097707477) (green) independently qualified actual Switcher MIKE `1:08.81` result at host 5783 and strictly failed guest-relative **+4704/+4702** onset. Read-only original Snes9x original `I_NMI+6` **`PHA 00:858E`** accumulator over `ICPU.Frame` 5778–5782: **`4040, 4004, 4042, 4042, 4004`**, with M=0 throughout. Original frame **5780** writes full A=`4042` at stack `01DD–01DE` (SP `01DE→01DC`), low byte `08→42`, high `00→40`; native separately writes full **A=`4004`** at the same stack address under `I_NMI_M1X1` with the same inferred SP delta at native `snes_frame_counter 5781`. The original uses A=`4004` also in source CPU frames **5779/5782**, but at *different SP*, not a proved exact cross-guest clock alignment. [Full executed source registers / CI artifact hash](../analysis/data/switcher-original-nmi-pha-full-accumulator-executed-20261010.json), [technical crosswalk](QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md). **No proven exact same-instruction A parity, no waived timing, USA 0/45 admitted.**

> **QA-01 original/native NMI accumulator-push agreement now established (2026-10-10):** No new emulator work was needed: [green artifact recovery run 38095592659](https://github.com/gamesbyian/UR-Recomp/actions/runs/38095592659) reexamined the exact logged native stack writer at Switcher frame **5781**. Native `I_NMI_M1X1` writes **word `4004` at `7E:01DD`**, with **A=`4004`**, 16-bit M=0 and S=`01DD` at write, following consecutive PHB, PHD, PHX, PHY stores. The pinned generated source implements precisely this **16-bit PHA** with SP **`01DE→01DC`**, exactly matching the already-executed original **`PHA 00:858E`** stack-pointer movement and target. **Original 01DD byte `42` and native byte `04` differ**, under unaligned original ICPU.Frame 5780 and native snes_frame_counter 5781; accumulator equality at the same CPU/beam instant and read-consumer liveness are unresolved. [Permanent raw writer/CPU register evidence](../analysis/data/switcher-native-nmi-01dd-exact-pha-source-20261010.json). Genuine MIKE result text still matches at host 5783; strict guest-relative +4704/+4702 remains red and official **USA 0/45** remains unchanged.

> **QA-01 executed fresh-original 01DD writer resolution (2026-10-10):** Verified [original/native Switcher run 38094600828](https://github.com/gamesbyian/UR-Recomp/actions/runs/38094600828) and [machine witness](../analysis/data/switcher-original-fresh-01dd-nmi-writer-20261010.json) now attribute the original fresh-original `7E:01DD` byte change in original `ICPU.Frame 5778–5782` specifically to **`PHA` opcode `48` at `00:858E`**, frame **5780**, PPU V-counter **225**, SP `01DE→01DC`, byte **08→42**. Five separately captured original automatic NMI-entry pushes (one per frame, each four-byte SP decrement) **never cover or change `01DD`**. The independently paired native trace instead shows a generated `I_NMI_M1X1`-scoped **write attempt** of **04** at native frame **5781** (SP 01DD); those frame clocks and AOT/CPU opcode scopes are **not yet proven aligned**. Real result time/text and same-host frame 5783 remain matched while **strict guest-relative +4704/+4702 still fails**. The pinned original symbols place `00:858E` at **`80:858E`, six bytes into `80:8588 I_NMI`**, directly corresponding to native `I_NMI_M1X1` function-owner scope; the original hardware NMI-entry pushes are separate. **Shared NMI routine ownership is now supported**, but exact same instruction, accumulator/stack phase, pushed byte value and live pop/reader are still unproven. **No original movie input changes, no waived parity, USA 0/45 admitted.**

> **QA-01 executed original/native Switcher stack writer handoff (2026-10-10):** Paired source-unaltered green original/native [run 38090897908](https://github.com/gamesbyian/UR-Recomp/actions/runs/38090897908) independently reconfirmed exact host **5782** eight WRAM offsets (and zero VRAM/CGRAM differences), original/native actual positive MIKE result text at **host 5783**, and the **strict +4704/+4702 guest-relative result timing mismatch**. A read-only native WRAM logger captured **32,333 writes** across the eight suspected stack-page bytes in native frames 5775–5788. Generated native `Res_LoadToVram_B1F2` scopes write **F4/FB** return-byte values to `7E:01F1`, corroborating original independent `JSR 82:B1F2/82:B1F9` stack pushes. Native `I_NMI_M1X1` scoped **one 7E:01DD write at frame 5781**, and native `Text_FormatRaceTime` scoped seven `7E:01E6` writes. Original-only source-17030 opcode observations and native host-5781 write *attempts* do **not** share a clock or equal byte-change semantics; original fresh-host writer/consumer liveness and native PC/NMI phase remain unresolved. Full [source-visible bounded native witness](../analysis/data/switcher-native-stack-actual-writers-20261010.json), [analysis](QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md), hash-attested [artifact 11684141556](https://github.com/gamesbyian/UR-Recomp/actions/runs/38090897908/artifacts/11684141556). **No complete original/native course admission: still 0/45 USA.**

> **QA-01 executed Switcher original writer classification (2026-10-10, merged #1235):** The actual original 2014 Snes9x Switcher terminal source trace (run **38088102870**, hash-pinned original artifact **11683670622**, recovered without replay by green run **38088688106**) records **13,709 opcode-scoped stack-page byte changes** in the bounded result window. Every observed change is push-family/opcode/SP/target compatible. At `7E:01F1`, original `JSR` instructions `82:B1F2` (6,469 changes) and `82:B1F9` (6,470) push the **exact low return-address bytes F4 and FB** with SP `01F2→01F0`; these two account for 12,939 of 13,204 recorded original `01F1` changes. Seven of the eight independently observed Switcher same-host difference offsets changed in this original-source movie window; `7E:01DD` did not. The postresult **same-host original/native restored track at 5778**, both actual result onset at host **5783**, and eight actual host-5782 WRAM residual bytes are separate evidence. [Permanent source/PC witness](../analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json); [cross-event detailed adjudication](QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md). This classifies original stack traffic, not native CPU/stack timing or read consumers. Full original/native strict guest-relative result and post-result journey acceptance remain unresolved; **USA 0/45 unchanged.**

> **QA-01 actual Switcher Race B paired witness (2026-10-10):** The original 2014 Snes9x track-3 result at source **17030** is now qualified through the narrowly bounded 34-frame track-0 result prelude (#1163). The first real original/native full Switcher diagnostic **38064406315** reproduces **MIKE 1:08.81** and identical PPU result text, correct final guest state, 28 matched sparse active samples and equivalent guest entries. Independently calibrated original entry host **1079** / Baldosa **1081** yield guest-relative terminal **+4704 / +4702**, but both actually reach their result at **absolute host frame 5783**. The strict relative parity gate correctly failed; that initial sample sequence stopped at +2400; subsequent original/native terminal probes located relative-frame menu/track contrasts but also matched course restoration at absolute host 5778 and result at host 5783 (see the newer superseding observation above). [Durable paired source witness](../analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json). Still **0/45** independently accepted full-USA event pairs. No input rebase or gameplay timing repair authorized.

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

**Terminal-result qualification for the Modern/Baldosa handoff:** the shared original/native complete-event comparator now records `result_outside_active_race_in_both_guests`: each guest's independently captured onset **and** stable snapshot must have `7E:0313 != 1`, alongside the separately checked event-specific result menu and actual PPU text. For Circuit `0xBC` it also records `circuit_zero_remaining_laps_at_onset_and_stable`: P1 `7E:0EF1 == 0` in all four original/native onset/stable captures, **in addition to** the two observed circuit lap decreases. Stunt/Race cannot inherit that Circuit-specific counter rule. A syntactically valid but zero-valued P1 race time (`0:00.00`) earns no timed-finish qualification. These checks reject false *candidates* even when a matching screen and intermediate samples could otherwise conceal active guest play or an uncredited final lap. They use genuine guest-state evidence already captured by the existing runner, do not change gameplay or controller scripts, and confer **no new 45-course release credit**. Modern must still distinguish read-only result observation from authorized record persistence and must not interpret the postresult stopwatch sentinel as elapsed time.

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

- **USA Dragster (course 01), partial:** an earlier seven-frame native
  WRAM witness observed the postframe checkpoint/lap/finish gate transition,
  without identifying the instruction-time dispatcher. **Now independently
  executed:** the historical 2014 original Snes9x movie enters Dragster
  at source frame **794** and shows genuine `0x99` Race A result at
  **2874**. A fresh original Snes9x and pinned Baldosa native guest were
  independently booted with its exact embedded original SRAM; both enter
  the stock first Crawler event at host **945**, and replay the same
  source-owned controller stream. **22/22** in-race semantic snapshots,
  original/fresh entry signature, P1 checkpoint/finish/laps and exact
  settled PPU text agree: **MIKE 0:25.08**. However the genuine result
  starts at **+2081 original / +2079 native**, a strict **two guest-frame
  native lead**, at absolute hosts **3026/3024**. This run predates Opus's
  staged RF-015 DRAM refresh correction, so it cannot establish how the
  corrected runtime behaves. No result-return, cold-process persisted
  record or complete event has been independently accepted.
  [Exact SHA-bound real witness](../analysis/data/qa01-dragster-2014-original-baldosa-first-pair-20261014.json);
  [one-shot native/Snes9x run 38665417679](https://github.com/gamesbyian/UR-Recomp/actions/runs/38665417679).
  **Still partial, 0/45 accepted.**
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
  fields. These transition/frame statements describe the older uncorrected
  guest, not the source-qualified integrated **RF-017** replay: on RF-017,
  original movie, fresh Snes9x and native all enter the following genuine Bowl
  race **267 frames after the Zoo result**, with all eleven complete 8-KiB
  original/native SRAM pairs identical. Two independent replays, including
  [the unmasked 128-KiB WRAM byte census](../analysis/data/qa01-zoo-unmasked-wram-20261015.json),
  reproduce the same genuine handoff; 39 of 48 sampled WRAM pairs still
  differ, confined to 25 low stack bytes plus two transient sound-queue
  bytes at Bowl entry. No accepted full instruction/logic trace, source
  read-liveness, shipping Windows executable or on-disk hard-kill persistence
  follows from the observed convergence. An additional real [fresh original/native
  guest record reload](QA01-ZOO-AUTHENTIC-NEXT-BOWL-ENTRY-20261015.md#executed-rf-017-cold-guest-ranked-record-reload-no-windows-durability-2026-10-15)
  preserves all 150 ranked-record values, holders and the Zoo 2510-centisecond
  best-lap/checksum on two fresh Linux research processes, but does not
  certify actual Windows host-file durability. One further genuine original/native
  Zoo [full-race sampled WRAM mesh](../analysis/data/qa01-zoo-fullrace-mesh-executed-20261015.json)
  (single-source Actions run 38830671735, 0 exclusions) now checks **66**
  same-race-relative pairs through +5120: **44/66 byte-exact complete
  128 KiB images**, 24 newly added late-course frames with **zero named-state
  disagreements**, and only eight unique WRAM difference addresses across
  the entire sample set. The novel late-race raw discrepancy is **+5040**
  `7E:0063/0069`, which converges by the next sampled +5100; this has
  *no established live-read or CPU opcode parity interpretation*, nor does
  sparse sampling certify intervening unsampled frames. This remains a paired
  **candidate**, not independent complete-event
  acceptance. The precise remaining causal uncertainty and artifact identifiers
  live in [the source-owner crosswalk](../analysis/data/zoo-original-native-sram-restore-source-owner-20261009.json).
  **Independent shipping-source identity blocker (2026-10-15, [#1686](https://github.com/gamesbyian/UR-Recomp/issues/1686)):**
  the source-qualified *research candidate* built original/native Zoo with both RF-015
  and RF-017, but the source-pinned Windows build currently stages **RF-015
  only**. Its compiled CPU timing source has not been demonstrated equivalent
  to the corrected research ELF; the known RF-015-only Linux result-relative
  Bowl offset was +265 rather than the original +267, but a Windows-specific
  failure has **not** yet been replayed. Integration/CPU owns patch staging and
  exact Windows executable binding, with independent QA-01 adjudication afterward.
  The +5040 direct-page mismatch remains unwaived. Two genuine original/native
  2014 Zoo replays ([run 38847972295](https://github.com/gamesbyian/UR-Recomp/actions/runs/38847972295),
  [run 38848262320](https://github.com/gamesbyian/UR-Recomp/actions/runs/38848262320))
  captured the thirteen adjacent +5034..+5046 full-WRAM samples on independently
  calibrated race-entry clocks, with identical native ELF and distinct original
  reference-core binary SHA-256s. The [independent SHA-bound receipt](../analysis/data/qa01-zoo-dp5040-independent-two-run-review-20261016.json)
  (merged #1690) retains both hosted ZIP/report digests and all 78 full
  128-KiB pair results: 45 byte-exact, 33 different, 109 unmasked differing
  byte occurrences. All WRAM bytes agree at +5039; sound-pointer/counter
  `7E:0063/0069` first differ at +5040 and throughout +5041..+5046, with
  `7E:0064` also differing at +5043. The **RF-018-only A/B has now been
  executed** on original/native Zoo ([run 38861174758](https://github.com/gamesbyian/UR-Recomp/actions/runs/38861174758);
  SHA-verified [negative receipt](../analysis/data/qa01-zoo-rf018-only-treatment-review-20261016.json),
  merged #1692): it narrows +5040 pointer/counter gaps from 38/39 to
  15/16 counts and aligns native scene entry at 1017, but **does not
  eliminate the +5040 raw mismatch**. Worse, the genuine native
  next-Bowl race activates at **Zoo result+265**, whereas archived
  original and fresh original activate at **+267**. Sampled native
  post-result menu differs by +16; SRAM first differs at +64 in one
  non-ranked cutscene-timer byte, and the eleven following Bowl
  samples disagree in three bytes each while all Crawler ranked
  records/holders/checksums agree. This is a strict negative for
  adopting RF-018 alone, not proof of scored-record corruption.
  CPU/APU [#1689](https://github.com/gamesbyian/UR-Recomp/issues/1689)
  now owns executed source writer/reader/SPC phase diagnosis at
  Zoo +5039..+5046 and actual Bowl/menu transition timing.
  These observations do not establish continuous-frame logic/instruction
  parity, authentic Windows executable identity, Windows disk durability, or
  a Windows-specific +265 next-Bowl entry. Source-qualified Zoo +5163 result,
  authentic next Bowl +267 and eleven exact full SRAM pairs are still
  **research candidate evidence only**, not any of 45 accepted events.
  **Still partial, 0/45 complete.**
  Reduced write provenance: `analysis/data/zoo-original-2014-live-progression.json`.
  Original terminal evidence: `analysis/generated/result-screens-probe.json`.
- **USA Bowl (course 03), partial:** the 2014 original Snes9x source
  reaches authentic scored 45-second Stunt tally `0x2F` at source frame
  **11915**, then result `0x18` at **11985**. The later independently
  booted Snes9x and pinned Baldosa guests replay the same scene-relative
  movie controller stream from the embedded source SRAM. Their **28/28
  sampled active-gameplay semantic states** and complete decoded PPU
  tally/settled-result text match, including **MIKE 764** and qualifying
  score **68**. Both hosts observe result at absolute script frame **4349**;
  scene-relative result is **+3365 original vs +3364 native** because
  fresh entry frames differ by one. This is a strong completed scored-Stunt
  **candidate**, not an admitted course. The result phase/clock and full
  instructional comparison still require independent adjudication.
  [Executed paired witness](../analysis/data/bowl-original-baldosa-scored-stunt-candidate-20261009.json)
  (CI [38021981513](https://github.com/gamesbyian/UR-Recomp/actions/runs/38021981513)).
  **Official credit: 0/45.**
- **USA Jumpover (course 20), partial:** six bounded input-only
  original/native stunt landing-reward thresholds match **on a circuit B
  course**, but no complete circuit lap/finish/result or 45-second stunt
  event is established on Jumpover. **No timed-Stunt identity has
  an accepted fresh original/native complete-event pair**, including Bowl.

**Pending source-qualified Switcher Race B census reconciliation (2026-10-14):**
The archived original USA Snes9x movie genuinely enters Switcher at movie
frame **12327** and reaches `0x99` result at **17030**. Fresh original/native
guests replay the preserved SRAM and controller scene with **28/28** matching
active semantic checkpoints and the identical real **MIKE 1:08.81** result
presented on both hosts at absolute frame **5783**. However, the independently
observed race entries differ (original host 1079/native 1081), so the result
is **+4704 original versus +4702 native** in guest-relative frames. The
34-frame course-ID-zero terminal prelude, instruction-time CPU/NMI parity,
menu continuation, and persistence remain unresolved. This is a useful
*completed-result investigative candidate*, and demonstrably **not** a strict
accepted event. [Source-executed paired witness](../analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json);
[source-qualified three-event timing matrix](../analysis/data/qa01-three-event-original-baldosa-timing-matrix-20261010.json).

At this point the independently owned `docs/RELEASE-QUALITY-LEDGER.json`
still binds QA-01 to **0 accepted, 4 partial, 41 unverified**, so Switcher
continues to be officially **unverified** in
`analysis/data/course-event-runtime-evidence.json`. A proposed direct
promotion to `partial` was rejected by ten independent release-ledger
unit assertions in PR #1589's initial test run
[38640225829](https://github.com/gamesbyian/UR-Recomp/actions/runs/38640225829);
the research witness and the source/census discrepancy are preserved here
instead. **Handoff to independent release QA owner:** assess whether Switcher
qualifies as `partial` under the existing source evidence policy and, if so,
reconcile the ledger, source register, derived 135-case census and tests as
one coherent reviewed change. No release count, comparator, candidate gate,
original guest, CPU/APU implementation or controller input has been changed
in this gameplay lane.

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
