# RF082 H18: width-aware post-RTS-marker read-footprint correction

Status: **independent QA HOLD, 0/45 complete USA events**, no ledger edit.
Source case: RF081 archive SHA256 `df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37`.
Original log SHA256 `0a40d15a06bdbfdbee0a38588c239131216709910e6035fa5a94265e49b778`;
native log SHA256 `6297007499e8684ba0348a602243b4fa25d80d3983290ec15d72f132e4cdbceb`.

## Corrected source interpretation

The H17 census accurately reported **zero reads whose *starting address* was
01F2 or 01F3** in its bounded three-read windows. However, a native `width=2`
read beginning at `00:01F1` has a byte footprint covering `01F1` and `01F2`.
Thus "no starting-address 01F2 read" does **not** establish "no observed byte
access to 01F2." H18's independent `qa01_rf081_read_footprint.py` enumerates
source-local byte footprints and labels any overlap as a **generic** read only.

For source host label 1017, after native decoded RTS marker ordinal 15 at
master 363394906, generic native reads begin at 01ED (width 2), 01EF
(width 2), 01F1 (width 2). For label 1018, after marker ordinal 13241 at
master 363752260, they begin at 01EF (width 2), 01F1 (width 2), 01EF
(width 1). In both cases the generic 01F1 width-2 read overlaps byte 01F2;
none of these rows is dynamically attributed to the RTS instruction, and
no corresponding 01F3 footprint appears in these three-read windows.

**No RTS return-target calculation or cross-source clock equivalence follows.**
The actual original fetched PC and native AOT decoded marker remain different
kinds of evidence. AOT decode does not establish executed native opcode fetch.
The width-2 read value cannot be interpreted as an RTS operand without its
executed instruction identity, stack S before/after, exact bus-read origin,
and native compiled continuation/return-target witness.

## Next smallest producer experiment (CPU owner, not QA agent)

Capture a single source-and-binary-pinned Zoo execution, original actual RTS
fetch PC, original stack reads, native *executed* fetched opcode PC, native
instruction-tagged byte reads for 01F2/01F3, pre/post S, native compiled
continuation and computed return PC. Preserve separate original v/h and native
master clock domains, same input and raw memory before first downstream
consumer. If native RTS is compiled away, explicitly show its generated-source
continuation instead of inventing a bus read. Independent QA checks the
immutable original/native archive and only then re-evaluates event obligations.

## Three-project reuse preflight, scoped

UR: retain `tools/qa01_event_acceptance_readiness.py`, RF081/082 source-local
parsers, and the bounded original/native event census. Baldosa: reuse its
source-side guest trace and first-difference tools only with matching binary
identity; do not import another timing oracle. Malmazuke: reuse its replay
manifest and source-label crosswalk as provenance aids, not USA timing proof.
The Agent 5 H17 source-equivalent register/matrix audit found 14 entries,
35 matrix rows, zero validation errors. **The full repo CLI was not run in
this H18 sandbox**, so that prior audit is cited as recovered evidence rather
than misrepresented as a new CLI execution.

Publication target: independent QA specialist knowledge, not shared
`WORK-QUEUE.md`, producer instrumentation, media, HD character art, or the
release ledger. See H18 test receipt for source SHA and adversarial controls.
