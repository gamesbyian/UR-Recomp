# Independent actual Windows CMD recovery-Q evidence, October 17, 2026

**Disposition:** bounded hosted Windows **Q-only positive** on exact PR-merge source; **not** a merged-main release candidate, a human R/T/S/Q acceptance, electrical power-loss test, physical controller/audio/UHD witness, or an accepted QA-02 gate. Original nominated owner source `11501a15dea38fa912335cfc63103ce3a7208001` / ZIP `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` remain unchanged. Ledger **0/12**, USA full events **0/45**.

## Actual qualifying execution and original bytes

- [Modern draft #1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) HEAD `995b472491a03989d02e478bfa4af167f3da8fd3`; fully green genuine [Win32 run 39064195415](https://github.com/gamesbyian/UR-Recomp/actions/runs/39064195415). Verified tested PR-merge `d0ea4d8dad8c8b96e9653cd1dadcdbd35e9505ed`, parents then-main `a26a741d20a66b48af452142397d506eedf67ee0` + exact Modern HEAD.
- Original Q Actions artifact **12112648233**, outer SHA256 `ac6a5df894fe3f3142771ad19c4c1db3cb2b0aaffebf1a5bf14d1b73627b31fd`: precisely 12 ZIP members, CRC-clean, eight complete original before/after binary copies and SHA/length receipts. Real Windows CMD printed one genuine R/T/S/Q recovery prompt; the separate actual Win32 `AttachConsole`/`WriteConsoleInputW` injector logged exit **0** and original transcript ends with **Q**; product CMD reports exit **7**, no guest boot or fallback.
- Independently decoded v5 `host-profile.txt`'s original 8,192-byte `stock_sram` hex, verifying exact 8,192-byte raw save with matching original header but **one changed byte**: a legitimate unjournaled full-length mismatch was created. Original raw, typed, selector and catalog bytes were **bit-identical before and after Q**, not merely normalized metadata. No manual recovery archive or attempted new progression was reported.
- Separate same-run original candidate artifact **12112747854** outer SHA256 `f425084a22a8ee8dfa6c4e681a088df08d5e11df772a20c8b8acdab01570e51a`, contained ROM-free ZIP SHA256 `5d95c202c733c1b623888036317f368481087c6bfe9040b379da3355a54b3142`, actual 20,327,424-byte PE32+ AMD64 SHA256 `7f18542ef8bfbfa2bf4dd9c68c37bac0d263bab1c55e9b9e1f52bcd158a96fc0` and original launcher CMD SHA256 `b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3`. Original separate binding **12112658129** matched tested source, immutable PE/ZIP and CMD; Q result reported precisely that CMD hash.
- On this *same tested source*, separately downloaded and SHA/CRC-verified packaged save-denial original **12112837630**: independently rehashed **22 binary source snapshots**, actual raw guest image changed **74 bytes**, old typed state persisted until restart recovery, selector/catalog remained unchanged, two cold snapshots stable; real NTFS typed-CAS sharing-denied native exit **8**. Original post-save selector contention **12112593687**: **24 original binary snapshots**, old Mike raw+typed save committed, unrelated Andrew unchanged, independent other-process selector publication then native exit **9** without rolling back saved Mike. The exit-9 scenario was **native** rather than executed via CMD; do not conflate its checked CMD branch with an operator-tested exit-9 launcher.
- Both preceding *red* Q sources are preserved as actual negatives: initial extracted CMD `<CONIN$` access-denied path and subsequent `AttachConsole` WinError 5 caused no Q injection and **no after-Q original bytes**. Do not call either a product recovery failure or a Q pass.

## Offline independent replay

```sh
python tools/check_qa02_win32_interactive_q_original.py \
  --zip <original-12112648233.zip> \
  --sha256 ac6a5df894fe3f3142771ad19c4c1db3cb2b0aaffebf1a5bf14d1b73627b31fd \
  --cmd-sha256 b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3
```

The read-only consumer refuses missing/added members, altered original binary snapshots or receipts, improper raw/typed mismatch, synthetic or missing Q source report, rejected console injection, failed CMD prompt and wrong external artifact/launcher SHA. Tests include actual Win32 CRLF transcript formatting and negative mutation controls. No personal ROM, SRAM or player files are published.

**Next P0 acceptance work:** independently test player choice **R/T/S** on the same fully extracted executable with exact archive-before-mutate and cold-restored canonical data, genuine NTFS full/short I/O and cross-process competition, then an integrated *merged-main* exact PE+ROM-free ZIP and physical two-gamepad/audio/real UHD/user-abort procedure. Q-only original console injection is a bounded hosted subtest, not proof that any human physically operated the packaged game. Leave Modern #1713 draft and #1214/#1751 open until independent release readiness is earned.
