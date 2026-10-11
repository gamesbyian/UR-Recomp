#!/usr/bin/env python3
"""R0 only: static native P2P seam inventory. No sockets, emulation or approval.

This script validates that the implementation points cited by the P2P R0
research inventory are still present at checkout. A PASS is merely a source
cross-reference check, NOT deterministic replay, a multiplayer connection,
or an acceptance result. Use existing native guest tests for execution proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Every item is a concrete on-disk source contract, not a promised future API.
# Keep zero dependencies and no automatic workflow trigger.
CHECKS = [
  [
    "guest_input",
    "tools/baldosa_native_product_execution.cpp",
    [
      "ur_baldosa_product_filter_human_frame_inputs",
      "g_input.filter(word)",
      "g_pending_stock_menu_mask",
      "ur_baldosa_product_set_host_focus"
    ],
    "source-mapped local input and one-frame stock-menu pulse; no remote input arbiter"
  ],
  [
    "human_word_layout",
    "native/product/baldosa_execution_backend.hpp",
    [
      "0x0fffu",
      "seat * 12",
      "word & ~0x00ffffffu",
      "modern_host_input_filter"
    ],
    "12-bit P1/P2 mapped masks plus separate framework presence bits"
  ],
  [
    "stock_two_player",
    "tools/baldosa_native_modern_root.cpp",
    [
      "ur_baldosa_modern_root_source_bound_2p_profiles",
      "g_two_seat_join.ready()",
      "g_stock_handed_off",
      "g_handed_off_players != 2u",
      "0x3du"
    ],
    "source-confirmed ordinary stock 2P entry and optional two-name binding"
  ],
  [
    "post_guest_observer",
    "tools/baldosa_native_pause_lifecycle.cpp",
    [
      "ur_baldosa_product_after_run_frame",
      "stats->resolved_controller_word",
      "g_native_result_observer.observe",
      "ur_baldosa_modern_publish_settled_two_player_match"
    ],
    "post-execution 2P result capture and canonical records path, not an input injection seam"
  ],
  [
    "restart_snapshot",
    "tools/baldosa_native_pause_lifecycle.cpp",
    [
      "RtlRollbackSnapshotBound()",
      "RtlRollbackSaveToMemory",
      "RtlRollbackLoadFromMemory",
      "ur_modern_session_load_preserving_persistent_bytes"
    ],
    "real restart-anchor save/load with preserved persistent SRAM; no demonstrated arbitrary-frame rollback"
  ],
  [
    "source_result",
    "native/product/baldosa_guest_result_observer.cpp",
    [
      "kOrdinaryTwoPlayerRaceResultMenu",
      "observe_ordinary_two_player_race_result",
      "captured_input_frames_++",
      "BaldosaSettledResultKind::OrdinaryTwoPlayerRace"
    ],
    "authentic 2P terminal result and mapped input-run capture"
  ],
  [
    "record_input_schema",
    "native/product/completed_run_record.hpp",
    [
      "struct RunRecordInputRun",
      "std::uint16_t p1_mask",
      "std::uint16_t p2_mask",
      "std::uint64_t start_frame"
    ],
    "p1/p2 archival RLE inputs are not a live wire format"
  ],
  [
    "profile_sram",
    "native/product/host_profile_state.hpp",
    [
      "kStockSramBytes = 8192",
      "std::optional<std::array<std::uint8_t, kStockSramBytes>> stock_sram"
    ],
    "exact cartridge SRAM lives in typed profile snapshot"
  ],
  [
    "imported_web_lockstep",
    "reference/imported/reverse-engineering/baldosa-uniracers-recomp/src/web_netplay.c",
    [
      "kDelay = 3",
      "kRing = 64",
      "kCrcEvery = 120",
      "WebNetplayFilterInputs",
      "web_net_recv_pad"
    ],
    "historical three-frame web lockstep and WRAM-only CRC example; not desktop proof"
  ],
  [
    "imported_broker",
    "reference/imported/reverse-engineering/baldosa-uniracers-recomp/web/netplay.js",
    [
      "new Peer(PREFIX + code)",
      "new Peer()",
      "peer.connect("
    ],
    "imported PeerJS lobby requires external signalling; cannot ship as required infrastructure"
  ],
  [
    "network_denial_reuse",
    "tools/audit_network_trace.py",
    [
      "NETWORK_CALL",
      "--require-none",
      "inet_attempt_count"
    ],
    "existing outbound traffic trace audit can be reused in future zero-service tests"
  ]
]

def inspect(root: Path) -> dict:
    items = []
    for key, relative, anchors, interpretation in CHECKS:
        path = root / relative
        if not path.is_file():
            items.append({"id": key, "path": relative, "present": False,
                          "missing": anchors, "interpretation": interpretation})
            continue
        source = path.read_text(encoding="utf-8")
        missing = [anchor for anchor in anchors if anchor not in source]
        items.append({"id": key, "path": relative, "present": True,
                      "missing": missing, "interpretation": interpretation})
    return {
        "schema_version": 1, "status": "STATIC_SOURCE_AUDIT_ONLY",
        "no_network_or_simulation_executed": True,
        "all_anchors_present": all(x["present"] and not x["missing"] for x in items),
        "checks": items,
        "unverified": [
            "cross_process_full_state_determinism",
            "arbitrary_frame_rollback_without_side_effects",
            "cross_platform_win_mac_guest_parity",
            "nat_traversal_or_permissionless_peer_discovery",
            "actual_online_paired_records"
        ],
    }

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    report = inspect(args.root)
    result = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(result, end="")
    if args.json_out:
        args.json_out.write_text(result, encoding="utf-8")
    return 0 if report["all_anchors_present"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
