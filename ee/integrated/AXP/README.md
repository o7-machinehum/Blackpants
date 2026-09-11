# A523 companion PMIC parts

`AXP:AXP717C` has 52 perimeter pins plus exposed pad 53, split into charger/control,
buck and LDO units. `AXP:AXP323` has 20 perimeter pins plus exposed pad 21.
The regulator units have enough pin spacing to draw their inductors and capacitors
directly alongside them. [review.pdf](review.pdf) shows the captured circuits.

Pin numbers and names were checked against X-Powers datasheets V1.1, PDF pages
7–8 for AXP717C and page 7 for AXP323, in [docs/a523](../../../docs/a523/README.md).
Every physical pin is explicit. Switching nodes are passive in the ERC model;
the schematic marks the regulated side of each output inductor with a power flag.
AXP717C FB3 is a power input because it also supplies CPUSLDO.

Footprints use the Allwinner reference-library land dimensions: 0.4mm pitch,
0.63 × 0.20mm perimeter lands, 4.6 × 4.6mm exposed pad for AXP717C and
1.65 × 1.65mm for AXP323. Perimeter lands use rounded rectangles rather than the
vendor's corner polygons; segmented exposed-pad paste gives about 75% coverage.
The original offset paste geometry is not reproduced. Thermal vias and final
stencil approval belong to PCB layout and assembly review. No 3D models are included.

These generic part names do **not** specify the required factory configuration.
Procurement must obtain the A523 voltage/sequence profile and AXP323 EN/parallel
mode. See [capture status](../capture/README.md) before using this design.

Regenerate with `python3 ee/integrated/AXP/generate.py` from the repository root.
`capture/validate.py` checks pin tables, KiCad symbol round-trips, numbered pad
counts, orientation anchors and the critical captured nets.
