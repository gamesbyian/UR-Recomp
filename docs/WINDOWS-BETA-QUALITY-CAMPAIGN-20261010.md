# Windows beta push: seven-day target, quality-first

**Planning target:** first polished Windows x64 beta readiness review around 2026-10-17. **Not a ship date, deadline guarantee, or permission to lower fidelity.** Nine or more days is acceptable when evidence shows player-facing quality, original-game fidelity, or architectural maintainability improves. Review actual integrated candidate and outstanding defects; do not forecast from green component CI.

This is a short-horizon coordination document, **not** another active queue. [WORK-QUEUE.md](WORK-QUEUE.md) owns daily assignments; [PROJECT-PLAN.md](PROJECT-PLAN.md) and [DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md](DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md) own the enduring product and reference ambition; [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) alone awards independent QA gate passes.

**Product checkpoint, 2026-10-10:** merged #1203 demonstrates the actual ROMless CMD launcher rejecting wrong ROMs and unsafe save roots with distinct diagnostics. Merged #1208 demonstrates a real 2P guest race paused via SDL, menu Quit through the existing SDL event loop, normal named-profile SRAM checkpoint and no fabricated result. #1209 merged the shared Modern root's unavailable-destination affordances and removed unwired racer shortcuts after exact-head CI. These are genuine component advances, **not** acceptance of a full Modern Windows player journey.

**Next authoritative product handoff:** the old Modern host already uses CompletedRunCapture to record actual mapped-frame input and splits, source-derived course identity, P1 line-crossing ticks and settled results; it owns .urrun/.urghost/.urmatch publication. The native Baldosa adapter must bind these **same** models to guest-authored observations, preserve the canonical named profile and 8-KiB SRAM root, and mint a distinct backend compatibility ID until cross-backend replay equivalence is proven. No record, tournament credit or victory may be published on a requested exit, clock timeout or incomplete result. Acceptance is one genuine P1 result and one local P2 result plus Records and fresh-process reload on one exact Windows candidate. The old backend remains rollback.

## User-visible beta bar

- One actual pinned portable Windows build: controller-first Modern root, profile/racer, 1P and local 2P race, proper original results, contextual navigation, pause/resume/restart/exit, persistent SRAM and host records after full process restart, no fake-success routes.
- Coherent visible identity: *real* logical 342-wide world, correct 7:6 original PAR and source-supported wider-world backing; true 3840x2160-capable physical output; robust stock Original fallback; authored 4x art only when registered and source-visible. Correct fixed Original mode, HUD, 1P/2P split, menus and indicators. Unfinished Remastered coverage must fall back gracefully, never guess pixels.
- Original behavior remains guest-authored. At least representative independently compared complete Race/Circuit/scored Stunt witnesses and a defensible divergence classification before external beta. Maintain full 45-USA-course census and all release gates transparently; beta and final release are distinct.
- No loss/corruption in profile, SRAM, results, ghosts/records/matches; release candidate is tied to one exact executable and portable ZIP digest. Exercise real Windows hardware, controllers, audio and display modes prior to broad beta circulation.
- A coherent experience rather than experimental UI fragments. Confirm keyboard/controller navigation, focus release, readable options/records/results, accessible presentation, graceful failure diagnostics, packaging and install-free startup.

## Three coordinated exclusive implementation lanes

**A. Windows Modern product integration and data authority.** Priority 1: get real controller-only root → authentic race → original result → existing host records/profile across process restart on pinned Baldosa and Windows packaging. Own Modern host and storage adapters, lifecycle/control focus, portable ZIP. Do not rewrite other two lanes' rendering or original comparator.

**B. Widescreen, Original/Remastered graphical coherence and output QA.** Integrate existing 342-wide materialization, authored 4x presenter, fallback, native 4K and fixed-stock renderer into actual shared product. Prove source-visible P1/P2/HUD and 7:6 PAR without guest changes. Existing #1197 rear-only Original OAM diagnostic belongs here; review branch carefully against merged #1198/#1199 before reuse, and do not let obscure same-colour sprite ownership become an unbounded beta blocker.

**C. End-to-end original gameplay QA and readiness.** Own original/native route witnesses, full result and score/progression comparisons, differential phase analysis, fault injection and candidate-based Windows QA checklist. Retain the original strict comparer and official denominator. Use observed host-5782 eight-WRAM-offset evidence; triage importance before archaeology. No bypasses or synthetic events.

All agents must read fresh main/PRs, claim exclusive files before editing, avoid duplicate workflows, use one pinned candidate/evidence corpus, commit frequently, run targeted tests and open narrow PRs. Merge only reviewed CI-green same-head branches; explicitly classify temporary never-merge experiments. CI is account-limited: no workflow storms, redundant codegen or waiting on runs while productive non-contingent work exists.

## Daily review questions, not invented completion percentages

1. Can a human play a complete real Modern Baldosa 1P/2P Windows journey today?
2. Does it look convincingly and consistently better than the baseline in real widescreen/4K, with stock fallback correct?
3. Are winner/time/score/progression and persisted records genuine and defensible against original evidence?
4. What exact P0 defect or product defect would prevent a *polished beta*? What belongs to later exhaustive reference/RC coverage?
5. Did the day's work improve game experience, reproducible understanding, or remove architectural debt?

**Exit from Baldosa-only focus:** integrated internal alpha works on Windows and no known critical gameplay/data issue is ignored; resume ordinary product development while QA and Technical Atlas proceed in parallel. **Beta readiness:** independent candidate-scoped assessment of quality and known limitations. **Release:** applicable independent QA gates accepted by the ledger. No calendar overrides these conditions.
