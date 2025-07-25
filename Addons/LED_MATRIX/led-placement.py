# ───────────────── USER CONFIG ────────────────────────────────────────────────
REF_PREFIX   = "D"          # your LED refs: D1…D240
ROWS         = 12           # LEDs per column
COLS         = 20           # number of columns
# D1 position will be read automatically from the PCB as the starting point
ROW_SPACING  = 1.8        # vertical spacing between adjacent LEDs in mm
COL_SPACING  = 3.0          # horizontal spacing between adjacent columns in mm
# ───────────────── END USER CONFIG ────────────────────────────────────────────

import pcbnew

board = pcbnew.GetBoard()

# Calculate spacing in board coordinates
X_STEP = pcbnew.FromMM(COL_SPACING)  # horizontal step between columns
Y_STEP = pcbnew.FromMM(ROW_SPACING)  # vertical step between rows

# Find D1 and use its current position as the starting point
d1_footprint = None
for f in board.GetFootprints():
    if f.GetReference() == f"{REF_PREFIX}1":
        d1_footprint = f
        break

if d1_footprint is None:
    print(f"❌ Error: Could not find {REF_PREFIX}1 on the PCB!")
    print("Make sure D1 exists and is placed where you want the matrix to start.")
    exit()

# Get D1's current position as the origin
ORIGIN = d1_footprint.GetPosition()
print(f"📍 Using {REF_PREFIX}1 position as origin: ({pcbnew.ToMM(ORIGIN.x):.3f}, {pcbnew.ToMM(ORIGIN.y):.3f}) mm")

# Collect and sort LEDs by reference number to ensure correct order
def extract_led_number(footprint):
    """Extract numeric part from reference like 'D123' -> 123"""
    ref = footprint.GetReference()
    if ref.startswith(REF_PREFIX):
        try:
            led_num = int(ref[len(REF_PREFIX):])
            # Only include LEDs from 1 to 240
            if 1 <= led_num <= 240:
                return led_num
            else:
                return float('inf')  # Exclude LEDs outside range
        except ValueError:
            return float('inf')  # Put invalid refs at the end
    return float('inf')

# Filter LEDs to only include D1 through D240
all_leds = [f for f in board.GetFootprints() if f.GetReference().startswith(REF_PREFIX)]
filtered_leds = [f for f in all_leds if extract_led_number(f) <= 240]
leds = sorted(filtered_leds, key=extract_led_number)
count = len(leds)
expected = ROWS * COLS
if count != expected:
    print(f"⚠️  Found {count} LEDs but expected {expected} (ROWS×COLS).")

print(f"📋 Processing LEDs D1 through D{min(240, count)} (limiting to D240)")

# Place each LED in column-major order, starting at D1's current position
for idx, f in enumerate(leds):
    col = idx // ROWS
    row = idx % ROWS

    # Compute new position relative to D1's position:
    #   x moves left for each column index
    #   y moves down by ROW_SPACING for each row index
    x = ORIGIN.x - col * X_STEP
    y = ORIGIN.y + row * Y_STEP

    # Set position using KiCad 9.0 compatible method
    try:
        # Try KiCad 9.0+ API first
        f.SetPosition(pcbnew.VECTOR2I(x, y))
    except (AttributeError, TypeError):
        # Fallback to older API
        f.SetPosition(pcbnew.wxPoint(x, y))

# Refresh to update the board view
pcbnew.Refresh()
print(f"✅  Placed {count} LEDs into {COLS} columns × {ROWS} rows.")
print(f"📏  Row spacing: {ROW_SPACING} mm, Column spacing: {COL_SPACING} mm")
print(f"📐  Total matrix dimensions: {(COLS-1) * COL_SPACING:.1f} × {(ROWS-1) * ROW_SPACING:.1f} mm")
print(f"🎯  Matrix starts at D1 position: ({pcbnew.ToMM(ORIGIN.x):.3f}, {pcbnew.ToMM(ORIGIN.y):.3f}) mm")