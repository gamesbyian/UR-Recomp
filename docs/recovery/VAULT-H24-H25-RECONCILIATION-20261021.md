# UR-Recomp vault H24/H25 intake and recovery decisions (2026-10-21)

This evidence-only update supplements the [340-item intake](UR-VAULT-INVENTORY-20261020.tsv) and [14-item H23 delta](UR-VAULT-DELTA-H23-20261020.tsv). The [new 25-item ID ledger](UR-VAULT-DELTA-H24-H25-20261021.tsv) brings the **static** Drive folder census to **379 top-level records** at the listed checkpoint. Hourly recovery agents may add more. Original files remain in Drive.

## Independently inspected recent archives

All five ZIPs were downloaded through the Drive connector and independently examined as raw bytes. Each passed `ZipFile.testzip()`, with zero duplicate member names. A full member-manifest check verified SHA-256 and byte length against every declared payload for four archives:

| Archive | Drive file ID | Outer SHA-256 | ZIP entries | Full manifest |
| --- | --- | --- | ---: | --- |
| Agent 3 H24 | `1AxrMLv7qUGYLiAPbgkn0wsuxqwHlCxhi` | `5554f6e75a0c00a846aa7c2564f0f10f19ab627330459264671b4c1674fbab44` | 50 | 49/49, no missing/extras/mismatches |
| Agent 4 H24 | `1AX0Q-Q57pxWK9QXpIFEXl1Ez3scSy0-4` | `c1d2b54f5f57999ab2e3038af1ae75228c4af9acd3f3412f51e0043e14b63301` | 51 | 50/50, no missing/extras/mismatches |
| Agent 5 H24 | `1Wl1_7CUaS47jrknqvGT1hNWmP4_EgrpY` | `5ff045513ab574569d19849e524efa30305cbfbdb827c4d55f675495af155906` | 27 | **No recognized exhaustive SHA-256 member inventory**; CRC only |
| Agent 2 H25 | `1bDrN1y5McDgrwIV4dSUe7x0GNGhcCait` | `eecc4d72fb55b0b2611828107d31b756e05609997279722b771eefa6e3af2c22` | 24 | 23/23, no missing/extras/mismatches |
| Agent 1 H25 | `1bwyXOq-J87Dw6-f-1bbAH3chAV_TQ1VR` | `d3837a2beaa7e83f3d98d0bfb2de68b331a8e504df9ecbb3eb247f632f6e4ee5` | 60 | 59/59, no missing/extras/mismatches |

Agent 5 H24 contains a `MANIFEST.json` describing patch provenance and tests rather than all ZIP payloads. Its lack of an exhaustive member digest map is **not** a corrupt-ZIP verdict, nor permission to discard its negative tests.

## Integration and evidence outcomes

- **Merged:** orphan Modern text overflow guard and boundary tests [#2072](https://github.com/gamesbyian/UR-Recomp/pull/2072), following green tooling, native boot, Modern heavy and hosted Windows workflows. Source now uses checked arithmetic before narrowing into signed 32-bit coordinates.
- **Merged earlier this recovery:** independent 342-wide OBJ depth research verifier and synthetic tests [#2071](https://github.com/gamesbyian/UR-Recomp/pull/2071), original 2014 Dragster source-bound trace record and tests [#2073](https://github.com/gamesbyian/UR-Recomp/pull/2073), and the canonical marshal cross-reference spelling out different-input limitations [#2074](https://github.com/gamesbyian/UR-Recomp/pull/2074). None is renderer/art approval or original/native event parity.
- **Recovered as already integrated:** local multiplayer browser .cpp/.hpp, native and Python tests from `agent/records-multiplayer-browser-host` were individually checked: every historical line appears in order in current `main`, which adds bounded visible-row tests. The historical experimental tournament command ABI is superseded by the Modern player-visible tournament panel using minted tournament/attempt IDs, coordinator scheduling and bounded read-only overview/fixture/standings APIs. Do not reintroduce old handlers.
- **Windows Records #2060:** workflow export-path recovery and direct path-regression tests passed current PR-head CI. It remains open for conservative Win32 naming safeguards, merge-tree qualification and independent physical tests. Passing PR-head workflows are not same as a clean-main merged release candidate.
- **Held / source publication explicitly rejected:** QA08 cumulative chronological/per-frame palette/RGB555 guards, QA04 path race and Unicode controls, exporter source-name controls, P2P SQLite anchor and capture/QA06 pilots. Source proposals and synthetic tests are retained in the vault. Do not retry rejected publication through a disguised or alternate route.
- **Issue decisions:** [#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075) records Win32-unsafe ZIP names admitted by the strict portable vault verifier; [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076) records a QA04 symlink-swap race between `safe_member` preflight and independent reopening. Neither issue claims an actual exploited Windows machine or grants a QA gate.
- **QA01 NMI and snapshots:** recovered sparse RF081 cross-stage memory results remain evidence for where to probe, not a complete same-input original/native event; H25 proposes narrower NMI record lexical constraints and next sampling intervals. No USA event credit.

## Retention policy

**No Drive files deleted.** A matching ZIP/member SHA proves byte identity, not that every source, negative result, historical reference and policy denial has been superseded. Deletion requires a closed per-Drive-ID disposition, independent exact content verification, resolution of unique provenance/failed experiments and confirmation that an authoritative copy is retained. Historical denied writes and standalone source patches remain explicitly on hold. Avoid copying large raw native captures, ROM bytes, unlicensed assets or research dumps into GitHub.
