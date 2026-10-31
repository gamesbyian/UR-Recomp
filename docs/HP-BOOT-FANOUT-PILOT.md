# HP Windows: isolated offscreen package boot fanout

**Scope:** improve the actual owner HP Windows acceptance critical path, without
changing the generated binary, the package, gate criteria, hosted CI, or
controller/audio concurrency. This is not a new release gate.

## Why this is worth trying

After the source-matched physical HP generator A/B (see
[the HP Ninja benchmark](HP-NINJA-GENERATOR-PILOT.md)), the compiled game
uses only **33–39 seconds** of the full 338–352 second native Windows job.
The largest remaining phase is the extracted-package acceptance sequence.
The three existing offscreen boot checks originally run consecutively:

1. **CMD-special path:** independently extract a checked ZIP into an install
   containing spaces, `&`, `!` and parentheses; run the stock verifier
   with an isolated user-data folder and inspect startup diagnostics.
2. **Read-only Unicode install:** copy a verified extracted package,
   restrict NTFS writes inside that copied tree, and require two separate
   boots to preserve configuration/keybindings under a Unicode path.
3. **Normal APPDATA:** launch the same read-only source package without an
   explicit data-root override, while setting a distinct per-process APPDATA
   folder, and assert correct first-boot user-state placement.

The first two operate on separately extracted/copied package trees and
write only inside distinct under-`RUNNER_TEMP` directories. The third only
reads the unchanged `TEST_PACKAGE` and writes to its own APPDATA, caller,
dumps and log directories. All three set `SDL_VIDEODRIVER=offscreen` and
`SDL_AUDIODRIVER=dummy`. None needs host window focus, gamepads, audio,
the mutable package refresh target or a shared user-data destination.

## Implementation and evidence contract

The **authoritative source of each check** is its own shell script:
`tools/ci/windows_package_special_path.sh`,
`tools/ci/windows_package_readonly_unicode.sh`, and
`tools/ci/windows_package_default_appdata.sh`. These were extracted
unchanged from the former inline CI steps.

- Hosted Windows continues executing those same three scripts
  **serially**, with its original step names. Its full Windows x64
  package and QA05/QA09 run must remain green.
- Only `inputs.run_on_hp=true` runs the small
  `tools/ci/hp_windows_isolated_boot_fanout.sh` coordinator. It refuses
  nonowner runners, other repositories/refs and PR events; the existing
  reusable workflow independently protects the self-hosted runner.
- The coordinator starts exactly three Bash workers, each with a unique
  log, then **waits for all three** and shows every log, even if one
  fails. There is **no retry that can silently convert a failed parallel
  experiment into a pass**, and no `taskkill /IM` or systemwide cleanup.
  All children must exit before the workflow proceeds.
- The separate real Win32 renderer/controller QA09, five QA05
  restart/audio attempts with the existing race-result overlap,
  package refresh, migration and startup checks remain serial and
  unchanged. They see the same original `TEST_PACKAGE` and shared
  `PACKAGE_USER_DATA` because those are never modified by the three
  isolated workers.
- Tests prove source-file presence, serial/parallel same-code routing,
  disjoint locations, trusted-main restriction, Bash syntax, all-child
  join on worker failure, refusal of an untrusted event and absence
  of false success after a worker fails.

## Qualification and decision

The actual source branch must pass full four-shard tooling, repository
hygiene and hosted real VS Windows PE/ZIP/race/QA05/QA09. A distinct
reviewer must check isolation and rollback. After merge, the first HP
main push runs on the already owner-approved compiled Ninja generator
and uses the unchanged acceptance. Compare a source-reconciled old main
HP job to the new one: whole-job span, new three-worker fanout elapsed,
actual each-check duration, ten-second CPU use, min available physical
and virtual memory, and all QA outcomes.

**Stop / rollback:** if Windows command quoting, concurrent output,
NTFS ACL cleanup, evidence integrity or a real product check fails, the
run must fail. Revert only the HP fanout routing: route all three steps
serially again, leaving their source scripts and hosted route intact.
Do not weaken assertions, skip QA or claim new physical H01–H07,
original/native USA event parity or release quality. A shorter elapsed
time is a benefit only if every original acceptance passes.
