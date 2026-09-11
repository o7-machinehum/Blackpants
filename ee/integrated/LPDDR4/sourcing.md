# LPDDR4 sourcing — checked 2026-09-08

The schematic still selects **Nanya NT6AN512T32AV-J2**, 16Gb / 2GB,
two 16-bit channels in one 200-ball 10 × 15 mm package. I did not find a
verified LCSC listing with stock available for immediate purchase for that MPN.

| Candidate | Purchase listing | Listed stock / single-unit price, USD | Qualification |
| --- | --- | --- | --- |
| **SK hynix H9HCNNNBKUMLXR-NEE** | [LCSC C21912322](https://www.lcsc.com/product-detail/C21912322.html) | **1,400 / $72.1015**, minimum 1, ships now | Best sourcing candidate found; 2GB LPDDR4, two x16 channels, 200-ball 10 × 15 mm, 1.8 / 1.1 / 1.1 V. All 200 ball assignments match the current Nanya part. DRAM initialization and timing remain unqualified. |
| Kingston D1621PM4CDGUIW-U | [Mouser](https://www.mouser.com/en/ProductDetail/Kingston/D1621PM4CDGUIW-U?qs=iLKYxzqNS75AZJ6Cpud91A%3D%3D) | 5 / $139.67, minimum 1 | 2GB LPDDR4 alternative. Package is 200-ball 10 × 14.5 mm; complete pin/mechanical/boot compatibility has not been checked. |

Stock and prices are listing snapshots, before shipping and taxes. No order was
placed and neither candidate has been substituted into the schematic or BOM.

The [SK hynix V1.0 datasheet](../../../docs/a523/H9HCNNNBKUMLXR-NEE_LPDDR4_V1.0.pdf)
was downloaded from the LCSC listing and added to the source manifest. Page 3
specifies organization, supply and speed; page 6 has the ball assignment and
page 7 the package drawing. The part uses LPDDR4 with 1.1 V I/O.

[hynix-pin-comparison.csv](hynix-pin-comparison.csv) compares all 200 cells on
that page with the current Nanya pin CSV. Names were normalized: `CK_t/CK_c`
to positive/negative clocks, `DQS_t/DQS_c` to positive/negative strobes,
`CS0`/`CKE0` to the single-rank names, and channel suffixes to `_a`/`_b`.
No ball assignments differ. This establishes pin compatibility only; it does
not validate controller initialization, timing, training, or board operation.

Kingston documentation: [manufacturer LPDDR4 catalog](https://media.kingston.com/pdfs/emmc/dram-lpddr4-en.pdf)
and [manufacturer datasheet hosted by Mouser](https://www.mouser.com/catalog/specsheets/Kingston_02-12-2025_D1621PM4CDGUIW-U_C3222PM4CDGUIW-U.pdf).
