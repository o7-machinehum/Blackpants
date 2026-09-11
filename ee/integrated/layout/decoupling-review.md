# Decoupling placement review — 2026-09-09

The saved placement is not acceptable as a completed decoupling layout. Several
SoC bypass capacitors are far from their supply-ball clusters, and some power
and ground connections are still open. Clearance and net-name checks did not
validate their decoupling loops.

This review covers the active `blackpants.kicad_pcb`, SHA-256
`be119b93cf3c544962fda48e6336237466ada074d5de6280878d4d9104c28b60`.
The [measurements](decoupling-audit.json) describe that saved checkpoint,
including its existing filled zones. They do not describe a corrected placement.

## Concrete findings

Distances below are straight-line XY distances from the capacitor's supply-pad
center to the nearest **same-net** pad on the associated IC. They are not routed
lengths, loop lengths, or inductance estimates. Where several functional
supplies share a net, the intended supply pin can be farther away.

| Capacitor | Function / rail | Nearest IC pad | Distance | Saved connection status |
| --- | --- | --- | --- | --- |
| C226, 100 nF | A523 CPU-big bypass | U201.N19 | 10.40 mm | No power connection to the SoC |
| C255, 100 nF | A523 RTC bypass | U201.AA10 | 9.05 mm | No power connection to the SoC |
| C233, 2.2 µF | A523 CPU-little bypass | U201.U18 | 7.62 mm | Power and ground open |
| C301, 2.2 µF | RAM VCC_DRAM bypass | U301.N1 | 3.79 mm | Power connected; ground open |
| C507, 100 nF | AXP717C VBAT bypass | U501.41 | 6.42 mm | Power connected; ground open |
| C521, 1 µF | AXP717C VSYS input bypass | U501.25 | 7.63 mm | Connected; local decoupling loop still needs review |

None of the seven CPU-big bypass capacitors C220–C226 or the six CPU-little
bypass capacitors C230–C235 is currently connected to its SoC supply cluster.
Some are connected only to other capacitors in the same bank. That is part of
the board's previously reported incomplete routing, but simply joining those
banks with long traces would not correct the placement.

The connectivity screen covered 111 shunt capacitors sharing a net with the
associated IC. It excluded crystal/signal capacitors, inductor-separated output
capacitors, and other peripheral circuits.

| Associated IC | Caps screened | Power not connected to that IC | Ground not connected to main GND network |
| --- | ---: | ---: | ---: |
| A523 U201 | 59 | 26 | 3 |
| RAM U301 | 17 | 0 | 1 |
| AXP717C U501 | 28 | 7 | 8 |
| AXP323 U502 | 7 | 0 | 0 |

RAM capacitor distances in this screen are 1.39–3.79 mm. The seven AXP323
capacitors are 1.13–2.45 mm away and electrically connected. These are better
starting points for placement review, not a power-integrity pass.

## Why the placement looks scattered

The initial placement in [start.py](start.py) averaged the positions of all
matching-net IC pads, searched a 0.5 mm grid for free space, and used component
and copper bounding boxes as obstacles. It did not optimize the actual
capacitor–supply-ball–ground loop or assign each capacitor to its functional
ball cluster. For example, SYS, GPU, VE and DE are tied to one board net but
still have distinct local bypass requirements. That initial pass was inadequate
for final placement.

## Required correction

1. Assign the SoC bypass banks to their intended supply-ball clusters. Give
   local bypass and analog/reference capacitors placement priority, with the
   bulk capacitors arranged around them.
2. Place and route each capacitor together with its power and ground
   connections. Opposite-face placement beneath a BGA can be useful, but only
   when the vias, their separation and the return path provide a short loop.
   Use the existing 0.4/0.2 mm through-via constraints without via-in-pad.
3. Review ground-via sharing using the resulting return geometry. Membership
   of one connected ground plane does not establish low mounting inductance.
   A nearby dedicated capacitor return may be needed even where other ground
   pins can share a via.
4. Review AXP717C input/output capacitors and VREF separately against their pin
   functions and switching loops; restore the open ground connections. The
   converter's output capacitors are additional to the SoC bypass banks.
5. Refill zones and repeat native connectivity/DRC checks after placement and
   routing changes. Then assess power-distribution impedance and voltage drop;
   those electrical checks have not been performed by this screen.

## References and limits

Allwinner's [A523 hardware guide, printed pp. 39–40](../../../docs/a523/A523_hwref/设计指南/硬件设计指南/A523硬件设计指南_V1.6-240712.pdf)
specifies the local CPU/SYS bypass banks and calls for capacitors close to their
supply pins, including PLL, EFUSE, RTC and GPIO supplies. Its [PCB guide,
§4.2 and §5.1](../../../docs/a523/A523_hwref/设计指南/硬件设计指南/A523%20PCB设计指南-V1.1.pdf)
also gives analog and PMIC placement guidance, including keeping VREF close to
its pin and its ground connection away from switching noise.

[TI's PDN implementation guide, §§2–3](https://www.ti.com/lit/pdf/sprac76)
explains the effect of mounting geometry, vias and plane placement on loop
inductance. It supports the general review method; its device-specific limits
are not A523 requirements.

The JSON's 5 mm marker is a sorting aid, not a vendor acceptance limit. No
maximum-distance rule alone can approve a decoupling network. This review has
not extracted loop inductance, capacitor ESR/ESL, voltage-biased effective
capacitance, or PDN impedance.
