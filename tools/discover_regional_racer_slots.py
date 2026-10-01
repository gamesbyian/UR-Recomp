#!/usr/bin/env python3
"""Recover regional P1/P2 persistent racer slots from bidirectional marshal edges.

Race_UpdateRacersFrame marshals one persistent racer record at a time into shared
current-player working state, simulates it, then writes the result back. This
tool discovers persistent slots that participate in BOTH directions instead of
assuming fixed regional address deltas.
"""
from __future__ import annotations

from pathlib import Path
import json

try:
    from tools.compare_semantic_anchors import ROMS, cpu_to_lorom_file, file_to_lorom_cpu
except ModuleNotFoundError:
    from compare_semantic_anchors import ROMS, cpu_to_lorom_file, file_to_lorom_cpu

OUT_JSON = Path("analysis/generated/regional-racer-slot-discovery.json")
OUT_MD = Path("analysis/generated/regional-racer-slot-discovery.md")

BUILDS = {
    "usa-retail": {
        "routine": "82:89B9", "x_work": 0x0F9F, "y_work": 0x0FA1, "boost_work": 0x11CD,
        "p1": {"xpos": 0x0411, "ypos": 0x0415, "xspeed": 0x04B7, "yspeed": 0x04BB, "boost": 0x11CF},
    },
    "pal-prototype-1994-11-29": {
        "routine": "82:89B6", "x_work": 0x0FA3, "y_work": 0x0FA5, "boost_work": 0x11D1,
        "p1": {"xpos": 0x0411, "ypos": 0x0415, "xspeed": 0x04B7, "yspeed": 0x04BB, "boost": 0x11D3},
    },
    "europe-retail": {
        "routine": "82:89CC", "x_work": 0x0FA9, "y_work": 0x0FAB, "boost_work": 0x11D7,
        "p1": {"xpos": 0x0415, "ypos": 0x0419, "xspeed": 0x04BB, "yspeed": 0x04BF, "boost": 0x11D9},
    },
}


def le16(value: int) -> bytes:
    return bytes((value & 0xFF, value >> 8))


def starts(region: bytes, pattern: bytes) -> list[int]:
    out=[]
    p=region.find(pattern)
    while p >= 0:
        out.append(p)
        p=region.find(pattern,p+1)
    return out


def discover_abs_y_pairs(region: bytes, working: int) -> dict[int, dict]:
    # LDY abs persistent; STY abs working  <->  LDY abs working; STY abs persistent
    w=le16(working)
    inbound={}
    outbound={}
    for p in range(len(region)-5):
        if region[p] == 0xAC and region[p+3] == 0x8C and region[p+4:p+6] == w:
            persistent=int.from_bytes(region[p+1:p+3], 'little')
            inbound.setdefault(persistent, []).append(p)
        if region[p] == 0xAC and region[p+1:p+3] == w and region[p+3] == 0x8C:
            persistent=int.from_bytes(region[p+4:p+6], 'little')
            outbound.setdefault(persistent, []).append(p)
    return {
        addr: {'in': inbound.get(addr, []), 'out': outbound.get(addr, [])}
        for addr in sorted(set(inbound) | set(outbound))
        if inbound.get(addr) and outbound.get(addr)
    }


def discover_abs_a_pairs(region: bytes, working: int) -> dict[int, dict]:
    # LDA abs persistent; STA abs working  <->  LDA abs working; STA abs persistent
    w=le16(working)
    inbound={}
    outbound={}
    for p in range(len(region)-5):
        if region[p] == 0xAD and region[p+3] == 0x8D and region[p+4:p+6] == w:
            persistent=int.from_bytes(region[p+1:p+3], 'little')
            inbound.setdefault(persistent, []).append(p)
        if region[p] == 0xAD and region[p+1:p+3] == w and region[p+3] == 0x8D:
            persistent=int.from_bytes(region[p+4:p+6], 'little')
            outbound.setdefault(persistent, []).append(p)
    return {
        addr: {'in': inbound.get(addr, []), 'out': outbound.get(addr, [])}
        for addr in sorted(set(inbound) | set(outbound))
        if inbound.get(addr) and outbound.get(addr)
    }


def discover_dp_y_pairs(region: bytes, dp: int) -> dict[int, dict]:
    # LDY abs persistent; STY dp  <->  LDY dp; STY abs persistent
    inbound={}
    outbound={}
    for p in range(len(region)-4):
        if region[p] == 0xAC and region[p+3] == 0x84 and region[p+4] == dp:
            persistent=int.from_bytes(region[p+1:p+3], 'little')
            inbound.setdefault(persistent, []).append(p)
        if region[p] == 0xA4 and region[p+1] == dp and region[p+2] == 0x8C:
            persistent=int.from_bytes(region[p+3:p+5], 'little')
            outbound.setdefault(persistent, []).append(p)
    return {
        addr: {'in': inbound.get(addr, []), 'out': outbound.get(addr, [])}
        for addr in sorted(set(inbound) | set(outbound))
        if inbound.get(addr) and outbound.get(addr)
    }


def decorate(pairs: dict[int,dict], base: int) -> list[dict]:
    return [
        {
            "persistent": f"7E:{addr:04X}",
            "copy_in": [file_to_lorom_cpu(base+p) for p in hit["in"]],
            "copy_out": [file_to_lorom_cpu(base+p) for p in hit["out"]],
        }
        for addr,hit in pairs.items()
    ]


def inspect_build(blob: bytes, spec: dict) -> dict:
    base=cpu_to_lorom_file(spec['routine'])
    region=blob[base:base+0xA00]
    fields={
        'xpos': decorate(discover_dp_y_pairs(region, 0xA5), base),
        'ypos': decorate(discover_dp_y_pairs(region, 0xA7), base),
        'xspeed': decorate(discover_abs_y_pairs(region, spec['x_work']), base),
        'yspeed': decorate(discover_abs_y_pairs(region, spec['y_work']), base),
        'boost': decorate(
            {
                **discover_abs_y_pairs(region, spec['boost_work']),
                **discover_abs_a_pairs(region, spec['boost_work']),
            },
            base,
        ),
    }
    assignment={}
    for name, rows in fields.items():
        p1=f"7E:{spec['p1'][name]:04X}"
        addresses=[r['persistent'] for r in rows]
        others=[a for a in addresses if a != p1]
        assignment[name]={
            'p1': p1,
            'p1_present': p1 in addresses,
            'p2_candidates': others,
            'exact_pair': p1 in addresses and len(others) == 1 and len(addresses) == 2,
        }
    return {
        'routine': spec['routine'],
        'fields': fields,
        'assignment': assignment,
        'all_exact_pairs': all(x['exact_pair'] for x in assignment.values()),
    }


def build_report() -> dict:
    blobs={name:path.read_bytes() for name,path in ROMS.items()}
    return {
        'schema_version': 1,
        'method': 'bidirectional persistent/current-player marshal and writeback edge discovery',
        'builds': {name:inspect_build(blobs[name],spec) for name,spec in BUILDS.items()},
    }


def render_md(r: dict) -> str:
    lines=[
        "# Regional racer persistent-slot discovery",
        "",
        "Each row is recovered from bidirectional copy edges in the matched racer-update routine. The P2 address is the unique second persistent slot paired with the same shared working state after the already-confirmed P1 slot is identified.",
        "",
        "| Build | Field | P1 | P2 recovered | Exact two-slot relation |",
        "|---|---|---|---|---|",
    ]
    for build,b in r['builds'].items():
        for name,a in b['assignment'].items():
            p2=', '.join(f'`{x}`' for x in a['p2_candidates']) or '-'
            lines.append(f"| {build} | {name} | `{a['p1']}` | {p2} | {'yes' if a['exact_pair'] else 'no'} |")
    lines += ['', 'This verifies structure membership and P1/P2 pairing, not equality of physics values between builds.', '']
    return '\n'.join(lines)


def main() -> int:
    r=build_report()
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
    OUT_JSON.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    OUT_MD.write_text(render_md(r),encoding='utf-8')
    print(OUT_MD.read_text())
    return 0 if all(x['all_exact_pairs'] for x in r['builds'].values()) else 2


if __name__ == '__main__':
    raise SystemExit(main())
