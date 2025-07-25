# Using KiCad 9.0+ API for removing silkscreen references
# This script removes all silkscreen references for LEDs D1 through D240 from the PCB

import pcbnew

def remove_led_silkscreen_refs():
    """
    Remove silkscreen reference text for LEDs D1 through D240
    """
    # Get the current board
    board = pcbnew.GetBoard()
    
    if board is None:
        print("Error: No board loaded")
        return False
    
    print("Starting to remove silkscreen references for LEDs D1-D240...")
    
    # Counter for tracking removals
    removed_count = 0
    
    # Iterate through all footprints on the board
    for footprint in board.GetFootprints():
        ref_text = footprint.GetReference()
        
        # Check if this is an LED with reference D1-D240
        if ref_text.startswith('D'):
            try:
                # Extract the number part
                ref_num = int(ref_text[1:])
                
                # Check if it's in our range (D1 to D240)
                if 1 <= ref_num <= 240:
                    # Hide the reference text by setting it invisible
                    reference = footprint.Reference()
                    if reference.IsVisible():
                        reference.SetVisible(False)
                        print(f"Removed silkscreen reference for {ref_text}")
                        removed_count += 1
                    else:
                        print(f"Reference {ref_text} was already hidden")
                        
            except ValueError:
                # Skip if the reference doesn't end with a number
                continue
    
    print(f"Completed! Removed {removed_count} LED silkscreen references.")
    
    # Refresh the board display
    pcbnew.Refresh()
    
    return True

def main():
    """Main function to run the script"""
    try:
        success = remove_led_silkscreen_refs()
        if success:
            print("Script completed successfully!")
            print("Remember to save your PCB file (Ctrl+S) to make the changes permanent.")
        else:
            print("Script failed to complete.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

# Run the script
if __name__ == "__main__":
    main()
