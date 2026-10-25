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
import shutil
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
    seed = config.get("source_sram")
    check(type(seed) is dict and set(seed) == {"path", "sha256"},
          "missing authenticated original-movie SRAM seed")
    check(type(seed["sha256"]) is str and bool(HEX64.fullmatch(seed["sha256"])),
          "invalid original-movie SRAM digest")
    seed_file = Path(seed["path"])
    check(seed_file.is_file() and not seed_file.is_symlink()
          and seed_file.stat().st_size == 8192
          and file_sha(seed_file) == seed["sha256"],
          "original-movie 8192-byte SRAM seed mismatched")
    observer = config.get("observation_script")
    check(type(observer) is dict and set(observer) == {"path", "sha256"},
          "missing qualified observation script source binding")
    check(type(observer["sha256"]) is str
          and bool(HEX64.fullmatch(observer["sha256"])), "invalid observer digest")
    observer_file = Path(observer["path"])
    check(observer_file.suffix == ".script" and
          file_sha(observer_file) == observer["sha256"],
          "qualified observer script changed")
    check(type(config.get("native_xvfb", False)) is bool,
          "native_xvfb must be explicit boolean")
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
        check("%ROM%" in joined, "both guests must use pinned original ROM")
        if key == "reference":
            check("%CORE%" in joined, "reference must load pinned original emulator core")
            check(cmd["environment"].get("SNESREF_SCRIPT") == "%OBSERVER%",
                  "reference must execute qualified observer script")
            check(cmd["environment"].get("SNESREF_SRAM_IN") == "%SRAM%"
                  and cmd["environment"].get("SNESREF_INPUT_FILE") == "%CANDIDATE%"
                  and cmd["environment"].get("SNESREF_DUMP_DIR") == "%DUMP_DIR%",
                  "reference must use pinned SRAM, input and real dump transport")
        else:
            check(cmd["environment"].get("UR_QA_SCENE_INPUT_FILE") == "%CANDIDATE%"
                  and cmd["environment"].get("SNESRECOMP_DUMP_DIR") == "%DUMP_DIR%"
                  and cmd["environment"].get("SNESRECOMP_ROM") == "%ROM%",
                  "native must use pinned source scene input and real dump transport")
            check(any(cmd["argv"][i:i+2] == ["--script", "%OBSERVER%"]
                      for i in range(len(cmd["argv"]) - 1)),
                  "native must execute the identical pinned observer script")
            check("--config" in cmd["argv"]
                  and "%CONFIG%" in cmd["argv"]
                  and "--no-launcher" in cmd["argv"],
                  "native must use explicit config and isolated save root")
        check(str(Path(cmd["argv"][0]).resolve()) ==
              str(Path(config[("reference_binary" if key == "reference" else "native_binary")]["path"]).resolve()),
              "command does not execute pinned binary")
    clocks = config.get("guest_clocks")
    check(type(clocks) is dict and set(clocks) ==
          {"reference_entry_frame", "native_entry_frame",
           "reference_observation_frame", "native_observation_frame"},
          "missing separate original/native guest clocks")
    check(all(type(value) is int and 0 <= value < 200000
              for value in clocks.values()), "invalid paired guest clock frame")
    check(clocks["reference_observation_frame"] > clocks["reference_entry_frame"]
          and clocks["native_observation_frame"] > clocks["native_entry_frame"]
          and clocks["reference_observation_frame"] - clocks["reference_entry_frame"]
              == clocks["native_observation_frame"] - clocks["native_entry_frame"],
          "unequal race-relative semantic observation phases")
    require_same_tag = config["reference"]["dump"] == config["native"]["dump"]
    check(require_same_tag, "original/native observers must produce same named checkpoint")
    tag = config["reference"]["dump"][:-len(".wram.bin")]
    source_text = observer_file.read_text(encoding="utf-8")
    source_lines = source_text.splitlines()
    check(source_lines.count("dump " + tag) == 1,
          "observer script must contain exactly one named target dump")
    bounded = config.get("bounded_observer_script")
    if bounded is not None:
        check(type(bounded) is dict and set(bounded) == {"path", "sha256"},
              "missing bound checkpoint-only observer identity")
        check(type(bounded["sha256"]) is str
              and bool(HEX64.fullmatch(bounded["sha256"])),
              "invalid checkpoint-only observer digest")
        bound_file = Path(bounded["path"])
        check(bound_file.suffix == ".script" and
              file_sha(bound_file) == bounded["sha256"],
              "checkpoint-only observer hash changed")
        check(bound_file.read_text(encoding="utf-8") ==
              checkpoint_only_observer(source_text, tag),
              "checkpoint-only observer changes source precheckpoint execution")
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
    pre = config.get("pre_target")
    is_zoo_sound = d["id"].startswith("original-zoo-first-sound")
    if is_zoo_sound:
        check(pre is not None, "Zoo causal reducer must protect preceding full WRAM")
    if pre is not None:
        check(type(pre) is dict and set(pre) == {"dump", "sha256"},
              "missing exact before-target WRAM source binding")
        check(type(pre["dump"]) is str
              and bool(re.fullmatch(r"[A-Za-z0-9_.-]+\.wram\.bin", pre["dump"]))
              and pre["dump"] != config["reference"]["dump"],
              "invalid distinct preceding WRAM dump")
        check(type(pre["sha256"]) is str and bool(HEX64.fullmatch(pre["sha256"])),
              "missing genuine source before-target SHA256")
        pretag = pre["dump"][:-len(".wram.bin")]
        check(source_lines.count("dump " + pretag) == 1
              and source_lines.index("dump " + pretag) < source_lines.index("dump " + tag),
              "source observer does not sample authentic preceding frame")
    after_pair = config.get("after_target_pair")
    if is_zoo_sound:
        check(after_pair is not None, "Zoo sound comparison must bind both original DP differences")
    if after_pair is not None:
        check(type(after_pair) is list and len(after_pair) == 2,
              "Zoo after-pair needs exactly two source-earned differences")
        check([row.get("offset") for row in after_pair if type(row) is dict]
              == [0x63, 0x69], "Zoo after-pair has wrong or incomplete offsets")
        for row in after_pair:
            check(type(row) is dict and set(row) ==
                  {"offset", "original_byte", "native_byte"}
                  and type(row["original_byte"]) is int
                  and type(row["native_byte"]) is int
                  and 0 <= row["original_byte"] <= 255
                  and 0 <= row["native_byte"] <= 255
                  and row["original_byte"] != row["native_byte"],
                  "invalid source-earned Zoo two-byte discrepancy")
        check(after_pair[0]["original_byte"] == d["original_byte"]
              and after_pair[0]["native_byte"] == d["native_byte"]
              and after_pair[0]["offset"] == d["offset"],
              "Zoo primary target differs from exact source DP pair")
    return config


def render(text, candidate, output, rom, core, seed, config, observer):
    return (text.replace("%CANDIDATE%", str(candidate))
            .replace("%DUMP_DIR%", str(output))
            .replace("%ROM%", str(rom))
            .replace("%CORE%", str(core))
            .replace("%SRAM%", str(seed))
            .replace("%CONFIG%", str(config))
            .replace("%OBSERVER%", str(observer)))


def checkpoint_only_observer(source: str, tag: str) -> str:
    """Exact source script prefix through a unique checkpoint, then quit.

    Never alter the pre-checkpoint script, frames or input clocks. The source
    SHA stays pinned independently of this deliberately derived observer.
    """
    check(bool(re.fullmatch(r"[A-Za-z0-9_.-]+", tag)), "invalid bounded checkpoint tag")
    lines = source.splitlines(keepends=True)
    markers = [i for i, line in enumerate(lines)
               if line.strip() == "dump " + tag]
    check(len(markers) == 1, "bounded observer requires one authentic checkpoint")
    end = markers[0]
    check(all(line.strip() != "quit" for line in lines[:end]),
          "source observer quits before selected checkpoint")
    check(any(line.strip() == "quit" for line in lines[end + 1:]),
          "source observer must include terminal quit")
    check(lines[end].endswith("\n"), "source checkpoint must end with newline")
    return "".join(lines[:end + 1]) + "quit\n"


def native_execution_argv(argv, use_xvfb):
    """Preserve the pinned native executable as argv[0], optionally under Xvfb."""
    if type(use_xvfb) is not bool:
        raise ValueError("native Xvfb transport must be explicit boolean")
    if not use_xvfb:
        return argv
    wrapper = shutil.which("xvfb-run")
    check(wrapper is not None and Path(wrapper).is_file(),
          "native Xvfb display wrapper is unavailable")
    return [wrapper, "-a", *argv]


def observe(command, candidate, rom, work, anchors, timeout, seed_bytes, observer, expected_frame,
            native_xvfb=False, pre_target=None):
    work.mkdir()
    # Both real engines must boot from the same independently verified
    # historical SRAM. A disposable native cwd gives it an isolated saves/
    # tree; the reference receives the matching file via SNESREF_SRAM_IN.
    source_seed = work / "source-seed.srm"
    source_seed.write_bytes(seed_bytes)
    saves = work / "saves"
    saves.mkdir()
    (saves / "save.srm").write_bytes(seed_bytes)
    config = work / "qa01-candidate.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = dict(os.environ)
    core = Path(command.get("_reference_core", rom))
    env.update({k: render(v, candidate, work, rom, core, source_seed, config, observer)
                for k, v in command["environment"].items()})
    args = [render(s, candidate, work, rom, core, source_seed, config, observer) for s in command["argv"]]
    args = native_execution_argv(args, native_xvfb)
    proc = subprocess.run(args, cwd=work, env=env, capture_output=True,
                          text=True, errors="replace", check=False, timeout=timeout)
    trace = proc.stdout + "\n" + proc.stderr
    # The original script has source-authenticated "until" gates. A reduced
    # controller candidate may legitimately fail to reach the result screen:
    # snesref/native then exits 3 with an explicit fixed-script timeout. Such a
    # candidate is NOT the sought divergence, but should not abort ddmin.
    # All other nonzero exits remain hard failures (broken infrastructure).
    if proc.returncode == 3 and re.search(
        r"\bscript f=\d+ until [0-9A-Fa-f]{4} (?:==|!=) [0-9A-Fa-f]{2} "
        r"\d+ TIMEOUT after \d+ frames \(value=[0-9A-Fa-f]{2}\)", trace
    ):
        return False, None
    check(proc.returncode == 0, "guest execution failed (exit " + str(proc.returncode)
          + "): " + (proc.stderr or proc.stdout)[-300:])
    checkpoint_tag = command["dump"][:-len(".wram.bin")]
    pattern = re.compile(r"\bscript f=(\d+) dump " + re.escape(checkpoint_tag) + r"(?:\s|$)")
    observed_frames = [int(f) for f in pattern.findall(proc.stdout + "\n" + proc.stderr)]
    if observed_frames != [expected_frame]:
        return False, None
    if pre_target is not None:
        pretag = pre_target["dump"][:-len(".wram.bin")]
        preframes = [int(f) for f in re.findall(
            r"\bscript f=(\d+) dump " + re.escape(pretag) + r"(?:\s|$)",
            proc.stdout + "\n" + proc.stderr)]
        if preframes != [expected_frame - 1]:
            return False, None
        previous = work / pre_target["dump"]
        if (not previous.is_file() or previous.is_symlink() or
                previous.stat().st_size != BYTES or
                sha(previous) != pre_target["sha256"]):
            return False, None
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
    from qa01_reducer_clock_rebase import paired_streams
    runs = load_controller_runs(candidate)
    source = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    check(source == cfg["source_sha"], "paired commands source SHA is stale")
    rom = Path(cfg["rom"]["path"]).resolve()
    observer = Path((cfg.get("bounded_observer_script")
                     or cfg["observation_script"])["path"]).resolve()
    seed_bytes = Path(cfg["source_sram"]["path"]).read_bytes()
    check(len(seed_bytes) == 8192 and hashlib.sha256(seed_bytes).hexdigest()
          == cfg["source_sram"]["sha256"], "original source SRAM changed after validation")
    with tempfile.TemporaryDirectory(prefix="ur-qa01-reduce-pair-") as tmp:
        root = Path(tmp)
        clocks = cfg["guest_clocks"]
        original_input, native_input = paired_streams(
            runs, clocks["reference_entry_frame"], clocks["native_entry_frame"])
        original_path = root / "original-clock.input"
        native_path = root / "native-clock.input"
        original_path.write_bytes(original_input)
        native_path.write_bytes(native_input)
        reference_command = {**cfg["reference"],
                             "_reference_core": cfg["reference_core"]["path"]}
        original_valid, original = observe(
            reference_command, original_path, rom, root / "original",
            cfg["anchors"], timeout, seed_bytes, observer,
            clocks["reference_observation_frame"],
            pre_target=cfg.get("pre_target"))
        native_valid, native = observe(
            cfg["native"], native_path, rom, root / "native",
            cfg["anchors"], timeout, seed_bytes, observer,
            clocks["native_observation_frame"], cfg.get("native_xvfb", False),
            pre_target=cfg.get("pre_target"))
        check(sha(observer) == (cfg.get("bounded_observer_script")
                                or cfg["observation_script"])["sha256"]
              and sha(Path(cfg["observation_script"]["path"])) ==
                  cfg["observation_script"]["sha256"],
              "source or executed observer changed during paired process execution")
        predicate = cfg["discrepancy"]
        reproduced = bool(original_valid and native_valid
                          and original[predicate["offset"]] == predicate["original_byte"]
                          and native[predicate["offset"]] == predicate["native_byte"])
        pair = cfg.get("after_target_pair")
        if reproduced and pair is not None:
            # The exact source had ONLY the $0063 and $0069 differences at
            # +5040. A new third WRAM mismatch or missing partner is a
            # different experiment, even if $0063 happens to match.
            positions = [i for i, (a, b) in enumerate(zip(original, native))
                         if a != b]
            reproduced = (positions == [0x63, 0x69] and all(
                original[row["offset"]] == row["original_byte"]
                and native[row["offset"]] == row["native_byte"] for row in pair))
    return {
        "schema": ORACLE_SCHEMA, "candidate_sha256": sha(candidate),
        "reference_supplied_input_sha256": hashlib.sha256(original_input).hexdigest(),
        "native_supplied_input_sha256": hashlib.sha256(native_input).hexdigest(),
        "guest_clocks": dict(clocks),
        "native_frame_shift": clocks["native_entry_frame"] - clocks["reference_entry_frame"],
        "source_sha": cfg["source_sha"],
        "source_sram_sha256": cfg["source_sram"]["sha256"],
        "observation_script_sha256": cfg["observation_script"]["sha256"],
        "executed_observer_sha256": (cfg.get("bounded_observer_script")
                                    or cfg["observation_script"])["sha256"],
        "preceding_source_wram_sha256": (cfg.get("pre_target") or {}).get("sha256"),
        "after_target_pair_sha256": (
            hashlib.sha256(json.dumps(cfg["after_target_pair"], sort_keys=True).encode()).hexdigest()
            if cfg.get("after_target_pair") is not None else None),
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
