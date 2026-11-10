#!/usr/bin/env python3
"""Offline fail-closed coherence check for manually proposed CI batches.

NOT proof of actual GitHub heads/diffs, mergeability, correct test routing,
Windows binaries, HP trust or release acceptance.
"""
import argparse
import json
import re
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,100}\Z")


def validate_manifest(d):
    if type(d) is not dict or set(d) != {"schema", "batch_id", "base_sha", "candidate_sha", "members"}:
        raise ValueError("unexpected or absent manifest keys")
    if type(d["schema"]) is not int or d["schema"] != 1 or type(d["batch_id"]) is not str or not ID.fullmatch(d["batch_id"]):
        raise ValueError("invalid schema or batch ID")
    for key in ("base_sha", "candidate_sha"):
        if type(d[key]) is not str or not SHA.fullmatch(d[key]):
            raise ValueError("invalid " + key)
    if d["base_sha"] == d["candidate_sha"]:
        raise ValueError("candidate equals base")
    members = d["members"]
    if type(members) is not list or not 2 <= len(members) <= 5:
        raise ValueError("expected 2 to 5 members")
    ids, prs, heads, paths = set(), set(), set(), {}
    for member in members:
        if type(member) is not dict or set(member) != {"work_id", "pr", "head_sha", "changed_paths"}:
            raise ValueError("invalid member fields")
        wid, pr, head = member["work_id"], member["pr"], member["head_sha"]
        if type(wid) is not str or not ID.fullmatch(wid) or type(pr) is not int or pr < 1:
            raise ValueError("invalid work ID or PR number")
        if type(head) is not str or not SHA.fullmatch(head):
            raise ValueError("invalid head SHA")
        if wid in ids or pr in prs or head in heads:
            raise ValueError("duplicate member identity")
        ids.add(wid)
        prs.add(pr)
        heads.add(head)
        changed = member["changed_paths"]
        if type(changed) is not list or not changed:
            raise ValueError("missing changed-file inventory")
        local = set()
        for path in changed:
            if (type(path) is not str or not path or path.startswith(("/", "\\"))
                    or "\\" in path or any(c in path for c in "\x00\r\n")
                    or any(segment in ("", ".", "..") for segment in path.split("/"))):
                raise ValueError("noncanonical repository path")
            for segment in path.split("/"):
                stem = segment.split(".")[0].upper()
                if (segment.endswith((" ", "."))
                        or any(ord(char) < 32 or char in '<>:"|?*' for char in segment)
                        or stem in ("CON", "PRN", "AUX", "NUL")
                        or stem in {"COM" + str(n) for n in range(1, 10)}
                        or stem in {"LPT" + str(n) for n in range(1, 10)}):
                    raise ValueError("path incompatible with Windows checkout")
            folded = path.casefold()
            if folded in local:
                raise ValueError("duplicate path within a member")
            if any(folded == earlier or folded.startswith(earlier + "/")
                   or earlier.startswith(folded + "/") for earlier in paths):
                raise ValueError("overlap: " + path)
            local.add(folded)
            paths[folded] = wid
    return {"status": "manifest-coherent-only", "batch_id": d["batch_id"],
            "members": len(members), "declared_paths": len(paths),
            "live_github_heads_and_diffs_verified": False,
            "required_exact_candidate_tests_executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(2, "candidate rejected: " + str(error) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
