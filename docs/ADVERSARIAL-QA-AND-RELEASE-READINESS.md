# Adversarial QA and Release Readiness Programme

Status: **active cross-cutting product-quality programme**, opened 2026-10-08. This is the canonical release-risk and QA prioritization document. `PROJECT-PLAN.md` remains the product intent; `WORK-QUEUE.md` owns active execution; subsystem contracts own original technical evidence. See `QA-PLAYER-JOURNEYS.md` for executable scenarios and `RELEASE-QUALITY-LEDGER.json` for current gate states.

## Why this programme exists

UR-Recomp has unusually strong, precise **representative** native/reference evidence and a real, verified Windows packaging path. These are genuine accomplishments, but a proven ROM byte, golden Dragster fixture, valid data format, or green hosted launch does **not** by itself establish whole-game content coverage, cross-feature correctness, hardware experience, or public release readiness. Recent course-contact phase correction #959 and the current audio limitations demonstrate this distinction concretely. This programme is about searching for *counterexamples*, not creating another generic infrastructure audit.

Keep distinct:
- **Observed defect**: reproduced unexpected behaviour with a reliable build and reproduction.
- **Confirmed evidence gap**: missing specified validation, even if implementation may be correct.
- **Risk hypothesis**: plausible interaction or failure mode not yet observed. Never report it as a bug without reproducing.
- **Passed gate**: specified evidence from the *exact candidate commit and artifact*.
- **Accepted limitation**: explicitly documented user-visible limitation with a recovery/fallback policy.

A passing unit test proves its own property; do not allow it to silently promote a whole subsystem to release-accepted. A correct fail-closed fallback can still constitute poor usability or unacceptable feature availability.

## Release decisions and entry conditions

1. **Internal engineering build**: authentic main/race boot, focused regression contracts, known provenance. May have experimental UI.
2. **Playtest alpha**: immutable candidate SHA and tested ZIP/sidecar; known issues; install/launch, clean-root and basic 1P/2P journeys; diagnostics/repro instructions; no assertion of broad fidelity or independent hardware.
3. **External beta**: representative course/event-class and complex journeys complete, no unresolved P0 integrity/correctness issue, recovery and controller checks, repeatable Windows packaged run *on candidate*, physical Windows/audio/gamepad evidence from dissimilar machines, understood accessibility/UI limitations.
4. **Release candidate**: whole playable-content event matrix and mode boundaries; persistent-state fault campaign; sustained play; all major visible routes and audio/visual presentation deliberately reviewed, clearly classified and owned; CI and manual gates from exact artifact; rollback/migration procedure; public ROM/legal distribution policy resolved if releasing beyond private circulation.
5. **Public release**: a separately recorded human release decision. A green CI matrix, merge, or agent-offered ZIP never automatically grants this status.

### Candidate provenance

Every playtest report must record commit SHA, ROM variant/hash, artifact ZIP/checksum, OS/GPU/controller/display/audio configuration, input script or reproducer, user-root policy, guest/core mode, presentation settings, expected/observed behaviour, screenshots/logs (private evidence only; never commit ROM/PCM/secrets), and whether it reproduced a second time. Historical green runs may support hypotheses but cannot certify a later candidate.

## P0: investigate before declaring even broad private beta readiness

| ID | Failure mode / coverage debt | Known evidence and missing discriminator | Stop condition |
| --- | --- | --- | --- |
| QA-01 | Wrong checkpoint/lap/finish credit on under-exercised courses | #959 corrected same-frame postframe slot-8 causality; actual dispatch-word/gate still lacks instruction-time witness. Representative Dragster is not every course | Run **every playable race course/event class** from legitimate entry to settled result, plus targeted near-boundary/side-approach/rewind and multi-lap tests; compare authoritative events; capture instruction-time finish witness for any discrepancy |
| QA-02 | Cross-artifact durability, corrupt progress or contradictory resumed session | Profile SRAM, run/ghost, tournament receipt/session and migration have separate transaction contracts; `.urrun`/ghost publication is atomic visibility, not power-loss fsync guarantee | Exact build fresh-process crash/fault matrix at each write transition: after run, before ghost, during receipt, between profile changes, out-of-space/unwritable, two instances, upgrade. Valid old records survive, recovery decisions are deterministic, users get usable diagnostics |
| QA-03 | Incomplete tournament/event pathways | Packaged Windows **single-fixture** completion validated (#946/#964); 3+ participant multi-session and actually completing leg 2/3 remain explicitly open. P2 control-word ownership is not filtered while tournament panel is open | Finish 2-player best-of-three and 3+ entrant round robin across real process restarts from candidate ZIP. Include seat swap, draw, cancellation, End Event, hotplug and held P2 input. Compare persisted receipts/standings/history to game-observed winners |
| QA-04 | Built artifact misrepresented as consumer-ready | Hosted Windows ZIP, native Win32 and offscreen launch evidence are real, **not physical GPU/audio/controller/monitor proof**. Last gate must match exact candidate | Verify checksum/provenance and complete manual journey on at least three dissimilar physical Windows setups or isolated clean VM + two real systems; record hard failures and input-to-photon/AV behaviour, do not silently use developer prerequisites |

## P1: exercise in parallel with P0 work

| ID | Work | Discriminators / quantitative signal |
| --- | --- | --- |
| QA-05 | Cross-feature route/input ownership | Pairwise+3-way combinations: modal close-held-button, profile switch, controller replug, graphics/resolution changes, Records/Replay, tournament. Assert guest freeze, correct player seat, no unintended guest action on first resumed frame |
| QA-06 | Audio correctness vs mere sound presence | Guest/sound-command-clock-aligned original/native musical phrase and SFX comparisons, phase-locked windows, hardware latency, pause/resume/exit/restart clicks, loss/reopen device; RMS alone cannot certify parity. Honor `AUDIO-NATIVE-OUTPUT-ACCEPTANCE.md` open caveats |
| QA-07 | Expert/edge-play physics | Counterexample-driven TAS/speedrunner reference seeds, high boost, repeated imperfect landings, multi-object collisions, stunt thresholds, tied racers; measure event-relative semantic state, not just absolute frame number |
| QA-08 | Widescreen/HD temporal coherence | Rapid backtracking, vertical transitions, multiple viewports, layout resize/fullscreen, sprites/OAM priority, multi-actor occlusion, camera reversals. Measure valid replacement *availability* and fallback/flicker across motion, not isolated approved pose count |
| QA-09 | New-user journey and accessibility | Unknown-player first-run without hotkeys manual; task success and confusion annotations; controller-only menus, TV-distance legibility, text/contrast/reduced flashing, semantic hints and actionable error states; finished original-style visuals before RC |
| QA-10 | Session longevity, scheduling & storage | 2h+ mixed real-world play/soak, pause/focus, sleep/wake, multi-monitor, slow I/O and user-root permissions. Track memory, frame pacing, AV drift, store growth, log spam, UI responsiveness |
| QA-11 | Durable replay/ghost integrity *and* usability | Finished-race fresh-process compare on more than Dragster, digest source-identity, one-frame results retirement bound versus semantic event parity, ghost draw-frame availability, source deletion/replacement, slow/fast camera, unsupported art |
| QA-12 | Evidence independent of fixtures and documentation freshness | Direct ROM/independent-emulator/original hardware reference versus fixture-derived assertions. Reject historical PR statuses in canonical docs, maintain owner + explicit claim scope, don't equate skipped tests with passes |

## P2 / deferred, unless blockers become visible

Cosmetics, wider HD asset scope beyond coherent first release families, network/hardware ports, optional achievements, speculative editor modes, new storage formats, unnecessary defensive gate proliferation, and unrelated CI speed experiments should not displace P0/P1. Critical user-visible graphics coherence still belongs to P1 even if additional individual art families are deferred. Current CI optimization has its own lane; do not modify workflows or rerun GHA merely to reduce wait time.

## Evidence quality: five independent layers

- L1: ROM bytes, independent decomp/decoder and source archaeology.
- L2: unit/property and deterministic native/reference comparison (including multi-emulator where appropriate).
- L3: representative **content/state-space coverage** and stateful randomized valid action sequences.
- L4: full cross-feature **player journeys** using the shipping executable, actual persistence, and clean-process reentry.
- L5: physical hardware, player comprehension, game feel, duration, accessibility, and audio/visual judgment.

Record for each gate the **denominator**, passed cases, coverage exclusions, expected failures, source independence, and exact artifact. Example: 1,380 HD selections / 5,282 measured player-frames is valid for *that* ordinary-2P census, never a whole-game percentage. A fallback is counted separately from a feature draw. A green L2 cannot be relabelled L4 or L5.

### Counterexample search protocol

For each `sufficient` subsystem, independently write a claim, its exact scope and test oracle. Generate disconfirming cases: alternate ROMs, new race/event class, unusual legal input edge, state after a failed attempt, two simultaneous users, and novel host configuration. First reproduce without mutating guest authority, then capture failing input and state; only then propose the smallest production fix. Explicitly retain refuted hypotheses (as in course #959) without rewriting raw observations.

### Test techniques

Use model-based stateful action generation with preconditions/invalid transitions, property-based boundary generators for inputs/artifact schemas, structured failure injection at persistence transitions, coverage-guided selection for playable course families, and pairwise/3-way covering arrays over content × host state × input × presentation × lifecycle. Avoid full Cartesian explosion: prioritize risky interfaces and specific 4-way interactions. Mutation-test critical oracles by deliberately introducing known defects on throwaway branches and verifying the right acceptance fails. Never merge mutants.

## Process and ownership

- Give **adversarial QA** an independent ownership lane: scenario documentation, static/unit test oracles, manual artifact witness review, and reproducible issue discovery. QA does not rewrite the same feature it certifies without a separate review.
- Features remain owned by gameplay, course, frontend, persistence/replay, tournament, graphics, audio and Windows/package lanes; don't mix them into one giant PR.
- Every exposed user-facing failure needs a cause-independent message and recovery path; silent non-render/skip is often *safe* but not release-sufficient.
- Open one issue per reproduced defect or bounded evidence gap with priority, owner surface, exact stop condition, and associated scenario ID. Link it in `WORK-QUEUE.md` where it changes critical path.
- The authoritative concise gate ledger is `RELEASE-QUALITY-LEDGER.json`. Historical docs can contain obsolete PR narratives; release gate status must not be inferred from them. Never auto-promote `merged` to `release-accepted`.

### Active counterexample result: P2 source edges versus guest word

Audit follow-up identified a credible structural leak: the original P2 human word is assembled from `g_gamepad[1].axis_buttons` in SNESRecomp, outside the P1 host filter. Pure P2 source-edge filtering alone therefore cannot certify a button held across entry/exit of a frame-held tournament modal. A newly pinned P2 human-word seam arms a 12-bit release latch on panel entry and filters held bits until release on actual guest input assembly. J-06 still requires a real guest/controller-word witness and hardware/packaged acceptance. Preserve the distinction between source-proven gap, mitigated code path and reproduced player-visible defect.

## Next concrete work

1. Freeze a current candidate and record the Windows package from *that* SHA.
2. Implement QA-03's two-player multi-leg + three-plus-entrant fresh-process journey; independently probe P2 held-button input after tournament modal close.
3. Begin QA-01 representative course family → all-course completion census, reporting executed/blocked/unsupported rather than extrapolating.
4. Implement QA-02 fault-injection harness at real storage boundaries, including immediate termination/reentry.
5. Capture QA-09 blind onboarding and QA-06 hardware audio sessions; polish only after reproducible evidence.

The initial ledger deliberately leaves L4/L5 gates **unverified**; do not fill them with predictions. The conditions above govern priority even if new agents offer a build earlier.
