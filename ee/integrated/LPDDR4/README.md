# Nanya 2GB LPDDR4

`LPDDR4:NT6AN512T32AV-J2` represents the 16Gb, two-channel, single-rank-per-channel
device listed in Allwinner's A523 DRAM Support List V1.3. The working capture
assumes 2GB; capacity has not been confirmed by the user.

The 200-ball map comes from the Nanya V1.8 datasheet, PDF page 8; package dimensions
are on page 10. See [source provenance](../../../docs/a523/README.md).
True and complementary clocks/strobes have explicit P/N names. All 200 balls,
including NC and DNU, appear once across six units: channel A data, channel B data,
command/clock/reset/ZQ, power, ground, and NC/DNU. The data units face the A523
so each data signal can be drawn as one continuous wire.

The footprint has a 10 × 15mm body, 0.8mm horizontal and 0.65mm vertical pitch,
0.30mm circular copper lands and 0.05mm mask expansion. A1 is upper left in top
view. The land pattern is derived from the package drawing, not a vendor PCB
land-pattern recommendation; fabrication/assembly review remains necessary.
No tracks or vias may attach to DNU pads. No 3D model is included.

Regenerate with `python3 ee/integrated/LPDDR4/generate.py` from the repository
root; Python and `pdftotext` are required. `capture/validate.py` checks all saved
pin assignments, complementary-clock spot checks, KiCad round-trip, footprint
count/orientation and every captured data connection. DRAM firmware parameters,
timing, layout and signal integrity still require validation.
