"""Fail-closed OpenSCAD color-pass extraction for offline, unapproved ART-4K blockouts.

OpenSCAD STL discards color(). Render each source-owned material separately,
keeping geometry under a common articulated GLB part pivot. Only the bounded
SCAD grammar used by the recovered blockout is supported.
"""
from __future__ import annotations

import re
from collections import OrderedDict

_MODULE = re.compile(r'\bmodule\s+([A-Za-z_]\w*)\s*\(')
_COLOR = re.compile(r'\bcolor\s*\(\s*(rig_color|\[\s*[^\[\]()]+\s*\])\s*\)')
_ANY_COLOR = re.compile(r'\bcolor\s*\(')
_NUMBER = re.compile(r'\A\s*(?:\d+(?:\.\d*)?|\.\d+)\s*\Z')
_RIG_DEFAULT = re.compile(
    r'\brig_color\s*=\s*is_undef\s*\(\s*rig_color\s*\)\s*\?\s*'
    r'(\[[^\[\]()]+\])\s*:\s*rig_color\s*;')
# Subtractive CSG does not distribute across separately rendered color passes.
# Until whole-part equivalence is checked, reject it in reachable modules.
_UNSUPPORTED_CSG = re.compile(r'\b(?:difference|intersection|intersection_for)\s*\(')
# Hull and Minkowski are additive but still do not distribute across
# separately colored children. A single enclosing color is safe.
_ADDITIVE_CSG = re.compile(r'\b(?:hull|minkowski)\s*\(\s*\)\s*(\{)?')


def _mask_comments(source: str) -> str:
    """Retain offsets while removing SCAD comments, honoring quoted strings."""
    chars = list(source)
    i = 0
    quoted = False
    while i < len(source):
        if quoted:
            if source[i] == '\\':
                i += 2
                continue
            if source[i] == '"':
                quoted = False
            i += 1
        elif source[i] == '"':
            quoted = True
            i += 1
        elif source.startswith('//', i):
            j = source.find('\n', i)
            j = len(source) if j < 0 else j
            chars[i:j] = ' ' * (j-i)
            i = j
        elif source.startswith('/*', i):
            j = source.find('*/', i+2)
            if j < 0:
                raise ValueError('unterminated SCAD comment')
            j += 2
            chars[i:j] = ['\n' if c == '\n' else ' ' for c in source[i:j]]
            i = j
        else:
            i += 1
    if quoted:
        raise ValueError('unterminated SCAD string')
    return ''.join(chars)


def _body_end(masked: str, opening: int) -> int:
    depth = 1
    quote = False
    i = opening+1
    while i < len(masked):
        c = masked[i]
        if quote:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                quote = False
        elif c == '"':
            quote = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('unterminated SCAD module')


def _modules(source: str) -> dict[str, str]:
    masked = _mask_comments(source)
    result = {}
    for match in _MODULE.finditer(masked):
        name = match.group(1)
        if name in result:
            raise ValueError('duplicate SCAD module: '+name)
        opening = masked.find('{', match.end())
        if opening < 0 or ';' in masked[match.end():opening]:
            raise ValueError('unsupported SCAD module declaration: '+name)
        result[name] = masked[opening+1:_body_end(masked, opening)]
    return result


def _rgba(expression: str, rig_default: str) -> tuple[int, int, int, int]:
    raw = rig_default if expression.strip() == 'rig_color' else expression
    if not raw.startswith('[') or not raw.endswith(']'):
        raise ValueError('unsupported SCAD material color')
    values = raw[1:-1].split(',')
    if len(values) not in (3, 4) or not all(_NUMBER.fullmatch(v) for v in values):
        raise ValueError('unsupported SCAD material color components')
    floats = [float(v) for v in values]
    if any(v < 0 or v > 1 for v in floats):
        raise ValueError('SCAD material color outside 0..1')
    if len(floats) == 3:
        floats.append(1.0)
    return tuple(int(v*255 + 0.5) for v in floats)


def _color_data(source: str):
    masked = _mask_comments(source)
    defaults = _RIG_DEFAULT.findall(masked)
    if len(defaults) != 1:
        raise ValueError('expected one source-owned rig_color default')
    matches = list(_COLOR.finditer(masked))
    if len(matches) != len(_ANY_COLOR.findall(masked)):
        raise ValueError('unsupported OpenSCAD color() expression')
    by_start = {m.start(): _rgba(m.group(1), defaults[0]) for m in matches}
    return masked, matches, by_start


def materials_for_part(source: str, part: str) -> list[tuple[int, int, int, int]]:
    """Discover all color groups in the part's transitive source module calls."""
    modules = _modules(source)
    if part not in modules:
        raise ValueError('missing source part module: '+part)
    _, _, _ = _color_data(source)
    defaults = _RIG_DEFAULT.findall(_mask_comments(source))[0]
    visited = set()
    colors = OrderedDict()

    def nested_colors(text: str, seen: frozenset[str]) -> set[tuple[int, int, int, int]]:
        """Find colors inside a CSG child, including called helper modules."""
        found = {_rgba(m.group(1), defaults) for m in _COLOR.finditer(text)}
        for called, subbody in modules.items():
            if called not in seen and re.search(r'\b'+re.escape(called)+r'\s*\(', text):
                found.update(nested_colors(subbody, seen | {called}))
        return found

    def guard_additive_csg(body: str, name: str) -> None:
        for operator in _ADDITIVE_CSG.finditer(body):
            if not operator.group(1):
                raise ValueError('unsupported unbraced OpenSCAD additive CSG: ' + name)
            # _body_end expects the opening brace, included in the regex match.
            child = body[operator.end():_body_end(body, operator.end()-1)]
            if len(nested_colors(child, frozenset())) > 1:
                raise ValueError('non-distributive OpenSCAD CSG needs whole-part material equivalence: ' + name)

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        body = modules[name]
        if _UNSUPPORTED_CSG.search(body):
            raise ValueError('non-distributive OpenSCAD CSG needs whole-part material equivalence: ' + name)
        guard_additive_csg(body, name)
        matches = list(_COLOR.finditer(body))
        if len(matches) != len(_ANY_COLOR.findall(body)):
            raise ValueError('unsupported OpenSCAD color() in '+name)
        for match in matches:
            rgba = _rgba(match.group(1), defaults)
            colors[rgba] = None
        for called in modules:
            if re.search(r'\b'+re.escape(called)+r'\s*\(', body):
                visit(called)
    visit(part)
    if not colors:
        raise ValueError('source part has no material colors: '+part)
    return list(colors)


def material_pass_source(source: str, rgba: tuple[int, int, int, int]) -> str:
    """Replace SCAD color decorators with matching/other pass predicates.

    OpenSCAD if(true) preserves the source child geometry, while if(false)
    removes only that colored geometry. No color is guessed.
    """
    _, matches, by_start = _color_data(source)
    result = []
    offset = 0
    for match in matches:
        result.append(source[offset:match.start()])
        result.append('if (true)' if by_start[match.start()] == rgba else 'if (false)')
        offset = match.end()
    result.append(source[offset:])
    return ''.join(result)


# The sentinel makes an empty-color geometry probe render a real STL on every
# supported OpenSCAD version. It is deliberately far outside this bounded rig.
UNCOLORED_PROBE_MIN = 100.0


def uncolored_probe_source(source: str) -> str:
    """Suppress every colored child and retain only accidentally uncolored geometry.

    A sole 1x1x1 sentinel at [100,100,100] is the expected output. Any other
    geometry would otherwise leak into *every* material export pass.
    """
    _, matches, _ = _color_data(source)
    result = []
    offset = 0
    for match in matches:
        result.append(source[offset:match.start()])
        result.append('if (false)')
        offset = match.end()
    result.append(source[offset:])
    return ''.join(result) + '\ntranslate([100,100,100]) cube([1,1,1]);\n'
