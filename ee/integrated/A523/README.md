# Allwinner A523 KiCad part

Open **A523:A523** in the integrated project's Symbol Editor. Its assigned
footprint is **A523:Allwinner_A523_FCCSP-522_15x15mm_P0.5mm**.

[review.pdf](review.pdf) shows all 14 symbol units followed by the footprint.
[pinout.csv](pinout.csv) lists every ball, pin type, unit, supply domain, alternate
function, and source correction. No A523 instance has been placed in the product
schematics or PCB as part of this work.

## Symbol

All 522 physical balls are represented exactly once, including the NC ball F14.
Power and ground pins are visible and individually connectable. GPIO names are
the default; their multiplexed functions are selectable KiCad pin alternates.
Alternate function numbers are recorded in the CSV, not encoded as extra pins.

| Unit | Function | Pins |
| --- | --- | ---: |
| A | DRAM data | 44 |
| B | DRAM address, control, and power | 45 |
| C | System, clocks, and boot | 18 |
| D | GPIO B, C, F | 40 |
| E | GPIO D, E | 43 |
| F | GPIO G, H | 36 |
| G | GPIO K, L, M | 48 |
| H | USB and PCIe | 23 |
| I | eDP | 14 |
| J | Audio and ADC | 37 |
| K | Core power and supply sense | 33 |
| L | Digital ground 1 | 62 |
| M | Digital ground 2 | 62 |
| N | Analog ground | 17 |

Electrical types follow the vendor pin-characteristics table, with functional
corrections checked against the reference design. ALDO-OUT, CPVEE and CPVDD are
power outputs; VRP is an analog output; the four VDD-*FB remote-sense taps are
passive. CPVDD has capacitor-only support in STD PDF page 13, and hardware-guide
PDF page 60 specifies measuring its internal 1.0V output. VRP is explicitly an
analog output in the datasheet function table, PDF page 67. The dedicated PCIe
reference-clock pins are inputs, grounded when unused per STD. GPIO alternates
retain the bidirectional type of the multiplexed pad. RESET and NMI also remain
bidirectional because the source describes them as input/output, open-drain.
X32KFOUT and PLLTEST use KiCad's open-collector type for open-drain outputs.
These types do not replace voltage-domain or mux-configuration checks during
schematic capture.

## Footprint

- FCCSP-522, nominal 15 × 15 mm body, 0.5 mm pitch, depopulated 29 × 29 grid.
- Top view: A1 at (-7, -7) mm; A29 at (7, -7); AJ1 at (-7, 7).
- Circular copper lands: 0.27 mm diameter.
- Solder-mask openings: 0.37 mm diameter (0.05 mm radial expansion).
- Paste openings: 0.32 mm diameter (0.025 mm radial expansion).
- Courtyard: 16.1 × 16.1 mm, allowing 0.5 mm around the maximum 15.1 mm body.
- Nominal fabrication outline, silkscreen outline, and A1 markers included.

Land and aperture sizes reproduce the vendor footprint. Its PADS BASIC export
has small coordinate quantization errors; ball centers are snapped to the exact
0.5 mm package grid after checking every coordinate within 0.0002 mm. Final
stencil/process approval belongs to the assembly stage. No 3D model is included.

## Source corrections to review

The V1.4 pin-characteristics worksheet and PDF contain errors. The following
corrections reconcile them with the separate ball-map worksheet and reference
schematic. The vendor source files themselves have not been modified.

| Source issue | Part uses | Cross-check |
| --- | --- | --- |
| TEST assigned to AE1, duplicating LINEOUTRN | TEST = AE11; LINEOUTRN = AE1 | Workbook `4 Pin Map`; STD schematic PDF page 11 (SYS) and page 13 (analog) |
| PB10–PB14 listed as their own ball numbers | L25, L26, L27, L28, L29 respectively | Workbook `4 Pin Map`; STD schematic PDF page 12 (GPIO) |
| J6 named VCC_PE | VCC-PE | Workbook `4 Pin Map`; STD schematic GPIO supply |
| USB2 DP/DM/REXT supply spelled VCC33-UAB-2 | VCC33-USB-2 in CSV metadata | Actual supply pin J15 and signal descriptions |

Primary inputs are in [docs/a523](../../../docs/a523/README.md):

- [Pinout V1.4](../../../docs/a523/A523_PINOUT_V1.4.xlsx): pin-characteristics, GPIO-mux, and ball-map worksheets.
- [Datasheet V1.4](../../../docs/a523/A523_Datasheet_V1.4.pdf): package drawing, PDF pages 131–132.
- [Vendor footprint archive](../../../docs/a523/A523_hwref/PCB参考/SoC套片PCB封装库/A523_SOC_Symbol.zip): BGA522 ASC file, ball numbering, positions, and pad stack.
- [Standard reference schematic](../../../docs/a523/A523_hwref/原理图/标案原理图/a523_std_axp717c_axp323_lpddr4_240712.pdf): cross-checks for source errors and power/sense pins.

## Regeneration and validation

From the repository root:

```sh
python3 ee/integrated/A523/generate.py
python3 ee/integrated/A523/validate.py
```

Generation requires Python's standard library and the downloaded source files.
Validation additionally requires KiCad CLI and its `pcbnew` Python module.

Validated with KiCad 10.0.6: all 522 corrected assignments agree with the vendor
ball map; every pad agrees with the vendor geometry; all symbol pins survive a
KiCad save/load round-trip; the footprint loads with the expected pad count,
positions, layers, copper sizes, mask/paste margins, and library association.
All units and the footprint were rendered for visual inspection. No board-level
ERC/DRC or electrical validation has been performed at this part-only stage.

This installation's `pcbnew` module emits three `PROPERTY_ENUM` initialization
diagnostics; it loads the footprint and completes all validation checks.
