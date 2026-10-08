#!/usr/bin/env python3
"""Classify changed paths for the heavyweight Modern native CI suites.

The manifests mirror the current pull-request path filters. A future router can
use this classifier to preserve suite selectivity while sharing one native build.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = {
    "shared": ROOT / ".github/ci/modern-native-shared-paths.txt",
    "onboarding": ROOT / ".github/ci/modern-native-onboarding-paths.txt",
    "ui": ROOT / ".github/ci/modern-native-ui-paths.txt",
}


def load_patterns(path: Path) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Translate the subset of GitHub path globs used by these manifests."""
    out: list[str] = ["^"]
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def path_matches(path: str, pattern: str) -> bool:
    return bool(_glob_regex(pattern).match(path))


def classify_paths(paths: Iterable[str]) -> dict[str, bool]:
    changed = tuple(dict.fromkeys(p.strip() for p in paths if p.strip()))
    result: dict[str, bool] = {}
    for suite, manifest in MANIFESTS.items():
        patterns = load_patterns(manifest)
        result[suite] = any(
            path_matches(path, pattern)
            for path in changed
            for pattern in patterns
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument(
        "--paths-file",
        type=Path,
        help="newline-delimited changed paths",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="also write suite=true/false lines for GITHUB_OUTPUT",
    )
    args = parser.parse_args()

    paths = list(args.paths)
    if args.paths_file:
        paths.extend(args.paths_file.read_text().splitlines())

    result = classify_paths(paths)
    print(json.dumps(result, sort_keys=True))

    if args.github_output:
        with args.github_output.open("a") as output:
            for suite, enabled in sorted(result.items()):
                output.write(f"{suite}={'true' if enabled else 'false'}\n")
            output.write(
                "any_heavy="
                f"{'true' if any(result.values()) else 'false'}\n"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
