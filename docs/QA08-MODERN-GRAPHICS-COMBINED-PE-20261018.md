# Graphics and Modern combined native Windows source qualification
18 October 2026 | disposable integration branch, **not a release build**

This candidate inherits exact Modern SRAM transaction/crash-recovery
[#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) source
`b9165d23437316dbfce0701f9ce5a237ad03bed0` and the six-file clean HDMA first-line + V0-before-HDMA
graphics candidate [#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780)
at `4cfede2f04d9ad48c6e6cd5e74fc31922a5a6280`. It modifies **zero Modern product/SRAM code lines**,
and keeps every line of the exact original **1330-line Modern Windows
bridge workflow** unchanged and in order, adding 14 graphics lines
(4 trigger paths, 2 unit checks, 8 scoped stage lines) after full
RF017 generated-game clock verification, before native Windows PE compile.

The PPU changes remain Uniracers title-scoped and pinned to the existing
Baldosa `10b864b9...` and SNESRecomp `075fbe4c...` git commits;
no universal emulator modifications are made. Full CPU/APU cycles,
guest simulation, input and native SRAM/typed persistence remain the
owner branch's responsibility. No experimental #1807 pre-math
colour fix, #1819/#1820 read-only diagnostics, HD racer art or
QA release-ledger changes enter this PE.

**Independent source evidence:** Merged #1821 demonstrates six actual
current RF017 CPU CGRAM palette packets agreeing with genuine 2014
Snes9x source; four packet pairs lead the original writer label by
two native fields, which does not establish CPU/NMI causal equivalence.
Merged #1822 preserves a genuine 263-frame, 256x224 compiled Windows
source archive from the clean production renderer with zero changed
pixels versus previously archived clean RF017 baseline; the
**890,205 remaining wrong RGB5 original/native pixels** in these 263
sampled frames remain open. The new combined PE is not that earlier
source observer executable and inherits *no* full-result pixel approval.

**Decisive test:** Compile and exercise the actual combined AMD64 PE,
Windows player-operated Modern SRAM fault/recovery journeys, 1P/2P
original routes/guest CRC checks and ROM-free portable ZIP with
exact SHA-bound source identity. Qualify only the tested facts; this
does not establish physical 3840x2160, all 342x224 HD art, human
visual approval, complete original USA course event, or final
independent release. Those still require independent QA adjudication.

**Disposition:** Keep as a DRAFT nonshipping integration rehearsal.
After QA identifies the exact source-specific fixes needed, integrate
the graphics correction separately into accepted main while preserving
Modern owners' latest transaction source and independently auditing the
final candidate, rather than merging this snapshot wholesale. If
Modern's head changes, do not treat this historical test as a new-head
certification. No ongoing speculative CI factory.
