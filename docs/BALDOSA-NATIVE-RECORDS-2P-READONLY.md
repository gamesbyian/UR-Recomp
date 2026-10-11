# Baldosa native Records: selected-profile ordinary-2P history

**Status:** product integration only. Neither native 2P result publishing nor
a complete player journey/independently admitted original event is implied.

## One existing archive and Records route

The Baldosa Modern root already provides a physically navigable **Records**
destination for read-only, named-profile historical 1P .urrun inspection.
That same modal now accepts P1 Up/Down to switch between **STORED RUNS** (1P)
and **TWO PLAYER RECORDS**, and B/Escape or Confirm returns to the existing
root without touching the guest. Anonymous roots explicitly remain
unattributed. The old Modern host's painter retains its prior default
records footer and view.

The 2P subview reads **only** the existing shared
`<modern-user-root>/multiplayer-runs` namespace and the verified native
selected profile ID. It reuses
`multiplayer_match_catalog` plus `multiplayer_match_summary`, and displays
the selected profile's validated match count and W/L/D. Only checksum- and
course-bound `race-2p` .urrun/.urmatch pairs count; wrong-mode, incomplete,
corrupt, mismatched and absent sidecars never count as a win or loss. Other
profile matches are not attributed to the selected racer. A missing
first-run archive is an empty history, but any symlinked/dangling archive
directory is refused. The native Records modal creates **no** run, sidecar
or opponent identities.

The existing Baldosa stage links the established codecs/aggregator once,
not an additional emulator, per-profile match directory, identity mapper
or storage grammar. A small adapter filters the canonical admitted pairs;
it has no write functions.

## Boundaries and acceptance

- C++ unit: `tests/unit/test_baldosa_native_multiplayer_records_cpp.py`
  constructs canonical isolated match pairs using the existing writer,
  verifies selected-player W/L/D, missing sidecars, wrong modes, unrelated
  identity, and directory symlink refusal. This is a synthetic store
  regression, **not** a played 2P match.
- Presenter: `tests/native/modern_root_overlay_presenter_test.cpp` checks
  1P/2P labels, pad navigation hints and old-client presentation defaults.
- Existing real native Win32 named-profile root smoke now dispatches Down
  and Up while Records is open, requires an actual empty 2P archive report
  and then enters the original stock 1P menu. This proves modal navigation
  and read-only consumption, not actual 2P match publication.
- Next blocker: verified 2P participant identities and native source-result
  to canonical paired `.urrun/.urmatch` publication, followed by a fresh
  Windows process reading that **newly played** pair. This work must reuse
  the independent local 2P join and the exact original stock rider indices,
  never synthesize a P2 profile from gamepad seat ownership.

Release ledger and QA-01/03/09/11 remain independently authoritative.
