# How to Run the LED Silkscreen Reference Removal Script

## Prerequisites
- KiCad 9.0 or later
- Your LED_MATRIX.kicad_pcb file should be open in KiCad PCB Editor

## Step-by-Step Instructions

### Method 1: Using KiCad's Script Console (Recommended)
1. Open your `LED_MATRIX.kicad_pcb` file in KiCad PCB Editor
2. Go to **Tools** → **Scripting Console** (or press **Ctrl+Shift+C**)
3. In the console, type the following command to run the script:
   ```python
   exec(open(r'd:\Users\Robert\Documents\GitHub\Others\hw_carriercard\ADDONS\LED_MATRIX\remove_d_refs.py').read())
   ```
4. Press **Enter** to execute the script
5. The script will print progress messages as it removes references
6. When complete, save your PCB file (**Ctrl+S**)

### Method 2: Copy and Paste (Alternative)
1. Open your `LED_MATRIX.kicad_pcb` file in KiCad PCB Editor
2. Open the `remove_d_refs.py` file in a text editor
3. Copy the entire contents of the script
4. Go to **Tools** → **Scripting Console** in KiCad
5. Paste the script into the console
6. Press **Enter** to execute
7. Save your PCB file when complete

### What the Script Does
- Searches for all footprints with references D1 through D240
- Hides the silkscreen reference text for these LEDs
- Prints progress messages showing which references were removed
- Refreshes the PCB display to show changes immediately

### Important Notes
- **Always backup your PCB file before running the script**
- The script only hides the reference text; it doesn't delete the footprints
- Changes are not permanent until you save the file
- If you need to show references again later, you can manually select footprints and change their reference visibility in the properties

### Troubleshooting
- If you get an error about the file path, make sure the path is correct for your system
- If KiCad seems frozen, wait a moment as it processes all 240 references
- If some references don't disappear immediately, try zooming or panning to refresh the display

### Verification
After running the script, you should see that the silkscreen text "D1", "D2", etc. no longer appears on your PCB layout, making it cleaner for manufacturing.
