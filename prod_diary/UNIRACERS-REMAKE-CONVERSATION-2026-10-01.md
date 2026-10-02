# Uniracers remake and AI-assisted SNES excavation conversation transcript

Captured: 2026-10-01
Updated: 2026-10-01

Source: ChatGPT conversation with Ian Wallace. This document preserves the useful project reasoning and repo-management turns from the conversation in transcript-style form for future agents. It is not an implementation plan by itself, and it does not supersede `docs/PROJECT-PLAN.md`, `docs/WORK-QUEUE.md`, `docs/SEMANTIC-SUFFICIENCY.md`, or `docs/AI-ASSISTED-REVERSE-ENGINEERING.md`.

Treat external factual claims below as leads unless already corroborated by repository evidence. URLs are included where the chat referenced public sources, but repository-local deterministic evidence remains the authority.

## Conversation arc

The conversation began as a casual evaluation of whether Uniracers would be a good Godot remake candidate and became a broader project thesis:

> Can a determined non-specialist, using 2026 AI coding agents plus modern emulator/reverse-engineering tooling, build a rigorous behavioral excavation pipeline for an under-documented SNES game, then use the recovered facts to make an extremely faithful Uniracers recreation and eventual modern expansion?

The recurring distinction was between a casual remake and a forensic reconstruction. The desired project is not just "learn Godot by cloning a game." It is closer to:

- tear the original game apart with emulator traces, RAM maps, disassembly, data extraction and controlled experiments;
- let AI coders build and operate repo-controlled instruments;
- inventory the game’s behavior and assets with evidence provenance;
- implement a faithful Godot recreation against trace-derived tests;
- then expand into widescreen, 4K, level editing, submission/review tooling, and community infrastructure.

The later repository-management turns moved this conversation capture into the root-level `prod_diary/` directory and then updated it directly on `main` under the same filename convention:

`prod_diary/UNIRACERS-REMAKE-CONVERSATION-2026-10-01.md`

## Transcript-style notes

### 1. Initial question: is Uniracers a good game to remake?

Ian asked about YouTube series where people remake classic games in Godot as a way to teach themselves game development, and asked for reasons Uniracers would be a good or bad choice.

The answer framed Uniracers as a deceptively compact but technically interesting candidate. Its visible content burden is low: one riderless unicycle, short side-view tracks, stunt/race modes, limited sprite families and UI. Its feel burden is high: acceleration, jumping, airborne rotation, landing validation, boosts, camera, track geometry and CPU racers would all need careful tuning.

Reasons it is a good candidate:

- compact design with many teachable systems;
- playable prototype can appear early: a dot/wheel following a curve, jumping, rotating, landing and getting a speed boost;
- art scope is low compared with RPGs/platformers;
- mechanics are crisp enough to support instrumentation and tests;
- Godot can support a custom kinematic movement model rather than relying on generic rigid-body physics.

Reasons it is a risky candidate:

- most of the charm is in feel, and feel is hard to specify;
- track geometry may become a serious spline/collision/editor problem;
- stunt validation and boost economy are subtle;
- CPU racer behavior may be annoying to reproduce faithfully;
- content can feel thin unless the core movement is excellent or there is an editor/challenge ecosystem.

The conclusion was that Uniracers is a good choice if the goal is a polished, systems-driven arcade reconstruction, but a bad choice if the expectation is an easy first remake.

### 2. Complexity is not a turnoff

Ian challenged the suggestion that the project quietly taking on complex subprojects would be a deterrent.

The answer corrected the framing: complexity is not the problem. Ian likely enjoys projects that become weird engineering labyrinths if they have structure, feedback and falsifiable progress. The real risk is "feel complexity without obvious correctness criteria."

For Pathfinder-style work, there are clear oracles: solve the level, pass the harness, improve runtime, satisfy constraints. For Uniracers, some of the hardest questions are tactile: does this acceleration, jump, landing, camera or boost behavior feel right?

The proposed mitigation was to turn feel into instrumentation:

- telemetry graphs;
- input traces;
- speed-over-distance plots;
- debug overlays for tangent/normal/grounded state;
- landing-angle diagnostics;
- trick-state timelines;
- ghost comparisons;
- original-vs-remake diffs.

A later term for this was the "feel lab." The danger is not many complicated subprojects. The danger is complexity becoming fog instead of machinery.

### 3. Would reverse-engineered source or data help AI coders?

Ian asked whether an LLM coder could make excellent use of reverse-engineered source code, if available, for behavior matching or map building.

The answer separated several forms of evidence:

- raw disassembly: useful but feral;
- commented disassembly/decompilation: much more useful;
- decoded data formats: especially valuable for tracks and maps;
- emulator traces and RAM maps: excellent behavioral oracles.

The assistant emphasized that the most valuable artifact might be decoded track data: segment definitions, curves, checkpoints, stunt zones, CPU routes, spawn positions, palettes and level metadata. An LLM coder could build parsers and converters into JSON, Godot resources, `Curve2D`s, SVG visualizers or editor formats.

For behavior, reverse-engineered material can identify invariants:

- speed and acceleration changes;
- boost values and decay;
- landing tolerances;
- trick eligibility;
- track attachment rules;
- camera offsets;
- CPU route rules.

Important caution: old implementation details may be hardware workarounds rather than behavior that should be reproduced directly. The remake should preserve spec-relevant behavior, translate or discard hardware barnacles, extract data faithfully, and avoid copying protected art/audio/branding in public artifacts.

At the time of the chat, no obvious mature public Uniracers/Unirally decompilation or full reverse-engineering project had been found.

### 4. What are emulator traces?

Ian asked whether an emulator can be configured to automatically "play" a game in order to extract information about how it works.

The answer: yes. An emulator can be used as a deterministic lab rig, not merely as a way to play the game.

Kinds of traces discussed:

- CPU instruction trace: disassembled 65c816 instructions, registers, branches, reads/writes;
- memory trace: reads/writes to RAM or selected values logged once per frame;
- frame/input trace: controller input plus derived state each frame;
- graphics trace: VRAM, tilemaps, palettes, sprites/OAM, backgrounds/layers.

Potential tooling leads:

- BizHawk for automation, TAS-style input, savestates and Lua scripting: https://github.com/TASEmulators/BizHawk and https://tasvideos.org/Bizhawk/LuaFunctions
- Mesen/Mesen2 for debugging, PPU viewing, trace logging and Lua-style inspection: https://www.mesen.ca/docs/debugging.html
- bsnes-plus for SNES debugger workflows and instruction logging: https://github.com/devinacker/bsnes-plus and https://bsnes.revenant1.net/documentation.html

Example experimental loop:

1. start from a savestate at the beginning of a track;
2. run scripted inputs: hold accelerate, jump on frame N, rotate for M frames, release, land;
3. log candidate RAM values every frame;
4. discover addresses for position, velocity, rotation, grounded state, trick state, boost, camera and score;
5. set write breakpoints on those addresses;
6. identify the routines responsible for motion, tricks, boost and landing;
7. produce behavior probes that become remake specs.

The important caveat was that automation produces observations, not automatic understanding. Hypotheses still need carefully designed experiments to isolate variables.

### 5. IP, YouTube educational remakes and the need for actual Uniracers

Ian argued that the game needs love from someone who does not care about Pixar or Rockstar, and noted that YouTubers often get away with educational remakes of prominent IP.

The answer distinguished practical risk from legal correctness. Educational/noncommercial framing is not a magic shield. Copyright/fair-use/fair-dealing questions depend on context, amount used, transformation, market harm and jurisdiction. But practical enforcement often depends on notice, substitution risk, brand confusion and whether a downloadable replacement is distributed.

A general risk ladder was described:

- safest: private exact remake, no public build, no asset sharing, no ROM sharing;
- relatively sane: devlog showing systems, telemetry, code and short commentary clips;
- spicy: public repo branded as an Uniracers remake;
- highly spicy: downloadable clone with copied tracks, sprites, UI, music or extracted ROM data;
- dragon’s mouth: distributing an Uniracers replacement package with original maps/assets.

At first, the suggestion was to make a spiritual successor with different rolling objects. Ian rejected that: the little unicycles are the whole point.

The answer accepted that for the creative goal, it has to be Uniracers. The unicycles are not decorative. They are the emotional payload. The project’s public/private split was then framed as:

- privately: make Uniracers, with the cute riderless unicycles;
- publicly: decide how much heat to stand near, and keep artifacts disciplined.

A possible public posture: an engineering autopsy/devlog about rebuilding the movement model of a neglected SNES stunt racer, while any exact playable clone remains private unless transformed later.

### 6. Project thesis: forensic reconstruction first, modernization second

Ian described the appealing project as spending a year remaking an insanely faithful recreation by tearing apart the original, letting AI coders inventory its guts, getting hung up on correctness, then making it widescreen/4K and adding a level editor plus submission/review tools.

The answer reframed the project as:

> Spend a year building a forensic reconstruction pipeline for a beloved dead arcade organism, then use Godot to give it a modern afterlife.

Three layers were proposed:

1. Forensics layer: emulator traces, RAM maps, savestates, track decoding, sprite/tile inspection, behavior tables, speed curves, trick validation, CPU racer behavior and hardware quirks.
2. Replica layer: Godot faithfully recreates the original engine/behavior. Same inputs from same states should produce comparable traces.
3. Expansion layer: widescreen, 4K, editor, ghosts, community challenge packs, submissions, review queues, validation and modern affordances.

Important ordering principle:

> Build the faithful fossil first. Then mutate it.

Widescreen was called out as a nontrivial gameplay change because it alters information available to the player. Possible modes:

- classic viewport mode: original framing/information limits;
- widescreen faithful mode: original camera behavior with expanded presentation;
- modern mode: reauthored camera with lookahead/smoothing;
- 4K asset mode: new high-res assets preserving timing/silhouette.

The editor was framed as proof that the grammar was recovered. If new tracks can feel native, the project recovered the system, not just the shipped content.

### 7. Super ZSNES and enhancement-profile relevance

Ian asked about the "Super ZSNES" project and whether it is known to work on Uniracers.

The chat found no public evidence that Super ZSNES currently has a Uniracers/Unirally enhancement profile. The official Super ZSNES site listed supported enhancement profiles for other titles and not Uniracers: https://www.zsnes.com/

Relevant takeaways:

- Super ZSNES’s architecture is relevant as a vision document: GPU-rendered SNES graphics plus per-game enhancement layers.
- Uniracers is historically an emulator edge case involving mid-screen/OAM behavior.
- Old ZSNES history noted fixes for mid-screen OAM updating so Uniracers 2-player mode would work: https://zsnes-docs.sourceforge.net/html/history.htm
- bsnes/Near/byuu discussion described Uniracers writing to OAM during HBlank and relying on specific hardware behavior: https://www.emu-land.net/news/bsnes_v066 and nesdev threads.

Conclusion: Super ZSNES is not currently a shortcut to an enhanced Uniracers, but it is a useful reference model for enhanced emulation. For this project, BizHawk/Mesen/bsnes-plus/Ghidra-style workflows remain more useful for excavation. Super ZSNES-style enhancement might become a later comparative architecture.

### 8. Active community and who may know the most

Ian asked whether the game has an active community, whether there are remake projects or ROM hacks, and who online has the most technical/historical information.

The chat found a small living fan/speedrun ecosystem, but not an obvious active technical scene like major Mario/Sonic/Metroid ROM-hacking communities.

Current/community leads:

- Speedrun.com Uniracers page: https://www.speedrun.com/uniracers
- Names surfaced: mrcab55, Segastar, FlyHec and other recent runners/moderators.
- Speedrun pages may be the closest active player/routing community.

Historical/community residue:

- Old Uniracers Player’s Page / Nathan Cromwell references via Speedrunwiki archive: https://archive.speedrunwiki.com/w/index.php?title=Uniracers

ROM hack lead:

- `Uniracers Uncensored` by `_Q_`, a small forbidden-name-list unlocker rather than a technical remake/editor/physics hack: https://romhackplaza.org/romhacks/uniracers-uncensored-snes/ and https://www.romhacking.net/games/3313/

Spiritual-successor lead:

- RingRaceR on Steam, explicitly pitched as a spiritual successor but not a remake or preservation project: https://store.steampowered.com/app/1626100/RingRaceR/

Historical/original-development leads:

- Nintendo Life, "The Making of Unirally": https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally
- Original DMA people mentioned in that article and/or credits: Andrew Innes, Robbie Graham, Mike Dailly, Martin Good, Steve Hammond, Colin Anderson.

Likely expertise split:

- Original developers: intent, history, maybe implementation memories or surviving notes;
- speedrunners: feel, routes, timing behavior, exploit surfaces, accepted emulator practices;
- emulator/SNESdev people: hardware-specific behavior, especially OAM/PPU weirdness;
- ROM-hack sites: minimal current evidence, but possible leads;
- spiritual-successor developers: proof that the idea still has design oxygen, but not preservation evidence.

The chat’s conclusion: a serious forensic Uniracers remake probably would not be joining an existing technical project. It would be creating the missing technical project.

### 9. From scratch: how deeply can the game be dissected?

Ian described having incomplete general compilation knowledge and no NES/SNES-specific knowledge, then asked how deeply Uniracers could be dissected with 2026 tools and AI coders, and what a perfect functional remake would need that could not be obtained.

The answer first corrected NES to SNES. Uniracers is SNES, which is materially more complex than NES.

Core distinction:

- Perfect functional remake: same observable behavior for gameplay purposes, given same inputs/states.
- Perfect source-level reconstruction: original source files, labels, comments, build scripts, editor tools, source assets and human intent.

The latter is not recoverable from the cartridge alone. The ROM is a fossil, not the animal’s diary.

What can be recovered deeply:

- observable gameplay behavior through controlled emulator experiments;
- RAM map for player position, velocity, grounded state, rotation, tricks, boost, camera, score, CPU state, menu state;
- control flow and routines that write important RAM addresses;
- large parts of track data, if decoded through load routines, tables and memory materialization;
- shipped visual assets: sprites, palettes, tilemaps, animation frames, OAM behavior, layer composition;
- audio playback behavior, sound triggers and shipped samples/music data;
- hardware-specific quirks, including OAM/HBlank behavior.

What likely cannot be obtained from the ROM alone:

- original source code;
- original function/variable names, comments and source file boundaries;
- original 3D/unicycle source assets, render scenes, lighting setup and source animation files;
- original track editor/development tools;
- human intent behind edge cases;
- formal proof of equivalence for every possible state in an independent Godot rewrite;
- hardware truth in every edge case without real hardware validation.

Useful tooling leads mentioned:

- SNESdev wiki for CPU/PPU/MMIO/background/sprite/register basics: https://snes.nesdev.org/wiki/SNESdev_Wiki and https://snes.nesdev.org/wiki/PPU_registers
- Mesen debugger docs: https://www.mesen.ca/docs/debugging.html
- BizHawk Lua automation docs: https://tasvideos.org/Bizhawk/LuaFunctions
- DiztinGUIsh SNES disassembler: https://github.com/IsoFrieze/DiztinGUIsh
- Ghidra SNES loader/extensions: https://github.com/joshleaves/ghidra-snes

The practical target should be behavioral reconstruction, not original-source recovery. The only truly perfect implementation is the original ROM running in an emulator. A Godot remake can approach practical equivalence with trace-driven tests, cross-emulator/hardware checks and speedrunner validation.

### 10. How many tools can be repo-integrated for AI coders?

Ian asked how many of the tools could be integrated into a GitHub repo or coder environment so AI coders can use them directly.

The answer split tools into three categories:

1. Fully or mostly automatable inside the repo.
2. Useful but GUI-shaped, better as interactive microscopes with exported artifacts.
3. External/source-material workflows better represented by notes and evidence ledgers.

Highly repo-friendly:

- BizHawk automation: command-line launch, Lua scripts, savestates, scripted input, frame logs, RAM-domain access, CSV/JSON traces.
- Ghidra headless analyzer: scripts for import, labeling, symbol export, call graph generation, RAM write searches, report generation.
- Godot command-line/headless workflows: tests, exports, trace replay and original-vs-remake comparisons.

Useful but GUI-shaped:

- Mesen/Mesen2 debugger, PPU viewer, event viewer, memory tools, Lua window and trace logger.
- bsnes-plus debugger, memory editor, VRAM/sprite/tilemap viewers and instruction logging.
- DiztinGUIsh disassembly projects, which are valuable but require manual guidance and judgment.

Suggested repo structure:

```text
/uniracers-lab
  /roms
    .gitignore
    README.md              # expected local ROM hash only

  /tools
    install_bizhawk.ps1
    install_bizhawk.sh
    install_ghidra.sh
    tool_manifest.json
    verify_environment.py

  /experiments
    /bizhawk
      flat_accel.lua
      jump_arc.lua
      trick_landing.lua
      boost_decay.lua
      cpu_racer_probe.lua

  /savestates
    .gitignore
    README.md

  /traces
    /raw
      .gitignore
    /processed
      flat_accel.csv
      jump_arc.csv
      boost_decay.csv

  /analysis
    parse_bizhawk_logs.py
    find_ram_candidates.py
    compare_trace_runs.py
    plot_speed_curve.py
    infer_fixed_point.py

  /research
    ram_map.yml
    behavior_claims.yml
    evidence_ledger.md
    open_questions.md
    glossary.md

  /ghidra
    /scripts
      import_rom.py
      export_symbols.py
      find_writes_to_ram.py
      label_known_routines.py
    /exports
      symbols.csv
      callgraph.json
      ram_writers.json

  /disassembly
    /diztinguish
      project_files_here
    /asm_exports
      uniracers.asm

  /extractors
    extract_tiles.py
    extract_palettes.py
    extract_track_candidates.py
    decode_track_format.py

  /godot
    project.godot
    /src
    /tests
    /trace_replay

  /comparisons
    original_vs_godot.py
    tolerances.yml
    reports

  Makefile
  README.md
```

The suggested magic file was `behavior_claims.yml`:

```yaml
- id: BOOST_DECAY_001
  claim: "Boost timer decreases by 1 per frame while active."
  status: confirmed
  evidence:
    - traces/processed/boost_decay_2026-07-06.csv
    - experiments/bizhawk/boost_decay.lua
  rom_hash: "..."
  godot_test: "res://tests/test_boost_decay.gd"
```

Example agent-facing loop:

```text
make verify-rom
make run-experiment EXP=flat_accel
make analyze EXP=flat_accel
make ghidra-report RAM=7E1234
make godot-test TEST=flat_accel
make compare EXP=flat_accel
```

The practical estimate was that 70-85% of day-to-day work could become repo-driven once the harness exists. The first month would likely build the lab: ROM verification, BizHawk scripts, trace formats, RAM-search helpers, Godot trace replay, evidence ledger and basic Ghidra import/export.

Things not fully repo-integrable:

- ROM ownership and copyrighted assets/data;
- GUI-only sessions unless special remote-GUI harnesses exist;
- interpretive judgment;
- real hardware capture;
- human interviews and memory.

### 11. Broader thesis: Uniracers plus AI-assisted ROM excavation

Ian observed that this could produce data about Uniracers in particular, and also about using AI coders to excavate SNES ROMs.

The answer agreed and reframed the broader research question:

> Can a non-specialist, using 2026 AI coding agents plus modern emulator tooling, build a rigorous reverse-engineering pipeline for an under-documented SNES game?

Potential outputs:

- best public technical record of Uniracers;
- RAM maps;
- behavior tables;
- track-format notes;
- animation extraction;
- stunt/boost logic;
- CPU racer behavior;
- emulator/hardware quirks;
- collision and camera rules;
- track editor/viewer;
- reusable SNES excavation template;
- public devlog or technical atlas;
- methodology report on where AI coders helped and where they hallucinated.

The spine of the project should be behavioral excavation. Everything else attaches to that:

- the remake validates the excavation;
- the editor proves the grammar was recovered;
- the devlog narrates the excavation;
- AI methodology accelerates and audits the excavation;
- 4K/widescreen comes after the original behavior is understood.

Suggested first serious milestone:

> Produce a reproducible trace report for one track and one behavior.

Minimal proof loop:

1. start from a known savestate;
2. run one scripted input sequence;
3. log position/speed/angle/grounded/boost/score/camera every frame;
4. identify RAM addresses behind those values;
5. implement the same sequence in a tiny Godot prototype;
6. generate an original-vs-Godot diff;
7. write evidence ledger entries.

That loop proves the methodology. Once it exists, everything else becomes iteration instead of fog.

### 12. Saving the conversation into the repo

Ian asked whether the transcript of the conversation could be saved to the repo.

The assistant used the GitHub connector, confirmed access to `gamesbyian/UR-Recomp`, and created an initial conversation capture under:

`docs/UNIRACERS-REMAKE-CONVERSATION-2026-10-01.md`

The file was committed directly to `main` with commit:

`50cf7960c4ffbefef0fcf7cf26eb6952be00ecd0`

The assistant described the initial file as preserving the reasoning thread, tool leads, project thesis, and candidate next steps rather than raw chat UI metadata.

### 13. Moving the diary file into `prod_diary/`

Ian asked to move the file into a root directory named `prod_diary` and merge it to `main`.

The assistant moved the conversation capture to:

`prod_diary/UNIRACERS-REMAKE-CONVERSATION-2026-10-01.md`

The old path was removed:

`docs/UNIRACERS-REMAKE-CONVERSATION-2026-10-01.md`

The move was committed directly to `main` with commit:

`e920d012673521b51557240d1ef0c7b46648eb28`

The assistant verified that the new path loaded and the old docs path returned 404.

### 14. Updating this transcript under the filename convention

Ian then asked to save a transcript of this conversation to the `prod_diary` directory with a filename matching the convention and commit it directly to `main`.

The assistant interpreted the existing convention as:

`UNIRACERS-REMAKE-CONVERSATION-YYYY-MM-DD.md`

Because a same-day file already existed, the assistant updated the existing diary file rather than creating a near-duplicate sibling. The update preserved the earlier project reasoning and added the repo-save/move/update turns.

## Project implications for UR-Recomp

This conversation reinforces several existing UR-Recomp priorities:

- Keep deterministic ROM/runtime evidence as the oracle.
- Make AI agents build and operate instruments, not act as unsupported authorities.
- Prefer short hypothesis-test loops.
- Preserve claim provenance.
- Build compact evidence packets instead of giant raw dumps.
- Separate observation, interpretation, confidence and implementation status.
- Keep ROMs/assets/data governance explicit.
- Treat public historical/community claims as leads until reproduced locally.
- Keep production diary entries in `prod_diary/` when they are conversation/process captures rather than durable design authorities.

## Candidate next work items

These are not automatically approved work items. They are candidate seeds for future planning.

1. Add a repo-local "behavioral excavation" milestone to the work queue if not already represented.
2. Define a minimal BizHawk or emulator-scripted trace loop for one representative behavior.
3. Create or extend a `behavior_claims.yml` / evidence-ledger schema if the current repo lacks an equivalent.
4. Add a small agent-facing harness command set, e.g. `verify-rom`, `run-experiment`, `analyze-experiment`, `compare-trace`.
5. Identify what current UR-Recomp artifacts already satisfy this structure before adding duplicate infrastructure.
6. Gather existing Uniracers-specific historical/community leads into a contact/source ledger.
7. Keep exact remake/public-distribution risk separate from private technical reconstruction.
8. Decide whether future ChatGPT/project conversation captures should append to same-day `prod_diary` files or create new topic-specific dated entries.

## Memorable framing from the conversation

- "The answer key is inside your thumbs."
- "The repo becomes the lab. The emulators become instruments. The AI coders operate the instruments through scripts."
- "The AI should be treated like an enthusiastic lab goblin with excellent typing speed and a tendency to confidently mislabel organs."
- "Build the faithful fossil first. Then mutate it."
- "The spine is behavioral excavation."
- "The first serious milestone is not making Uniracers in Godot; it is producing a reproducible trace report for one track and one behavior."
