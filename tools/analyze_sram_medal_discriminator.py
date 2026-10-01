#!/usr/bin/env python3
"""Summarize a controlled Uniracers SRAM before/after experiment."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def ranges(before: bytes, after: bytes):
    out=[]; start=None
    for i,(a,b) in enumerate(zip(before,after)):
        if a!=b and start is None: start=i
        if a==b and start is not None:
            out.append((start,i-1)); start=None
    if start is not None: out.append((start,len(before)-1))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--known-no-hunter")
    ap.add_argument("--known-with-hunter")
    ap.add_argument("--json-out",required=True)
    ap.add_argument("--md-out",required=True)
    a=ap.parse_args()
    before=Path(a.before).read_bytes(); after=Path(a.after).read_bytes()
    if len(before)!=8192 or len(after)!=8192:
        raise SystemExit("expected 8192-byte SRAM images")
    diffs=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
    rs=ranges(before,after)
    payload={
      "schema_version":1,
      "before":a.before,"after":a.after,
      "size_bytes":len(before),
      "differing_bytes":len(diffs),
      "ranges":[{"start":f"0x{s:04X}","end":f"0x{e:04X}","length":e-s+1} for s,e in rs],
      "changes":[{"offset":f"0x{i:04X}","before":before[i],"after":after[i]} for i in diffs],
    }
    comparisons={}
    for label,path in (("all_silvers_no_hunter",a.known_no_hunter),("all_silvers_with_hunter",a.known_with_hunter)):
        if path:
            known=Path(path).read_bytes()
            comparisons[label]={
              "equal_bytes":sum(x==y for x,y in zip(after,known)),
              "differing_bytes":sum(x!=y for x,y in zip(after,known)),
              "changed_offsets_matching_known":sum(after[i]==known[i] for i in diffs),
              "changed_offset_count":len(diffs),
            }
    payload["comparisons_to_recovered_snapshots"]=comparisons
    Path(a.json_out).write_text(json.dumps(payload,indent=2)+"\n")
    lines=[
      "# Controlled SRAM medal discriminator",
      "",
      "Generated from a clean recovered SRAM image, one deterministic stock Dragster completion, and the resulting emulator SRAM dump.",
      "",
      f"- SRAM size: {len(before)} bytes",
      f"- changed bytes: {len(diffs)}",
      f"- changed contiguous ranges: {len(rs)}",
      "",
      "## Changed ranges",
      "",
      "| Start | End | Length |",
      "|---:|---:|---:|",
    ]
    for s,e in rs: lines.append(f"| `0x{s:04X}` | `0x{e:04X}` | {e-s+1} |")
    lines += ["","## Byte changes","","| Offset | Before | After |","|---:|---:|---:|"]
    for i in diffs: lines.append(f"| `0x{i:04X}` | `0x{before[i]:02X}` | `0x{after[i]:02X}` |")
    if comparisons:
        lines += ["","## Comparison with recovered all-silver snapshots",""]
        for label,c in comparisons.items():
            lines.append(f"- {label}: {c['changed_offsets_matching_known']}/{c['changed_offset_count']} changed offsets equal the recovered snapshot value; whole-image differences {c['differing_bytes']}.")
    Path(a.md_out).write_text("\n".join(lines)+"\n")

if __name__=="__main__": main()
