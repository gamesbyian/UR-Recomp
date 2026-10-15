# Independent Windows candidate executable binding: actual #1609 run (2026-10-14)

**Result:** exact CI original Windows executable-to-package **hash-binding step completed green**, and its original archived receipt agrees with independently rehashed actual ROM-free ZIP, EXE, manifest and sidecar. This establishes a stronger **source/producer-run artifact binding**, not final merged-main release readiness or independent physical hardware acceptance.

- Source: [original GitHub Windows run 38664542215](https://github.com/gamesbyian/UR-Recomp/actions/runs/38664542215), job `116193315399`, green, PR [#1609](https://github.com/gamesbyian/UR-Recomp/pull/1609) head `5ba40b031e5e1ad43975ee434076b1bb6cef2bcc`.
- Actual Windows **synthetic test-merge checkout** `a05431aefe2e8317e1476a8a19351fd57f17024c`, verified original GitHub commit parents `e52a9d3cc66769204d38479c0b9760104bb84653` (then-base) and `5ba40b...` (PR head). Neither is an integrated post-merge `main` candidate.
- Independently downloaded original Actions `baldosa-win32-candidate-binding` artifact **11941125235**, outer ZIP SHA-256 `d4834ce03ecd527152f5366a3d1430a0398b3b5e1d489d2a50bc31ab1c12c964`, containing one `candidate-binding.json`.
- Independently downloaded original ROM-free Windows wrapper artifact **11941160194**, outer ZIP SHA-256 `95d1038215d0bca518c9ee2ac992283969b6768a827585308f0a2f736cf51df7`. Its genuine **inner ZIP** SHA-256 is `7ec14670c19ee05fc61371e0704a97b63a8bce168b075e6be114e77996a5bd49`, 5,958,913 bytes; **AMD64 PE32+ executable** SHA-256 is `d765df78ab24aa08ae631ed9b268be30b225739ef09d1948075a62289414504b`, 19,778,560 bytes.
- Independently rehashed every canonical `BALDOSA-CANDIDATE-MANIFEST.json` immutable file, README revision, ZIP sidecar and actual packaged EXE. The **original producer's successful Windows binding step** reports `journey_and_packaged_executable_sha256` equal to that independently rehashed packaged PE SHA; the same receipt's ZIP SHA and tested checkout equal independent observations. The journey executable's actual bytes were **not separately exported** outside the package. The assertion that the native source games ran that byte-identical EXE therefore rests on the reviewed native Windows in-process filesystem hash step and its green job, not an independently downloaded second copy of the running executable. No arbitrary external source or producer-text claim was substituted for actual ZIP bytes.

## Independent same-run original 2P gameplay cross-check

On the **same exact #1609 run**, independently downloaded archived 52-member original-source/post-Records ZIP **11940053889**, SHA256 `5ccc0e845c44ca061bad085bb9debbe6dd4a2f30720df12eeee3ad9a0c1e7002`, and pre-Records ZIP **11940896143**, SHA256 `5837d277c47604dd314abccdbd2057efb1b9c80a303922b787ae86f4b32d16f9`. Original native source processes create MIKE P1 and MARTIN P2 via controller-semantic frontend, enter actual original 2P stock source gameplay, and record MARTIN **WIN 27.57** vs MIKE **LOSS 27.61**. Independently checked saved `.urrun` and `.urmatch` byte equality before and after later fresh MIKE/MARTIN Records; all actual source logs report **zero real SDL joystick devices**. Separate P2 five-stage raw ZIP **11940128657** SHA `42f6d20691563a01f6339615eb961d26790d665109cb814d8d0514a0a54ee876`.

**Do not splice evidence:** this run does **not** include the later #1584 Practice hard-kill lifecycle from its own distinct exact green cohort [38645114899](QA-WINDOWS-PR-CANDIDATE-38645114899-INDEPENDENT-ACCEPTANCE.md). The CI hash-binding claim cannot be retroactively applied to that other PR-head binary. Both product lines need an integrated source and a **new** single-source Windows run.

The new machine-readable read-only audit receipt is [here](../analysis/evidence/qa-win32-38664542215-independent-candidate-binding.json). No source ROM, executable, profile or saved bytes are committed to the repository.

## Still-blocking release evidence

1. Exact stable merged-main source and single executable/ZIP with *both* genuine Practice OS-kill and full 2P journey plus binding receipt, all from the same Windows job; no PR synthetic merge substitution.
2. Independent stored-byte crash/powercut/post-SAVE-PENDING and multi-process simultaneous writer ownership, including ongoing EEXIST paired-publish staging race reviewed in Modern [#1615](https://github.com/gamesbyian/UR-Recomp/pull/1615); a Linux eight-thread hammer is not native NTFS process death.
3. Two real controllers, actual audio and display/GPU/high-DPI/Widescreen/4x output, and official **0/45** USA strict original-emulator complete-event census unchanged.

Keep `candidate.commit_sha=null`, `candidate.zip_sha256=null`, `release_decision=not_assessed`, and QA-02/05/09/12 status unpromoted. These are coherent source/packaging checks, not player-hardware or release-grade validation.
