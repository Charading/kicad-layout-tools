import pcbnew
import os
import wx
from .dialog import RotateDialog


class RotateIndividuallyPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Rotate Items Individually"
        self.category = "Layout"
        self.description = "Rotate each selected item around its own center"
        self.show_toolbar_button = True
        
        # Set icon path
        icon_path = os.path.join(os.path.dirname(__file__), "menu_icon.png")
        self.icon_file_name = icon_path if os.path.exists(icon_path) else ""

    def Run(self):
        board = pcbnew.GetBoard()
        
        # Get all selected items
        selected_items = []
        
        # Get footprints
        for footprint in board.GetFootprints():
            if footprint.IsSelected():
                selected_items.append(footprint)
        
        # Get drawings (text, lines, etc.)
        for drawing in board.GetDrawings():
            if drawing.IsSelected():
                selected_items.append(drawing)
        
        # Get tracks
        for track in board.GetTracks():
            if track.IsSelected():
                selected_items.append(track)
        
        if not selected_items:
            wx.MessageBox("No items selected!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Show dialog to get rotation angle
        dlg = RotateDialog(None)
        
        if dlg.ShowModal() == wx.ID_OK:
            angle = dlg.GetAngle()
            
            # Rotate each item around its own center
            for item in selected_items:
                center = item.GetPosition()
                # EDA_ANGLE in KiCad uses degrees
                item.Rotate(center, pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
            
            pcbnew.Refresh()
        
        dlg.Destroy()
