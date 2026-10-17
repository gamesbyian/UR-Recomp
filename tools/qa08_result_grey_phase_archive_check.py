#!/usr/bin/env python3
"""Archive-only 2014 Snes9x / RF017 Win32 QA08 results grey-phase witness.

Not original/native guest equivalence or permission to offset output frames.
All actual producer ZIPs, 263 image SHA manifests and 5484 guest CRCs pinned.
"""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

ORIG_BUNDLE = "3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e"
ORIG_NESTED = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
WINDOWS_ZIP = "91e0bf8f5d7b86b188526740d825af890a99b02ecc05093f9a2143fa56ce49cd"
ROUTE = "ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
GUEST = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
P7 = b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
PIXELS = 256 * 224
FIELDS = range(1280, 5473, 16)
RESULTS = range(4032, 5473, 16)
PEAKS = set(range(4064, 5409, 112))


def sha(data):
    return sha256(data).hexdigest()


def loaded(original_bundle: Path, windows_zip: Path):
    original_bytes, native_bytes = original_bundle.read_bytes(), windows_zip.read_bytes()
    if sha(original_bytes) != ORIG_BUNDLE or sha(native_bytes) != WINDOWS_ZIP:
        raise ValueError("source-epoch archive SHA mismatch")
    with ZipFile(BytesIO(original_bytes)) as bundle:
        nested = bundle.read("original.zip")
    if sha(nested) != ORIG_NESTED:
        raise ValueError("original nested Snes9x SHA mismatch")
    original, native = {}, {}
    with ZipFile(BytesIO(nested)) as o, ZipFile(BytesIO(native_bytes)) as n:
        om = json.loads(o.read("qa08-original-2p-fullroute.json"))
        nm = json.loads(n.read("qa08-windows-2p-fullroute.json"))
        if len(om["each_authentic_callback"]) != 263 or nm["actual_source_count"] != 263:
            raise ValueError("not the 263 original/native source callbacks")
        if (nm["actual_native_simulations"] != 5484
                or nm["actual_two_pad_route_sha256"] != ROUTE
                or nm["actual_native_guest_CRC_sha256"] != GUEST
                or not nm["current_RF017_5484_guest_CRC_exact_match_to_firstline_only"]):
            raise ValueError("native guest/input epoch differs from source control")
        oh = {x["original_1based_frame"]: x["original_unchanged_BGRX_sha256"]
              for x in om["each_authentic_callback"]}
        nh = nm["source_frame_P7_SHA256_by_guest"]
        for f in FIELDS:
            a = o.read(f"frames/frame_{f - 1:06d}_256x224.raw")
            b = n.read(f"source/ur-baldosa-original-source-{f:06d}.pam")
            if (len(a) != PIXELS * 4 or sha(a) != oh.get(f)
                    or not b.startswith(P7) or len(b) != len(P7) + PIXELS * 4
                    or sha(b) != nh.get(str(f))):
                raise ValueError(f"corrupt/cropped or unauthenticated source frame {f}")
            original[f], native[f] = a, b[len(P7):]
    return original, native


def frame_large_counts(original_bytes, native_bytes, future_original=None):
    wrong = large = forward = 0
    for pos in range(0, PIXELS * 4, 4):
        # Original raw B,G,R,X, native post-PPU P7 R,G,B,A.
        o = (original_bytes[pos + 2] >> 3, original_bytes[pos + 1] >> 3,
             original_bytes[pos] >> 3)
        n = (native_bytes[pos] >> 3, native_bytes[pos + 1] >> 3,
             native_bytes[pos + 2] >> 3)
        if o != n:
            wrong += 1
        if max(abs(a - b) for a, b in zip(o, n)) > 1:
            large += 1
            if future_original is not None:
                future = (future_original[pos + 2] >> 3, future_original[pos + 1] >> 3,
                          future_original[pos] >> 3)
                forward += (future == n)
    return wrong, large, forward


def result_large_colour_components(original_bytes, native_bytes):
    """Separate palette-phase greys from fixed-position chromatic source faults.

    Actual 2014 Snes9x BGRX and original-size Win32 P7 RGBA. One RGB5
    step is excluded here; no image repair, temporal re-registration or
    rendering override is performed.
    """
    if len(original_bytes) != PIXELS * 4 or len(native_bytes) != PIXELS * 4:
        raise ValueError("result image was cropped or source bytes missing")
    grey_pairs = {}
    non_grey_positions = []
    for position in range(PIXELS):
        off = position * 4
        original = (original_bytes[off + 2] >> 3,
                    original_bytes[off + 1] >> 3,
                    original_bytes[off] >> 3)
        native = (native_bytes[off] >> 3,
                  native_bytes[off + 1] >> 3,
                  native_bytes[off + 2] >> 3)
        if max(abs(a - b) for a, b in zip(original, native)) <= 1:
            continue
        if original[0] == original[1] == original[2] and (
                native[0] == native[1] == native[2]):
            key = (native[0], original[0])
            grey_pairs[key] = grey_pairs.get(key, 0) + 1
        else:
            non_grey_positions.append(position)
    return grey_pairs, tuple(non_grey_positions)


def measure(original, native):
    values = []
    all_grey_pairs = {}
    chromatic_masks = {}
    for f in RESULTS:
        wrong, large, forward = frame_large_counts(
            original[f], native[f], original.get(f + 32) if f in PEAKS else None)
        values.append((f, wrong, large, forward))
        if large:
            grey_pairs, chromatic_positions = result_large_colour_components(
                original[f], native[f])
            if sum(grey_pairs.values()) + len(chromatic_positions) != large:
                raise ValueError("not all large original/native errors classified")
            for key, count in grey_pairs.items():
                all_grey_pairs[key] = all_grey_pairs.get(key, 0) + count
            if chromatic_positions:
                chromatic_masks[f] = chromatic_positions
    chromatic_hashes = {
        f: sha(b"".join(pos.to_bytes(4, "little") for pos in positions))
        for f, positions in chromatic_masks.items()
    }
    static_positions = next(iter(chromatic_masks.values()), ())
    bounding_box = [
        min((pos % 256 for pos in static_positions), default=-1),
        min((pos // 256 for pos in static_positions), default=-1),
        max((pos % 256 for pos in static_positions), default=-1),
        max((pos // 256 for pos in static_positions), default=-1)
    ]
    phase_grey_count = sum(all_grey_pairs.values())
    chromatic_count = sum(len(x) for x in chromatic_masks.values())
    out = {
        "result_frames": len(values),
        "original_native_wrong_RGB5_pixels": sum(v[1] for v in values),
        "large_greater_than_one_RGB5": sum(v[2] for v in values),
        "large_on_thirteen_112_frame_pulses": sum(v[2] for v in values if v[0] in PEAKS),
        "same_position_native_equals_original_at_plus32_within_pulse": sum(v[3] for v in values),
        "pulse_count": len(PEAKS),
        "pulse_spacing_guest_frames": 112,
        "large_source_components": {
            "phase_grey_pulses": phase_grey_count,
            "palette_pairs_native_to_original": {
                f"{native}_to_{original}": count
                for (native, original), count in sorted(all_grey_pairs.items())
            },
            "identical_chromatic_masks": len(set(chromatic_hashes.values())) == 1,
            "chromatic_mask_occurrences": len(chromatic_masks),
            "chromatic_mask_frames": sorted(chromatic_masks),
            "pixels_per_chromatic_mask": len(static_positions),
            "chromatic_large_error_pixels": chromatic_count,
            "mask_xy_bounding_box_inclusive": bounding_box,
            "chromatic_mask_index_le_u32_sha256": (
                next(iter(chromatic_hashes.values()), "")),
            "all_source_large_errors_disjointly_classified":
                phase_grey_count + chromatic_count ==
                sum(v[2] for v in values)
        },
        "global_frame_shift_admitted": False,
        "CPU_or_CGRAM_causality_proven": False,
        "release_approved": False
    }
    observed = tuple(out[k] for k in ("result_frames", "original_native_wrong_RGB5_pixels",
                   "large_greater_than_one_RGB5", "large_on_thirteen_112_frame_pulses",
                   "same_position_native_equals_original_at_plus32_within_pulse", "pulse_count"))
    if observed != (91, 599536, 165366, 159339, 157027, 13):
        raise ValueError("primary-source grey result phase observation changed")
    components = out["large_source_components"]
    if (phase_grey_count != 158191
            or all_grey_pairs != {(17, 20): 104533, (20, 15): 53658}
            or chromatic_count != 7175
            or len(chromatic_masks) != 25
            or not components["identical_chromatic_masks"]
            or len(static_positions) != 287
            or bounding_box != [202, 91, 227, 153]
            or components["chromatic_mask_index_le_u32_sha256"] !=
               "9331534bc26928e66949644303bf1f4ae9b1185436f0090923a1f6dd6219da15"):
        raise ValueError("original/native large-error pixel provenance drift")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-bundle", type=Path, required=True)
    p.add_argument("--windows-source", type=Path, required=True)
    a = p.parse_args()
    original, native = loaded(a.original_bundle, a.windows_source)
    print(json.dumps(measure(original, native), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
