# External reverse-engineering practice archaeology

Date: 2026-09-29  
Status: active project guidance  
Scope: decompilation, disassembly, static recompilation, ROM reverse engineering, emulator-assisted archaeology, and agent-assisted workflows relevant to UR-Recomp.

## Why this exists

UR-Recomp already has strong project-local practice: deterministic controller fixtures, multiple execution engines, first-divergence reduction, a four-ROM corpus, provenance discipline, symbol fan-out, an islanded toolchain, and explicit separation between durable recovered knowledge and disposable generated code.

This note records techniques and failure modes found in outside reverse-engineering projects and practitioner writeups, including native-language Japanese and Portuguese material. The goal is not to import another project's ceremony. It is to steal scar tissue where it improves work ordering, evidence quality, or agent efficiency.

External claims remain leads until reproduced locally where practical.

## Sources reviewed

### SNES / 65816 specific

- Super Famicom Development Wiki, **SNES逆汗解析･改造入門** (Japanese): https://wiki.superfamicom.org/snes-%E9%80%86%E6%B1%97%E8%A7%A3%E6%9E%90-%E6%94%B9%E9%80%A0%E5%85%A5%E9%96%80
- 夢想メモリ, **レトロゲームのROM解析・逆アセンブルの方法メモ** (Japanese): https://musou.hatenablog.jp/entry/2022/07/31/232508
- ドラクエ解析系資料, **逆アセンブラー** (Japanese): https://showa-yojyo.github.io/dqbook/tools_disasm.html
- nesdev forum, **Best method of doing a full disassembly of a SNES ROM?**: https://forums.nesdev.org/viewtopic.php?t=15161
- DiztinGUIsh, SNES disassembler rationale: https://github.com/furious/diztinguish
- bsnes-plus debugger documentation: https://bsnes.revenant1.net/documentation.html
- Jeff Tranter, **65816 Disassembly - 8 and 16 bit modes**: https://jefftranter.blogspot.com/2012/07/65816-disassembly-8-and-16-bit-modes.html
- DKC SNES disassembly: https://github.com/DKC-Recomp/DKC-disassembly
- Final Fantasy VI disassembly: https://github.com/everything8215/ff6

### Matching-decomp / recomp practice

- ZeldaRET Majora's Mask contributing guide: https://github.com/zeldaret/mm/blob/main/docs/CONTRIBUTING.md
- ZeldaRET Wind Waker decompiling guide: https://github.com/zeldaret/tww/blob/main/docs/decompiling.md
- ZeldaRET OoT/VC diff and decomp tooling examples: https://github.com/zeldaret/oot-vc
- Decomp Academy: https://decomp-academy.dev/
- SFRush2049 decomp lessons learned: https://github.com/cabi24/SFRush2049-decomp/blob/master/reference/lessons-learned.md
- N64: Recompiled project family: https://github.com/N64Recomp/N64Recomp
- Ars Technica interview on N64 static recompilation workflow: https://arstechnica.com/gaming/2024/05/how-to-port-any-n64-game-to-the-pc-in-record-time/

### Behavior-first / emulator-assisted porting

- Nivando Soares, **Porting Test Drive II from SNES to PC: from disassembly dump to port workbench**: https://dev.to/nivandosoares/porting-test-drive-ii-from-snes-to-pc-from-disassembly-dump-to-port-workbench-1l73
- Follow-up on the first native slice: https://dev.to/nivandosoares/porting-test-drive-ii-from-snes-to-pc-part-2-the-first-native-intro-slice-3096
- Matt Greer, **ROM Hacking Learnings**: https://www.mattgreer.dev/blog/rom-hacking-learnings/
- Matt Greer, **MAME Lua for Better Retro Dev** / debugger notes: https://www.mattgreer.dev/blog/Debugging/
- FCEUX Code/Data Logger documentation, useful as a general explanation of dynamic code/data evidence: https://fceux.com/web/help/CodeDataLogger.html
- mesen-for-ai: https://github.com/paulomanrique/mesen-for-ai

### Portuguese / multilingual material

- Bruno Macabeus, **Engenharia Reversa num jogo de Gameboy Advance** (Portuguese): https://macabeus.medium.com/pt-br-engenharia-reversa-num-jogo-de-gameboy-advance-introdu%C3%A7%C3%A3o-21ebffe2f794
- Serroot, **Engenharia reversa de jogos de GBA** (Portuguese): https://serroot.dev/pt/labs/workshops/gba-firered/00-comece-aqui/
- N64 Perfect Dark Research Lab, GoldenEye decompilation overview (Japanese): https://pdlab.knowhow.jp/hacking/ge-decompilation/

### Agent-assisted reverse engineering

- Chris Lewis, **Using Coding Agents to Decompile Nintendo 64 Games**: https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/
- Macabeus, **Starting a Decompilation Project from Zero: Claude Code and 51% of a 2001 GBA Game**: https://gambiconf.substack.com/p/starting-a-decompilation-project
- Free Wortley, **How agent swarms decompile games byte-for-byte**: https://freeqaz.com/blog/how-agent-swarms-decompile-games
- Free Wortley, **The Milo engine decompilation saga**: https://freeqaz.com/blog/the-milo-engine-saga

The Free Wortley posts explicitly describe themselves as AI-drafted and not line-by-line fact checked. They are useful as hypothesis generators, not authority.

## Findings that matter to UR-Recomp

### 1. Make the original measurable before trying to understand all of it

The strongest directly comparable SNES example is the Test Drive II port work. It moved from a raw bank disassembly to deterministic emulator probes first: frames, input logs, VRAM, CGRAM, OAM, PPU state, callback selectors and traces. That changed reverse engineering from manual observation into artifact-producing experiments.

**UR-Recomp status:** already strong. Our deterministic fixture grammar, full-WRAM checkpoints, frame captures, emulator cross-checks and Mesen path are the same general strategy.

**Sharpening:** whenever a new subsystem becomes an active reverse-engineering target, define its minimal evidence packet before deep static archaeology begins. For rendering this may be framebuffer + PPU + OAM + relevant VRAM/CGRAM. For gameplay it may be input + selected WRAM + writers + first-divergence CPU context. Avoid bespoke one-off captures when an existing fixture can be extended.

### 2. Dynamic evidence should constrain static disassembly, especially on 65816

SNES practitioners repeatedly warn about two related traps:

1. code and data are intermixed;
2. immediate instruction widths depend on the 65C816 M/X state, so a wrong assumption can desynchronize the remainder of a linear disassembly.

Japanese SNES material recommends comparing interpretations where accumulator width is ambiguous; DiztinGUIsh explicitly treats processor-state context as part of disassembly; nesdev practitioners recommend debugger-guided correction rather than trusting whole-ROM linear output.

**UR-Recomp implication:** Mesen CDL should not be treated merely as a nice coverage visualization. It should become one input to a **confidence-bearing executable map**. Static boundaries discovered by snes2asm/da65/Ghidra should carry evidence such as executed-as-code, read-as-data, reached from known control flow, or still ambiguous.

For 65816 specifically, when a region matters, record enough entry-state information to justify M/X assumptions. Do not allow a pretty static listing to silently outrank runtime processor state.

### 3. Coverage is evidence of observation, not proof of absence

Code/data logging is powerful, but emulator documentation makes its limitation plain: bytes not observed during the exercised routes remain unknown. A CDL map says what happened in the corpus, not what can happen in the game.

**UR-Recomp implication:** retain per-fixture provenance for coverage and union maps. Any region classified only because it has never executed must remain unknown, not data. Coverage growth across deliberately varied fixtures is more meaningful than a single "percentage covered" number.

This matters particularly for menus, rare stunt branches, two-player/Vs., progression screens, error/erase flows, and region-specific behavior.

### 4. Separate "matching", "behaviorally equivalent", "understood", and "documented"

Mature decomp projects distinguish code that byte-matches, code that behaves equivalently but does not match, and code that is still non-equivalent. ZeldaRET also treats documentation and naming as a separate step after matching.

UR-Recomp is a static-recomp project rather than a full matching-C decomp, but the epistemic distinction transfers directly.

Recommended vocabulary for recovered knowledge:

- **observed**: behavior/state seen in one or more deterministic runs;
- **structurally supported**: static control/data evidence supports the interpretation;
- **behaviorally verified**: an independently implemented/parser/hook interpretation reproduces the relevant original behavior on a stated corpus;
- **byte/trace verified**: exact bytes, writes, or execution sequence match where that level is meaningful;
- **named hypothesis**: useful semantic name, not yet sufficiently verified.

Do not let a confident symbol name erase its evidence class.

### 5. Work smallest-first around natural boundaries

ZeldaRET deliberately recommends self-contained actor/object translation units for early work because they are bounded and independently reviewable. Japanese ROM-analysis notes similarly recommend narrowing the region and producing per-subroutine summaries rather than reading indefinitely.

**UR-Recomp implication:** preserve the existing seam-first posture. For new unknowns, prefer the smallest discriminator that can answer the current question:
- one caller path instead of whole-bank decompilation;
- one writer instead of global RAM archaeology;
- one fixture window instead of whole-game tracing;
- one asset family instead of bulk graphics decoding;
- one dispatch table instead of naming every routine nearby.

Only widen scope when the local question proves coupled.

### 6. Reverse-engineer only as deeply as the product requires

Static recompilation projects repeatedly make the same economic point: readable reconstruction is valuable where modifications, hooks or understanding are required; generated translated code can carry the rest.

That is particularly applicable here. The port does not need a human-readable decompilation of every instruction before shipping.

**UR-Recomp implication:** retain the current architecture rule that generated C is disposable. Use deep decompilation selectively around:
- physics/state that must be validated or extended;
- camera/culling for widescreen;
- course loading/representation;
- sprite/OAM construction and asset selection;
- frontend state that must be modernized without semantic breakage;
- save/progression;
- audio/presentation hooks.

Do not create "100% decompiled" as a project milestone unless some later requirement genuinely needs it.

### 7. Treat extracted assets and decoded structures as reproducible build products

Mature projects use explicit extraction stages and re-run them as part of builds or verification. Behavior-first ports similarly turn ROM content into typed intermediate artifacts instead of manually copying discoveries.

**UR-Recomp implication:** every promoted decoder should eventually have:
- exact source ROM/hash contract;
- machine-readable manifest;
- deterministic extraction;
- semantic intermediate representation where useful;
- round-trip or reconstruction validation where possible;
- provenance back to ROM offsets/streams.

The course pipeline is already moving this way. Graphics and audio should follow the same pattern.

### 8. Multi-version support is most valuable early

Several decomp projects recommend multi-version handling from the beginning because later retrofitting turns duplicated differences into architectural debt.

**UR-Recomp status:** unusually good. The four-ROM differential corpus is already central.

**Sharpening:** when symbols/structures are promoted, record whether they are:
- invariant across all four builds;
- retail-only invariant;
- region-shifted but structurally equivalent;
- prototype-specific;
- unknown outside the canonical USA build.

Prefer signatures/relationships over raw addresses when that lowers future alignment cost.

### 9. The best agent workflow is oracle-heavy and hallucination-hostile

Recent agent-assisted decomp writeups are consistent on one important point: agents become useful when every claim can be tested cheaply and become dangerous when screenshots, game semantics, or progress are interpreted without hard checks. Macabeus gives concrete examples of agents confidently misreading ordinary gameplay events until deterministic scripts and memory observations constrained them.

**UR-Recomp implication:** our current fixture/oracle posture is correct. Add one explicit operating rule:

> An agent may propose semantic meaning from static or visual evidence, but promotion to project knowledge requires a local discriminator whenever one is reasonably available.

High-value agent tasks:
- generate candidate names from xrefs and behavior;
- cluster similar routines/structures;
- propose bounded experiments;
- translate one proven observation into tests/docs/adapters;
- search for cross-version correspondences;
- mine traces for first-difference neighborhoods.

Low-value/risky agent tasks:
- free-form whole-ROM "understanding";
- semantic naming based only on decompiler pseudocode;
- declaring dead/unreachable code from one coverage corpus;
- inferring gameplay meaning from screenshots without state probes.

### 10. Preserve exact failure artifacts, not just successful end states

The strongest projects use objective diffs or traces, making the first mismatch the unit of progress. This is more efficient than diagnosing from a final broken screen.

**UR-Recomp status:** already implemented in important places.

**Sharpening:** standardize a small "failure capsule" concept for expensive investigations:
- fixture + exact tool revisions;
- earliest failing checkpoint/frame;
- compact state diff;
- bounded trace around first divergence;
- relevant coverage/symbol context;
- one-line current hypothesis.

This should be generated only when useful, not for every green run.

### 11. Reassembly/reconstruction is a powerful checksum on understanding

SNES disassembly practice consistently recommends rebuilding and binary-comparing the result. Matching-decomp communities take this to its logical extreme.

UR-Recomp does not require a complete matching source reconstruction, but local round trips are still extremely valuable.

Use exact or bounded reconstruction where practical for:
- decoded RNC payloads;
- extracted graphics/palettes;
- tables/pointer structures;
- any patched or relocated bounded ASM region;
- save/SRAM structures.

If the project can decode something but cannot regenerate the original bytes for a controlled unchanged case, the model may still be incomplete.

### 12. Debugger automation is worth more than prettier static output

Older ROM-hacking posts and current Mesen tooling converge here: watchpoints, writer breakpoints, traces, scripted input, save states and automated memory inspection usually answer targeted questions faster than manually reading broad disassembly.

**UR-Recomp implication:** prioritize finishing the real Mesen execution/CDL path before adding another static workbench. Ghidra remains valuable for xrefs and structure, but runtime queries should usually lead when the question is "what code causes this observed state?"

## Concrete changes to project practice

### P0 / immediate

1. Finish the canonical Mesen first-race execution path and CDL adapter already queued.
2. Extend the CDL design so outputs preserve:
   - per-fixture provenance;
   - code/data/unknown distinctions;
   - union vs individual coverage;
   - any Mesen flag semantics that do not map exactly to other tools.
3. When CDL begins feeding static tooling, prohibit "unseen == data" classification.
4. Add M/X-state-aware notes to any static 65816 region promoted to canonical understanding where immediate-width ambiguity is possible.
5. Use the first meaningful graphics or course decoder as a pilot for deterministic extract -> semantic artifact -> unchanged reconstruction validation.

### Near-term

6. Add evidence classes to promoted symbols or the generated symbol metadata rather than treating a name alone as certainty.
7. Add a compact optional failure-capsule generator around the existing first-divergence workflows if repeated investigations show manual bundling is recurring work.
8. Make coverage reports corpus-aware: show which fixtures contributed to a claimed code/data observation.
9. For every major new reverse-engineering subsystem, define its standard evidence packet before broad analysis.
10. Preserve cross-ROM structural identity alongside addresses for newly promoted functions/tables.

### Explicitly do not do

- Do not launch a full matching-C decompilation program merely because mature communities use one.
- Do not attempt whole-ROM semantic naming before the product needs it.
- Do not let CDL become an oracle for unreachable code.
- Do not add another heavyweight GUI analyzer unless it answers a question the current toolchain cannot answer cheaply.
- Do not require elaborate evidence packets for trivial local facts; use the smallest artifact that makes the claim reproducible.

## Search vocabulary for future passes

Use native-language terms, not only English translations.

Japanese:
- スーパーファミコン ROM 解析
- SNES 逆アセンブル
- 逆汗解析
- ROM 改造 解析
- ゲーム デコンパイル
- リコンパイル
- エミュレータ デバッガ
- コード データ ロガー

Portuguese:
- engenharia reversa ROM
- descompilação de jogos
- desmontagem ROM
- depuração emulador
- engenharia reversa Super Nintendo

Spanish:
- ingeniería inversa ROM
- desensamblado Super Nintendo
- descompilación videojuegos
- depuración emulador ROM

French:
- rétro-ingénierie ROM
- désassemblage Super Nintendo
- décompilation jeu vidéo
- débogueur émulateur

German:
- ROM Reverse Engineering
- SNES Disassemblierung
- Spiele Dekompilierung
- Emulator Debugger ROM

Chinese:
- 游戏 ROM 逆向工程
- 超级任天堂 反汇编
- 游戏 反编译
- 模拟器 调试 ROM

Korean:
- 게임 ROM 리버스 엔지니어링
- SNES 롬 해킹 역공학
- 디스어셈블 에뮬레이터 디버거

Russian:
- реверс ROM игр
- декомпиляция игр
- дизассемблирование SNES
- отладчик эмулятора ROM

## Revisit trigger

Repeat a small external-practice archaeology pass when one of these happens:

- a new major reverse-engineering phase begins;
- the team is repeatedly doing a manual task that feels toolable;
- an investigation stalls because evidence from static and dynamic tools disagree;
- a new recomp/decomp tool family becomes materially more capable;
- a failure pattern recurs across agents.

The pass should answer a concrete project question. Avoid open-ended "read more reverse-engineering blogs" work.
