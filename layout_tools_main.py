import pcbnew
import os
import wx
from .tabbed_dialog import LayoutToolsDialog


class LayoutToolsPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Layout Tools"
        self.category = "Layout"
        self.description = "Multiple layout tools: Rotate items, Chain route LEDs, and more"
        self.show_toolbar_button = True
        
        # Set icon path
        icon_path = os.path.join(os.path.dirname(__file__), "tools_icon.png")
        self.icon_file_name = icon_path if os.path.exists(icon_path) else ""

    def Run(self):
        # Show the tabbed dialog (non-modal)
        dlg = LayoutToolsDialog(None)
        dlg.Show()
