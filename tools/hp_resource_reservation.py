#!/usr/bin/env python3
"""Fail-closed, cooperative HP resource reservation for future runner hooks.

No automatic expiry. Every reservation requires an explicit matching release.
This protocol offers coordination only if ALL competing compute clients
participate; installation on the live GHA runner is deliberately separate.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import time
import uuid

ROLE = ("github-actions", "hp-broker")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def locked(root, callback, wait_s=2.0):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "operation.lock"
    deadline = time.monotonic() + wait_s
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                return {"ok": False, "state": "lock-unavailable",
                        "reason": "reservation-operation lock needs inspection"}
            time.sleep(0.05)
    try:
        return callback()
    finally:
        lock.rmdir()


def read_active(root):
    path = root / "active.json"
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"invalid": f"{type(exc).__name__}: {exc}"}
    if not isinstance(record, dict) or not {"role", "token", "reservation_id"} <= record.keys():
        return {"invalid": "incomplete active reservation"}
    return record


def write_atomic(path, record):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n",
                        encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def reserve(root, role, token):
    if role not in ROLE or not TOKEN.fullmatch(token):
        raise ValueError("unsupported reservation role or invalid token")

    def operation():
        existing = read_active(root)
        if existing is not None:
            return {"ok": False, "state": "occupied", "active": existing}
        record = {"role": role, "token": token, "reservation_id": uuid.uuid4().hex,
                  "started_utc": utc(), "pid_at_reservation": os.getpid()}
        write_atomic(root / "active.json", record)
        return {"ok": True, "state": "reserved", "active": record}
    return locked(root, operation)


def release(root, role, token, reservation_id):
    if (role not in ROLE or not TOKEN.fullmatch(token)
            or not re.fullmatch(r"[0-9a-f]{32}", reservation_id)):
        raise ValueError("unsupported role, invalid token or reservation ID")

    def operation():
        existing = read_active(root)
        if existing is None:
            return {"ok": False, "state": "missing"}
        if (existing.get("role") != role or existing.get("token") != token
                or existing.get("reservation_id") != reservation_id):
            return {"ok": False, "state": "not-owner", "active": existing}
        (root / "active.json").unlink()
        return {"ok": True, "state": "released", "reservation_id": existing["reservation_id"]}
    return locked(root, operation)


def status(root):
    return {"active": read_active(root), "lock_present": (root / "operation.lock").exists(),
            "shared_enforcement_enabled": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("reserve", "release"):
        p = sub.add_parser(command)
        p.add_argument("--role", choices=ROLE, required=True)
        p.add_argument("--token", required=True)
        if command == "release":
            p.add_argument("--reservation-id", required=True)
    sub.add_parser("status")
    args = parser.parse_args()
    root = args.state_dir.resolve()
    if args.command == "reserve":
        result = reserve(root, args.role, args.token)
    elif args.command == "release":
        result = release(root, args.role, args.token, args.reservation_id)
    else:
        result = status(root)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    if result.get("ok") is False:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
