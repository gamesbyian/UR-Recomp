# Verified Windows playtest artifact: preservation receipt (November 6, 2026)

**Purpose:** retain source-bound, ROM-free playtest bytes before a GitHub Actions retention deadline. This is an artifact-storage/P7 preservation result under the [collective qualification plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md), not a new Windows build, current-main release candidate, machine execution result or product acceptance.

## Source and verified identities

| Field | Observed and verified value |
| --- | --- |
| GitHub workflow | [Windows run #40763949905](https://github.com/gamesbyian/UR-Recomp/actions/runs/40763949905) |
| Actions artifact | [#12850662557, `verified-romfree-windows-playtest`](https://github.com/gamesbyian/UR-Recomp/actions/runs/40763949905/artifacts/12850662557) |
| Source producer main epoch | `250e0803a1791d9deda7a715614d49f4752cd374` (historical, **not** current main) |
| Artifact ZIP size | **6,136,204 bytes** |
| GitHub expires | **2026-11-11T20:54:01Z**, as reported by artifact metadata on November 6 |
| Outer ZIP SHA-256 | `d8f5cbaaf958a9bf59321f025804cafcb0b51ac7cafc84033f30c61dc8850f97` |
| Inner `UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip` SHA-256 | `586c32e344af30cfeb61152c475838fbc6aeab7c64d239e560ecd8c4a6bd7616` |
| Inner `UniracersSNESRecomp.exe` SHA-256 | `c9f51257fb84aaddec54c728a64b5c5738393d62932956b6855c1413ba82f3e0` |

On November 6, the exact Actions artifact ZIP was downloaded through the repository's authenticated artifact API and locally hashed. Its outer ZIP contains four entries: `PLAYTEST-PROVENANCE.json`, `RELEASE-NOTES.md`, the ROM-free inner Windows ZIP and the inner ZIP's checksum text. The inner ZIP contains its candidate manifest, README, Windows executable and Modern start script. A separate byte-only ZIP inspection independently recomputed both nested hashes above. The prior [independent production-byte audit](https://github.com/gamesbyian/UR-Recomp/issues/970#issuecomment-6480463516) and [active playtest queue](WORK-QUEUE.md) already bind these same hashes to the historical source candidate.

## Durable owner-machine copy

The verified outer ZIP was also fetched using the HP's existing authenticated `gh` credentials, saved only after checking SHA-256, and left **unextracted and unexecuted** in a new dedicated user-visible folder:

```text
%USERPROFILE%\Downloads\UR-Recomp-Playtests\verified-romfree-windows-playtest-20261028-artifact-12850662557.zip
```

The download used a temporary file, checked the full 64-character outer digest and refused to overwrite an existing destination if its bytes differed. It moved the verified ZIP into place only after successful verification, then removed the temporary data. The local copy is the exact same 6,136,204-byte ZIP; it is no longer dependent on GitHub's November 11 expiry. No local executable was launched, and no runner, scheduled task, OS configuration, credentials or user project files were modified.

## What this does and does not satisfy

- **Satisfied:** preservation of one independently audited October 28 ROM-free playtest artifact on the authorized Windows machine, with exact outer/inner/PE digests and a stable local destination.
- **Still outstanding:** actual human H01–H07 physical playtest, real two-pad/display/audio/cold-save/fault journeys, user-visible behavior verdicts and independently accepted Windows release gates. Preserve the release ledger's current 0/12 gates and 0/45 original/native full events unless separately qualified evidence changes them.
- **Source freshness:** the original product source is `250e080...`, while current main has advanced. This copy is historical candidate evidence and a readily testable build, **not** proof that a later main commit has the same executable or that a new build would pass the same acceptance checks.
- **Retention and safety:** do not delete the source GitHub artifact before natural expiry as a storage optimization, do not redistribute protected ROM content, and do not treat nested checksums alone as a malware audit or physical run. The staged ZIP contains no ROM by its vetted evidence contract. Additional archive backups should preserve the same hashes and naming without overwriting foreign files.
