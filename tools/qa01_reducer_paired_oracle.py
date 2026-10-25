#!/usr/bin/env python3
"""Run a qualified original/native paired WRAM oracle for replay reduction.

Exact original/native producers are specified in a SHA-pinned private manifest.
This is a transport adapter, never an independent SNES or release oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ur-qa01-reducer-paired-commands/1"
ORACLE_SCHEMA = "ur-controller-reducer-oracle/1"
ROM_USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
BYTES = 131072


def check(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_sha(path):
    check(path.is_file() and not path.is_symlink(), "missing/redirected pinned binary: " + str(path))
    return sha(path)


def validate(config):
    check(type(config) is dict and config.get("schema") == SCHEMA,
          "invalid paired-command manifest")
    check(type(config.get("source_sha")) is str
          and bool(HEX40.fullmatch(config["source_sha"])), "invalid source commit")
    check(type(config.get("reference_engine")) is str
          and config["reference_engine"].strip(), "missing independent reference-engine name")
    for key in ("rom", "reference_binary", "reference_core", "native_binary"):
        obj = config.get(key)
        check(type(obj) is dict and set(obj) == {"path", "sha256"},
              "missing exact binary binding " + key)
        check(type(obj["sha256"]) is str and bool(HEX64.fullmatch(obj["sha256"])),
              "invalid SHA-256 for " + key)
        check(file_sha(Path(obj["path"])) == obj["sha256"], "mismatched pinned " + key)
    check(config["rom"]["sha256"] == ROM_USA_SHA256, "only canonical original USA ROM")
    for key in ("reference", "native"):
        cmd = config.get(key)
        check(type(cmd) is dict and set(cmd) == {"argv", "environment", "dump"},
              "invalid " + key + " producer")
        check(type(cmd["argv"]) is list and len(cmd["argv"]) >= 1
              and all(type(arg) is str and arg for arg in cmd["argv"]), "invalid command argv")
        check(type(cmd["environment"]) is dict and all(
            type(k) is str and type(v) is str and k.isidentifier()
            for k, v in cmd["environment"].items()), "invalid producer env")
        check(type(cmd["dump"]) is str and bool(re.fullmatch(r"[A-Za-z0-9_.-]+\.wram\.bin", cmd["dump"])),
              "invalid named WRAM snapshot")
        joined = json.dumps({"argv": cmd["argv"], "environment": cmd["environment"]})
        check("%CANDIDATE%" in joined and "%DUMP_DIR%" in joined,
              "both guests must consume exact controller candidate and write isolated dumps")
        check(str(Path(cmd["argv"][0]).resolve()) ==
              str(Path(config[("reference_binary" if key == "reference" else "native_binary")]["path"]).resolve()),
              "command does not execute pinned binary")
    d = config.get("discrepancy")
    check(type(d) is dict and set(d) ==
          {"id", "phase", "offset", "original_byte", "native_byte"}, "invalid discrepancy predicate")
    check(type(d["id"]) is str and bool(d["id"].strip())
          and type(d["phase"]) is str and bool(d["phase"].strip()), "unnamed discrepancy/phase")
    check(type(d["offset"]) is int and 0 <= d["offset"] < BYTES
          and all(type(d[k]) is int and 0 <= d[k] <= 255 for k in ("original_byte", "native_byte"))
          and d["original_byte"] != d["native_byte"], "not an actual exact-byte divergence")
    anchors = config.get("anchors")
    check(type(anchors) is list and len(anchors) >= 1, "no authentic stage anchors supplied")
    offsets = set()
    for row in anchors:
        check(type(row) is dict and set(row) == {"offset", "value"}
              and type(row["offset"]) is int and 0 <= row["offset"] < BYTES
              and type(row["value"]) is int and 0 <= row["value"] <= 255
              and row["offset"] not in offsets, "invalid or duplicate checkpoint anchor")
        offsets.add(row["offset"])
    check(d["offset"] not in offsets, "divergent target cannot be an equal-stage anchor")
    return config


def render(text, candidate, output, rom):
    return (text.replace("%CANDIDATE%", str(candidate))
            .replace("%DUMP_DIR%", str(output))
            .replace("%ROM%", str(rom)))


def observe(command, candidate, rom, work, anchors, timeout):
    work.mkdir()
    env = dict(os.environ)
    env.update({k: render(v, candidate, work, rom)
                for k, v in command["environment"].items()})
    args = [render(s, candidate, work, rom) for s in command["argv"]]
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                          text=True, errors="replace", check=False, timeout=timeout)
    check(proc.returncode == 0, "guest execution failed (exit " + str(proc.returncode)
          + "): " + (proc.stderr or proc.stdout)[-300:])
    checkpoint = work / command["dump"]
    if not checkpoint.is_file() or checkpoint.is_symlink() or checkpoint.stat().st_size != BYTES:
        return False, None
    raw = checkpoint.read_bytes()
    valid = all(raw[row["offset"]] == row["value"] for row in anchors)
    return valid, raw


def execute(config, candidate, timeout=120):
    cfg = validate(config)
    check(1 <= timeout <= 3600, "invalid finite execution timeout")
    check(candidate.is_file() and not candidate.is_symlink(), "missing candidate controller file")
    # Validate the actual canonical P1/P2 controller grammar, including overlap.
    from controller_input import load_controller_runs
    load_controller_runs(candidate)
    source = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    check(source == cfg["source_sha"], "paired commands source SHA is stale")
    rom = Path(cfg["rom"]["path"]).resolve()
    with tempfile.TemporaryDirectory(prefix="ur-qa01-reduce-pair-") as tmp:
        root = Path(tmp)
        original_valid, original = observe(
            cfg["reference"], candidate.resolve(), rom, root / "original",
            cfg["anchors"], timeout)
        native_valid, native = observe(
            cfg["native"], candidate.resolve(), rom, root / "native",
            cfg["anchors"], timeout)
        predicate = cfg["discrepancy"]
        reproduced = bool(original_valid and native_valid
                          and original[predicate["offset"]] == predicate["original_byte"]
                          and native[predicate["offset"]] == predicate["native_byte"])
    return {
        "schema": ORACLE_SCHEMA, "candidate_sha256": sha(candidate),
        "source_sha": cfg["source_sha"],
        "original_rom_sha256": cfg["rom"]["sha256"],
        "native_binary_sha256": cfg["native_binary"]["sha256"],
        "reference_engine": cfg["reference_engine"] + ":" + cfg["reference_binary"]["sha256"]
                            + ":" + cfg["reference_core"]["sha256"],
        "discrepancy_id": predicate["id"], "semantic_phase": predicate["phase"],
        "original_valid": bool(original_valid), "native_valid": bool(native_valid),
        "result": ("reproduced" if reproduced else "not_reproduced"
                   if original_valid and native_valid else "invalid_route"),
        "release_gate_credit": 0,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args()
    config = json.loads(args.manifest.read_text(encoding="utf-8"))
    receipt = execute(config, args.candidate, args.timeout)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(receipt["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
