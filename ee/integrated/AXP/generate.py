#!/usr/bin/env python3
"""Generate X-Powers PMIC parts; pin tables: datasheets V1.1, p7-8/p7.

Land dimensions follow the Allwinner reference library, using rectangular
perimeter lands and a segmented thermal-pad stencil (see README).
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
q = json.dumps

PINS = {
    "AXP717C": """
1 PWROK bidirectional
2 DM bidirectional
3 DP bidirectional
4 CC1 bidirectional
5 CC2 bidirectional
6 PWRON input
7 VREF passive
8 GND power_in
9 VIN1 power_in
10 LX1 passive
11 LX1 passive
12 FB1 input
13 ALDO1 power_out
14 ALDO2 power_out
15 ALDOIN power_in
16 ALDO3 power_out
17 ALDO4 power_out
18 BLDO1 power_out
19 BLDO2 power_out
20 BLDOIN power_in
21 BLDO3 power_out
22 BLDO4 power_out
23 CLDO1 power_out
24 CLDO2 power_out
25 CLDOIN power_in
26 CLDO3 power_out
27 CLDO4 power_out
28 CPUSLDO power_out
29 FB3 power_in
30 LX3 passive
31 VIN3 power_in
32 VIN2 power_in
33 LX2 passive
34 FB2 input
35 VRTC power_out
36 BACKUP passive
37 IRQ open_collector
38 CHGLED open_collector
39 TS input
40 DCDCEN output
41 BAT passive
42 BAT passive
43 VSYS power_out
44 VSYS passive
45 SW passive
46 SW passive
47 VMID power_out
48 VMID passive
49 VBUS power_in
50 VBUS power_in
51 SDA bidirectional
52 SCK input
53 EP power_in
""",
    "AXP323": """
1 DCDC2 input
2 VIN3 power_in
3 LX3 passive
4 DCDC3 input
5 SDA bidirectional
6 SCL bidirectional
7 RTCLDO power_out
8 VREF passive
9 GND power_in
10 NC no_connect
11 IRQ bidirectional
12 DLDO1 power_out
13 PWROK bidirectional
14 PWRON input
15 ALDO1 power_out
16 DCDC1 input
17 VIN1 power_in
18 LX1 passive
19 LX2 passive
20 VIN2 power_in
21 EP power_in
"""
}
UNITS = {
    "AXP717C": [
        ("Charger / system / control",
         [49, 50, None, 41, 42, None, 2, 3, 4, 5, None, 51, 52, None, 6, 39],
         [47, 48, 45, 46, 43, 44, None, 7, 35, 36, None, 1, 37, 38, 40, None, 8, 53]),
        ("Buck regulators",
         [9, None, None, None, None, 32, None, None, None, None, 31],
         [10, 11, 12, None, None, 33, 34, None, None, None, 30, 29]),
        ("LDO regulators",
         [15, None, None, None, None, 20, None, None, None, None, 25],
         [13, 14, 16, 17, None, 18, 19, 21, 22, None, 23, 24, 26, 27, None, 28]),
    ],
    "AXP323": [
        ("CPU / DNR power",
         [17, None, None, 20, None, None, 2, None, None, 5, 6, None, 14, 13, 11, None, 9, 21, 10],
         [18, 16, None, 19, 1, None, 3, 4, None, 15, 12, 7, None, 8]),
    ]
}
# Buck pins align with complete inductor / capacitor stages. LDO outputs are
# spaced to accept a bypass capacitor and ground symbol on each row.
UNITS['AXP717C'][0] = ('Charger / control',
    [49,50,None,None,41,42,None,None,2,3,None,4,5,None,51,52,None,6,None,39],
    [47,48,None,45,46,None,43,44,None,None,7,None,None,None,None,35,None,36,None,1,37,38,None,40,None,8,53])
UNITS['AXP717C'][1] = ('Buck regulators',
    [9]+[None]*11+[32]+[None]*11+[31],
    [10,11,None,12]+[None]*8+[33,None,None,34]+[None]*8+[30,None,None,29])
UNITS['AXP717C'][2] = ('LDO regulators',
    [15]+[None]*15+[20]+[None]*15+[25],
    [v for n in [13,14,16,17,18,19,21,22,23,24,26,27,28] for v in [n,None,None,None]][:-3])
UNITS['AXP323'][0] = ('CPU / DNR power',
    [17]+[None]*11+[20]+[None]*11+[2]+[None]*7+[14,None,13,None,11,None,5,None,6,None,9,21,10],
    [18,None,None,16]+[None]*8+[19,None,None,1]+[None]*8+[3,None,None,4]+[None]*4+[15,None,None,None,12,None,None,None,7,None,None,None,8])
FOOTPRINTS = {
    "AXP717C": "QFN-52-1EP_6x6mm_P0.4mm_EP4.6x4.6mm",
    "AXP323": "QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm",
}


def footprint(name, n, body, ep):
    fp = FOOTPRINTS[name]
    # Perimeter land centers/size from the vendor PADS library, rounded to microns.
    center = body / 2 - 0.115
    lines = [f'(footprint "{fp}" (version 20241229) (generator "axp_generator")',
             ' (layer "F.Cu") (attr smd)',
             f' (descr "{name}, reference-library land dimensions, segmented EP paste; see ../README.md")',
             ' (solder_mask_margin 0.05)',
             f' (fp_text reference "REF**" (at 0 {-body/2-1.2}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             f' (fp_text value "{name}" (at 0 {body/2+1.2}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
             f' (fp_rect (start {-body/2} {-body/2}) (end {body/2} {body/2}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
             f' (fp_line (start {-body/2} {-body/2+0.6}) (end {-body/2+0.6} {-body/2}) (stroke (width 0.1) (type default)) (layer "F.Fab"))',
             f' (fp_rect (start {-body/2-0.5} {-body/2-0.5}) (end {body/2+0.5} {body/2+0.5}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
             f' (fp_poly (pts (xy {-body/2-0.3} {-body/2-0.3}) (xy {-body/2-0.6} {-body/2-0.3}) (xy {-body/2-0.3} {-body/2-0.6})) (stroke (width 0.1) (type default)) (fill solid) (layer "F.SilkS"))']
    sidepins = n // 4
    for pin in range(1, n + 1):
        side, i = divmod(pin - 1, sidepins)
        t = (i - (sidepins - 1) / 2) * 0.4
        x, y = [(-center, t), (t, center), (center, -t), (-t, -center)][side]
        sx, sy = (0.63, 0.2) if side % 2 == 0 else (0.2, 0.63)
        lines.append(f' (pad "{pin}" smd roundrect (at {x:.3f} {y:.3f}) (size {sx} {sy}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')
    lines.append(f' (pad "{n+1}" smd rect (at 0 0) (size {ep} {ep}) (layers "F.Cu" "F.Mask"))')
    # 75-76% EP stencil coverage, with 0.2mm webs; thermal vias belong to PCB layout.
    count, aperture, spacing = (3, 1.33, 1.53) if n == 52 else (2, 0.72, 0.92)
    for i in range(count):
        for j in range(count):
            x, y = (i-(count-1)/2)*spacing, (j-(count-1)/2)*spacing
            lines.append(f' (pad "" smd rect (at {x:.3f} {y:.3f}) (size {aperture} {aperture}) (layers "F.Paste"))')
    lines.append(')')
    (HERE / "AXP.pretty" / (fp + ".kicad_mod")).write_text("\n".join(lines) + "\n")


def main():
    lib = ['(kicad_symbol_lib (version 20241209) (generator "axp_generator")']
    audit = []
    for name, raw in PINS.items():
        pins = {int(n): (label, etype) for n, label, etype in (r.split() for r in raw.strip().splitlines())}
        used = [n for _, left, right in UNITS[name] for n in left+right if n]
        assert len(used) == len(set(used)) == len(pins) and set(used) == set(pins)
        lib += [f' (symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
                f'  (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))',
                f'  (property "Value" "{name}" (at 0 7.62 0) (effects (font (size 1.27 1.27))))',
                f'  (property "Footprint" "AXP:{FOOTPRINTS[name]}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
                f'  (property "Datasheet" "${{KIPRJMOD}}/../../docs/a523/pmu_xpowers/{name}_Datasheet_V1.1_en.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
                f'  (property "Description" "X-Powers {name} PMIC; specify A523 factory configuration" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))']
        for unit, (title, left, right) in enumerate(UNITS[name], 1):
            lib += [f'  (symbol "{name}_{unit}_1"',
                    f'   (rectangle (start -20.32 5.08) (end 20.32 {-2.54*max(len(left),len(right))}) (stroke (width 0.254) (type default)) (fill (type background)))',
                    f'   (text {q(title)} (at 0 2.54 0) (effects (font (size 1.016 1.016))))']
            for sign, col in [(-1, left), (1, right)]:
                for row, pin in enumerate(col):
                    if not pin:
                        continue
                    label, etype = pins[pin]
                    x, y, angle = sign*25.4, -row*2.54, 0 if sign < 0 else 180
                    lib += [f'   (pin {etype} line (at {x} {y:.2f} {angle}) (length 5.08)',
                            f'    (name {q(label)} (effects (font (size 1.016 1.016))))',
                            f'    (number "{pin}" (effects (font (size 1.016 1.016)))))']
                    audit.append(dict(part=name, pin=pin, name=label, type=etype, unit=unit, x=x, y=round(y,2)))
            lib.append('  )')
        lib.append(' )')
    lib.append(')')
    (HERE / "AXP.kicad_sym").write_text("\n".join(lib)+"\n")
    with (HERE / "pinout.csv").open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0]))
        w.writeheader()
        w.writerows(sorted(audit, key=lambda r:(r['part'],r['pin'])))
    footprint("AXP717C", 52, 6, 4.6)
    footprint("AXP323", 20, 3, 1.65)
    print('Generated AXP717C (53 pins / 3 units) and AXP323 (21 pins / 1 unit).')


if __name__ == '__main__':
    main()
