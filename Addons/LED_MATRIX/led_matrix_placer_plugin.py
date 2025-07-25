import pcbnew
import wx
import os

class LEDMatrixPlacerPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "LED Matrix Placer"
        self.category = "Layout"
        self.description = "Place LED matrix components precisely"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")  # Optional icon

    def Run(self):
        try:
            # Execute the LED placement script
            script_path = os.path.join(os.path.dirname(__file__), "led-placement.py")
            exec(open(script_path).read())
            
            wx.MessageBox(
                "LED matrix placement completed successfully!",
                "LED Matrix Placer",
                wx.OK | wx.ICON_INFORMATION
            )
        except Exception as e:
            wx.MessageBox(
                f"Error running LED placement script:\n{str(e)}",
                "LED Matrix Placer - Error",
                wx.OK | wx.ICON_ERROR
            )

# Register the plugin
LEDMatrixPlacerPlugin().register()
