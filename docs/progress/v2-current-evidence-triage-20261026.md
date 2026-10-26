# Progress v2 source triage: October 26, 2026

**Reviewed main:** `683e1087770a3376ad77e0e4a102772d62306c9c` (22:43 UTC). **Previous formal v2 inventory review:** `2636e284d7917e127a5fc5b1acaf5322a42b583b` (October 24). This is a bounded, explicit review of the most likely newly satisfied criteria, **not** a claim to have independently exhausted every intervening commit.

## Measured state and qualification

Frozen v2 inventory still scores **48/135 provisionally verified requirements, 48.000% weighted product coverage and 6.000% independently reviewed bounded coverage**. The official release ledger is **0/12 full Windows gates**; the authoritative workboard still reports **0/45 independently accepted complete USA events**. Both product completion and audit figures are historical exact-source measurements until a full new v2 review. No new score credit is awarded by this triage.

| Previously unverified requirement | Recent source / evidence | Decision |
| --- | --- | --- |
| DATA-05: Native profile and replay file paths preserve UTF-8 Windows names | [#2405](https://github.com/gamesbyian/UR-Recomp/pull/2405), [#2629](https://github.com/gamesbyian/UR-Recomp/pull/2629), [#2404](https://github.com/gamesbyian/UR-Recomp/pull/2404) | **Still unverified as complete**: path conversion is implemented at multiple boundaries, but #2629 explicitly excludes a held Options quarantine seam and states no integrated real Win32 non-ACP cold reopen has been exercised. Qualify one exact-current Windows binary using a non-ACP path through profile creation, save/reopen, replay read, Options and Practice before awarding 1.000 point. |
| MENU-01: Physical-controller root exposes five Modern destinations | [#2640](https://github.com/gamesbyian/UR-Recomp/pull/2640), [#2641](https://github.com/gamesbyian/UR-Recomp/pull/2641) | **Still unverified**: title/root now merged with six applicable checks and hosted Win32 captures, but the requirement explicitly asks for a real physical controller. Require controller-only traversal and modal/back/wake journeys on exact integrated candidate. |
| MENU-10: Title idle leads to genuine stock attract/demo and wake control | [#2640](https://github.com/gamesbyian/UR-Recomp/pull/2640) | **Still unverified**: a merged title painter and opt-in original-stock wake adapter do not by themselves prove timed idle/demo full-cycle and reliable input wake. |
| RECOVERY-09: Power-cut torn-file and second cold restart | [#2617](https://github.com/gamesbyian/UR-Recomp/pull/2617), [#2615](https://github.com/gamesbyian/UR-Recomp/pull/2615), [#2614](https://github.com/gamesbyian/UR-Recomp/pull/2614) | **Still unverified**: impressive real-process staged-save and sharing-denial tests, but not documented real power interruption / second cold restart on a nominated package. |
| QA-01: Immutable current nominated Windows package binary receipt | [#2624](https://github.com/gamesbyian/UR-Recomp/pull/2624), [#2605](https://github.com/gamesbyian/UR-Recomp/pull/2605) | **Still unverified**: source-exact ROM-free artifacts and independent PE bytes exist, but not the separate release-owner nomination and official pinned package acceptance. |

## Verified developments that don't satisfy another criterion yet

- Windows staged-save conflicts and actual Win32 process races now have materially stronger regression coverage ([#2611](https://github.com/gamesbyian/UR-Recomp/pull/2611), [#2613](https://github.com/gamesbyian/UR-Recomp/pull/2613), [#2615](https://github.com/gamesbyian/UR-Recomp/pull/2615)).
- Latest Modern title and source-exact Windows capture landed ([#2640](https://github.com/gamesbyian/UR-Recomp/pull/2640)).
- CI/build acceleration and five-agent shared ranked work allocation are merged ([#2627](https://github.com/gamesbyian/UR-Recomp/pull/2627), [#2621](https://github.com/gamesbyian/UR-Recomp/pull/2621), [#2643](https://github.com/gamesbyian/UR-Recomp/pull/2643)).
- Source-bound Zoo sound-writer instrumentation improved discrimination but does not count as independent full-event equivalence ([#2592](https://github.com/gamesbyian/UR-Recomp/pull/2592)).

## Immediate action and report integrity

1. Independent Windows QA: run the exact `DATA-05` Unicode full-cycle and `MENU-01` physical controller traversal, recording binary SHA, source HEAD, actual machine, failure matrix and negative controls.
2. Windows release integrator: nominate one exact current portable package for QA-01 after confirming inner ZIP/PE hashes; do not inherit the historical candidate.
3. Original/native QA: continue first full USA-event witness, not more source-local partial comparisons alone.
4. Integration/measurement: append a **complete** v2 reviewed merge interval through this head before moving `current-v2-review.json` or promoting any v2 criterion. The short triage here is explicitly **not** such a complete source-review interval. Keep it separate from the authoritative pointer until that validation finishes.

**Conclusion:** current implementation has advanced, but none of the five highest-potential unverified requirements can be responsibly promoted using the inspected evidence. The provisional 48.000% and audited 6.000% values are unchanged *as recorded*, not proof that no development happened.
