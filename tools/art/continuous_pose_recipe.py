"""Fail-closed OpenSCAD continuous-rig sampling for experimental ART-4K GLBs.

This parser intentionally supports only the canonical authored formula, not a
general OpenSCAD interpreter. Unrecognized refits must be reviewed explicitly.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_NUMBER = r"(?:\d+(?:\.\d*)?|\.\d+)"
_COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
_FUNCTION_DECLARATION = re.compile(r"\bfunction\s+([A-Za-z_]\w*)\s*\(")
_MODULE_DECLARATION = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*\(")
# OpenSCAD also allows user modules to shadow the builtin transforms and
# primitives used by this canonical rig. The receipt must not assume that a
# literal rotate()/translate() in the formula invokes the real builtin.
_RIG_BUILTIN_MODULES = frozenset({
    "translate", "rotate", "scale", "color", "union", "hull", "minkowski",
    "sphere", "cube", "cylinder", "rotate_extrude", "circle",
})
_FORMULA = re.compile(
    r"modulecontinuous_rig\(time,spin=false\)\{"
    r"u=unit_time\(time\);pitch=spin\?(?P<spin>" + _NUMBER + r")\*ease_time\(u\):0;"
    r"translate\(\[0,0,(?P<pivot>" + _NUMBER + r")\]\)"
    r"rotate\(\[0,-pitch,0\]\)"
    r"translate\(\[0,0,-(?P<back>" + _NUMBER + r")\]\)"
    r"rotate\(\[(?P<wobble>" + _NUMBER + r")\*sin\((?P<wobble_rate>" + _NUMBER + r")\*u\),"
    r"0,(?P<bank>" + _NUMBER + r")\*sin\((?P<bank_rate>" + _NUMBER + r")\*u\)\]\)"
    r"shared_rig\(pedal=(?P<pedal_base>" + _NUMBER + r")\+(?P<pedal_rate>" + _NUMBER + r")\*u,"
    r"seat_lean=(?P<lean>" + _NUMBER + r")\*sin\((?P<lean_rate>" + _NUMBER + r")\*u\)\);\}"
)


def _multiply(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(4))
                       for j in range(4)) for i in range(4))


def _translate(z):
    return ((1., 0., 0., 0.), (0., 1., 0., 0.),
            (0., 0., 1., z), (0., 0., 0., 1.))


def _rotate(axis, angle):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    if axis == "x":
        return ((1., 0., 0., 0.), (0., c, -s, 0.),
                (0., s, c, 0.), (0., 0., 0., 1.))
    return ((c, 0., s, 0.), (0., 1., 0., 0.),
            (-s, 0., c, 0.), (0., 0., 0., 1.)) if axis == "y" else (
            (c, -s, 0., 0.), (s, c, 0., 0.),
            (0., 0., 1., 0.), (0., 0., 0., 1.))


def continuous_pose_recipe(source: str, name: str, time: float):
    """Return rendered crank phase, saddle lean, world transform and source metadata.

    The 1994 game's frame cadence, geometry and likeness are NOT inferred.
    """
    if name not in ("ride", "stunt_cycle"):
        raise ValueError("unknown continuous blockout pose")
    if not isinstance(time, (int, float)) or not math.isfinite(time) or not 0 <= time <= 1:
        raise ValueError("continuous rig time must be finite and within 0..1")
    uncommented = _COMMENTS.sub("", source)
    functions = Counter(_FUNCTION_DECLARATION.findall(uncommented))
    duplicates = sorted(name for name, count in functions.items() if count > 1)
    if duplicates:
        # OpenSCAD silently lets later function declarations override earlier
        # ones, even with a different formal argument name. A canonical body
        # still present in the source does not prove which body rendered.
        raise ValueError("duplicate OpenSCAD function declaration: " + ", ".join(duplicates))
    # A SINGLE user function can also shadow an OpenSCAD builtin. The authored
    # continuous formula uses sin/min/max; the shared rig uses cos/is_undef.
    # Python's recipe would otherwise evaluate the original builtin while
    # OpenSCAD renders the shadowed function, producing a false source match.
    shadowed = sorted(set(functions) & {"sin", "cos", "min", "max", "is_undef"})
    if shadowed:
        raise ValueError("OpenSCAD builtin function shadowed: " + ", ".join(shadowed))
    modules = Counter(_MODULE_DECLARATION.findall(uncommented))
    # OpenSCAD also resolves duplicate user-defined modules to the later
    # declaration. A second shared_rig(), rig() or part helper can change
    # the rendered mesh while the recognized continuous formula remains.
    duplicate_modules = sorted(name for name, count in modules.items() if count > 1)
    if duplicate_modules:
        raise ValueError("duplicate OpenSCAD module declaration: "
                         + ", ".join(duplicate_modules))
    shadowed_modules = sorted(set(modules) & _RIG_BUILTIN_MODULES)
    if shadowed_modules:
        raise ValueError("OpenSCAD builtin module shadowed: " + ", ".join(shadowed_modules))
    clean = re.sub(r"\s+", "", uncommented)
    if (clean.count("functionunit_time(t)=min(1,max(0,t));") != 1
            or clean.count("functionease_time(t)=let(u=unit_time(t))u*u*(3-2*u);") != 1
            or clean.count("modulecontinuous_rig(") != 1
            or clean.count('elseif(p=="ride")continuous_rig(rig_time,false);') != 1
            or clean.count('elseif(p=="stunt_cycle")continuous_rig(rig_time,true);') != 1):
        raise ValueError("unsupported continuous rig source contract")
    matches = list(_FORMULA.finditer(clean))
    if len(matches) != 1:
        raise ValueError("unsupported continuous rig formula")
    values = {k: float(v) for k, v in matches[0].groupdict().items()}
    if values["pivot"] != values["back"]:
        raise ValueError("continuous rig pivot is not reversible")
    u = float(time)
    sine = lambda rate: math.sin(math.radians(rate * u))
    pitch = values["spin"] * (u * u * (3 - 2 * u)) if name == "stunt_cycle" else 0.
    bank = values["bank"] * sine(values["bank_rate"])
    wobble = values["wobble"] * sine(values["wobble_rate"])
    unwrapped = values["pedal_base"] + values["pedal_rate"] * u
    pedal = unwrapped % 360.
    lean = values["lean"] * sine(values["lean_rate"])
    matrix = _translate(values["pivot"])
    for part in (_rotate("y", -pitch), _translate(-values["pivot"]),
                 _rotate("z", bank), _rotate("x", wobble)):
        matrix = _multiply(matrix, part)
    return pedal, lean, matrix, {
        "rig_time": u, "pedal_phase_unwrapped_degrees": unwrapped,
        "continuous_pitch_degrees": pitch, "continuous_bank_degrees": bank,
        "continuous_wobble_degrees": wobble,
        "source_formula_validated": True,
    }
