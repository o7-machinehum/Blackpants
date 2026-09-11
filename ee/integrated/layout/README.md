# A523 layout — routing in progress

The active [KiCad project](../blackpants.kicad_pro) contains 319 physical
footprints and six copper layers. All **65 SoC-to-RAM signals are connected**.
There are **139 open connections overall**, measured with KiCad's full
connectivity API. Routing is incomplete; the board is not ready for fabrication.

- [Bottom/component-side preview](bottom.svg), viewed from the bottom.
- [Top/keyboard-side preview](top.svg).
- [Native DRC report](drc.json).
- [Pin/net, via and full connectivity checks](validation.json).
- [Remaining net islands and pad positions](unconnected-nets.json).
- [Verified DQ swizzle](../LPDDR4/swizzling.md).
- [Neck-down audit and preliminary electrical calculation](ddr-neckdown-review.md).
- [Decoupling placement audit and required corrections](decoupling-review.md).

## Placement and routing

The A33/DDR3 hierarchy and placement have been replaced by A523, AXP717C +
AXP323, and Nanya 2GB LPDDR4. The existing outline, mounting holes, keyboard,
battery holder and external connector positions are retained. The SoC is on
B.Cu at (65, 54) mm, rotated 45 degrees. RAM placement follows Allwinner's
single-package template. The Wi-Fi module and BGA bypass capacitors are on F.Cu.
Existing STEP/mechanical exports predate this placement.

The DQ mapping now follows the verified reference's within-byte permutations.
27 RAM DQ assignments changed; byte lanes, DQS, DMI and command/address mapping
were preserved. [The swizzle-stage record](ddr-swizzle-routing.json) documents
that change. All 65 DDR signal paths are connected. Length matching is left to
the user, as requested.

The existing DDR routing is frozen at the user’s request. `validate.py` compares
all DDR track/via geometry, widths, drills, layers, and the SoC/RAM placement
against [the saved baseline](ddr-frozen.json). Peripheral routing changes must
pass this comparison; the baseline must not be regenerated to bypass a failure.

The PMIC and boost-converter placement, local switching connections, thermal
arrays and power pours have been added. Ordinary signal routing no longer
applies automatic neck-downs. 399 ordinary narrow segments were widened or
rerouted at 0.15 mm. The 27 DDR segments that had been narrowed beyond the
reference have been rerouted at their reference widths. The original reference
escapes remain; retaining them is not electrical approval.

The decoupling placement audit found scattered SoC bypass banks and open
capacitor power/ground connections. Their placement and return paths require
rework before routing can be considered complete; the existing placement has
not passed a power-integrity review.

83 redundant GND vias were removed where a nearby via was already joined by
continuous surface ground copper. Ground and thermal connections are being
rechecked after routing changes. The RAM ground mesh and exposed-pad thermal
arrays are retained. Some local ground connections and power feeds remain open.

## Stack and dimensions

The 1.6 mm stack follows Allwinner's six-layer reference, mirrored for a SoC on
B.Cu. Dielectric constants and thicknesses are preliminary; the fabricator has
not characterized or approved this stack.

| Layer | Purpose | Copper thickness |
| --- | --- | --- |
| F.Cu | Signals, bypass capacitors and keyboard | 40.64 µm |
| In1.Cu | GND reference plane | 30.48 µm |
| In2.Cu | Inner DDR, other signals and power | 30.48 µm |
| In3.Cu | Power and other signals | 30.48 µm |
| In4.Cu | GND reference plane | 30.48 µm |
| B.Cu | SoC, RAM, PMICs and signal escape | 40.64 µm |

Dielectrics from top to bottom: 73.66 / 561.24 / 101.60 / 561.24 / 73.66 µm.
Both ground planes are filled. Reference-plane continuity and power-current
capacity still need review, including the reference seen by inner DDR traces.
DDR targets are 50 Ω single-ended and 85 Ω differential. USB targets 90 Ω
differential; DSI targets 100 Ω. Cross-section estimates are preliminary and do
not establish channel compliance.

All **1046 vias use 0.40 mm pads and 0.20 mm drills** and are ordinary F.Cu-to-B.Cu
through vias. There are no microvias or blind/buried vias. Via drills are
excluded from SMD copper except for the explicitly permitted GND thermal arrays:
U501 (9), U502 (4), U901 (6) and U1 (2). The board uses a 0.10 mm annular ring,
0.15 mm hole-to-other-net-copper clearance and 0.20 mm hole-to-hole clearance.
BGA escape clearance is 0.0762 mm. [Project rules](../blackpants.kicad_dru)
enforce these restrictions; fabricator acceptance remains outstanding.

## Validation and remaining work

Pin/net checks pass for all **1,818 physical schematic pins**, with all 65 DDR
signals connected. The saved native DRC snapshot has **0 error-severity physical
violations**, plus 624 warnings and 139 unconnected items.
Warnings include solder-mask bridges, silkscreen, library differences, dangling
copper and an inherited courtyard issue. No new exclusions were added.

Remaining work includes peripheral differential pairs, support signals,
power/ground connections, cleanup of dangling copper, mask/silkscreen checks,
and mechanical/assembly review. DDR timing, signal integrity, power integrity,
thermal adequacy, firmware DRAM initialization and the PMIC factory profile
are not approved. The [neck-down review](ddr-neckdown-review.md) records what
was calculated and what remains unvalidated.

## Reproducing checks

From the repository root:

```sh
python3 ee/integrated/capture/validate.py
python3 ee/integrated/layout/validate.py
python3 ee/integrated/layout/validate.py --require-complete
kicad-cli pcb drc --refill-zones --save-board --all-track-errors --format json \
  -o ee/integrated/layout/drc.json ee/integrated/blackpants.kicad_pcb
```

The completion gate currently fails because routing is incomplete. `start.py`
is a one-time migration: do not run it on the active A523 board. `import_ddr.py`
rejects a second import and now preserves reference widths with metric vias;
it does not reproduce subsequent routing repairs. `planes.py` only applies to
a board with no copper zones. `sync.py` synchronizes canonical net names and
fields; it does not add footprints or perform general schematic updates.
