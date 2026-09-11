#!/usr/bin/env python3
"""Check the saved part against vendor data and KiCad's own readers."""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
import generate as source


def parse(text):
    stack, root = [], None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            node = []
            if stack:
                stack[-1].append(node)
            else:
                assert root is None
                root = node
            stack.append(node)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack
    return root


def children(node, key):
    return [x for x in node if isinstance(x, list) and x[0] == key]


def one(node, key):
    return children(node, key)[0]


def check_symbol(path, expected):
    library = parse(path.read_text())
    symbol = one(library, "symbol")
    assert symbol[1] == "A523"
    units = children(symbol, "symbol")
    assert len(units) == 14
    assert {u[1] for u in units} == {f"A523_{i}_1" for i in range(1, 15)}
    found = {}
    for unit in units:
        positions = set()
        for pin in children(unit, "pin"):
            ball, name = one(pin, "number")[1], one(pin, "name")[1]
            assert ball not in found, ball
            assert name == expected[ball]["name"], ball
            assert pin[1] == source.electrical_type(expected[ball]), ball
            assert "hide" not in pin
            at = tuple(float(x) for x in one(pin, "at")[1:3])
            assert at not in positions, (unit[1], ball)
            assert all(abs(v / 1.27 - round(v / 1.27)) < 0.00001 for v in at)
            positions.add(at)
            found[ball] = name
    assert set(found) == set(expected)
    footprint = next(p[2] for p in children(symbol, "property") if p[1] == "Footprint")
    assert footprint == f"{source.LIB}:{source.FP}"
    return found


def main():
    sheets = source.workbook()
    expected = {p["ball"]: p for p in source.read_pins(sheets)}
    source.check_vendor_geometry(list(expected.values()))
    sym = source.HERE / "A523.kicad_sym"
    original = check_symbol(sym, expected)
    with tempfile.TemporaryDirectory(prefix="a523-verify-") as directory:
        canonical = Path(directory) / "A523.kicad_sym"
        subprocess.run(["kicad-cli", "sym", "upgrade", "--force", "--output", str(canonical), str(sym)], check=True)
        assert check_symbol(canonical, expected) == original

    import pcbnew
    fp = pcbnew.FootprintLoad(str(source.HERE / "A523.pretty"), source.FP)
    assert fp is not None and fp.GetPadCount() == 522
    pads = {p.GetNumber(): p for p in fp.Pads()}
    assert set(pads) == set(expected)
    assert fp.GetLocalSolderMaskMargin() == pcbnew.FromMM(0.05)
    assert fp.GetLocalSolderPasteMargin() == pcbnew.FromMM(0.025)
    assert fp.GetLocalSolderPasteMarginRatio() == 0
    for ball, pad in pads.items():
        x, y = source.position(ball)
        assert (pad.GetPosition().x, pad.GetPosition().y) == (pcbnew.FromMM(x), pcbnew.FromMM(y))
        assert pad.GetSize().x == pad.GetSize().y == pcbnew.FromMM(0.27)
        assert pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
        assert pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        assert set(pad.GetLayerSet().Seq()) == {pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste}
    for table, suffix in (("sym-lib-table", "A523.kicad_sym"), ("fp-lib-table", "A523.pretty")):
        entries = children(parse((source.HERE.parent / table).read_text()), "lib")
        entry = next(e for e in entries if one(e, "name")[1] == source.LIB)
        assert one(entry, "uri")[1] == "${KIPRJMOD}/A523/" + suffix
    print("PASS: 522 unique pins in 14 units; 522 matching round SMD pads; no hidden or stacked pins.")
    print("PASS: vendor ball map and footprint geometry; KiCad symbol round-trip and footprint load.")
    print("PASS: pad positions, layers, copper/mask/paste sizes, pin types, and library association.")


if __name__ == "__main__":
    main()
