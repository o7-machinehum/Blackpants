# DDR neck-down review

The altered DDR neck-downs have **not** passed an electrical signal-integrity review. The previous clearance and connectivity checks did not establish their impedance or acceptable length.

The geometric audit in [ddr-neckdown-audit.json](ddr-neckdown-audit.json) compares the routed segments against Allwinner's native PADS template, matching endpoints to 0.001 mm. Among segments narrower than 0.1 mm:

| Origin | Segments | Copper length |
| --- | ---: | ---: |
| Same width and geometry as the reference | 272 | 156.08 mm |
| Reference geometry subsequently narrowed | 27 | 23.04 mm |
| Changed/new geometry, including endpoint adjustments | 17 | 4.20 mm |

The longest continuous narrow section is approximately 4.79 mm. Length alone does not establish that a neck-down is unacceptable: the reference itself includes narrow sections several millimetres long. Conversely, retaining a reference segment does not validate a different stackup, reference-plane arrangement, or termination configuration.

Allwinner's [DDR layout guide](../../../docs/a523/A523_hwref/设计指南/DDR%20Layout指南/A523%20DDR%20layout设计指南-V1.1-0403.pdf), section 3.3.1, specifies 50 ohm single-ended and 85 ohm differential routing with widths derived from the stackup. Section 3.3.3(6) recommends approximately one ground/power via per RAM ball where space permits. These statements do not support either blanket removal of neck-downs or blanket removal of RAM ground vias.

The design currently uses a preliminary reference stackup. Its nominal dielectric constants are not a fabricator's characterized materials. A first-order isolated, uncoated microstrip estimate is not an adequate substitute for the coated BGA escape geometry, coupled DQS/clock traces, reference-plane discontinuities, and vias. No such estimate is used here to mark the DDR channel as passing.

The downloaded A523 LPDDR4 IBIS file contains drive/termination variants and fast edge models, but an end-to-end simulation with the selected RAM, settings, and extracted board geometry has not been run. Length matching remains deferred to the user. This review does not approve DDR timing or signal integrity.

## Preliminary cross-section calculation

A [two-dimensional finite-volume calculation](cross_section.py) was subsequently run for ideal coated microstrip, using 0.07366 mm of dielectric at relative permittivity 4.0, 0.04064 mm copper and a 0.0127 mm conformal solder-mask approximation at relative permittivity 3.6. These are assumptions from the preliminary stack, not measured fabricator values. [Results](cross-section-estimates.json) include a mesh-refinement comparison.

At a 1 micrometre mesh step, the isolated 0.1143 mm trace estimates 49.77 ohm, and the 0.0762 mm trace estimates 58.90 ohm. Changing the mesh from 2 to 1 micrometre changed these estimates by less than 0.06 ohm; this checks numerical convergence only, not the material/geometry assumptions. An isolated step between those impedances has an approximately 8.4% voltage reflection coefficient. A finite neck-down has two transitions, so this number is not the receiver error or eye degradation.

The model does not include adjacent BGA pads/traces, finite reference pours, the inner-layer cross-section, via barrels/stubs, package parasitics, driver/receiver behavior, or loss. It therefore cannot approve any neck-down length or the complete memory channel.

The 27 segments additionally narrowed from the template have since been restored to their reference widths by changing their paths. All 65 SoC-to-RAM signal connections remain connected. The initial audit above is retained as the before-change record, not a claim about the final width distribution.

Using the same preliminary model, a 4.79 mm narrow section has approximately
27.5 ps of one-way flight time, or 55 ps round trip. For comparison, the
vendor `a523_lpddr4.ibs` model `DQ_PD33_ODT40_VOH25_LPDDR4` gives fast-corner
ramp intervals of 56.663 ps rising and 45.643 ps falling (in its specified
50 ohm test fixture). That comparison is sufficient to reject an assumption
that every such section is electrically negligible. It is not a channel
pass/fail result: the selected drive setting, termination, receiver model and
actual interconnect still need to be included.
