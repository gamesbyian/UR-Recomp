"""Recovered H25 first-party design for a *future* QA08 chromatic witness.

Grayscale observations cannot distinguish the six RGB channel permutations
or two competing integer brightness scalings. This predicts the smallest
useful next genuine observation; never treats prediction as measurement.
"""
from itertools import permutations
from qa08_chromatic_discriminator import census

CHANNEL5 = (5, 13, 22)
SCALINGS = ((14, 15), (187, 200))


def expand5(value):
    if type(value) is not int or not 0 <= value <= 31:
        raise ValueError("invalid 5-bit channel")
    return (value << 3) | (value >> 2)


def model_predictions(channels=CHANNEL5):
    if (type(channels) is not tuple or len(channels) != 3 or
            any(type(v) is not int or not 0 <= v <= 31 for v in channels)):
        raise ValueError("invalid RGB5 probe")
    predictions = {}
    for perm in permutations((0, 1, 2)):
        for numerator, denominator in SCALINGS:
            predictions[f"perm{perm}-scale{numerator}/{denominator}"] = tuple(
                expand5(channels[i]) * numerator // denominator for i in perm)
    return predictions


def design(path):
    evidence = census(path)
    if not evidence["all_observed_source_and_final_are_grayscale"]:
        raise ValueError("chromatic observation already exists; redesign probe")
    predictions = model_predictions()
    if len(set(predictions.values())) != 12:
        raise ValueError("candidate does not distinguish all twelve hypotheses")
    r, g, b = CHANNEL5
    return {"schema": "qa08-chromatic-source-probe-request/1",
            "candidate_rgb555_hex": f"{r | (g << 5) | (b << 10):04x}",
            "channel5": list(CHANNEL5),
            "hypotheses_distinguished": 12,
            "hypothesis_predictions": predictions,
            "observed_source_triplets": evidence["triplets"],
            "chromatic_pixel_observed": False,
            "same_epoch_native_effective_ppu_proven": False,
            "release_gate_credit": 0}
