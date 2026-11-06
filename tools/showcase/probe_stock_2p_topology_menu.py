#!/usr/bin/env python3
"""Probe ORIGINAL 2P menu control semantics without changing guest state."""
import argparse
import json
from pathlib import Path
from build_topology_2p_routes import SOURCE_ANCHOR
# Each choice is a distinct real stock controller edge, no screen-state hacks.
CHOICES={
 "all-start":("start","start","start"),
 "all-a":("a","a","a"),
 "start-then-a":("start","a","a"),
 "a-then-start":("a","start","start"),
}
def produce(source:str,choices:tuple[str,str,str]):
 if source.count(SOURCE_ANCHOR)!=1:
  raise ValueError("Unexpected 2P racer/tour menu anchor")
 p=source.split(SOURCE_ANCHOR,1)[0]
 route=p+"press p2:start 2\nuntil 009F == 6D 1200\nwait 60\n"
 route+="press down 2\nuntil 009B == 02 600\nwait 30\n"
 route+="dump touring-shuffler\n"
 for tag,button in zip(("after-tour-accept","after-track-accept","after-race-accept"),choices):
  if tag=="after-track-accept":
   route+="press down 2\nwait 40\ndump selected-course-row\n"
  route+=f"press {button} 2\nwait 90\ndump {tag}\n"
 route+="quit\n"
 return route
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--source",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 a.out.mkdir(parents=True,exist_ok=True)
 source=a.source.read_text()
 for name,buttons in CHOICES.items():
  (a.out/f"{name}.txt").write_text(produce(source,buttons))
 (a.out/"menu-probe-provenance.json").write_text(json.dumps({
  "schema":"UR-STOCK-2P-MENU-DIAGNOSTIC/1",
  "choices":CHOICES,
  "actual_menu_still_unverified":True,
  "purpose":"read-only guest scene dumps of route divergence in native 2P UI",
  "no_guest_memory_writes":True,
 },indent=2)+"\n")
 print("Stock 2P menu probes:",list(CHOICES))
if __name__=="__main__":main()
