#!/usr/bin/env python3
"""Regenerate the A523 library from the checked-in vendor sources (stdlib only)."""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[2] / "docs/a523"
ROWS = "A B C D E F G H J K L M N P R T U V W Y AA AB AC AD AE AF AG AH AJ".split()
FP = "Allwinner_A523_FCCSP-522_15x15mm_P0.5mm"
LIB = "A523"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PINOUT = DOCS / "A523_PINOUT_V1.4.xlsx"
VENDOR_FP = DOCS / "A523_hwref/PCB参考/SoC套片PCB封装库/A523_SOC_Symbol.zip"


def workbook():
    with ZipFile(PINOUT) as z:
        strings = ["".join(t.text or "" for t in e.findall(".//m:t", NS))
                   for e in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        sheets = {}
        for i in (2, 3, 5):
            rows = []
            xml = ET.fromstring(z.read(f"xl/worksheets/sheet{i}.xml"))
            for row in xml.findall("m:sheetData/m:row", NS):
                values = {}
                for cell in row:
                    value = cell.find("m:v", NS)
                    if value is not None:
                        col = re.sub(r"\d", "", cell.get("r"))
                        values[col] = (strings[int(value.text)] if cell.get("t") == "s"
                                       else value.text).strip()
                rows.append((int(row.get("r")), values))
            sheets[i] = rows
    return sheets


def read_pins(sheets):
    pins = []
    group = ""
    for row_number, row in sheets[2]:
        ball = row.get("A", "")
        if re.fullmatch(r"[A-Z]+\d+(?:,\s*[A-Z]+\d+)*", ball):
            for b in ball.split(","):
                name = row["B"]
                b = b.strip()
                correction = ""
                # Both the workbook ball map and STD reference schematic confirm these.
                if name == "TEST":
                    assert b == "AE1"
                    b, correction = "AE11", "TEST: AE1 -> AE11"
                if re.fullmatch(r"PB1[0-4]", b):
                    assert name == b
                    b = "L" + str(15 + int(name[2:]))
                    correction = f"{name}: invalid ball {name} -> {b}"
                if name == "VCC_PE":
                    name, correction = "VCC-PE", "VCC_PE -> VCC-PE"
                supply = row["G"]
                if supply == "VCC33-UAB-2":
                    supply = "VCC33-USB-2"
                    correction = "Supply spelling: VCC33-UAB-2 -> VCC33-USB-2"
                pins.append(dict(ball=b, name=name, vendor_type=row["C"], group=group,
                                 supply=supply, source_row=row_number, correction=correction))
        elif len(row) == 1:
            group = ball
    assert len(pins) == len({p["ball"] for p in pins}) == 522

    # Independent worksheet: check occupied balls and every ball-to-signal assignment.
    header = sheets[5][0][1]
    ballmap = {}
    for _, row in sheets[5][1:]:
        if "B" in row:
            for col, name in row.items():
                if col in header and header[col].isdigit() and name:
                    ballmap[row["B"] + header[col]] = name
    assert {p["ball"]: p["name"] for p in pins} == ballmap
    return pins


def check_vendor_geometry(pins):
    with ZipFile(VENDOR_FP) as z:
        path = "A523_SOC_Symbol/BGA522P50B1500_1500H98/BGA522P50B1500_1500H98.asc"
        asc = z.read(path).decode()
    decal = asc.split("*PARTDECAL*")[1].split("*PARTTYPE*")[0]
    coords = re.findall(r"^T(-?\d+)\s+(-?\d+)", decal, re.M)
    names = asc.split(" I UND  0   0   522   0 Y")[1].split("*PART*")[0].split()
    assert len(coords) == len(names) == 522
    assert set(names) == {p["ball"] for p in pins}
    # PADS BASIC units: 1,500,000 per mm. PADS has Y up; KiCad PCB has Y down.
    for name, (x, y) in zip(names, coords):
        expected = position(name)
        actual = (int(x) / 1500000, -int(y) / 1500000)
        assert max(abs(a - b) for a, b in zip(actual, expected)) < 0.0002, name
    # Top copper, solder mask and paste apertures; round vendor export quantization.
    padstack = decal.split("PAD 0 7")[1].strip().splitlines()
    sizes = {int(line.split()[0]): int(line.split()[1]) / 1500000 for line in padstack}
    assert round(sizes[-2], 2) == 0.27
    assert round(sizes[21], 2) == 0.37
    assert round(sizes[23], 2) == 0.32


def position(ball):
    row, column = re.fullmatch(r"([A-Z]+)(\d+)", ball).groups()
    return ((int(column) - 15) * 0.5, (ROWS.index(row) - 14) * 0.5)


def electrical_type(pin):
    # Internal regulator/charge-pump outputs and remote supply-sense taps.
    if pin["name"] in {"ALDO-OUT", "CPVEE", "CPVDD"}:
        return "power_out"
    if pin["name"] == "VRP":
        return "output"  # Datasheet function table: internal analog reference.
    if pin["name"] in {"PCIE-REF-CLKP", "PCIE-REF-CLKN"}:
        return "input"  # Dedicated reference-clock inputs; grounded when unused.
    if pin["name"] in {"VDD-CPUBFB", "VDD-CPULFB", "VDD-SYSFB", "VDD-DNRFB"}:
        return "passive"
    return {"I": "input", "AI": "input", "O": "output", "AO": "output",
            "I/O": "bidirectional", "A I/O": "bidirectional", "I/O, OD": "bidirectional",
            "AO, OD": "open_collector", "P": "power_in", "G": "power_in",
            "N/A": "no_connect"}[pin["vendor_type"]]


def q(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    manifest = json.loads((DOCS / "sources.json").read_text())
    for path in (PINOUT, VENDOR_FP):
        record = next(e for e in manifest["files"] if e["path"] == str(path.relative_to(DOCS)))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    sheets = workbook()
    pins = read_pins(sheets)
    check_vendor_geometry(pins)
    mux = {}
    for _, row in sheets[3]:
        if re.fullmatch(r"P[B-HK-M]\d+", row.get("B", "")):
            mux[row["B"]] = [(n, re.sub(r"\(\d+\)", "", row[c]).strip())
                              for c, n in zip("DEFGHI", (2, 3, 4, 5, 6, 14)) if row.get(c)]
    assert len(mux) == 158
    for p in pins:
        p["electrical_type"] = electrical_type(p)
        p["mux"] = mux.get(p["name"], [])

    def group(*groups):
        return [p for p in pins if p["group"] in groups]

    def select(pattern):
        return [p for p in pins if re.fullmatch(pattern, p["name"])]

    def blocks(*lists):
        result = []
        for values in lists:
            if result:
                result.append(None)
            result.extend(values)
        return result

    data = select(r"SDQ\d+|SDQM\d|SDQS\d[PN]")
    dram = [p for p in group("SDRAM") if p not in data]
    ground = select("GND")
    # Each unit has two pin columns. Gaps preserve functional/rail groupings.
    units = [
        ("DRAM data", data[:16] + data[32:34] + data[36:40],
         data[16:32] + data[34:36] + data[40:44]),
        ("DRAM address / control / power", dram[:24], blocks(dram[24:32], dram[32:])),
        ("System / clocks / boot", blocks(group("System"), select("VCC-EFUSE"), group("Others")),
         blocks(group("RTC&PLL"), group("DCXO"))),
        ("GPIO B / C / F", blocks(group("Port B"), group("Port F")), group("Port C")),
        ("GPIO D / E", group("Port D"), group("Port E")),
        ("GPIO G / H", group("Port G"), group("Port H")),
        ("GPIO K / L / M", group("Port K"), blocks(group("Port L"), group("Port M"))),
        ("USB / PCIe", blocks(group("USB2.0 DRD"), group("USB2.0 Host")), group("PCIe2.1&USB3.1 DRD")),
        ("eDP", group("eDP1.3")[:4] + group("eDP1.3")[12:], group("eDP1.3")[4:12]),
        ("Audio / ADC", blocks(group("Audio Codec")[:6], group("Audio Codec")[12:19], group("GPADC"), group("LRADC")),
         blocks(group("Audio Codec")[6:12], group("Audio Codec")[19:])),
        ("Core power / sense",
         blocks(select("VCC-IO"), select("VDD-CPUS"), select("VDD-CPUB|VDD-CPUBFB"), select("VDD-CPUL|VDD-CPULFB")),
         blocks(select("VDD-SYS|VDD-SYSFB"), select("VDD-VE"), select("VDD-DE"), select("VDD-GPU"), select("VDD-DNR|VDD-DNRFB"))),
        ("Digital ground 1", ground[:31], ground[31:62]),
        ("Digital ground 2", ground[62:93], ground[93:]),
        ("Analog ground", select("AVSS")[:9], select("AVSS")[9:]),
    ]
    used = [p["ball"] for _, left, right in units for p in left + right if p]
    assert Counter(used) == Counter(p["ball"] for p in pins)

    sym = ['(kicad_symbol_lib (version 20241209) (generator "a523_generator")',
           '  (symbol "A523"', '    (pin_names (offset 1.016))',
           '    (exclude_from_sim no) (in_bom yes) (on_board yes)',
           '    (property "Reference" "U" (at 0 15.24 0) (effects (font (size 1.27 1.27))))',
           '    (property "Value" "A523" (at 0 12.7 0) (effects (font (size 1.27 1.27))))',
           f'    (property "Footprint" "{LIB}:{FP}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "Datasheet" "${KIPRJMOD}/../../docs/a523/A523_Datasheet_V1.4.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "Description" "Allwinner A523, octa-core Cortex-A55 SoC, FCCSP-522, 15x15mm, 0.5mm pitch" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "ki_keywords" "Allwinner A523 sun55iw3 sun55i application processor" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "ki_fp_filters" "{FP}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))']
    unit_counts = []
    for index, (title, left, right) in enumerate(units, 1):
        width = 30.48 if title == "USB / PCIe" else 25.4
        bottom = -2.54 * max(len(left), len(right))
        sym += [f'    (symbol "A523_{index}_1"',
                f'      (rectangle (start {-width} 10.16) (end {width} {bottom}) (stroke (width 0.254) (type default)) (fill (type background)))',
                f'      (text {q(title)} (at 0 7.62 0) (effects (font (size 1.27 1.27))))']
        for side, column in ((-1, left), (1, right)):
            for row, p in enumerate(column):
                if p is None:
                    continue
                p["unit"] = chr(64 + index)
                p["unit_title"] = title
                sym += [f'      (pin {p["electrical_type"]} line (at {side * (width + 5.08)} {2.54 - row * 2.54:.2f} {0 if side < 0 else 180}) (length 5.08)',
                        f'        (name {q(p["name"])} (effects (font (size 1.016 1.016))))',
                        f'        (number {q(p["ball"])} (effects (font (size 1.016 1.016))))']
                for alias in dict.fromkeys(name for _, name in p["mux"]):
                    sym.append(f'        (alternate {q(alias)} bidirectional line)')
                sym.append('      )')
        sym.append('    )')
        unit_counts.append({"unit": chr(64 + index), "title": title,
                            "pins": sum(p is not None for p in left + right)})
    sym += ['  )', ')']
    (HERE / "A523.kicad_sym").write_text("\n".join(sym) + "\n")

    fp = [f'(footprint "{FP}" (version 20241229) (generator "a523_generator")',
          '  (layer "F.Cu")', '  (attr smd)',
          '  (descr "Allwinner A523 FCCSP-522; 15x15mm; 29x29 depopulated grid; 0.5mm pitch; vendor 0.27mm copper / 0.37mm mask / 0.32mm paste")',
          '  (tags "Allwinner A523 FCCSP BGA 522")',
          '  (property "Reference" "REF**" (at 0 -8.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
          '  (property "Value" "A523" (at 0 8.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
          '  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
          '  (solder_mask_margin 0.05)', '  (solder_paste_margin 0.025)', '  (solder_paste_ratio 0)',
          '  (fp_rect (start -8.05 -8.05) (end 8.05 8.05) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))']
    # Chamfered assembly outline: actual nominal body, A1 at upper left in top view.
    body = [(-6.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5), (-7.5, -6.5), (-6.5, -7.5)]
    for a, b in zip(body, body[1:]):
        fp.append(f'  (fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    silk = [(-6.6, -7.7), (7.7, -7.7), (7.7, 7.7), (-7.7, 7.7), (-7.7, -6.6)]
    for a, b in zip(silk, silk[1:]):
        fp.append(f'  (fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    fp.append('  (fp_poly (pts (xy -7.7 -7.7) (xy -7.7 -7.15) (xy -7.15 -7.7)) (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))')
    for p in sorted(pins, key=lambda p: (position(p["ball"])[1], position(p["ball"])[0])):
        x, y = position(p["ball"])
        fp.append(f'  (pad {q(p["ball"])} smd circle (at {x:g} {y:g}) (size 0.27 0.27) (layers "F.Cu" "F.Paste" "F.Mask"))')
    fp.append(')')
    (HERE / "A523.pretty").mkdir(exist_ok=True)
    (HERE / "A523.pretty" / (FP + ".kicad_mod")).write_text("\n".join(fp) + "\n")

    with (HERE / "pinout.csv").open("w", newline="") as f:
        fields = ["ball", "name", "vendor_type", "electrical_type", "unit", "unit_title", "group", "supply", "source_row", "correction", "mux"]
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        for p in sorted(pins, key=lambda p: (position(p["ball"])[1], position(p["ball"])[0])):
            writer.writerow(dict(p, mux="; ".join(f"{n}:{name}" for n, name in p["mux"])))
    print(json.dumps({"pins": len(pins), "pads": len(pins), "units": unit_counts,
                      "corrections": [p["correction"] for p in pins if p["correction"]]}, indent=2))


if __name__ == "__main__":
    main()
