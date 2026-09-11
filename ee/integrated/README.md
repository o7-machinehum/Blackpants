# Blackpants hardware

Open **blackpants.kicad_pro** for the active A523 schematic and PCB. It replaces
the A33 hierarchy and uses AXP717C + AXP323 with 2GB LPDDR4.

- [Schematic review PDF](capture/review.pdf)
- [Capture status and interface mapping](capture/README.md)
- [Six-layer layout status and previews](layout/README.md)
- [RAM sourcing](LPDDR4/sourcing.md)
- [Source documents](../../docs/a523/README.md)

All 65 SoC-to-RAM signal paths are connected. There are 139 open connections
overall. Routing remains incomplete; DDR timing and signal/power integrity
have not been approved.
