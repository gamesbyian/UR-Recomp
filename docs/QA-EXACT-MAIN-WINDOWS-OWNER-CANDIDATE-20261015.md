# First independently source-pinned exact-main Windows owner-playtest ZIP

**2026-10-15 | Independent release QA | Hosted Windows technical playtest, not beta, hardware approval or accepted release.**

## An actually executed main workflow, not an inferred PR ZIP

The pre-existing manual **[Manual ROM-free Windows technical playtest, run 38813101482](https://github.com/gamesbyian/UR-Recomp/actions/runs/38813101482)** was dispatched as `workflow_dispatch` against **branch `main`**, source **`11501a15dea38fa912335cfc63103ce3a7208001`**. The full reused `tested_candidate / native-windows-x64` job and `verify_provenance` job finished **success**. `publish_provisional_preview` was **skipped**: no GitHub release was published or authorized by this result. This was exactly `main` when dispatched and remains a source-pinned immutable checkout even if the branch later advances.

| Independently downloaded Actions artifact | Artifact ID | Original ZIP wrapper SHA256 |
| --- | --- | --- |
| **Four-file verified owner-playtest** | `12009612842` | `5a4de66f09a9ceea5cb7b431f808a17821f770bf09c48117a8cb3bd9a0c83722` |
| Separate tested Windows candidate and SHA sidecar | `12010371123` | `3a466ba30e512057c61d14e8be0dea12c6b5cc47eff854aabb72a1554e894545` |
| Same-run Windows binary-binding receipt | `12010675093` | `d396c11061f34b751c6138670cb160c01d011022b93800ac14b57eb2854c2a69` |
| 20-member Options/Practice/Pause native evidence | `12010555537` | `0dc7618f81136a8288459e6ad8908d368c0a20bffffc098c6917b1a7ba6145b1` |

These are **original, externally SHA-pinned GitHub Actions ZIPs**, not re-created repository tests or guessed filenames. Independent QA downloaded and rehashed each referenced wrapper.

### The one nominated portable Windows ZIP

- **Source `main` revision:** `11501a15dea38fa912335cfc63103ce3a7208001`
- **Original actual portable ROM-free ZIP SHA256:** `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`; **5,973,812 bytes**.
- **Original Windows PE32+ AMD64 executable SHA256:** `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`; **19,808,768 bytes**.
- **Owner archive:** exactly one original portable ZIP, canonical GNU SHA256SUM sidecar, `PLAYTEST-PROVENANCE.json`, and `RELEASE-NOTES.md`. No private ROM, SRAM, user profile or player saves are contained in the portable ZIP.
- **Manifest:** exactly four immutable ROM-free inner members: native EXE, `run-baldosa-modern.cmd`, README, candidate manifest. Every enumerated original byte size and SHA256 was independently rehashed.
- **Same-run equality:** inner portable ZIP and sidecar are **byte-identical** in both the source-bound native candidate artifact and the four-file owner artifact; the separately retained original Windows `candidate-binding.json` gives that same source, ZIP and executable hash. Both original Options/Practice producer reports bind the same `github_sha` and `exe_sha256`.
- **Independent offline verifier:** `tools/check_baldosa_owner_playtest_download_qa.py` is the existing stricter canonical four-file production QA consumer; the separately run bounded read-only independent script rechecked all members, ZIP manifest and PE32+ header against external digest pins. Its conclusion is *package identity only*, not guest-source parity or hardware acceptance.

### Real Windows behaviour and its evidence limit

The actual main-dispatched hosted Windows runner completed original guest 1P/2P, genuine scored source results and cold-process Records; first and second racer creation, P1 selector, interrupted P2 catalog recovery, real pause lifecycle, multiple Practice course entry, persistent Options, and actual extracted CMD/ROM/data-root refusal tests. This is better than test fixtures alone, yet the CI drives semantic controllers and dummy audio, with **no physically attached USB/Bluetooth pads, audible output, actual GPU/display/fullscreen/pixel inspection, or power-loss cycle**.

As a bounded independent regression comparison, **all 15** corresponding Options/Practice source-event streams in the exact-main 20-member evidence artifact were identical to the previously independently verified Win32 PR archive 11958820226. Three extra exact-main process logs test paused Options via semantic-pad and keyboard paths and delayed in-Practice restart. This is reproducibility and native process behaviour, **not** evidence that all 45 original USA events completed or that the guest is instruction/PPU exact.

### Release/QA decision

**Nominate the exact source+ZIP pair for subsequent private physical QA only**, keeping `candidate.release_decision = not_assessed`, `candidate.physical_hardware_verified = false`, all individual gate statuses/witnesses unchanged, **0/12 accepted release gates**, and **0/45 accepted complete original/native USA events**. The package is a *candidate to test*, not an accepted beta or public release.

**The strongest outstanding data-integrity blocker is still [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214)**: the real native Windows post-raw-SRAM/pre-typed-save process-kill leaves divergent bytes and then safely refuses fresh load. That is preservation and safe refusal, **not yet user-recoverable power-loss transaction consistency**.

Next use **this exact ZIP SHA** on disposable physical Windows setups, record real two-pad identification and interaction, audio and monitor/presentation behaviour, actual process kill/restart and read-only/full storage, and independently inspect original/native scored completion and durable progress. Never copy a private ROM or personal SRAM into the public test artifact. Do not promote release-gate status from the package checksum or from the present successful hosted workflow.

### Minimal external reproducibility

Download Actions artifact `12009612842` from run `38813101482`; verify the **outer** artifact SHA above *before* opening it. Demand exactly the four members and canonical provenance claiming source `11501a15…`, zero gate credit and no hardware certification. Independently hash the inner ZIP as `5605aaf2…` and the embedded EXE as `0701f724…`, validate the immutable manifest and the separate same-run binding artifact `12010675093`. This is also independently cross-checked by the existing `tools/check_baldosa_owner_playtest_download_qa.py` contract, which must never confuse wrapper SHA with the playable ZIP SHA.

For the owner: extract the inner ZIP, place your own verified USA `Uniracers_USA.sfc` next to the extracted executable, and invoke `run-baldosa-modern.cmd` with a disposable `UR_RECOMP_USER_DATA_ROOT`. Follow [the practical physical playtest instructions](WINDOWS-PLAYTEST-INSTRUCTIONS.md).
