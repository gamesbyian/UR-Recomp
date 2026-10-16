# Actual Win32 rooted-relative CMD rejection: independent artifact review (2026-10-15)

**Disposition:** verified Windows process **stderr bytes and cross-artifact executable identity**, with exit-code/input-path and filesystem-noncreation claims explicitly bounded to producer receipts. This is [merged #1680](https://github.com/gamesbyian/UR-Recomp/pull/1680), **not** a new nomination of the separately retained owner source `11501a15dea38fa912335cfc63103ce3a7208001` / ZIP `5605aaf2…`. **No QA-09 or QA-12 release witness is granted.**

## Original Win32 origin and binary binding

The actual passed hosted Windows workflow [38831297147](https://github.com/gamesbyian/UR-Recomp/actions/runs/38831297147) ran at PR head `4a0ce91c8c6bb58375007b3a660718f76cc873f9` with the **synthetic tested merge source** `173d49e9706fd5b018cd2b8441665fd16769b5cb` (confirmed GitHub parents: then-base `6b522e0a509fb7c1e9b66554f04db9330cbe734b` and that exact PR head). A green Actions job is a producer signal; independent QA downloaded **three original job archives**, recomputed *entire wrapper* SHA-256 and decoded their real retained contents:

| Actual artifact | ID | Independently rehashed whole ZIP SHA-256 |
| --- | --- | --- |
| Extracted-CMD 10-file source evidence | `12017294058` | `24bbc0640d94612ec6d26ff23aa3d980c9963da9d224e091f3a357fcfc67dbb7` |
| Separate journey/executable binding | `12017353439` | `7b7489e6cbae07f358d8f75ac41cde1ddaf78a4d15e9a2bf37859168b7e01c5f` |
| Separate ROM-free portable Windows candidate | `12017368467` | `b90f72f382fec99c3cd264a6e15af3bcc8a51cf9d8483aec5442a12f060e3b7d` |

The independent checker enforced the exact original archive population, ZIP CRC and safe names. It extracted and SHA-256-rehashed the **actual inner portable ZIP** (`e42913e0b3840660462e75192f30f090b152a0c5dc39964e433bd98ed49ecd2a`, 5,973,815 bytes), its canonical `sha256sum` sidecar, all three immutable manifest members and the valid PE32+ AMD64 executable (`c02d563741d60ef1061562eb31e224e34fae97e5d19b0a0d836ed348661f5fef`, 19,808,768 bytes). They match the separate Windows `candidate-binding.json`, live launcher report and new negative source receipt, all pinned to the synthetic tested merge SHA. The archive and manifest contain **no bundled ROM or profile save**. Its different source and ZIP hash must never replace the historical nominated owner candidate.

## Two actual retained subprocess output streams

The new `rooted-relative-rejections.json` has the precise intended inputs, code 3 and source/ZIP/EXE pins. Independently decoded **both** retained Windows CMD transcript files:

| Test case named in producer receipt | Original log | Actual decoded output |
| --- | --- | --- |
| `C:qa-drive-relative-root` (drive-relative) | `drive-relative-root-refusal.log` | Empty stdout; original stderr root-refusal marker and user-facing instructions |
| `\\qa-current-drive-root-relative` (current-drive rooted-relative) | `current-drive-root-refusal.log` | Empty stdout; same real stderr rejection and instructions |

For **each** transcript, independently recomputed SHA-256 of the decoded UTF-8 stdout (empty: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) and stderr (`10585ab78729dcdc2e8c3509aefca1bda6a78ed6d68936b35ca7ad1498eedfda`) against its receipt. Both transcript files have SHA-256 `4e3eddda5641364b46cf2a874504fbcd19136b13128d76a59b8953d91655dc33` and are exactly **290 bytes each**. A local single-byte deliberate change to the stderr was rejected by the SHA oracle. The actual stderr explicitly starts with the `UR-BALDOSA-STARTUP-SAVE-ROOT` rejection and advises how to restore the default user-data root. Both original source logs are byte-identical because the launcher emits generic guidance rather than echoing the supplied path.

### Strict proof boundary

The two output transcripts **do not themselves contain the supplied test root or the OS process exit status**. Their pairing with `C:...` versus `\\...`, the observed return code **3**, and the absence of created user-data folders come from the adjacent source-bound producer receipt and verified test source, **not independently retained NTFS snapshots or an independent executable invocation**. The bounded independent positive is that the *actual* Windows source job retained the two expected refusal-message byte streams, which match its own source and packaged executable. This closes the prior *missing raw stdout/stderr* gap, but is not independent physical-access, whole-system failure-recovery or release certification.

The package runs scripted semantic input in hosted CI with no independently tested physical pads, audible audio, GPU/4K display, storage-full condition or abrupt power loss. Original/native complete USA course acceptance remains **0/45**, full release gate witnesses **0/12**, and P0 [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) still requires crash-safe, player-recoverable raw/typed SRAM reconciliation.

[Machine receipt](../analysis/evidence/qa-win32-rooted-relative-pr1680-independent-20261015.json) records exact original digests, conditions and limitations. Reuse preflight: reused existing exact-source Windows launcher acceptance, portable candidate audit, and UR candidate evidence envelope, without changing the production launcher, product state, GitHub Actions topology, private saves or ROM files.
