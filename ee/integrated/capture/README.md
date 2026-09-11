# A523 schematic capture

Open [blackpants.kicad_pro](../blackpants.kicad_pro). The main project now contains
the A523, AXP717C + AXP323, 2GB LPDDR4 and the migrated product peripherals.
[review.pdf](review.pdf) is the complete 33-page project export.

The former A33 GPIO, power and RAM sheets, DDR3 sheet and old PMIC sheet have been
removed, along with the A33/DDR3 libraries and their table entries. There is no
separate A523 draft project. The keyboard matrix and its user edits are preserved.
The root STM32, USB multiplexer, hub, USB-A connectors, display and keyboard
backlight remain in the product hierarchy.

**The PCB has an initial six-layer A523 placement and partial DDR routing.** See
[layout status](../layout/README.md). Routing, timing and manufacturing checks
remain open; this is not a fabrication release.

## Circuit and interface changes

The capture follows Allwinner STD V2.4 (2024-07-12), using Nanya
NT6AN512T32AV-J2, a 16Gb/2GB LPDDR4 part. The power architecture uses one Li-ion
cell. Sources and hashes are in [docs/a523](../../../docs/a523/README.md).

| Function | Captured connection |
| --- | --- |
| SoC/DRAM power | AXP717C + AXP323; dedicated SoC feedback pins; load-side DRAM feedback through NT301 |
| Battery | AXP717C replaces IP5306; BT1, F1, cell-attached TH901, power key and charge LED are connected |
| Peripheral power | VSYS → TPS61230 → +5V → AOZ1280 → +3V3; separate from PMIC rails and connector VBUS |
| Boot storage | PF0..PF5 SDC0 → J105 microSD; PF6 detect; R203 clock termination |
| Display | PD0..PD5 DSI0 → J801; PB7 reset, PB6 TE, PB8 PWM → existing AP3036B |
| Wi-Fi | PG0..PG5 SDIO1 → RTL8723DS; PH0/PH1 enable/wake; module VBAT on filtered +3V3 and VDD_IO on VCC_PG |
| Bluetooth | PG6..PG9 UART1, TX/RX and RTS/CTS crossed; PH2..PH4 reset/wake |
| Standby clock | X32KFOUT → module LPO, with VCC_PG pull-up |
| Host USB | USB1 → USB2514B upstream; downstream 1/3 retain USB-A, port 2 retains STM32 mux, port 4 serves CH340C |
| Recovery | J101 → ESD → USB0; separate sense-only VBUS divider → PB11; SW101 grounds FEL |
| Console | UART0 PB9/PB10 → CH340C and J102; open JP101 before an external adapter drives RX |
| Charge/keyboard USB | J8 retains STM32 mux and charger; PMIC DP/DM sense uses 470-ohm resistors, CC uses 1k series resistors |
| Expansion | PB4/PB5 I2C1 → J103, with 3.3V pull-ups |

Regulator loops, oscillators and RAM data use direct wires. Local labels and
hierarchical ports identify signals between blocks. New capture contains no
global labels. Circuit pages use A4; larger hierarchy overviews use A3.

The original USB-A footprint was recovered from the PCB into the project
blackpants footprint library because its old installed-library name was missing.
Its pad geometry is preserved.

## Verification

KiCad 10.0.6 exports the active project with **0 ERC errors and 31 warnings**, with
no ERC exclusions added. [erc.json](erc.json) records 29 library-copy
mismatches and two existing unused STM32 USART labels. These warnings remain
open; library refreshes must check pin compatibility before replacing caches.

The validators check vendor pin tables and geometry, KiCad symbol round-trips
and footprints, all 796 SoC/RAM/PMIC pins, power/feedback/reset nets, 44 DRAM data
and 21 command/control connections, clocks and ground balls. They also check
physical pad-to-pad paths through USB hub/mux/ESD, SD, DSI, Wi-Fi/BT, console,
battery controls and peripheral converters. These checks pass.

CPVDD is modeled as a charge-pump output: the reference connects only a capacitor
and the guide specifies measuring its internal 1.0V rail. VRP uses the datasheet
function table's analog-output type. Dedicated PCIe reference clocks are inputs,
grounded for the unused interface per the reference.

## Items requiring resolution before fabrication

- Obtain the exact A523 PMIC factory profile: voltages/sequence, AXP323 EN mode
  and parallel operation. Generic part numbers do not establish these defaults.
- Set BLDO1 to 3.3V before enabling Wi-Fi/BT I/O. Prevent PH outputs from driving
  the module before its I/O rail is ready.
- Build and verify Nanya DRAM initialization for strap set 1; the index does not
  establish that the bootloader already contains the correct timing data.
- Finish the **whole-system** power and thermal budget. Peripheral allocation is
  1.6A at 5V: two 500mA USB ports, 0.4A equivalent logic/radio and 0.2A backlights.
  This is a design allocation, not a measured load or guaranteed simultaneous
  operating point. Add SoC/DRAM demand and losses, check AXP717C power-path limits,
  and reconcile with the provisional 4A cell fuse, holder, protected cell and
  minimum battery voltage. USB-power and DVFS limits must follow that budget.
- Select the protected cell and NTC curve, then set charge voltage/current and
  TS thresholds together. TH901's wire pads connect a remote NTC bonded to the
  cell. Confirm the factory TS/charging configuration before battery power-up.
- Verify USB-C surge protection and signal integrity against the guide. The
  inherited USBLC6 protection is captured; compliance/surge testing is pending.
  Validate startup, shutoff, backfeeding, load steps and capacitor derating.
- Complete the PCB stackup, escape, placement, routing and thermal design;
  approve final inductor/capacitor selections and assembly footprints.

## Regeneration

The generators overwrite their named sheets; reconcile manual edits first.
The main root, USB hub, display and keyboard/backlight sheets are maintained
directly in KiCad. Run from the repository root:

```sh
python3 ee/integrated/AXP/generate.py
python3 ee/integrated/LPDDR4/generate.py
python3 ee/integrated/capture/power.py
python3 ee/integrated/capture/soc.py
python3 ee/integrated/capture/memory.py
python3 ee/integrated/capture/peripherals.py
python3 ee/integrated/capture/review.py
python3 ee/integrated/A523/validate.py
python3 ee/integrated/capture/validate.py
kicad-cli sch erc --format json -o ee/integrated/capture/erc.json ee/integrated/blackpants.kicad_sch
kicad-cli sch export pdf -o ee/integrated/capture/review.pdf ee/integrated/blackpants.kicad_sch
```
