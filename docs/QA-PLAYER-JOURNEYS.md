# Player-journey and cross-feature adversarial acceptance matrix

Status: test specification, **not a claim these cases have passed**. Date 2026-10-08. Owner: cross-cutting QA. Priorities and release thresholds: ADVERSARIAL-QA-AND-RELEASE-READINESS.md. Gate states: RELEASE-QUALITY-LEDGER.json.

## Common protocol

Run the exact release candidate portable ZIP with recorded SHA-256 and source revision. Use clean Windows user data and separately an established multi-version root. Retain: build/artifact ID, OS/GPU/display/audio/controllers, initial state, guest-frame and wall-time observations, outcome, artifact inventory, logs, recording when possible, and independent repeat. Report unverified, blocked, unsupported and failed explicitly. Do not count offscreen runner acceptance as physical input/display/audio or first-user comprehension.

## P0 packaged journeys

| ID | Actions | Observables and stop condition |
| --- | --- | --- |
| J-01 | Cold Windows ZIP, no developer tools. Launch shipped CMD, create racer/profile, race, finish, view result, repeat, quit, relaunch. | Real gameplay; recoverable navigation; saves/settings external to immutable package; no undocumented required shortcuts. |
| J-02 | Existing unfinished tour: quit during Resume or Restart, cancel confirmation, switch profile, relaunch, resume correctly. | Other profile remains untouched; only legitimate stock restore/retirement applies; player retains recoverable progress. |
| J-03 | Distinct pads/profiles joined in stock 2P; swap input seat after ending a race, rejoin after relaunch, compare match record. | No profile alias; distinct inputs; winner/participants align with actual guest result. |
| J-04 | Three entrant Local Tournament, rotate pairs through all fixtures and several processes, restore standings and History after every session. | Exactly one receipt per played fixture; course, seat swap, points and champion correct; unplayed fixtures remain uncredited. |
| J-05 | Two-player 3X meet, play second leg after results panel, third leg as appropriate, End Event/cancel. | Chronology, correct opponent/orientation, complete best-of-three, durable results and explicit cancellation of pending attempt. |
| J-06 | With tournament panel visible P2 holds A/Start/D-pad; P1 navigates/closes it; release/repress P2. Repeat disconnect/reconnect during panel. | Guest freezes while panel owns input; no phantom P2 action after close; new press after release works; no false fixture or profile selection. |
| J-07 | Two simultaneous instances share same user root; both close a run; terminate one between run, ghost and receipt publication. | No filename clobber, duplicate fixture credit, false PB; incomplete staging ignored and valid existing runs preserved. |
| J-08 | Disk full, read-only root, sudden termination at durable writes, partial upgrade, corrupt record/ghost/match. | Valid old data preserved; invalid records cannot influence ranking/progression; actionable failure and deterministic recovery. |
| J-09 | All playable courses and supported event types: launch, contact, checkpoint/lap/finish, results; repeat edge approach with ROM-authoritative reference. | Course by course results table and semantic-event parity, not extrapolated from Dragster or CRC success. |
| J-10 | Same candidate ZIP on dissimilar real Windows systems, varied GPU/audio/pads/60-144 Hz and multi-monitor. | Launch, rendering, controls, device replug, readable UI and audible correct gameplay with no development dependencies. |

### Additional J-06 oracle (P2 held-word boundary)

Record guest `controller_word` for the last active frame before opening tournament panel and first N frames after closing. Hold P2 A/Start/D-pad **before** F4, continue holding for 5+ resumed frames, then release each independently and repress. During panel, guest frame count must not advance for human sessions. On the first resumed guest frame P2 gameplay bits must be clear even if the physical button remains held, and stay clear until its release; subsequent independent button presses must work. Also press P2 *only while* modal is visible and release after close; no phantom input may reach the guest. Compare against Authentic unchanged and scripted/input-file 2P deterministic route unchanged. The C++ pure latch and framework hook tests are prerequisites, **not** substitutes for this route.

### Additional J-07 oracle (simultaneous completed fixture writers)

Exercise a real Windows candidate with two processes sharing the same tournament instance and fixture before either has credited it. Each records a separately valid ordinary-2P run/match pair and attempts to publish the fixture receipt. The expected result is exactly one committed fixture result, conflict for the other, no overwritten incumbent receipt, no double points, valid independent Records retained, and fresh-process restoration crediting only the chosen winner. Repeat with termination after staged write but before publish, and after publish but before stale launch retirement; abandoned `.pending-urfixture-*` directories cannot count as receipts. Native eight-thread acceptance of the low-level adapter is a prerequisite, not substitute for this J-07 exact ZIP witness.

## P1 integrated journeys

| ID | Combined path | Oracle |
| --- | --- | --- |
| J-11 | Race, Pause, Options volume/graphics/resolution, Controls remap, Back, Resume, Restart, Records | Correct guest freeze, no wrong-context navigation, settings persist and input binding authority remains singular. |
| J-12 | Hold confirm/Start on modal open and close; press another key while one held, release and repress; repeat two pads | Held input cannot slip into first resumed guest frame; fresh press passes; no stuck key. |
| J-13 | Selected PB ghost, unusual stunt, scrolling, resize, widescreen and Remastered, finish, replay | Guest parity, correct live-camera placement, quantified draw availability/fallback and temporal coherence. |
| J-14 | Mix corrupt/incompatible runs, ghosts and matches with healthy records; switch profile and open Records | Unavailable without false authority, correct explanation and no unrelated artifact suppression. |
| J-15 | Repeated imperfect landing/boost, borderline stunt, scenery and rival collisions, near-simultaneous finishes | Event-relative original/reference parity across high-risk edge cases. |
| J-16 | 4:3/16:9 and 1x/4x, split-screen, backtracking and vertical motion, modal overlays | No exposed invalid strip, raster priority problems, misplaced original indicators or flicker. |
| J-17 | Guest Start versus Modern host Pause, volume, resume/restart/exit, unplug/reopen audio device | Aligned original/native SFX and music; no clicks or sustained silence after resume; no unintended guest progress. |
| J-18 | Two-plus-hour mixed gameplay and UI session, focus lost, sleep/wake, replay and relaunch | No accumulating memory/timing/audio drift or unrecoverable UI state. |
| J-19 | Blind first-time player tries Practice, Settings, Records, 2P, recovery after pad disconnect | Record task completion, instruction requests, errors, legibility at TV distance, without coaching or hotkey list. |
| J-20 | Stateful random-but-legal action generator plus invalid transitions; retain seed and minimize failures | No cross-profile progress mutation, no ghost/record authority inversion, no guest action during host modal. |

## Content census protocol (J-09)

Create one record per canonical course/event, each ROM variant as applicable, containing original-menu entry, guest course identity, start-state validity, checkpoint/lap/finish sequence and result, reference source, native result, edge-case coverage, and known exclusion. Distinguish 45 RNC stream CRC recovery from gameplay/event pass. Record denominators, not just successful examples.

## Cross-factor combinatorial selection

Dimensions: content/event family, fresh/existing/old/corrupt state, keyboard/1 pad/2 pad/held-disconnected, Original/Remastered, 4:3/16:9, 1x/4x, Modern/Authentic, fresh/quit/restart/crash/upgrade, and 60/120/144 Hz. Cover eligible 3-way combinations and seed selected 4-way interactions (tournament + P2 + panel + relaunch; save + ghost + crash + upgrade). Exclude impossible combinations explicitly, never treat them as passes. Store seed, ordered actions and minimized reproduction.

## Reporting

Every case includes J-ID, linked QA-ID from the risk register, exact candidate SHA/ZIP, observed and expected results, independent reference, host configuration, guest/wall clocks, evidence path, repeat count, impact severity (P0 corruption/wrong original result, P1 common feature/input/audio failure, P2 recoverable polish), and next owned action. An L2 pass never substitutes for packaged L4 or physical L5.

Develop short local/manual probes before coordinating new automatic CI jobs with the active CI-speed owner.
