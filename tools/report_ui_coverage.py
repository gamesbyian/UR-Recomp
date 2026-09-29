#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

STATE_RE = re.compile(r"^  - id: ([A-Z0-9_]+)\s*$")
STATUS_RANK = {"verified":0,"documented":1,"historical":2,"hypothesis":3}

def state_ids(path):
    out=[]; inside=False
    for line in path.read_text().splitlines():
        if line=="states:": inside=True; continue
        if inside and line=="open_questions:": break
        if inside:
            m=STATE_RE.match(line)
            if m: out.append(m.group(1))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--out",type=Path)
    a=ap.parse_args(); root=a.root
    states=state_ids(root/"analysis/ui-state-map.yml")
    transition_data=json.loads((root/"analysis/ui-transition-contract.json").read_text())
    edges=transition_data["edges"]
    capture_exempt=set(transition_data.get("capture_exempt_states", []))
    caps=json.loads((root/"analysis/ui-capture-manifest.json").read_text())["captures"]
    menus=json.loads((root/"analysis/ui-menu-index.json").read_text())["entries"]
    refs=json.loads((root/"analysis/ui-reference-index.json").read_text())["entries"]
    inc={s:[] for s in states}; out={s:[] for s in states}
    for e in edges:
        out.setdefault(e["from"],[]).append(e); inc.setdefault(e["to"],[]).append(e)
    dependencies=transition_data.get("capability_dependencies", {})
    blockers={s:set() for s in states}
    for s in states:
        incoming=inc.get(s,[])
        open_blocked=[e for e in incoming if e.get("blocked_by") and dependencies.get(e["blocked_by"],{}).get("status")!="complete"]
        unblocked=[e for e in incoming if not e.get("blocked_by") or dependencies.get(e.get("blocked_by"),{}).get("status")=="complete"]
        if incoming and open_blocked and not unblocked:
            blockers[s].update(e["blocked_by"] for e in open_blocked)
    cb={}; mb={}; rb={}
    for c in caps: cb.setdefault(c["state_id"],[]).append(c)
    for m in menus: mb.setdefault(m["state_id"],[]).append(m)
    for r in refs: rb.setdefault(r["state_id"],[]).extend(r.get("references",[]))
    lines=["# UI State Coverage","",
      "| State | Menu byte(s) | Required captures | Optional captures | Public visual leads | Blockers | In | Out | Strongest edge evidence |",
      "|---|---|---:|---:|---:|---|---:|---:|---|"]
    gaps=[]
    for s in states:
        cs=cb.get(s,[]); ms=mb.get(s,[])
        statuses=[e["status"] for e in inc.get(s,[])+out.get(s,[])]
        strongest=min(statuses,key=lambda x:STATUS_RANK[x]) if statuses else ""
        menu=", ".join(m["value"]+("" if m.get("status")=="verified" else "?") for m in ms)
        req=sum(1 for c in cs if c.get("required",True)); opt=len(cs)-req
        leads=len(rb.get(s,[]))
        blocker_text=", ".join(sorted(blockers.get(s,set())))
        lines.append(f"| {s} | {menu} | {req} | {opt} | {leads} | {blocker_text} | {len(inc.get(s,[]))} | {len(out.get(s,[]))} | {strongest} |")
        if not cs and s not in capture_exempt: gaps.append((s,"no capture contract"))
        if not cs and not rb.get(s) and s not in capture_exempt: gaps.append((s,"no local capture or public visual lead"))
        if ms and not any(m.get("status")=="verified" for m in ms): gaps.append((s,"menu id remains historical/unverified"))
        if not out.get(s) and s!="ENDING": gaps.append((s,"no outgoing transition in executable contract"))
        for blocker in sorted(blockers.get(s,set())):
            if transition_data.get("capability_dependencies",{}).get(blocker,{}).get("status")!="complete":
                gaps.append((s,f"blocked by open capability {blocker}"))
    lines += ["","## Evidence gaps",""]
    lines += [f"- {s}: {reason}" for s,reason in gaps]
    lines += ["","## Summary","",
      f"- conceptual states: {len(states)}",
      f"- executable transitions: {len(edges)}",
      f"- capture contracts: {len(caps)}",
      f"- menu-index entries: {len(menus)}",
      f"- locally verified menu-index entries: {sum(1 for m in menus if m.get('status')=='verified')}",
      f"- states with at least one capture contract: {len(cb)}",
      f"- states with at least one public visual lead: {len(rb)}",
      f"- open capability dependencies: {sum(1 for d in transition_data.get('capability_dependencies',{}).values() if d.get('status')=='open')}",
      f"- raw gap observations: {len(gaps)}",""]
    output="\n".join(lines)
    if a.out: a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(output)
    else: print(output)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
