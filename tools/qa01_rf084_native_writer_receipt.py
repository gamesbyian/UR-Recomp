#!/usr/bin/env python3
"""RF084: validate bounded *executed native* sound writer rows, not parity.

Consumes the already-retained replay/native.log from one genuine Zoo case.
No guest execution, source edits, input replay, or event/release admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROW = re.compile(
    r"^QA01RF084NATIVE seq=(\d+) site=([0-9A-F]{6}) width=([12]) "
    r"variant=M1X0 f=(\d+) D=([0-9A-F]{4}) addr=([0-9A-F]{4}) "
    r"old=([0-9A-F]{4}) supplied=([0-9A-F]{4}) "
    r"rawAfter=([0-9A-F]{4}) native_master=(\d+)$"
)
SITES = {"8280E0": (1, 0x69), "828154": (2, 0x63)}
ORIG_ROW = re.compile(
    r"^QA01RF083ORIG seq=(\d+) type=(opcode_delta|setter_entry) frame=(\d+) "
    r"pc=([0-9A-F]{6}) op=([0-9A-F]{2}) pre_v=(\d+) pre_h=(-?\d+) "
    r"post_v=(\d+) post_h=(-?\d+) slot=([0-9A-F]{4}) "
    r"old=([0-9A-F]{2}) new=([0-9A-F]{2}) setterCount=(\d+) "
    r"setterAddr=([0-9A-F]{6,8}) setterVal=([0-9A-F]{2}) clock=original_cpu$"
)
ORIG_HEART = re.compile(r"^QA01RF083ORIG_HEART frame=(\d+) v=(\d+) h=(-?\d+)$")
ORIG_WORD = re.compile(
    r"^QA01RF083ORIG_WORD seq=(\d+) frame=(\d+) pc=828154 "
    r"addr=([0-9A-F]{6}) word=([0-9A-F]{4}) wrap=(\d+) "
    r"order=(\d+) rawBefore=([0-9A-F]{4})$"
)


ORIG_INC16 = re.compile(
    r"^QA01RF083ORIG_INC16 seq=(\d+) frame=(\d+) pc=828154 "
    r"addr=([0-9A-F]{6}) wrap=(\d+) old=([0-9A-F]{4}) "
    r"supplied=([0-9A-F]{4}) rawAfter=([0-9A-F]{4})$"
)


def audit(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="strict")
    lines = text.splitlines()
    if any("QA01RF084NATIVE_TRUNCATED" in line for line in lines):
        raise ValueError("RF084 native writer stream truncated")
    rows = []
    counts = {site: 0 for site in SITES}
    for line in lines:
        if not line.startswith("QA01RF084NATIVE"):
            continue
        match = ROW.fullmatch(line)
        if not match:
            raise ValueError("malformed RF084 native writer row")
        seq, site, width, frame, d, addr, old, supplied, after, master = match.groups()
        seq, width, frame, master = map(int, (seq, width, frame, master))
        d, addr, old, supplied, after = (int(x, 16) for x in (d, addr, old, supplied, after))
        if site not in SITES or (width, (addr - d) & 0xFFFF) != SITES[site]:
            raise ValueError("RF084 native writer site/width/effective DP address mismatch")
        if seq != len(rows) + 1 or not 6054 <= frame <= 6068:
            raise ValueError("RF084 native writer sequence/frame out of bounds")
        if rows and (frame < rows[-1]["frame"] or
                     (frame == rows[-1]["frame"] and master < rows[-1]["master"])):
            raise ValueError("RF084 native writer chronology reversed")
        if width == 1 and (old > 0xFF or supplied > 0xFF or after > 0xFF):
            raise ValueError("RF084 8-bit native writer values exceed byte width")
        rows.append({"seq": seq, "site": site, "width": width, "frame": frame,
                     "master": master, "raw_after_matches_supplied": after == supplied})
        counts[site] += 1
    if not rows or any(not count for count in counts.values()):
        raise ValueError("RF084 actual native 8-bit AND 16-bit writer executions required")
    if len(rows) > 10000:
        raise ValueError("RF084 native writer row budget exceeded")
    return {
        "schema_version": 1,
        "work_id": "UR-CPU-CAUSE-20261026",
        "scope": "one executed native Zoo writer stream; not original/native parity",
        "native_log_sha256": hashlib.sha256(raw).hexdigest(),
        "native_writer_events": len(rows),
        "site_counts": counts,
        "first_frame": rows[0]["frame"],
        "last_frame": rows[-1]["frame"],
        "first_event": rows[0],
        "last_event": rows[-1],
        "raw_after_mismatch_count": sum(not row["raw_after_matches_supplied"] for row in rows),
        "native_execution_proven": True,
        "original_native_parity_proven": False,
        "release_credit": 0,
    }


def audit_original(raw: bytes) -> dict:
    lines = raw.decode("utf-8", errors="strict").splitlines()
    if any(("QA01RF083ORIG_TRUNCATED" in line or
            "QA01RF083ORIG_WORD_TRUNCATED" in line or
            "QA01RF083ORIG_INC16_TRUNCATED" in line) for line in lines):
        raise ValueError("RF083 original writer stream truncated")
    hearts = []
    count = 0
    word_count = 0
    inc16_count = 0
    sites = {"8280E0/0069": 0, "828154/0063": 0}
    for line in lines:
        if line.startswith("QA01RF083ORIG_HEART"):
            match = ORIG_HEART.fullmatch(line)
            if not match:
                raise ValueError("malformed RF083 original heartbeat")
            hearts.append(int(match.group(1)))
        elif line.startswith("QA01RF083ORIG_INC16 "):
            match = ORIG_INC16.fullmatch(line)
            if not match:
                raise ValueError("malformed RF083 original INC16 post-write witness")
            seq, frame, addr, wrap, old, supplied, after = match.groups()
            inc16_count += 1
            if (int(seq) != inc16_count or not 6069 <= int(frame) <= 6079 or
                int(addr, 16) & 0xFFFF != 0x0063 or int(wrap) > 2 or
                int(supplied, 16) != ((int(old, 16) + 1) & 0xFFFF) or
                supplied != after):
                raise ValueError("RF083 original INC16 writer/commit mismatch")
        elif line.startswith("QA01RF083ORIG_WORD"):
            match = ORIG_WORD.fullmatch(line)
            if not match:
                raise ValueError("malformed RF083 original word-setter entry")
            seq, frame, addr, _word, wrap, order, _before = match.groups()
            word_count += 1
            if (int(seq) != word_count or not 6069 <= int(frame) <= 6079 or
                int(addr, 16) & 0xFFFF != 0x0063 or
                int(wrap) > 2 or int(order) > 1):
                raise ValueError("RF083 original word-setter identity/sequence invalid")
        elif line.startswith("QA01RF083ORIG "):
            match = ORIG_ROW.fullmatch(line)
            if not match:
                raise ValueError("malformed RF083 original writer row")
            seq, kind, frame, pc, opcode, *rest = match.groups()
            count += 1
            if int(seq) != count or not 6069 <= int(frame) <= 6079:
                raise ValueError("RF083 original writer sequence/frame out of bounds")
            slot = rest[4]
            key = f"{pc}/{slot}"
            if kind == "opcode_delta" and key in sites:
                if opcode != "E6":
                    raise ValueError("RF083 original sound increment opcode changed")
                # The RF083 producer emits opcode_delta only after an actual
                # byte change. Reject a syntactically plausible no-op receipt.
                if rest[5] == rest[6]:
                    raise ValueError("RF083 original opcode_delta has unchanged byte")
                sites[key] += 1
    if (hearts != list(range(6069, 6080)) or not count or
        not (word_count or inc16_count) or not all(sites.values())):
        raise ValueError("RF083 original internal-frame/actual opcode coverage incomplete")
    return {"original_log_sha256": hashlib.sha256(raw).hexdigest(),
            "original_heartbeats": hearts, "original_writer_rows": count,
            "original_word_setter_entries": word_count,
            "original_inc16_committed_rows": inc16_count,
            "original_inc16_postwrite_proven": inc16_count > 0,
            "original_word_entry_not_commit": True,
            "original_increment_site_counts": sites,
            "original_opcode_execution_proven": True,
            "native_clock_registration_proven": False,
            "release_credit": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-log", type=Path, required=True)
    parser.add_argument("--native-log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.native_log.is_file() or args.native_log.is_symlink():
        parser.error("real replay native log absent or symlinked")
    if not args.original_log.is_file() or args.original_log.is_symlink():
        parser.error("real replay original log absent or symlinked")
    report = audit(args.native_log.read_bytes())
    report.update(audit_original(args.original_log.read_bytes()))
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QA01_RF084_NATIVE_WRITER_RECEIPT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
