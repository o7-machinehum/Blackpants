# A523 LPDDR4 bit swizzle

The active schematic and PCB use the exact DQ permutation in Allwinner's
`A523-REF-LPDDR4-4X-32X1-S6L-V2-0(C0402)` reference. All 32 SoC/RAM
ball pairs were checked against the PCB's route endpoints and independently
against the net labels beside RAM balls in its schematic PDF, page 1.

- [Allwinner schematic](../../../docs/a523/A523_hwref/PCB参考/硬件DDR模板&叠层文件/A523-REF-LPDDR4-4X-32X1-S6L-V2-0(C0402)/A523-REF-LPDDR4-4X-32X1-S6L-V2-0-20221014.pdf)
- [Allwinner PCB source](../../../docs/a523/A523_hwref/PCB参考/硬件DDR模板&叠层文件/A523-REF-LPDDR4-4X-32X1-S6L-V2-0(C0402)/A523-REF-LPDDR4-4X-32X1-S6L-V2-0_pads.asc)
- [Exact ball mapping and source SHA-256 hashes](a523-swizzle.json)

The verified mapping changes 27 DQ connections, all within their original
eight-bit byte. DQS pairs, DMI, channel/byte assignments, clocks, reset and
command/address wiring retain their existing assignments. This is evidence
for the specific reference permutation below, not a claim that arbitrary
byte/channel or command-pin permutations are supported.

| SoC signals, in ascending order | RAM DQ indices, in that same order |
| --- | --- |
| SDQ0..SDQ7 | Channel A: 5, 4, 2, 3, 0, 7, 1, 6 |
| SDQ8..SDQ15 | Channel A: 13, 12, 15, 14, 9, 8, 11, 10 |
| SDQ16..SDQ23 | Channel B: 3, 2, 4, 1, 5, 0, 7, 6 |
| SDQ24..SDQ31 | Channel B: 15, 8, 10, 9, 12, 11, 14, 13 |

Schematic net names `DDR_DQn` identify SoC bits. The RAM symbol retains its
datasheet pin names and ball numbers; only their visual order changes so the
connections remain straight and readable. The generator and capture validator
use this mapping, and the validator independently checks the vendor PCB pairs.

The 32 DQ routes now follow the reference topology. The RAM V4 escape is
adjusted for the selected 0.30 mm lands, one adjacent through via is 0.35/0.20 mm
pad/drill, and three conflicting bypass-ground vias were replaced by connections
to nearby ground vias. DQ via count fell from 67 to 42. All 65 DDR signals are
connected. No new length matching was performed; timing adjustment is reserved
for the user. See [routing record](../layout/ddr-swizzle-routing.json).

Boot firmware must still be configured and tested for the selected Nanya part,
its timings and this reference wiring. Hardware connectivity checks do not
establish successful training or mode-register reads.
