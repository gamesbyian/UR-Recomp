from tools.analyze_rom_lineage_deltas import (
    beta_delta_classes,
    coalesce,
    equality_signature,
)


def test_equality_signature_preserves_build_groups():
    assert equality_signature((1, 2, 1, 2)) == "usa+beta|europe+prototype"
    assert equality_signature((1, 2, 1, 3)) == "usa+beta|europe|prototype"


def test_coalesce_requires_adjacent_same_signature():
    rows = [
        {"offset": 2, "signature": "A", "values": {}},
        {"offset": 3, "signature": "A", "values": {}},
        {"offset": 4, "signature": "B", "values": {}},
        {"offset": 6, "signature": "B", "values": {}},
    ]
    runs = coalesce(rows)
    assert [(r["start"], r["end_inclusive"], r["signature"]) for r in runs] == [
        (2, 3, "A"),
        (4, 4, "B"),
        (6, 6, "B"),
    ]


def test_beta_delta_cross_classification():
    blobs = {
        "usa": bytes([1, 2, 3]),
        "europe": bytes([1, 9, 8]),
        "beta": bytes([1, 7, 4]),
        "prototype": bytes([1, 7, 3]),
    }
    out = beta_delta_classes(blobs, bytearray(3))
    assert out["counts"]["europe=other,prototype=beta"] == 1
    assert out["counts"]["europe=other,prototype=usa"] == 1
