#!/usr/bin/env python3
"""Constrained, durable HP job receipts for unattended ChatGPT agents.

Only two read-only jobs are admitted. No submitted shell command is executed.
The runner is deliberately one-shot; scheduling and resource policy belong to
the machine owner, not a remote agent.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

KINDS = ("repo-status", "agent-selector")
SHA = re.compile(r"[0-9a-f]{40}\Z")
STATES = ("pending", "running", "complete", "failed")
MAX_OUTPUT = 65536


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_json(path, data):
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=15, check=True).stdout.strip()


def trusted_sha(repo, commit):
    if not SHA.fullmatch(commit):
        raise ValueError("expected full lowercase 40-character commit SHA")
    found = git(repo, "rev-parse", "--verify", commit + "^{commit}")
    if found != commit:
        raise ValueError("commit resolution mismatch")
    # Do not run arbitrary PR-controlled source on the personal HP.
    if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", commit,
                       "refs/remotes/origin/main"], timeout=15).returncode != 0:
        raise ValueError("commit is not on locally fetched trusted origin/main")


def submit(root, repo, kind, commit, agent):
    if kind not in KINDS or not re.fullmatch(r"agent-[1-5]", agent):
        raise ValueError("unsupported job kind or agent")
    trusted_sha(repo, commit)
    job_id = uuid.uuid4().hex
    record = dict(job_id=job_id, kind=kind, commit=commit, agent=agent,
                  state="pending", created_utc=utc())
    atomic_json(root / "pending" / (job_id + ".json"), record)
    return record


def execute(repo, record):
    # Executing only immutable checked-in scripts from main; never accept a command string.
    trusted_sha(repo, record["commit"])
    if record["kind"] == "repo-status":
        return ["git", "-C", str(repo), "show", "-s", "--format=%H%n%s", record["commit"]]
    if record["kind"] == "agent-selector":
        # Board is read from a pinned main worktree only when it equals the requested SHA.
        # This protects the selector against mixed working-tree/source epochs.
        if git(repo, "rev-parse", "HEAD") != record["commit"]:
            raise ValueError("selector requires checkout HEAD equal to the submitted SHA")
        if git(repo, "status", "--porcelain"):
            raise ValueError("selector requires clean worktree")
        return [sys.executable, "-X", "utf8", str(repo / "tools" / "agent_control.py"),
                "--agent", record["agent"].split("-")[1]]


def diagnose(root):
    """Read-only crash diagnostics; never assume that an old lock is safe to break."""
    lock = root / "worker.lock"
    owner = lock / "owner.json"
    result = {"lock_present": lock.is_dir(), "running_jobs": [], "owner": None}
    if owner.is_file():
        try:
            result["owner"] = json.loads(owner.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            result["owner_error"] = f"{type(exc).__name__}: {exc}"
    for path in sorted((root / "running").glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            result["running_jobs"].append({"job_id": record.get("job_id"),
                                           "started_utc": record.get("started_utc")})
        except (OSError, ValueError) as exc:
            result["running_jobs"].append({"file": path.name,
                                           "read_error": f"{type(exc).__name__}: {exc}"})
    result["needs_operator_inspection"] = bool(result["running_jobs"] or result["lock_present"])
    return result


def host_status():
    """Advisory Windows resource snapshot; not an exclusive runner reservation."""
    if os.name != "nt":
        return {"available": False, "reason": "Windows-only resource probe"}
    try:
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong),
                        ("memory_load", ctypes.c_ulong),
                        ("total_phys", ctypes.c_ulonglong),
                        ("avail_phys", ctypes.c_ulonglong),
                        ("total_page", ctypes.c_ulonglong),
                        ("avail_page", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong),
                        ("avail_virtual", ctypes.c_ulonglong),
                        ("avail_extended", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        output = subprocess.run(["tasklist.exe", "/fo", "csv", "/nh"], check=True,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=15).stdout
        names = {"runner.worker.exe", "msbuild.exe", "cl.exe", "link.exe",
                 "ninja.exe", "cmake.exe", "clang-cl.exe"}
        active = sorted({row[0].casefold() for row in csv.reader(io.StringIO(output))
                         if row and row[0].casefold() in names})
        # Positive observation is useful; absence is not proof that GHA is idle.
        return {"available": True, "free_physical_mib": status.avail_phys // 1048576,
                "total_physical_mib": status.total_phys // 1048576,
                "observed_build_processes": active,
                "exclusive_reservation": False}
    except (OSError, subprocess.SubprocessError, IndexError) as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}


def run_once(root, repo):
    lock = root / "worker.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        return dict(state="busy", reason="another worker holds the lock")
    owner = lock / "owner.json"
    try:
        atomic_json(owner, {"pid": os.getpid(), "started_utc": utc()})
        # Never process another job while an earlier attempt has an uncertain
        # outcome. Operator investigation is required, even for read-only work.
        stale = sorted((root / "running").glob("*.json"))
        if stale:
            return {"state": "blocked", "reason": "unresolved running receipts",
                    "running_job_ids": [path.stem for path in stale]}
        pending = sorted((root / "pending").glob("*.json"))
        if not pending:
            return dict(state="empty")
        src = pending[0]
        running = root / "running" / src.name
        os.replace(src, running)
        record = json.loads(running.read_text(encoding="utf-8"))
        record["state"] = "running"
        record["started_utc"] = utc()
        atomic_json(running, record)
        try:
            command = execute(repo, record)
            start = time.monotonic()
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", env=env, timeout=45)
            record.update(state="complete" if result.returncode == 0 else "failed",
                          exit_code=result.returncode, duration_s=round(time.monotonic() - start, 3),
                          stdout=result.stdout[:MAX_OUTPUT], stderr=result.stderr[:MAX_OUTPUT])
        except Exception as exc:
            record.update(state="failed", error=f"{type(exc).__name__}: {exc}")
        record["finished_utc"] = utc()
        dest = root / record["state"] / src.name
        atomic_json(dest, record)
        running.unlink(missing_ok=True)
        return record
    finally:
        owner.unlink(missing_ok=True)
        lock.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    sub = p.add_subparsers(dest="command", required=True)
    submit_p = sub.add_parser("submit")
    submit_p.add_argument("--kind", choices=KINDS, required=True)
    submit_p.add_argument("--sha", required=True)
    submit_p.add_argument("--agent", choices=[f"agent-{i}" for i in range(1, 6)], required=True)
    sub.add_parser("run-once")
    sub.add_parser("diagnose")
    sub.add_parser("host-status")
    status = sub.add_parser("status")
    status.add_argument("--job-id", required=True)
    args = p.parse_args()
    repo = args.repo.resolve(strict=True)
    root = args.state_dir.resolve()
    for state in STATES:
        (root / state).mkdir(parents=True, exist_ok=True)
    if args.command == "submit":
        result = submit(root, repo, args.kind, args.sha, args.agent)
    elif args.command == "run-once":
        result = run_once(root, repo)
    elif args.command == "diagnose":
        result = diagnose(root)
    elif args.command == "host-status":
        result = host_status()
    else:
        if not re.fullmatch(r"[0-9a-f]{32}", args.job_id):
            p.error("invalid job id")
        result = None
        for state in STATES:
            path = root / state / (args.job_id + ".json")
            if path.is_file():
                result = json.loads(path.read_text(encoding="utf-8"))
                break
        if result is None:
            p.error("job not found")
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
