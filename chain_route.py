import pcbnew
import os
import wx
import re
from .chain_dialog import ChainRouteDialog


class ChainRouteLEDsPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Chain Route LEDs"
        self.category = "Layout"
        self.description = "Auto-route chains of LEDs (e.g., WS2812) by connecting output pad to input pad"
        self.show_toolbar_button = True
        
        # Set icon path
        icon_path = os.path.join(os.path.dirname(__file__), "chain_icon.png")
        self.icon_file_name = icon_path if os.path.exists(icon_path) else ""

    def Run(self):
        board = pcbnew.GetBoard()
        
        # Show dialog to get parameters
        dlg = ChainRouteDialog(None)
        
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        
        ref_prefix = dlg.GetRefPrefix()
        output_pad = dlg.GetOutputPad()
        input_pad = dlg.GetInputPad()
        track_width = dlg.GetTrackWidth()
        layer_name = dlg.GetLayer()
        
        dlg.Destroy()
        
        # Find all footprints matching the prefix
        matching_footprints = []
        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if ref.startswith(ref_prefix):
                # Extract number from reference (e.g., "D23" -> 23)
                match = re.search(r'\d+', ref)
                if match:
                    num = int(match.group())
                    matching_footprints.append((num, footprint))
        
        if len(matching_footprints) < 2:
            wx.MessageBox(f"Found only {len(matching_footprints)} footprints with prefix '{ref_prefix}'. Need at least 2 to chain.",
                         "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Sort by reference number
        matching_footprints.sort(key=lambda x: x[0])
        
        # Get the layer
        layer_table = board.GetLayerTable()
        layer_id = None
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            if board.GetLayerName(i) == layer_name:
                layer_id = i
                break
        
        if layer_id is None:
            wx.MessageBox(f"Layer '{layer_name}' not found!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Create tracks between consecutive LEDs
        tracks_created = 0
        errors = []
        
        for i in range(len(matching_footprints) - 1):
            num1, fp1 = matching_footprints[i]
            num2, fp2 = matching_footprints[i + 1]
            
            # Find the output pad on the first footprint
            out_pad = fp1.FindPadByNumber(output_pad)
            if not out_pad:
                errors.append(f"{fp1.GetReference()}: pad {output_pad} not found")
                continue
            
            # Find the input pad on the second footprint
            in_pad = fp2.FindPadByNumber(input_pad)
            if not in_pad:
                errors.append(f"{fp2.GetReference()}: pad {input_pad} not found")
                continue
            
            # Create a track
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(out_pad.GetPosition())
            track.SetEnd(in_pad.GetPosition())
            track.SetWidth(pcbnew.FromMM(track_width))
            track.SetLayer(layer_id)
            
            # Set the net from the output pad
            track.SetNet(out_pad.GetNet())
            
            board.Add(track)
            tracks_created += 1
        
        # Refresh the board
        pcbnew.Refresh()
        
        # Show results
        if errors:
            msg = f"Created {tracks_created} tracks.\n\nErrors:\n" + "\n".join(errors)
            wx.MessageBox(msg, "Completed with Errors", wx.OK | wx.ICON_WARNING)
        else:
            wx.MessageBox(f"Successfully created {tracks_created} tracks!", 
                         "Success", wx.OK | wx.ICON_INFORMATION)
