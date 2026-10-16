# Two real Windows executables differ only in linked PE timestamps

**2026-10-15/16 | Independent QA-12 package reproducibility forensic review.** This is a source-bound, **offline byte comparison** of *two genuine, separately retained Windows Actions packages*. It is not a new compile, OS execution, approved beta, release candidate identity change, acceptance witness, or executable modification.

## Original immutable source identity

The first nominated actual former-main owner download comes from [Windows run 38813101482](https://github.com/gamesbyian/UR-Recomp/actions/runs/38813101482), source `11501a15dea38fa912335cfc63103ce3a7208001`, owner artifact `12009612842`, EXE SHA-256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`. It remains the **sole nominated** owner-playtest ZIP, SHA-256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`.

The later [successful actual Win32 PR run 38831297147](https://github.com/gamesbyian/UR-Recomp/actions/runs/38831297147) is a **different** candidate ZIP from original package artifact `12017368467`, tested synthetic merge checkout `173d49e9706fd5b018cd2b8441665fd16769b5cb`, PR head `4a0ce91c8c6bb58375007b3a660718f76cc873f9` (merged implementation #1680). Its exe SHA-256 is `c02d563741d60ef1061562eb31e224e34fae97e5d19b0a0d836ed348661f5fef`. The two SHA values are **not** interchangeable despite the source-bound relationship.

## Direct complete-file byte comparison

Independently extracted the **entire original PE32+ AMD64** executable from each of the original Windows candidate ZIPs. Each is **19,808,768 bytes**. Whole-file comparison finds exactly **four changed bytes**: the lower two bytes in the PE COFF `IMAGE_FILE_HEADER.TimeDateStamp` at file offsets `0x80–0x81`, and the matching lower two bytes of `IMAGE_DEBUG_DIRECTORY.TimeDateStamp` at `0x10B8E04–0x10B8E05`, inside the actual `.buildid` debug section.

The full corresponding four-byte little-endian timestamp fields are `9c4bd16a` (**2026-10-15 21:54:36 UTC**) for the owner build and `7174d16a` (**2026-10-16 00:48:49 UTC**) for the later source PR build; the upper two bytes of each are identical. Identified the debug directory via actual PE optional-header DataDirectory index 6, section RVA-to-file mapping, not a guessed offset.

After zeroing **only these two four-byte timestamp fields in temporary forensic copies**, the entire **19,808,768 bytes** of both copies are identical. The independently computed equal normalized SHA-256 is:

`14da350379b5da2c0a319dde08e0808f6108ec83f3b4c7b1ae75162c648bce5b`

This is a strong bounded **code-content reproducibility observation**, even though the complete original binary hash, original ZIP checksum and source commit are different. It does **not** prove unrelated new source revisions, different toolchains, physical behavior, Windows save durability, sound, graphics, or original-emulator gameplay parity.

## Owner handoff and decision

Integration/release engineering owns whether future Windows packaging should use deterministic linker/build timestamps. Do **not** rewrite, timestamp-normalize, recompress, rename, or republish the *existing* nominated ZIP to manufacture equality. Its **original, unmodified SHA-256 remains the only actual tested candidate identity**. A future changed build must receive its own source/ZIP/EXE hash, complete same-artifact verification and independent QA.

The [machine-readable forensic receipt](../analysis/evidence/qa-windows-owner-vs-1680-pe-timestamp-only-20261015.json) records the precise old/new bytes, original artifact IDs, timestamp offsets and normalized-copy SHA. A separate original Windows launcher artifact review preserves the [two actual non-sensitive generic refusal transcript bytes](../analysis/evidence/qa-win32-rooted-relative-pr1680-independent-20261015.json) rather than losing them on the October 23 Actions expiry; they still do not independently encode exit 3 or input root.

**Release acceptance unchanged:** 0/12 gate witnesses, 0/45 complete USA original/native events, QA-12 unverified, hardware unverified, `release_decision=not_assessed`, and P0 crash-consistency [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) remains open. Three-project reuse: existing UR candidate-evidence envelope and separately pinned Baldosa Win32 hosted build; no new build, runner, test farm or production compilation policy is implemented here.
