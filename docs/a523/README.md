# A523 redesign reference documents

Downloaded on 2026-09-08 to support the proposed A33-to-A523 redesign in
`ee/integrated/`. Parts and the integrated schematic are described in
[the capture notes](../../ee/integrated/capture/README.md).

91 source files, 266,398,150 bytes (approximately 254 MiB). The collection includes
the current A523 core documents in the source snapshot, the complete `A523_hwref`
directory, and three relevant X-Powers PMIC datasheets. Older A523 core-document
versions and the separate A527/T527 design collections were not downloaded.

## Source and verification

The original 91 files were downloaded from the public
[DeciHD/allwinner_docs mirror](https://github.com/DeciHD/allwinner_docs/tree/d6cfc7c4c4ef35868322149776f7503a671367d6/a523_a527_t527)
at commit `d6cfc7c4c4ef35868322149776f7503a671367d6`. These are vendor-authored
documents hosted by a third party, rather than downloads authenticated by the
manufacturer. Original filenames and file contents have been preserved.

[sources.json](sources.json) records each download URL, upstream path, expected
size, Git blob SHA-1, local SHA-256, and PDF page count where applicable.
[SHA256SUMS](SHA256SUMS) contains checksums relative to this directory.
All 91 downloads matched their upstream sizes and Git blob hashes; all 24 PDFs
were readable by `pdfinfo`. This verifies download integrity, not engineering
correctness or vendor authenticity. The complete contents have not yet been
reviewed. CAD import into KiCad and IBIS simulation have not been tested.

The subsequent memory capture adds the 302-page
[Nanya NT6AN512T32AV LPDDR4 datasheet V1.8](NT6AN512T32AV_LPDDR4_V1.8.pdf),
downloaded from the [Ampheo mirror](https://resources.ampheo.com/static/datasheets/nanya-technology/nt6an512t32av-j2.pdf).
This is a Nanya-authored document hosted by a distributor. Its size, SHA-256 and
source URL are recorded in the manifest; it has no upstream Git-hash check.
The peripheral power capture also adds the manufacturer-hosted
[TPS61230 datasheet](https://www.ti.com/lit/ds/symlink/tps61230.pdf) and
[AOZ1280CI datasheet](https://www.aosmd.com/res/datasheets/AOZ1280CI.pdf), stored
locally as `TPS61230.pdf` and `AOZ1280CI.pdf`.

The sourcing review adds the 251-page
[SK hynix H9HCNNNBKUMLXR-NEE LPDDR4 datasheet V1.0](H9HCNNNBKUMLXR-NEE_LPDDR4_V1.0.pdf),
downloaded from [LCSC C21912322](https://www.lcsc.com/product-detail/C21912322.html).
This is a candidate replacement for the selected Nanya RAM; see the
[sourcing and pin-comparison notes](../../ee/integrated/LPDDR4/sourcing.md).
There are now 95 source files in the manifest.

## Start here

| Document | Purpose |
| --- | --- |
| [A523 datasheet V1.4](A523_Datasheet_V1.4.pdf) | 143 pages: package, ball assignments, electrical limits, supply timing, and thermal information. |
| [A523 pinout V1.4](A523_PINOUT_V1.4.xlsx) | Machine-readable input for symbol generation and pin-by-pin checking. |
| [A523 user manual V1.4](A523_User_Manual_V1.4.pdf) | 1,725 pages: peripheral and register reference. |
| [Hardware design guide V1.6](A523_hwref/设计指南/硬件设计指南/A523硬件设计指南_V1.6-240712.pdf) | 87 pages, Chinese; dated 2024-07-12. Circuit design guidance. |
| [PCB design guide V1.1](<A523_hwref/设计指南/硬件设计指南/A523 PCB设计指南-V1.1.pdf>) | 39 pages, Chinese. Placement and routing guidance. |
| [DDR layout guide](<A523_hwref/设计指南/DDR Layout指南/A523 DDR layout设计指南-V1.1-0403.pdf>) | 27 pages, Chinese. Memory topology, stackup, and routing guidance. Filename says V1.1; cover says V1.0. Check revision history before applying constraints. |
| [Standard reference schematic](A523_hwref/原理图/标案原理图/a523_std_axp717c_axp323_lpddr4_240712.pdf) | 31 pages, V2.4 dated 2024-07-12. A523, AXP717C, AXP323, and LPDDR4/4X, including power tree and sequencing. Native DSN and changelist are alongside it. |
| [Evaluation-board files](A523_hwref/原理图/开发板资料/) | Schematics, native PCB, BOM, and board user guide. |
| [SoC and companion footprint library](A523_hwref/PCB参考/SoC套片PCB封装库/A523_SOC_Symbol.zip) | Vendor BRD/ASC/spreadsheet geometry, including the 522-ball SoC package. Not a KiCad library. |
| [DDR templates and stackups](A523_hwref/PCB参考/硬件DDR模板&叠层文件/) | Native BRD/DSN, PADS ASC/PCB, schematic PDFs, and stackup spreadsheets for multiple DDR4, LPDDR3, and LPDDR4/4X arrangements. |
| [DDR routing rules](A523_hwref/PCB参考/硬件DDR模板&叠层文件/AW1890-A523_DDR走线规则.xlsx) | Spreadsheet of A523 DDR routing constraints. |
| [IBIS models](A523_hwref/IBIS模型/A523_IBIS_20230321.7z) | Electrical interface models for subsequent signal-integrity work. |
| [Hardware checklists](A523_hwref/硬件checklist/) | Vendor schematic and PCB review spreadsheets. |
| [DRAM support list V1.3](<Allwinnertech A523 DRAM Support List V1.3.xls>) | Candidate memory parts; not a final BOM selection. |
| [eMMC support list](A523_eMMC_支持列表.xls) | Candidate eMMC parts. |
| [PMIC selection reference](A523_hwref/PMIC搭配选型说明/) | Vendor AXP717B/C selection spreadsheet. |
| [AXP717C datasheet V1.1](pmu_xpowers/AXP717C_Datasheet_V1.1_en.pdf) | 53 pages, English. |
| [AXP323 datasheet V1.1](pmu_xpowers/AXP323_Datasheet_V1.1_en.pdf) | 31 pages, English. |
| [AXP717B datasheet V1.0](pmu_xpowers/AXP717B_Datasheet_V1.0_en.pdf) | 40 pages, English; alternate PMIC reference. |

## Remaining design inputs

The A523 datasheet identifies a 522-ball, 15 x 15 mm FCCSP package with 0.5 mm
pitch. The reference templates provide a starting point for package escape and
memory routing, but do not establish that the existing Blackpants stackup or
placement can be retained.

The schematic uses Nanya 2GB LPDDR4 and retains the existing product peripherals.
Exact PMIC factory configuration, whole-system power/thermal limits, cell/NTC
selection, bootloader DRAM initialization, mechanical constraints, and a
fabricator-supported stackup/via geometry remain design inputs. See the capture
notes for the current status. ERC/DRC alone do not validate those requirements.
