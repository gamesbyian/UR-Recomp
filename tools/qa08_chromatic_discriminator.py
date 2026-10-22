"""ROM-free H25 QA08 source-colour census from an immutable archive.

This authenticates original source observations, not native CGRAM/PPU parity.
No ROM, capture bytes, or release evidence are embedded in this module.
"""
from pathlib import Path
from collections import Counter
import hashlib
import zipfile

ARCHIVE_SHA = "10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2"


def census(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA:
        raise ValueError("QA08 immutable source archive SHA mismatch")
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError("ambiguous or corrupt QA08 ZIP")
        if "on-source.log" not in names:
            raise ValueError("missing QA08 source observations")
        lines = archive.read("on-source.log").decode("ascii").splitlines()
    if len(lines) != 264:
        raise ValueError("expected 264 source-stage rows")
    source, final = Counter(), Counter()
    identities = set()
    for i in range(0, len(lines), 3):
        a, b, c = lines[i:i + 3]
        if not (a.startswith("UR_QA08_LATE_PPU_SOURCE ") and
                b.startswith("UR_QA08_LATE_PPU_SOURCE ") and
                c.startswith("UR_QA08_LATE_PPU_FINAL ")):
            raise ValueError("source/final triplet ordering")
        try:
            aa = dict(token.split("=", 1) for token in a.split()[1:])
            bb = dict(token.split("=", 1) for token in b.split()[1:])
            cc = dict(token.split("=", 1) for token in c.split()[1:])
            identity = tuple(aa[x] for x in ("frame", "x", "logical_y"))
            if (identity in identities or aa["sub"] != "0" or bb["sub"] != "1" or
                    any(bb[x] != aa[x] or cc[x] != aa[x]
                        for x in ("frame", "x", "logical_y"))):
                raise ValueError("duplicate or mismatched stage")
            identities.add(identity)
            word = int(aa["selected_rgb555"], 16)
            colour = tuple(int(x) for x in cc["RGB8"].split(","))
        except (ValueError, KeyError) as exc:
            raise ValueError("malformed QA08 colour observation") from exc
        if not 0 <= word <= 0x7fff or len(colour) != 3 or any(not 0 <= c <= 255 for c in colour):
            raise ValueError("noncanonical QA08 colour")
        source[tuple((word >> shift) & 31 for shift in (0, 5, 10))] += 1
        final[colour] += 1
    grayscale = all(len(set(v)) == 1 for v in source) and all(len(set(v)) == 1 for v in final)
    return {"triplets": 88, "unique_source_rgb555": len(source),
            "unique_final_rgb8": len(final),
            "all_observed_source_and_final_are_grayscale": grayscale,
            "same_epoch_native_effective_ppu_proven": False, "release_gate_credit": 0}
