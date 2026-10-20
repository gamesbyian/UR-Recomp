# Independent Modern visual acceptance: native title and menus

**Status 2026-10-20: HOLD for the integrated redesign; actual Windows native SDL3 baseline now proven.** The first source review used `main` `2cfe335...`; later QA commits successfully built and captured the existing Baldosa Modern engineering root at 640×480, 1280×720 and 1024×768. The four independent title/grammar/destination/motion visual PRs remain unmerged. **0/25 integrated-redesign acceptance cases, 0 final visual approvals.** Do not change `docs/RELEASE-QUALITY-LEDGER.json`. All pre-capture observations later in this document refer to historical snapshots, not the latest native baseline.

The quality authority is [MODERN-UI-VISUAL-FIDELITY.md](MODERN-UI-VISUAL-FIDELITY.md); navigation and animation intent are in [MODERN-FRONTEND-MASTER-DESIGN.md](MODERN-FRONTEND-MASTER-DESIGN.md). Functional host limitations and the actual player path are in [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md), [MODERN-NATIVE-PLAYER-JOURNEY.md](MODERN-NATIVE-PLAYER-JOURNEY.md), [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) and [WORK-QUEUE.md](WORK-QUEUE.md). This is a per-candidate visual evidence **consumer**, never another frontend, renderer, route authority or release-gate owner.

## Actual source-exact Windows SDL3 baseline (independent, 2026-10-20)

[Workflow run #39413231035](https://github.com/gamesbyian/UR-Recomp/actions/runs/39413231035) passed native capture, tooling tests and repository hygiene at QA PR head `7b9d756fc1f0427c98279657d4be39912cc1a435`. Its checked-out PR merge source SHA is `2a24fb734f2c5f9b38dcb767e27f751c7ecc4b3e` and the actual Win32 PE SHA256 is `5cbcd8ee8224d72be6eba7b55fdfc810f0b0f6c8e5ec74c1ee2d6426c9386e48`. The real renderer reported SDL3, exactly 62 simulations and 62 presentations, with the selected **40th SDL present** captured after the original five-destination root reached native painting. The source-derived input route used the P1 semantic quit handler without an attached physical pad, and the original ROM/private saves were excluded from the artifact.

The [retained original Windows artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/39413231035/artifacts/12259948598) contains each P7 SDL readback, a losslessly converted PNG, exact log and hash receipt. Independent local re-reading verified every RGBA component of each saved PNG equals its corresponding P7 raw pixel, without resize or crop:

| Output | Captured non-black content bounds (inclusive) | PNG SHA256 | Baseline observation |
| --- | --- | --- | --- |
| 1280×720, 16:9 | x=190..1089, y=32..687, actual content 900×656 | `5ca95395eaf12ead9e5fbccdaef717a5cf7be2ee47d97ee4b6f18adf6a4189ca` | Entire menu remains 4:3-proportioned inside pillarboxes; no true widescreen composition |
| 1024×768, 4:3 | x=32..991, y=34..733, content 960×700 | `16ca946a0e97ee2d98a5c62c609563c4c3387750817bcb69e64a1ff425942201` | Source 4:3 engineering menu is centered with black perimeter |

Both images visibly abbreviate the identifying text after `RACER: STOCK RACER - NO PROF`, so the label's complete meaning is absent. This is a **present, native, observed baseline defect**, independent of the final visual agents' upcoming layout. Track source identity and the missing characters separately in the redesigned 16:9 and 4:3 screenshots; do not hide the issue behind a shorter string without an explicit UX decision. Structured hashes/bounds and conservative zero-credit claims live in [`analysis/evidence/modern-visual-native-baseline-20261020.json`](../analysis/evidence/modern-visual-native-baseline-20261020.json).

A baseline 16:9 *SDL output* is not evidence that the Modern 342×224 logical **world/UI** ever became wide, because that particular engineering build pillarboxes its existing 256-wide frontend. Likewise, green Windows and unit checks here do not certify redesigned styling, physical pads, 4K monitor output, sound, profile persistence, stock simulation parity or any of the 25 case gates. Human review remains pending.

The subsequent QA workflow now also drives preexisting test-only **native keyboard Records, P1 Options and P1 profile** handlers after their real input edges, with dedicated logged SDL draw ordinals and separately archived screenshots. Those new journey states remain unaccepted until their own exact-head Windows run and pixel evidence succeed.

## Independent native navigation receipts and Authentic black-frame hold

[Win32 run #39481155085](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481155085) produced genuine SDL3 final-drawable images for **keyboard Records**, **P1 Options** and **P1 first-racer creation** from one AMD64 PE SHA256 `cfc17a3694d3a40e1934a1af322f127a8a8343738b0f425ea38da2f8201ea49c`, Git checkout source `018085b4852b39c0bc279ee48f391a37b5e84270`. The original [navigation artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481155085/artifacts/12290874605) retains exact in-process logs, P7, PNG and conversion receipt. Independent re-reading confirmed **every pixel equals its source P7**, with no resizing. The route-specific logs establish: Records opened and visited 1P→2P→1P→closed; Options opened and subsequently adjusted Display/VSync/Volume; a real first named preset was created and marked for next-process activation. Screenshots were presented at draws 64/65/66 respectively at 1024×768/1280×720/1280×720. Results remain **engineering UI baseline**, not redesigned-destination sign-off. The first-profile screenshot does not by itself prove next-process restoration. See [`analysis/evidence/modern-visual-native-journeys-20261020.json`](../analysis/evidence/modern-visual-native-journeys-20261020.json) for exact image/log/PE hashes and event claims.

**Authentic-mode source and presentation follow-up, corrected by byte evidence.** At guest frame 40 the readback at both 16:9 and 4:3 is fully zero because the original game has not yet painted its introductory content. The frame-240 attempt [run #39482399403](https://github.com/gamesbyian/UR-Recomp/actions/runs/39482399403) was rejected because the SDL3 readback's **alpha was zero across the entire image**, even though independently inspecting its preserved RGB channels later revealed the original Nintendo splash screen. The earlier assertion `if alpha and nonblack RGB` was overstrict for this SDL3 backend, and has been corrected to assess RGB content independently without editing raw captures.

I downloaded the exact [native pre-SDL vs SDL3 diagnostic artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/39483494667/artifacts/12292523002) from [run #39483494667](https://github.com/gamesbyian/UR-Recomp/actions/runs/39483494667), containing the pinned host's authentic post-composition P6 source frame at 256×224 and SDL3 final readback P7 at 1280×720, both native guest frame/present 240. The original composed P6 has 57,344 nonblack pixels and 16 RGB colours; SDL P7 has a 960×720 centre viewport from x160..1119 with exactly **691,200 nonblack RGB pixels**, plus **230,400 black pixels** in the pillarboxes, and those identical original 16 colours. Independent nearest-neighbour centre-of-pixel sampling of the 256×224 source to that 960×720 viewport is **691,200/691,200 = 100% RGB pixel-exact**, with all 230,400 outer pixels black. The framebuffer alpha is all zero, so the standard RGBA PNG displays transparently; the independent RGB-only viewing preview discards alpha *only for visualization*, and the raw unaltered native P7 remains the acceptance evidence.

Full hashes, exact coordinate formula and unapproved boundaries are in [`analysis/evidence/authentic-native-presdl-sdl-rgb-parity-20261020.json`](../analysis/evidence/authentic-native-presdl-sdl-rgb-parity-20261020.json). This establishes **genuine original guest RGB composition and SDL pixel-preserving presentation**, with the Modern root excluded in the observed process, and definitively resolves the mistaken claim that the game was visually empty at guest frame 240. It **does not** establish original USA emulation source CRC parity, physical-monitor alpha semantics or human original-style approval; Authentic-mode final gate and all 25 redesigned visual cases remain on HOLD. The corrected readback acceptance tests still need their own exact-head Windows CI result.

## Three-project reuse preflight

Read `tools/select_three_project_reuse.py` and its grounded inputs `analysis/three-project-reuse-opportunities.json`, `analysis/data/three-project-apparatus-capability-matrix-20261010.json`, `analysis/agent-context-lanes.json`. Select the `release-qa` lane with `--include-conditional` for this work; `modern-product` is a relevant secondary owner reference. The resulting applicable existing choices are **candidate-evidence-envelope**, **route-input-identity** and **agent-work-packets**. First-divergence and effective-address pilots are irrelevant until an actual guest-bound difference demands them. Do not adopt new executable upstream code for screenshot auditing.

Actual pinned source examples inspected:

- **UR**: `native/product/modern_root_overlay_presenter.hpp` is the shared state-fed painter; `native/product/modern_root_physical_edges.hpp` already separates keyboard and P1 edge latches; `native/product/modern_overlay_composition.hpp`, `tools/evidence_contract.py` and hosted native `baldosa_native_*_probe.py` already supply layout/input/evidence infrastructure. Keep them as sole owners; this change only verifies captured output.
- **Baldosa USA**, pinned `10b864b9d14a7b7416dd909eb7b054c88faef101`: `src/main.c` delegates its SDL/window/controller presenter to SNESRecomp's existing host. Reuse its actual native host and controller seams rather than importing or writing another one.
- **Malmazuke PAL**, pinned `42d444594641d23f5d3c15da7b7c454bb5180e43`: `src/app/frontend.cpp` represents pad/keyboard state separately; it is useful for an independent conceptual input-review comparison, **not** a USA pixel oracle or shipping UI code.

Disposition: **reuse existing host and source-native smoke scripts; add one narrow, dependency-free, fail-closed capture receipt checker.** No imported executable/source or third-party art is added, no guest timing, state, records, renderer or control mapping is changed.

## Native capture matrix, currently pending

Machine-readable exact cases are in [`analysis/modern-visual-acceptance-matrix.json`](../analysis/modern-visual-acceptance-matrix.json). Every case requires a **real final-presented native output PNG**, the **same process's route log**, a **retained exact executable**, case-specific route metadata, and a correct full-file SHA256. The PNG's actual dimensions must be the requested final output size; a 256x224 or 342x224 logical raster relabeled `1920x1080` fails.

| Visual integration surface | Case identifiers | Independent finding / remaining discriminator |
| --- | --- | --- |
| Modern title, animated entry and reduced motion | `title-wide-1080`, `title-wide-keyboard`, `title-compact-43`, `title-reduced-motion` | **Uncaptured.** Verify stock-derived title, transition and stable reduced-motion frame against source art. |
| Root dimensions, 1x/higher density and focus | `root-wide-720`, `root-wide-1080`, `root-wide-4k-virtual`, `root-43-768`, `root-43-480`, `root-moved-selection`, `root-keyboard`, `root-disabled` | **Uncaptured in redesign.** Check actual selected art, safe-area typography and stale-profile lock; virtual UHD geometry is *not* physical 4K. |
| Profile creation, profile switch, P2 seat | `profile-first-run`, `profile-switch-existing`, `multiplayer-p2-owner` | **Uncaptured in redesign.** Reuse existing source-run/switch evidence and prove feedback, nested Back and two controller owners on same candidate. |
| Practice, Options and Records | `practice-locked`, `options-available`, `options-refused`, `records-empty`, `records-earned-1p`, `records-earned-2p` | **Uncaptured in redesign.** Distinguish disabled state from missing capabilities; inspect earned 1P/2P record bytes separately from screenshot. |
| Transition, Authentic isolation, focus loss | `transition-back-release`, `authentic-title-stock`, `authentic-stock-wide`, `focus-loss-modal` | **Uncaptured.** Exact same-source stock screenshots/guest input observation and modal release proof remain required. |

Older hosted Windows journeys demonstrate controller-semantic functionality of the *then-current* engineering UI, not this redesign's visual accuracy. The October 19 [independent Windows candidate audit](QA-WINDOWS-INDEPENDENT-OWNER-CANDIDATE-MATRIX-20261019.md) confirms zero real SDL joystick devices and dummy audio for hosted owner evidence. It cannot establish human-operated controller usability, audible cues, source likeness, physical display, 4K/PAR, or the new title's appearance. No screenshots have been fabricated, and no media/trailer assets are used.

## Capture and independent verification

Capture from a specific **actual Windows packaged Modern/Baldosa binary** (prefer source-once native SDL final-output readback, retaining viewport dimensions and sampled-frame/route timing). For each case:

1. Start the **exact executable** with the legal owner-supplied ROM, private clean user-data root and a deterministic controller/keyboard route. Never archive the ROM, private profile contents, real names or another person's data.
2. Preserve the entire process stdout/stderr and input route, exact exit status, tested Git commit, native executable hash, output geometry, rendering density, guest frame, host frame, mode, keyboard/gamepad semantic seat and selected/cancelled state. Record the actual process, not a prior process's log. Pad injection on CI remains **semantic**, not physical device certification.
3. Extract an unaltered final-presented screenshot to PNG (RGB/RGBA 8-bit, non-interlaced). Keep a sequence or brief native capture for transitions and reduced-motion comparisons. Do not crop, upscale, retouch, recompose, or generate the evidence image.
4. Add a JSON manifest beside these files with `schema_version: 1`, the full 40-character lowercase `source_sha`, `capture_runtime: "native-sdl-final-output"`, `exe_sha256`, relative `executable`, and `captures`. Each capture gives `case_id`, `screen`, `mode`, `input`, `state`, `source_sha`, `exe_sha256`, `driver` (`native-semantic-pad` or `native-keyboard`), `png`, `png_sha256`, `capture_p7`, `capture_p7_sha256`, `conversion_receipt`, `conversion_receipt_sha256`, `route_log`, `route_log_sha256` and nonempty `route_markers` containing **actual** runtime log substrings, not expected invented events.
5. Audit extracted bytes from an independent reader:

```sh
python3 -m unittest -v tests.unit.test_check_modern_visual_capture_bundle
python3 tools/check_modern_visual_capture_bundle.py /path/to/evidence/manifest.json \
  --require-complete --json-out /path/to/evidence/structural-audit.json
```

Incomplete inventories can be assessed without `--require-complete`, but are clearly reported as incomplete. An invalid hash, path traversal/symlink, duplicate case, fake/mismatched image dimensions, mode/seat confusion, unsupported capture type or missing log marker is fatal. The test suite synthesizes cases only to test **rejection logic** and earns no native evidence.

**Scope of the tool:** byte integrity of cited files, declared source/executable consistency *within the bundle*, PNG-envelope CRCs and dimensions, route-log substring presence, and inventory completeness. It cannot prove that an executable actually emitted those pixels, that an image is visually correct or that a cited marker reflects the claimed button event. Those require independent execution/frame witnesses and source comparison. Its response therefore permanently contains `visual_approved: false`, `hardware_approved: false`, `authentic_isolation_approved: false`, `release_gate_credit: 0`; no automated path to human approval exists. An executable SHA binding still needs the recorded build SHA and artifact source chain independently checked, not a producer claim alone.


**Mandatory capture chain:** A PNG alone is never sufficient. Each case also submits the exact SDL readback P7 file, the SHA256-bound lossless conversion receipt, and one actual same-process log line containing \`UR_MODERN_VISUAL_SDL_CAPTURE status=saved ... output=WxH source=SDL_RenderReadPixels\`. The checker independently inflates CRC-valid IDAT bytes and compares every RGBA row, with no crop, scaling, palette conversion, alpha adjustment or undocumented filter. Any pixel mismatch, source-P7 header error, missing SDL marker or receipt claiming prior approval fails. An arbitrary mock can still impersonate a log, so the source/PE/native-process cross-witness and real player/physical checks remain external.

## Adversarial visual review per accepted *candidate*

After structurally verified captures exist, compare **real PNGs**, sequential frames and original stock title/menu reference, assessing original-derived glyphs, approximate font strokes/kerning, semantic color ramps, selection feedback, logo proportions, racer silhouette/poses, safe area and all status strings. Inspect contrasting bright/dark backgrounds and the worst text length; check a whole text glyph envelope against the image bounds, not merely that the panel rect fits. Run root moved-selection, disabled stale-profile, locked Practice, empty and populated Records, two P1/P2 profiles, controller ownership, held A/Back and focus-loss cancellation. Support keyboard navigation, remapped prompts and reduced motion by **observed** independent routes.

Keep functional, visual and release decisions disjoint:

- **Functional / structural**: native execution with known-exact binary and source, observed button edges, route logs, screenshot dimensions and navigation assertions.
- **Visual review**: explicit independent stock-comparison decision at 4:3 and 16:9 across outputs and densities; original-derived art approval from the project owner where required.
- **Physical and human**: actual Windows display/TV safe areas, 4K/PAR, two independent controllers, sound and uncoached navigation, on exact packaged hash.
- **Authentic isolation**: paired source-aligned stock mode comparisons and guest-state/CRC authority; similar screenshots or unused Modern handlers alone cannot prove it.

**Stop/merge criterion for this lane:** independent QA code and regression checks can merge without claiming the redesign accepted. Final visual/physical approval remains a separate documented hold until verified final PR heads, native captures, human design review and actual hardware results exist. Visual agents own their art/title/menu animation/source; this lane owns only audit cases, evidence verification and cross-PR integration review. If another visual agent changes a case schema, resolve by PR discussion instead of making competing route/painter edits. Do not merge the new visual design merely because this structural checker goes green.


## Parallel visual-PR integration review (source inspection, 2026-10-20)

Each review was posted directly to the owning PR. **These findings are at the inspected commit only**, not whole-program runtime results. Visual approval and hardware validation are withheld.

| Owner PR / inspected head | Independent evidence and disposition |
| --- | --- |
| [#2038 shared grammar](https://github.com/gamesbyian/UR-Recomp/pull/2038), \`2e4784aed2c1b223cfdeea0f54da6f27f9f520ef\` | Shared native palette/checker/focus primitives preserve typed route authority. **Conditional integration**: original 16x16 glyph atlas and rotating OBJ cursor still missing; wide-layout contract exists but actual native Baldosa call remains fixed to 240-wide panel in its original baseline. Cross-check exact combined title/destination head before visual approval. Reviewed with comment. |
| [#2040 destination child views](https://github.com/gamesbyian/UR-Recomp/pull/2040), \`ed472059433efcaba616c583d4ce1916b0e79e75\` | **Reachability blocker**: C++ tests compute 342-wide canvas but the production native painter hook still invokes the child with 240-wide panel on 256 output. This cannot prove native 16:9 destination rendering. P2's two unconfirmed rows both receive the same selected/focus styling; native two-controller comprehension requires direct testing. Draft owner alerted; no art or input owner code changed by QA. |
| [#2042 root animation](https://github.com/gamesbyian/UR-Recomp/pull/2042), \`d2438d573e855fd5db903b078aaa57efd49c588f\` | **Host integration blocker**: new tick/painter call lives solely in \`native/product/uniracers_modern_host.cpp\`, not the Baldosa Windows \`tools/baldosa_native_modern_root.cpp\` frontend. The environment-only \`UR_REDUCED_MOTION\` guard is not yet a user-facing stored setting. Same-candidate actual native motion/pad observations pending. Draft owner alerted; no animation code changed in QA. |
| [#2043 title](https://github.com/gamesbyian/UR-Recomp/pull/2043), first inspected \`5de21ebe94442e7beab20cbcbfcd1a165ded0a82\` | **Source-provable 4:3 draw-bounds defect**: \`for (x=0; x<w; x+=3)\` paints width three at \`x=255, w=256\`, extending to column 257. A real painter must clamp the last strip. The owner's native fixture bounds assertion should detect the defect. Source-cropped P7 PAM diagnostic is useful but is not final-presented SDL PNG. Also the title painter animates/repeats prompt brightness without a reduced-motion preference guard. Owner alerted in review and follow-up. Reinspect after head changes before considering resolved. |

**Integration dependency:** Title's new Baldosa \`prepare_frame\` and 342-wide draw seam in #2043 may unlock geometry blocked at the earlier #2040 snapshot, but these branches still independently edit \`tools/baldosa_native_modern_root.cpp\`; neither can be awarded wide screen reachability from **another PR's unmerged code**. Rebase and compose single ownership of native title/root/child/motion once, then run **same executable** 4:3/16:9 keyboard/P1/P2/modal, held-edge/reduced-motion and source parity cases. Present ownership cannot be decided by unit-level painter width assertions alone.

None of these are an approval/veto of visual taste. They identify traceable code/readiness gaps, with human aesthetic comparison and attached physical device checks explicitly deferred.


## Opt-in actual SDL drawable readback (independent QA transport)

The repository already has an empirical 3840×2160 SDL readback probe for graphics QA at \`tools/baldosa_sdl_physical_4k_capture_spike.py\`. To avoid mistaking an internal 342×224 host source raster for a consumer-visible 16:9 screenshot, this QA lane adds the **separate disposable** \`tools/qa_modern_visual_sdl_capture.py\` with a strict exact-native SDL2/SDL3 renderer anchor. Nothing in the normal game binary is changed unless this test-only script is explicitly staged into a **throwaway copy** of the pinned Baldosa framework before native compilation. Source-drift/ambiguous anchors fail closed. The adapter is disabled unless all four environment variables are set; there is one capture per *real SDL EndDraw ordinal*, not per paused guest frame.

Example execution within an already established pinned Windows native source/build workflow, **before the CMake build**:

\`\`\`sh
python3 tools/qa_modern_visual_sdl_capture.py --framework baldosa/snesrecomp
# Rebuild the native game from that modified disposable host.

# During one isolated existing original-native + Modern title/menu process:
export UR_MODERN_VISUAL_SDL_CAPTURE_DRAW=70
export UR_MODERN_VISUAL_SDL_CAPTURE_FILE="$RUNNER_TEMP/actual-drawable.pam"
export UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH=1280
export UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT=720
# Invoke the already-established real native executable and controller route.
# Retain same-process stderr, script/semantic buttons, exact PE and source SHA.

python3 tools/qa_modern_visual_pam_png.py \
  "$RUNNER_TEMP/actual-drawable.pam" \
  "$RUNNER_TEMP/actual-drawable.png" \
  --expect 1280x720 \
  --receipt "$RUNNER_TEMP/drawable-conversion.json"
\`\`\`

The readback is taken **after host texture composition and before SDL_RenderPresent**. It uses \`SDL_RenderReadPixels\` into an actual drawable-sized RGBA P7, enforcing a caller-specified observed width/height (maximum 3840×2160), and prints \`UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=N guest_frame=F output=WxH source=SDL_RenderReadPixels\` in the genuine native process log. A mismatch, invalid parameter, absent renderer, existing output, failed allocation or readback does not create accepted evidence. This diagnostic uses a distinct native SDL3 `SDL_Surface` readback and SDL2 destination-buffer branch; it has been successfully exercised through the default pinned Windows SDL3 host. Unsupported or source-drifted renderer APIs are rejected rather than silently substituted.

For Authentic controls, the pinned native host also exposes a pre-SDL post-composition P6 frame. `tools/qa_authentic_presdl_sdl_rgb_parity.py` checks **every** corresponding native P6-to-SDL3 P7 RGB pixel, using the original 4:3 nearest-neighbour centre-of-pixel viewport; it rejects unexpected border content. Its reported zero-alpha pixels remain unmodified and are not interpreted as physical monitor alpha. The test suite includes mismatched RGB, forged borders, invalid dimensions and symlink cases. The current Windows baseline workflow now makes this exact RGB check a required test at both 1280×720 and 1024×768, while withholding hardware/guest CRC and the 25 integrated visual approvals.

The PNG converter validates a strict P7 RGB_ALPHA header, size and complete raw length. It preserves RGBA samples exactly, inserts only required PNG per-scanline filter bytes, CRCs each native PNG chunk, and records both P7 and PNG SHA256s. Its tests decompress the resulting image again and compare the entire row stream to the source. It cannot prove the supplied P7 was captured from SDL, that the native executable matches its filename, or that the image looks correct. The independent capture manifest must retain the actual game log's SDL readback marker, input route evidence, exact native PE, source SHA, **P7 and conversion receipt** in addition to the PNG. The primary 25-case verifier checks final-output PNG hashes/dimensions/route markers and never grants approval. Cross-file provenance from P7 and the source binary still needs independent investigation; future instrumented runs must bind these bytes to one immutable executable.

**Execution status (superseding the original preflight):** the adapter was staged into the pinned Windows SDL3 host, native AMD64 executable was compiled, and real SDL frames were successfully captured at 640×480, 1280×720 and 1024×768. Additional Records/Options/profile journeys and Authentic 16:9/4:3 stock RGB parity were verified against their raw image and process logs. Those runs cover the existing engineering UI, **not the combined title + grammar + destinations + motion candidate**. The final integrated candidate still requires an independent capture campaign and human/hardware review.


## Combined native owner-hook preflight (integration-only)

All four independent visual implementation PRs touch a shared native frontend. Individual source/unit success is **not compositional integration proof**:

- \`#2038\` supplies the shared source-measured visual grammar and edits the existing root presenter.
- \`#2040\` supplies actual native destination paint and uses \`tools/baldosa_native_modern_root.cpp\` to overpaint children without ghosting legacy dialogs. Its later candidate supports a 320-logical-pixel panel **conditional on** a 342-wide host buffer.
- \`#2042\` supplies the Modern root animation model and also patches the Baldosa native draw callback, including reduced-motion and held-guest host ticks.
- \`#2043\` supplies the opt-in 342-wide native title/host viewport callback and original retail title assets; its draw and input callbacks overlap the other two branches. The shared \`.github/workflows/baldosa-windows-native-bridge.yml\` path is edited by **#2038, #2040 and #2043**.

After integrating these in one source epoch, run:

\`\`\`sh
python3 tools/qa_modern_visual_integration_contract.py --strict \
  --out /tmp/combined-modern-visual-native-hooks.json
python3 -m unittest tests.unit.test_qa_modern_visual_integration_contract
\`\`\`

The inventory requires the title, grammar, destination and animation modules plus **actual native Baldosa host callsites** for title painting, child painting, motion input and focus ornament, real 342-wide preparation, semantic P1/keyboard edge ownership, and an Authentic execution exclusion. If a merge silently drops a child renderer, animation hook or source-mode guard, it rejects the supposed integrated source. An apparent green result is expressly \`eligible_for_native_acceptance_run\`, with \`native_executed=false\`, \`screenshots_captured=0\` and zero approval/gate credit. It does not compile the Windows candidate, verify call ordering or override screenshot/identity proof.

Integration owner must reconcile the four PR heads and shared workflow once, preserving all unowned functional states; then run **exact combined-head** native Windows compile, title→root→destination/back and 1P/2P journeys, P7/drawable capture and independent source-aligned visual review. Avoid claiming wide-menu acceptance from a component's theoretical 342-wide layout while the real host still supplies 240px.
