import wx
import pcbnew
import re


# Persistent settings storage
_SETTINGS = {
    'rotate_angle': 90.0,
    'chain_ref_prefix': 'D',
    'chain_output_pad': '1',
    'chain_input_pad': '3',
    'chain_track_width': 0.25,
    'chain_layer': 'F.Cu',
    'chain_use_45deg': True,
    'via_ref_prefix': 'D',
    'via_pad_num': '2',
    'via_size': 0.8,
    'via_drill': 0.4,
    'via_type': 0,
    'via_selected_only': False,
    'select_ref_prefix': 'C',
    'select_pad_num': '1',
    'select_mode_selected': False,
    'pin_label_h_align': 1,
    'pin_label_v_align': 1,
    'pin_label_offset_x': 2.0,
    'pin_label_offset_y': 0.0,
    'pin_label_size': 1.0,
    'pin_label_thickness': 0.15,
    'pin_label_layer': 'F.SilkS',
    'pin_label_rotation': 0.0,
    'offset_source_pattern': 'AMB{}',
    'offset_target_pattern': 'CA{}',
    'offset_x': 0.0,
    'offset_y': 0.0,
    # Pad-to-Pad Route settings
    'p2p_source_pattern': 'D{}',
    'p2p_source_pad': '2',
    'p2p_target_pattern': 'C{}',
    'p2p_target_pad': '1',
    'p2p_track_width': 0.25,
    'p2p_layer': 'F.Cu',
    'p2p_use_45deg': True,
    'p2p_use_via_transition': False,
    'p2p_via_layer': 'B.Cu',
    'p2p_via_size': 0.8,
    'p2p_via_drill': 0.4,
    'p2p_stub_length': 1.0,
    # Unroute Pads settings
    'unroute_pattern': 'D{}',
    'unroute_pad': '2',
    'unroute_follow_traces': True,
}


class LayoutToolsDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Layout Tools", size=(520, 580))
        
        # Create notebook (tabbed interface)
        notebook = wx.Notebook(self)
        
        # Add tabs
        self.rotate_panel = RotatePanel(notebook)
        self.flip_panel = FlipPanel(notebook)
        self.chain_route_panel = ChainRoutePanel(notebook)
        self.pad_to_pad_route_panel = PadToPadRoutePanel(notebook)
        self.unroute_pads_panel = UnroutePadsPanel(notebook)
        self.select_pads_panel = SelectPadsPanel(notebook)
        self.via_panel = AddViasPanel(notebook)
        self.pin_label_panel = PinLabelPanel(notebook)
        self.relative_offset_panel = RelativeOffsetPanel(notebook)

        notebook.AddPage(self.rotate_panel, "Rotate Items")
        notebook.AddPage(self.flip_panel, "Flip Items")
        notebook.AddPage(self.chain_route_panel, "Chain Route LEDs")
        notebook.AddPage(self.pad_to_pad_route_panel, "Pad-to-Pad Route")
        notebook.AddPage(self.unroute_pads_panel, "Unroute Pads")
        notebook.AddPage(self.select_pads_panel, "Select Pads")
        notebook.AddPage(self.via_panel, "Add Vias to Pads")
        notebook.AddPage(self.pin_label_panel, "Pin Header Labels")
        notebook.AddPage(self.relative_offset_panel, "Relative Offset")
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        # Close button at bottom
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        sizer.Add(close_btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        
        # Bind ESC key to close dialog
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)
    
    def OnKeyPress(self, event):
        """Handle keyboard events"""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()


class RotatePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Rotate Selected Items Individually")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Rotate each selected item around its own center.")
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Angle input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label="Rotation Angle (degrees):")
        hbox1.Add(label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        
        self.angle_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['rotate_angle']), min=-360, max=360, initial=_SETTINGS['rotate_angle'], inc=15)
        self.angle_ctrl.SetDigits(2)
        hbox1.Add(self.angle_ctrl, proportion=1)
        
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Quick angle buttons
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_90 = wx.Button(self, label="90°")
        btn_90.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(90))
        hbox2.Add(btn_90, flag=wx.RIGHT, border=5)
        
        btn_180 = wx.Button(self, label="180°")
        btn_180.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(180))
        hbox2.Add(btn_180, flag=wx.RIGHT, border=5)
        
        btn_270 = wx.Button(self, label="270°")
        btn_270.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(270))
        hbox2.Add(btn_270)
        
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        # Rotate button
        rotate_btn = wx.Button(self, label="Rotate Selected Items")
        rotate_btn.Bind(wx.EVT_BUTTON, self.OnRotate)
        vbox.Add(rotate_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        
        self.SetSizer(vbox)
    
    def OnRotate(self, event):
        board = pcbnew.GetBoard()
        angle = self.angle_ctrl.GetValue()
        
        # Save settings
        _SETTINGS['rotate_angle'] = angle
        
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
        
        # Rotate each item around its own center
        for item in selected_items:
            center = item.GetPosition()
            item.Rotate(center, pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        
        pcbnew.Refresh()


class FlipPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Flip Selected Items Individually")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Flip each selected item around its own center.")
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Flip direction selection
        direction_box = wx.StaticBox(self, label="Flip Direction")
        direction_sizer = wx.StaticBoxSizer(direction_box, wx.VERTICAL)
        
        self.flip_horizontal = wx.RadioButton(self, label="Horizontal (Left ↔ Right)", style=wx.RB_GROUP)
        self.flip_vertical = wx.RadioButton(self, label="Vertical (Top ↔ Bottom)")
        self.flip_horizontal.SetValue(True)
        
        direction_sizer.Add(self.flip_horizontal, flag=wx.ALL, border=5)
        direction_sizer.Add(self.flip_vertical, flag=wx.ALL, border=5)
        
        vbox.Add(direction_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Flip button
        flip_btn = wx.Button(self, label="Flip Selected Items")
        flip_btn.Bind(wx.EVT_BUTTON, self.OnFlip)
        vbox.Add(flip_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        
        self.SetSizer(vbox)
    
    def OnFlip(self, event):
        board = pcbnew.GetBoard()
        is_horizontal = self.flip_horizontal.GetValue()
        
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
        
        if not selected_items:
            wx.MessageBox("No items selected!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Flip each item around its own center
        for item in selected_items:
            center = item.GetPosition()
            
            if is_horizontal:
                # Flip horizontally (mirror across vertical axis through center)
                item.Flip(center, False)  # False = flip left-right
            else:
                # Flip vertically (mirror across horizontal axis through center)
                item.Flip(center, True)  # True = flip top-bottom
        
        pcbnew.Refresh()
        
        direction = "horizontally" if is_horizontal else "vertically"
        wx.MessageBox(f"Flipped {len(selected_items)} items {direction}", 
                     "Success", wx.OK | wx.ICON_INFORMATION)


class ChainRoutePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Chain Route LEDs")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Auto-route chains of LEDs (e.g., WS2812) by connecting output to input pads.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['chain_ref_prefix'])
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text1 = wx.StaticText(self, label="(e.g., 'D' for D1, D2, D3...)")
        help_text1.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text1, flag=wx.LEFT | wx.TOP, border=10)
        
        # Output pad number
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(self, label="Output Pad:")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.output_pad_ctrl = wx.TextCtrl(self, value=_SETTINGS['chain_output_pad'], size=(60, -1))
        hbox2.Add(self.output_pad_ctrl)
        
        hbox2.Add(wx.StaticText(self, label="Input Pad:"), 
                 flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        self.input_pad_ctrl = wx.TextCtrl(self, value=_SETTINGS['chain_input_pad'], size=(60, -1))
        hbox2.Add(self.input_pad_ctrl)
        
        vbox.Add(hbox2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text2 = wx.StaticText(self, label="(DO/DOUT → DI/DIN)")
        help_text2.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text2, flag=wx.LEFT | wx.TOP, border=10)
        
        # Track width and layer
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(self, label="Track Width (mm):")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.track_width_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['chain_track_width']), min=0.1, max=10, 
                                                   initial=_SETTINGS['chain_track_width'], inc=0.05, size=(80, -1))
        self.track_width_ctrl.SetDigits(2)
        hbox3.Add(self.track_width_ctrl)
        
        hbox3.Add(wx.StaticText(self, label="Layer:"), 
                 flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        
        # Get layer names
        board = pcbnew.GetBoard()
        layers = []
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            layer_name = board.GetLayerName(i)
            if layer_name and not layer_name.startswith("User."):
                layers.append(layer_name)
        
        self.layer_choice = wx.Choice(self, choices=layers, size=(100, -1))
        if "F.Cu" in layers:
            self.layer_choice.SetStringSelection("F.Cu")
        elif layers:
            self.layer_choice.SetSelection(0)
        
        hbox3.Add(self.layer_choice)
        vbox.Add(hbox3, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # 45-degree routing checkbox
        self.use_45deg_check = wx.CheckBox(self, label="Use 45°/90° routing (diagonal in middle)")
        self.use_45deg_check.SetValue(_SETTINGS['chain_use_45deg'])
        vbox.Add(self.use_45deg_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Create tracks button
        route_btn = wx.Button(self, label="Create Chain Tracks")
        route_btn.Bind(wx.EVT_BUTTON, self.OnChainRoute)
        vbox.Add(route_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.SetSizer(vbox)
    
    def OnChainRoute(self, event):
        board = pcbnew.GetBoard()

        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        output_pad = self.output_pad_ctrl.GetValue().strip()
        input_pad = self.input_pad_ctrl.GetValue().strip()
        track_width = self.track_width_ctrl.GetValue()
        layer_name = self.layer_choice.GetStringSelection()
        use_45deg = self.use_45deg_check.GetValue()

        # Save settings
        _SETTINGS['chain_ref_prefix'] = ref_prefix
        _SETTINGS['chain_output_pad'] = output_pad
        _SETTINGS['chain_input_pad'] = input_pad
        _SETTINGS['chain_track_width'] = track_width
        _SETTINGS['chain_layer'] = layer_name
        _SETTINGS['chain_use_45deg'] = use_45deg

        # Find all footprints matching the prefix
        matching_footprints = []
        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if ref.startswith(ref_prefix):
                match = re.search(r'\d+', ref)
                if match:
                    num = int(match.group())
                    matching_footprints.append((num, footprint))

        if len(matching_footprints) < 2:
            wx.MessageBox(f"Found only {len(matching_footprints)} footprints with prefix '{ref_prefix}'.\nNeed at least 2 to chain.",
                         "Error", wx.OK | wx.ICON_ERROR)
            return

        # Sort by reference number
        matching_footprints.sort(key=lambda x: x[0])

        # Get the layer
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
        width_iu = pcbnew.FromMM(track_width)

        for i in range(len(matching_footprints) - 1):
            num1, fp1 = matching_footprints[i]
            num2, fp2 = matching_footprints[i + 1]

            out_pad = fp1.FindPadByNumber(output_pad)
            if not out_pad:
                errors.append(f"{fp1.GetReference()}: pad {output_pad} not found")
                continue

            in_pad = fp2.FindPadByNumber(input_pad)
            if not in_pad:
                errors.append(f"{fp2.GetReference()}: pad {input_pad} not found")
                continue

            start_pos = out_pad.GetPosition()
            end_pos = in_pad.GetPosition()
            net = out_pad.GetNet()

            if use_45deg:
                # Create 45°/90° route with diagonal in middle
                tracks_created += self._create_45deg_middle_route(board, start_pos, end_pos, width_iu, layer_id, net)
            else:
                # Direct track
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(start_pos)
                track.SetEnd(end_pos)
                track.SetWidth(width_iu)
                track.SetLayer(layer_id)
                track.SetNet(net)
                board.Add(track)
                tracks_created += 1

        pcbnew.Refresh()

        if errors:
            msg = f"Created {tracks_created} track segments.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more errors"
            wx.MessageBox(msg, "Completed with Errors", wx.OK | wx.ICON_WARNING)
        else:
            wx.MessageBox(f"Successfully created {tracks_created} track segments between {len(matching_footprints)} LEDs!",
                         "Success", wx.OK | wx.ICON_INFORMATION)

    def _create_45deg_middle_route(self, board, start_pos, end_pos, width, layer_id, net):
        """Create a route with 45° diagonal in the middle.

        Pattern: straight → 45° diagonal → straight
        Returns the number of track segments created.
        """
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y

        # If already aligned (horizontal, vertical, or 45°), use single track
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(start_pos)
            track.SetEnd(end_pos)
            track.SetWidth(width)
            track.SetLayer(layer_id)
            track.SetNet(net)
            board.Add(track)
            return 1

        # Calculate diagonal and straight portions
        diag_len = min(abs(dx), abs(dy))

        if abs(dx) > abs(dy):
            # More horizontal - split horizontal portion, diagonal handles all vertical
            straight_total = abs(dx) - diag_len
            straight_half = straight_total // 2

            # First point: go horizontal half
            mid1_x = start_pos.x + (straight_half if dx > 0 else -straight_half)
            mid1_y = start_pos.y

            # Second point: after diagonal (handles all dy and matching dx)
            mid2_x = mid1_x + (diag_len if dx > 0 else -diag_len)
            mid2_y = mid1_y + (diag_len if dy > 0 else -diag_len)
        else:
            # More vertical - split vertical portion, diagonal handles all horizontal
            straight_total = abs(dy) - diag_len
            straight_half = straight_total // 2

            # First point: go vertical half
            mid1_x = start_pos.x
            mid1_y = start_pos.y + (straight_half if dy > 0 else -straight_half)

            # Second point: after diagonal (handles all dx and matching dy)
            mid2_x = mid1_x + (diag_len if dx > 0 else -diag_len)
            mid2_y = mid1_y + (diag_len if dy > 0 else -diag_len)

        mid1_pos = pcbnew.VECTOR2I(int(mid1_x), int(mid1_y))
        mid2_pos = pcbnew.VECTOR2I(int(mid2_x), int(mid2_y))

        segments_created = 0

        # First segment (straight) - only if there's distance to cover
        if mid1_pos != start_pos:
            track1 = pcbnew.PCB_TRACK(board)
            track1.SetStart(start_pos)
            track1.SetEnd(mid1_pos)
            track1.SetWidth(width)
            track1.SetLayer(layer_id)
            track1.SetNet(net)
            board.Add(track1)
            segments_created += 1

        # Middle segment (45° diagonal)
        track2 = pcbnew.PCB_TRACK(board)
        track2.SetStart(mid1_pos)
        track2.SetEnd(mid2_pos)
        track2.SetWidth(width)
        track2.SetLayer(layer_id)
        track2.SetNet(net)
        board.Add(track2)
        segments_created += 1

        # Last segment (straight) - only if there's distance to cover
        if mid2_pos != end_pos:
            track3 = pcbnew.PCB_TRACK(board)
            track3.SetStart(mid2_pos)
            track3.SetEnd(end_pos)
            track3.SetWidth(width)
            track3.SetLayer(layer_id)
            track3.SetNet(net)
            board.Add(track3)
            segments_created += 1

        return segments_created


class AddViasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Add Vias to Pads")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Add vias to specific pads across multiple footprints (e.g., all GND pads on LEDs).")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['via_ref_prefix'])
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text1 = wx.StaticText(self, label="(e.g., 'D' for all D1, D2, D3... or leave blank for ALL footprints)")
        help_text1.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text1, flag=wx.LEFT | wx.TOP, border=10)
        
        # Checkbox for selected footprints only
        self.selected_only_check = wx.CheckBox(self, label="Work only on selected footprints")
        self.selected_only_check.SetValue(_SETTINGS['via_selected_only'])
        vbox.Add(self.selected_only_check, flag=wx.LEFT | wx.TOP, border=10)
        
        # Pad number
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(self, label="Pad Number:")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.pad_num_ctrl = wx.TextCtrl(self, value=_SETTINGS['via_pad_num'], size=(80, -1))
        hbox2.Add(self.pad_num_ctrl)
        vbox.Add(hbox2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text2 = wx.StaticText(self, label="(Pad to place via on, e.g., '2' for GND pad)")
        help_text2.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text2, flag=wx.LEFT | wx.TOP, border=10)
        
        # Via parameters
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(self, label="Via Size (mm):")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.via_size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['via_size']), min=0.2, max=5.0, 
                                                initial=_SETTINGS['via_size'], inc=0.1, size=(80, -1))
        self.via_size_ctrl.SetDigits(2)
        hbox3.Add(self.via_size_ctrl)
        
        hbox3.Add(wx.StaticText(self, label="Drill (mm):"), 
                 flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        self.via_drill_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['via_drill']), min=0.1, max=3.0, 
                                                 initial=_SETTINGS['via_drill'], inc=0.1, size=(80, -1))
        self.via_drill_ctrl.SetDigits(2)
        hbox3.Add(self.via_drill_ctrl)
        
        vbox.Add(hbox3, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Layer selection
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        label4 = wx.StaticText(self, label="Via Type:")
        hbox4.Add(label4, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        
        self.via_type_choice = wx.Choice(self, choices=["Through", "Blind/Buried"])
        self.via_type_choice.SetSelection(_SETTINGS['via_type'])
        hbox4.Add(self.via_type_choice, proportion=1)
        
        vbox.Add(hbox4, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Buttons
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        
        select_btn = wx.Button(self, label="Select Pads")
        select_btn.Bind(wx.EVT_BUTTON, self.OnSelectPads)
        hbox_btns.Add(select_btn, flag=wx.RIGHT, border=10)
        
        via_btn = wx.Button(self, label="Create Vias in Pads")
        via_btn.Bind(wx.EVT_BUTTON, self.OnCreateVias)
        hbox_btns.Add(via_btn)
        
        vbox.Add(hbox_btns, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=15)
        
        self.SetSizer(vbox)
    
    def OnSelectPads(self, event):
        """Select pads without creating vias"""
        board = pcbnew.GetBoard()
        
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        pad_num = self.pad_num_ctrl.GetValue().strip()
        selected_only = self.selected_only_check.GetValue()
        
        # Save settings
        _SETTINGS['via_ref_prefix'] = ref_prefix
        _SETTINGS['via_pad_num'] = pad_num
        _SETTINGS['via_selected_only'] = selected_only
        
        # Find all matching pads
        matching_pads = self._find_matching_pads(board, ref_prefix, pad_num, selected_only)
        
        if not matching_pads:
            wx.MessageBox("No matching pads found!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Select all matching pads
        for ref, pad in matching_pads:
            pad.SetSelected()
        
        pcbnew.Refresh()
        wx.MessageBox(f"Selected {len(matching_pads)} pads!", "Success", wx.OK | wx.ICON_INFORMATION)
    
    def _find_matching_pads(self, board, ref_prefix, pad_num, selected_only):
        """Helper to find matching pads"""
        matching_pads = []
        
        for footprint in board.GetFootprints():
            # If selected_only, skip non-selected footprints
            if selected_only and not footprint.IsSelected():
                continue
            
            ref = footprint.GetReference()
            
            # Check if matches prefix (or no prefix means all footprints)
            if not ref_prefix or ref.startswith(ref_prefix):
                pad = footprint.FindPadByNumber(pad_num)
                if pad:
                    matching_pads.append((ref, pad))
        
        return matching_pads
    
    def OnCreateVias(self, event):
        board = pcbnew.GetBoard()
        
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        pad_num = self.pad_num_ctrl.GetValue().strip()
        via_size = self.via_size_ctrl.GetValue()
        via_drill = self.via_drill_ctrl.GetValue()
        via_type = self.via_type_choice.GetSelection()
        selected_only = self.selected_only_check.GetValue()
        
        # Save settings for next time
        _SETTINGS['via_ref_prefix'] = ref_prefix
        _SETTINGS['via_pad_num'] = pad_num
        _SETTINGS['via_size'] = via_size
        _SETTINGS['via_drill'] = via_drill
        _SETTINGS['via_type'] = via_type
        _SETTINGS['via_selected_only'] = selected_only
        
        # Validate drill size
        if via_drill >= via_size:
            wx.MessageBox("Drill size must be smaller than via size!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Find all matching pads
        matching_pads = self._find_matching_pads(board, ref_prefix, pad_num, selected_only)
        
        if not matching_pads:
            msg = f"No pads found"
            if ref_prefix:
                msg += f" on footprints starting with '{ref_prefix}'"
            msg += f" with pad number '{pad_num}'"
            wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Create vias
        vias_created = 0
        
        for ref, pad in matching_pads:
            # Create a via at the pad's position
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pad.GetPosition())
            via.SetWidth(pcbnew.FromMM(via_size))
            via.SetDrill(pcbnew.FromMM(via_drill))
            
            # Set via type
            if via_type == 0:  # Through
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
            else:  # Blind/Buried
                via.SetViaType(pcbnew.VIATYPE_BLIND_BURIED)
            
            # Set the net from the pad
            via.SetNet(pad.GetNet())
            
            # Add to board
            board.Add(via)
            vias_created += 1
        
        pcbnew.Refresh()
        
        msg = f"Successfully created {vias_created} vias"
        if ref_prefix:
            msg += f" on {ref_prefix}* footprints"
        msg += f" at pad {pad_num}!"
        
        wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)


class SelectPadsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Select Pads")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Select specific pads across footprints for further operations.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Selection mode
        mode_box = wx.StaticBox(self, label="Selection Mode")
        mode_sizer = wx.StaticBoxSizer(mode_box, wx.VERTICAL)
        
        self.mode_all = wx.RadioButton(self, label="All matching footprints", style=wx.RB_GROUP)
        self.mode_selected = wx.RadioButton(self, label="Only selected footprints")
        self.mode_all.SetValue(not _SETTINGS['select_mode_selected'])
        self.mode_selected.SetValue(_SETTINGS['select_mode_selected'])
        
        mode_sizer.Add(self.mode_all, flag=wx.ALL, border=5)
        mode_sizer.Add(self.mode_selected, flag=wx.ALL, border=5)
        
        vbox.Add(mode_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['select_ref_prefix'])
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text1 = wx.StaticText(self, label="(e.g., 'C' for capacitors, 'D' for LEDs, blank for all)")
        help_text1.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text1, flag=wx.LEFT | wx.TOP, border=10)
        
        # Pad number
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(self, label="Pad Number:")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.pad_num_ctrl = wx.TextCtrl(self, value=_SETTINGS['select_pad_num'], size=(80, -1))
        hbox2.Add(self.pad_num_ctrl)
        vbox.Add(hbox2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        help_text2 = wx.StaticText(self, label="(Pad number to select, e.g., '1', '2', 'A1', etc.)")
        help_text2.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text2, flag=wx.LEFT | wx.TOP, border=10)
        
        # Action buttons
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        
        select_btn = wx.Button(self, label="Select Pads")
        select_btn.Bind(wx.EVT_BUTTON, self.OnSelectPads)
        hbox_btns.Add(select_btn, flag=wx.RIGHT, border=10)
        
        deselect_btn = wx.Button(self, label="Deselect All")
        deselect_btn.Bind(wx.EVT_BUTTON, self.OnDeselectAll)
        hbox_btns.Add(deselect_btn)
        
        vbox.Add(hbox_btns, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        
        self.SetSizer(vbox)
    
    def OnSelectPads(self, event):
        board = pcbnew.GetBoard()
        
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        pad_num = self.pad_num_ctrl.GetValue().strip()
        selected_footprints_only = self.mode_selected.GetValue()
        
        # Save settings
        _SETTINGS['select_ref_prefix'] = ref_prefix
        _SETTINGS['select_pad_num'] = pad_num
        _SETTINGS['select_mode_selected'] = selected_footprints_only
        
        # Find and select all matching pads
        pads_selected = 0
        
        for footprint in board.GetFootprints():
            # If mode is selected footprints only, skip unselected ones
            if selected_footprints_only and not footprint.IsSelected():
                continue
            
            ref = footprint.GetReference()
            
            # Check if matches prefix
            if not ref_prefix or ref.startswith(ref_prefix):
                pad = footprint.FindPadByNumber(pad_num)
                if pad:
                    pad.SetSelected()
                    pads_selected += 1
        
        pcbnew.Refresh()
        
        if pads_selected > 0:
            msg = f"Selected {pads_selected} pads"
            if ref_prefix:
                msg += f" on {ref_prefix}* footprints"
            if selected_footprints_only:
                msg += " (selected footprints only)"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No matching pads found!", "Error", wx.OK | wx.ICON_ERROR)
    
    def OnDeselectAll(self, event):
        board = pcbnew.GetBoard()
        
        # Deselect all items
        for footprint in board.GetFootprints():
            footprint.ClearSelected()
            for pad in footprint.Pads():
                pad.ClearSelected()
        
        for drawing in board.GetDrawings():
            drawing.ClearSelected()
        
        for track in board.GetTracks():
            track.ClearSelected()
        
        pcbnew.Refresh()
        wx.MessageBox("Deselected all items", "Success", wx.OK | wx.ICON_INFORMATION)


class PinLabelPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Generate Pin Header Labels")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)
        
        # Description
        desc = wx.StaticText(self, label="Generate silkscreen labels for pin headers using net names.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Horizontal Alignment
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Horizontal Align:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.h_align_choice = wx.Choice(self, choices=["Left", "Center", "Right"])
        self.h_align_choice.SetSelection(_SETTINGS['pin_label_h_align'])
        hbox1.Add(self.h_align_choice, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Vertical Alignment
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(self, label="Vertical Align:")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.v_align_choice = wx.Choice(self, choices=["Top", "Middle", "Bottom"])
        self.v_align_choice.SetSelection(_SETTINGS['pin_label_v_align'])
        hbox2.Add(self.v_align_choice, proportion=1)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Offset X
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(self, label="X Offset (mm):")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.offset_x_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['pin_label_offset_x']), 
                                                min=-50, max=50, initial=_SETTINGS['pin_label_offset_x'], inc=0.5)
        self.offset_x_ctrl.SetDigits(2)
        hbox3.Add(self.offset_x_ctrl, proportion=1)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Offset Y
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        label4 = wx.StaticText(self, label="Y Offset (mm):")
        hbox4.Add(label4, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.offset_y_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['pin_label_offset_y']), 
                                                min=-50, max=50, initial=_SETTINGS['pin_label_offset_y'], inc=0.5)
        self.offset_y_ctrl.SetDigits(2)
        hbox4.Add(self.offset_y_ctrl, proportion=1)
        vbox.Add(hbox4, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Text Size
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        label5 = wx.StaticText(self, label="Text Size (mm):")
        hbox5.Add(label5, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['pin_label_size']), 
                                            min=0.1, max=10, initial=_SETTINGS['pin_label_size'], inc=0.1)
        self.size_ctrl.SetDigits(2)
        hbox5.Add(self.size_ctrl, proportion=1)
        vbox.Add(hbox5, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Text Thickness
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        label6 = wx.StaticText(self, label="Text Thickness (mm):")
        hbox6.Add(label6, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.thickness_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['pin_label_thickness']), 
                                                 min=0.01, max=2, initial=_SETTINGS['pin_label_thickness'], inc=0.05)
        self.thickness_ctrl.SetDigits(2)
        hbox6.Add(self.thickness_ctrl, proportion=1)
        vbox.Add(hbox6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Layer Selection
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        label7 = wx.StaticText(self, label="Layer:")
        hbox7.Add(label7, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.layer_choice = wx.Choice(self, choices=["F.SilkS", "B.SilkS", "F.Fab", "B.Fab"])
        layer_index = 0
        layer_choices = ["F.SilkS", "B.SilkS", "F.Fab", "B.Fab"]
        if _SETTINGS['pin_label_layer'] in layer_choices:
            layer_index = layer_choices.index(_SETTINGS['pin_label_layer'])
        self.layer_choice.SetSelection(layer_index)
        hbox7.Add(self.layer_choice, proportion=1)
        vbox.Add(hbox7, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Rotation
        hbox8 = wx.BoxSizer(wx.HORIZONTAL)
        label8 = wx.StaticText(self, label="Rotation (degrees):")
        hbox8.Add(label8, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.rotation_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['pin_label_rotation']), 
                                                min=-360, max=360, initial=_SETTINGS['pin_label_rotation'], inc=90)
        self.rotation_ctrl.SetDigits(1)
        hbox8.Add(self.rotation_ctrl, proportion=1)
        vbox.Add(hbox8, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Generate button
        generate_btn = wx.Button(self, label="Generate Labels for Selected Footprints")
        generate_btn.Bind(wx.EVT_BUTTON, self.OnGenerate)
        vbox.Add(generate_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        
        # Delete button
        delete_btn = wx.Button(self, label="Delete Selected Labels")
        delete_btn.Bind(wx.EVT_BUTTON, self.OnDelete)
        vbox.Add(delete_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        self.SetSizer(vbox)
    
    def OnGenerate(self, event):
        board = pcbnew.GetBoard()
        
        # Save settings
        _SETTINGS['pin_label_h_align'] = self.h_align_choice.GetSelection()
        _SETTINGS['pin_label_v_align'] = self.v_align_choice.GetSelection()
        _SETTINGS['pin_label_offset_x'] = self.offset_x_ctrl.GetValue()
        _SETTINGS['pin_label_offset_y'] = self.offset_y_ctrl.GetValue()
        _SETTINGS['pin_label_size'] = self.size_ctrl.GetValue()
        _SETTINGS['pin_label_thickness'] = self.thickness_ctrl.GetValue()
        layer_choices = ["F.SilkS", "B.SilkS", "F.Fab", "B.Fab"]
        _SETTINGS['pin_label_layer'] = layer_choices[self.layer_choice.GetSelection()]
        _SETTINGS['pin_label_rotation'] = self.rotation_ctrl.GetValue()
        
        # Get settings
        h_align = self.h_align_choice.GetSelection()  # 0=Left, 1=Center, 2=Right
        v_align = self.v_align_choice.GetSelection()  # 0=Top, 1=Middle, 2=Bottom
        offset_x = pcbnew.FromMM(self.offset_x_ctrl.GetValue())
        offset_y = pcbnew.FromMM(self.offset_y_ctrl.GetValue())
        text_size = pcbnew.FromMM(self.size_ctrl.GetValue())
        text_thickness = pcbnew.FromMM(self.thickness_ctrl.GetValue())
        layer_name = layer_choices[self.layer_choice.GetSelection()]
        layer_id = board.GetLayerID(layer_name)
        rotation = self.rotation_ctrl.GetValue()
        
        # Get selected footprints
        selected_footprints = [fp for fp in board.GetFootprints() if fp.IsSelected()]
        
        if not selected_footprints:
            wx.MessageBox("No footprints selected! Please select pin headers.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        labels_created = 0
        created_labels = []
        
        for footprint in selected_footprints:
            for pad in footprint.Pads():
                # Get the net name
                net = pad.GetNet()
                if not net:
                    continue
                
                net_name = net.GetNetname()
                if not net_name or net_name == "":
                    continue
                
                # Remove '/' from net name
                net_name = net_name.replace('/', '')
                
                # Get pad position and size
                pad_pos = pad.GetPosition()
                pad_size = pad.GetSize()
                
                # Calculate label position based on alignment and offset
                label_x = pad_pos.x + offset_x
                label_y = pad_pos.y + offset_y
                
                # Create text object
                text = pcbnew.PCB_TEXT(board)
                text.SetText(net_name)
                text.SetPosition(pcbnew.VECTOR2I(int(label_x), int(label_y)))
                text.SetLayer(layer_id)
                
                # Set text size
                text.SetTextSize(pcbnew.VECTOR2I(int(text_size), int(text_size)))
                text.SetTextThickness(int(text_thickness))
                
                # Set rotation
                text.SetTextAngle(pcbnew.EDA_ANGLE(rotation, pcbnew.DEGREES_T))
                
                # Set horizontal alignment
                if h_align == 0:  # Left
                    text.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
                elif h_align == 1:  # Center
                    text.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
                else:  # Right
                    text.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
                
                # Set vertical alignment
                if v_align == 0:  # Top
                    text.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_TOP)
                elif v_align == 1:  # Middle
                    text.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
                else:  # Bottom
                    text.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_BOTTOM)
                
                # Add to board
                board.Add(text)
                created_labels.append(text)
                labels_created += 1
        
        # Deselect footprints and select the newly created labels
        for footprint in selected_footprints:
            footprint.ClearSelected()
        
        for label in created_labels:
            label.SetSelected()
        
        if labels_created > 0:
            pcbnew.Refresh()
            wx.MessageBox(f"Created {labels_created} pin labels!", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No labels created. Make sure selected footprints have pads with nets.", "Warning", wx.OK | wx.ICON_WARNING)
    
    def OnDelete(self, event):
        board = pcbnew.GetBoard()
        
        # Get all selected text items
        deleted_count = 0
        items_to_delete = []
        
        for drawing in board.GetDrawings():
            if drawing.IsSelected() and isinstance(drawing, pcbnew.PCB_TEXT):
                items_to_delete.append(drawing)
        
        # Delete selected text items
        for item in items_to_delete:
            board.Remove(item)
            deleted_count += 1
        
        if deleted_count > 0:
            pcbnew.Refresh()
            wx.MessageBox(f"Deleted {deleted_count} text items!", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No text items selected!", "Error", wx.OK | wx.ICON_ERROR)


class RelativeOffsetPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Relative Offset by Reference Designator")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Position target footprints relative to source footprints by matching reference designator patterns.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Source pattern input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        source_label = wx.StaticText(self, label="Source Pattern:")
        hbox1.Add(source_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.source_pattern_ctrl = wx.TextCtrl(self, value=_SETTINGS['offset_source_pattern'])
        self.source_pattern_ctrl.Bind(wx.EVT_TEXT, self.OnPatternChange)
        hbox1.Add(self.source_pattern_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Target pattern input
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        target_label = wx.StaticText(self, label="Target Pattern:")
        hbox2.Add(target_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.target_pattern_ctrl = wx.TextCtrl(self, value=_SETTINGS['offset_target_pattern'])
        self.target_pattern_ctrl.Bind(wx.EVT_TEXT, self.OnPatternChange)
        hbox2.Add(self.target_pattern_ctrl, proportion=1)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Help text
        help_text = wx.StaticText(self, label="Use {} as placeholder for numbers (e.g., AMB{} matches AMB1, AMB2, ...)")
        help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # X offset input
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        x_label = wx.StaticText(self, label="X Offset (mm):")
        hbox3.Add(x_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.x_offset_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['offset_x']),
                                                min=-1000, max=1000, initial=_SETTINGS['offset_x'], inc=0.5)
        self.x_offset_ctrl.SetDigits(3)
        hbox3.Add(self.x_offset_ctrl, proportion=1)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Y offset input
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        y_label = wx.StaticText(self, label="Y Offset (mm):")
        hbox4.Add(y_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.y_offset_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['offset_y']),
                                                min=-1000, max=1000, initial=_SETTINGS['offset_y'], inc=0.5)
        self.y_offset_ctrl.SetDigits(3)
        hbox4.Add(self.y_offset_ctrl, proportion=1)
        vbox.Add(hbox4, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Matched pairs display
        self.matched_label = wx.StaticText(self, label="Matched pairs: 0")
        vbox.Add(self.matched_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.pairs_list = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 80))
        vbox.Add(self.pairs_list, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Preset buttons
        preset_hbox = wx.BoxSizer(wx.HORIZONTAL)
        preset_label = wx.StaticText(self, label="Presets:")
        preset_hbox.Add(preset_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)

        led_cap_btn = wx.Button(self, label="LED/Cap (4.80, 0.75)")
        led_cap_btn.Bind(wx.EVT_BUTTON, self.OnLedCapPreset)
        preset_hbox.Add(led_cap_btn, flag=wx.RIGHT, border=5)

        vbox.Add(preset_hbox, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Apply button
        apply_btn = wx.Button(self, label="Apply Offset")
        apply_btn.Bind(wx.EVT_BUTTON, self.OnApplyOffset)
        vbox.Add(apply_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.SetSizer(vbox)

        # Initial update of matched pairs
        self.OnPatternChange(None)

    def OnLedCapPreset(self, event):
        """Fill in LED/Capacitor offset preset values."""
        self.x_offset_ctrl.SetValue(4.80)
        self.y_offset_ctrl.SetValue(0.75)

    def OnPatternChange(self, event):
        """Update matched pairs when patterns change."""
        source_pattern = self.source_pattern_ctrl.GetValue()
        target_pattern = self.target_pattern_ctrl.GetValue()

        pairs = self._find_matching_pairs(source_pattern, target_pattern)

        self.matched_label.SetLabel(f"Matched pairs: {len(pairs)}")

        if pairs:
            # Sort by number and format display
            sorted_nums = sorted(pairs.keys(), key=lambda x: int(x) if x.isdigit() else x)
            pair_strs = []
            for num in sorted_nums[:10]:  # Show first 10
                src, tgt = pairs[num]
                pair_strs.append(f"{src.GetReference()} -> {tgt.GetReference()}")
            if len(pairs) > 10:
                pair_strs.append(f"... and {len(pairs) - 10} more")
            self.pairs_list.SetValue("\n".join(pair_strs))
        else:
            self.pairs_list.SetValue("No matching pairs found")

    def _find_matching_pairs(self, source_pattern, target_pattern):
        """Find footprint pairs where source and target numbers match."""
        if not source_pattern or not target_pattern or "{}" not in source_pattern or "{}" not in target_pattern:
            return {}

        board = pcbnew.GetBoard()

        # Convert patterns to regex
        source_regex = re.escape(source_pattern).replace(r"\{\}", r"(\d+)")
        target_regex = re.escape(target_pattern).replace(r"\{\}", r"(\d+)")

        # Find all footprints matching each pattern
        source_footprints = {}  # {number: footprint}
        target_footprints = {}  # {number: footprint}

        for footprint in board.GetFootprints():
            ref = footprint.GetReference()

            source_match = re.fullmatch(source_regex, ref)
            if source_match:
                source_footprints[source_match.group(1)] = footprint

            target_match = re.fullmatch(target_regex, ref)
            if target_match:
                target_footprints[target_match.group(1)] = footprint

        # Find pairs with matching numbers
        pairs = {}
        for num in source_footprints:
            if num in target_footprints:
                pairs[num] = (source_footprints[num], target_footprints[num])

        return pairs

    def OnApplyOffset(self, event):
        """Apply relative offset to matched footprint pairs."""
        source_pattern = self.source_pattern_ctrl.GetValue()
        target_pattern = self.target_pattern_ctrl.GetValue()
        x_offset_mm = self.x_offset_ctrl.GetValue()
        y_offset_mm = self.y_offset_ctrl.GetValue()

        # Save settings
        _SETTINGS['offset_source_pattern'] = source_pattern
        _SETTINGS['offset_target_pattern'] = target_pattern
        _SETTINGS['offset_x'] = x_offset_mm
        _SETTINGS['offset_y'] = y_offset_mm

        # Find matching pairs
        pairs = self._find_matching_pairs(source_pattern, target_pattern)

        if not pairs:
            wx.MessageBox("No matching footprint pairs found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Convert mm to internal units
        x_offset = pcbnew.FromMM(x_offset_mm)
        y_offset = pcbnew.FromMM(y_offset_mm)

        # Apply offset to each pair
        for num, (source_fp, target_fp) in pairs.items():
            source_pos = source_fp.GetPosition()
            new_x = source_pos.x + x_offset
            new_y = source_pos.y + y_offset
            new_pos = pcbnew.VECTOR2I(int(new_x), int(new_y))
            target_fp.SetPosition(new_pos)

        pcbnew.Refresh()
        wx.MessageBox(f"Applied offset to {len(pairs)} footprint(s)", "Success", wx.OK | wx.ICON_INFORMATION)


class PadToPadRoutePanel(wx.Panel):
    """Route tracks between corresponding pads on matched footprint pairs."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Pad-to-Pad Route")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Route tracks between corresponding pads on matched footprint pairs (e.g., connect LED GND pads to capacitor pads).")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Source pattern input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        source_label = wx.StaticText(self, label="Source Pattern:")
        hbox1.Add(source_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.source_pattern_ctrl = wx.TextCtrl(self, value=_SETTINGS['p2p_source_pattern'])
        self.source_pattern_ctrl.Bind(wx.EVT_TEXT, self.OnPatternChange)
        hbox1.Add(self.source_pattern_ctrl, proportion=1)
        hbox1.Add(wx.StaticText(self, label="Pad:"), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.source_pad_ctrl = wx.TextCtrl(self, value=_SETTINGS['p2p_source_pad'], size=(50, -1))
        hbox1.Add(self.source_pad_ctrl, flag=wx.LEFT, border=5)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Target pattern input
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        target_label = wx.StaticText(self, label="Target Pattern:")
        hbox2.Add(target_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.target_pattern_ctrl = wx.TextCtrl(self, value=_SETTINGS['p2p_target_pattern'])
        self.target_pattern_ctrl.Bind(wx.EVT_TEXT, self.OnPatternChange)
        hbox2.Add(self.target_pattern_ctrl, proportion=1)
        hbox2.Add(wx.StaticText(self, label="Pad:"), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.target_pad_ctrl = wx.TextCtrl(self, value=_SETTINGS['p2p_target_pad'], size=(50, -1))
        hbox2.Add(self.target_pad_ctrl, flag=wx.LEFT, border=5)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Help text
        help_text = wx.StaticText(self, label="Use {} as placeholder for numbers (e.g., D{} matches D1, D2, ...)")
        help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Track width and layer
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(self, label="Track Width (mm):")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.track_width_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['p2p_track_width']), min=0.1, max=10,
                                                   initial=_SETTINGS['p2p_track_width'], inc=0.05, size=(80, -1))
        self.track_width_ctrl.SetDigits(2)
        hbox3.Add(self.track_width_ctrl)

        hbox3.Add(wx.StaticText(self, label="Layer:"),
                 flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)

        # Get layer names
        board = pcbnew.GetBoard()
        layers = []
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            layer_name = board.GetLayerName(i)
            if layer_name and not layer_name.startswith("User."):
                layers.append(layer_name)

        self.layer_choice = wx.Choice(self, choices=layers, size=(100, -1))
        if _SETTINGS['p2p_layer'] in layers:
            self.layer_choice.SetStringSelection(_SETTINGS['p2p_layer'])
        elif "F.Cu" in layers:
            self.layer_choice.SetStringSelection("F.Cu")
        elif layers:
            self.layer_choice.SetSelection(0)

        hbox3.Add(self.layer_choice)
        vbox.Add(hbox3, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # 45-degree routing checkbox
        self.use_45deg_check = wx.CheckBox(self, label="Use 45°/90° routing (instead of direct diagonal)")
        self.use_45deg_check.SetValue(_SETTINGS['p2p_use_45deg'])
        vbox.Add(self.use_45deg_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Via transition checkbox and options
        self.use_via_check = wx.CheckBox(self, label="Use via transition (stub → via → other layer → via → stub)")
        self.use_via_check.SetValue(_SETTINGS['p2p_use_via_transition'])
        self.use_via_check.Bind(wx.EVT_CHECKBOX, self.OnViaCheckChange)
        vbox.Add(self.use_via_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Via options (initially hidden based on checkbox)
        self.via_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.via_options_sizer.Add(wx.StaticText(self, label="Via layer:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_layer_choice = wx.Choice(self, choices=layers, size=(80, -1))
        if _SETTINGS['p2p_via_layer'] in layers:
            self.via_layer_choice.SetStringSelection(_SETTINGS['p2p_via_layer'])
        elif "B.Cu" in layers:
            self.via_layer_choice.SetStringSelection("B.Cu")
        self.via_options_sizer.Add(self.via_layer_choice, flag=wx.RIGHT, border=10)

        self.via_options_sizer.Add(wx.StaticText(self, label="Via:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['p2p_via_size']), min=0.2, max=3.0,
                                                initial=_SETTINGS['p2p_via_size'], inc=0.1, size=(60, -1))
        self.via_size_ctrl.SetDigits(2)
        self.via_options_sizer.Add(self.via_size_ctrl, flag=wx.RIGHT, border=5)

        self.via_options_sizer.Add(wx.StaticText(self, label="/"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_drill_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['p2p_via_drill']), min=0.1, max=2.0,
                                                 initial=_SETTINGS['p2p_via_drill'], inc=0.1, size=(60, -1))
        self.via_drill_ctrl.SetDigits(2)
        self.via_options_sizer.Add(self.via_drill_ctrl, flag=wx.RIGHT, border=10)

        self.via_options_sizer.Add(wx.StaticText(self, label="Stub:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.stub_length_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['p2p_stub_length']), min=0.1, max=10.0,
                                                   initial=_SETTINGS['p2p_stub_length'], inc=0.25, size=(60, -1))
        self.stub_length_ctrl.SetDigits(2)
        self.via_options_sizer.Add(self.stub_length_ctrl)
        self.via_options_sizer.Add(wx.StaticText(self, label="mm"), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=3)

        vbox.Add(self.via_options_sizer, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=25)

        # Preset buttons
        preset_hbox = wx.BoxSizer(wx.HORIZONTAL)
        preset_label = wx.StaticText(self, label="Presets:")
        preset_hbox.Add(preset_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)

        led_cap_btn = wx.Button(self, label="LED/Cap GND")
        led_cap_btn.Bind(wx.EVT_BUTTON, self.OnLedCapPreset)
        preset_hbox.Add(led_cap_btn, flag=wx.RIGHT, border=5)

        vbox.Add(preset_hbox, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Matched pairs display
        self.matched_label = wx.StaticText(self, label="Matched pairs: 0")
        vbox.Add(self.matched_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Create tracks button
        route_btn = wx.Button(self, label="Create Tracks")
        route_btn.Bind(wx.EVT_BUTTON, self.OnCreateTracks)
        vbox.Add(route_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=15)

        self.SetSizer(vbox)

        # Initial update of matched pairs
        self.OnPatternChange(None)

    def OnLedCapPreset(self, event):
        """Fill in LED/Capacitor preset values for GND connection."""
        self.source_pattern_ctrl.SetValue("D{}")
        self.source_pad_ctrl.SetValue("2")
        self.target_pattern_ctrl.SetValue("C{}")
        self.target_pad_ctrl.SetValue("1")

    def OnViaCheckChange(self, event):
        """Show/hide via options based on checkbox state."""
        # The via options are always visible but this could be used for validation
        pass

    def OnPatternChange(self, event):
        """Update matched pairs count when patterns change."""
        source_pattern = self.source_pattern_ctrl.GetValue()
        target_pattern = self.target_pattern_ctrl.GetValue()

        pairs = self._find_matching_pairs(source_pattern, target_pattern)
        self.matched_label.SetLabel(f"Matched pairs: {len(pairs)}")

    def _find_matching_pairs(self, source_pattern, target_pattern):
        """Find footprint pairs where source and target numbers match."""
        if not source_pattern or not target_pattern or "{}" not in source_pattern or "{}" not in target_pattern:
            return {}

        board = pcbnew.GetBoard()

        # Convert patterns to regex
        source_regex = re.escape(source_pattern).replace(r"\{\}", r"(\d+)")
        target_regex = re.escape(target_pattern).replace(r"\{\}", r"(\d+)")

        # Find all footprints matching each pattern
        source_footprints = {}  # {number: footprint}
        target_footprints = {}  # {number: footprint}

        for footprint in board.GetFootprints():
            ref = footprint.GetReference()

            source_match = re.fullmatch(source_regex, ref)
            if source_match:
                source_footprints[source_match.group(1)] = footprint

            target_match = re.fullmatch(target_regex, ref)
            if target_match:
                target_footprints[target_match.group(1)] = footprint

        # Find pairs with matching numbers
        pairs = {}
        for num in source_footprints:
            if num in target_footprints:
                pairs[num] = (source_footprints[num], target_footprints[num])

        return pairs

    def OnCreateTracks(self, event):
        """Create tracks between matched pad pairs."""
        board = pcbnew.GetBoard()

        source_pattern = self.source_pattern_ctrl.GetValue()
        target_pattern = self.target_pattern_ctrl.GetValue()
        source_pad_num = self.source_pad_ctrl.GetValue().strip()
        target_pad_num = self.target_pad_ctrl.GetValue().strip()
        track_width = self.track_width_ctrl.GetValue()
        layer_name = self.layer_choice.GetStringSelection()
        use_45deg = self.use_45deg_check.GetValue()
        use_via_transition = self.use_via_check.GetValue()
        via_layer_name = self.via_layer_choice.GetStringSelection()
        via_size = self.via_size_ctrl.GetValue()
        via_drill = self.via_drill_ctrl.GetValue()
        stub_length = self.stub_length_ctrl.GetValue()

        # Save settings
        _SETTINGS['p2p_source_pattern'] = source_pattern
        _SETTINGS['p2p_source_pad'] = source_pad_num
        _SETTINGS['p2p_target_pattern'] = target_pattern
        _SETTINGS['p2p_target_pad'] = target_pad_num
        _SETTINGS['p2p_track_width'] = track_width
        _SETTINGS['p2p_layer'] = layer_name
        _SETTINGS['p2p_use_45deg'] = use_45deg
        _SETTINGS['p2p_use_via_transition'] = use_via_transition
        _SETTINGS['p2p_via_layer'] = via_layer_name
        _SETTINGS['p2p_via_size'] = via_size
        _SETTINGS['p2p_via_drill'] = via_drill
        _SETTINGS['p2p_stub_length'] = stub_length

        # Find matching pairs
        pairs = self._find_matching_pairs(source_pattern, target_pattern)

        if not pairs:
            wx.MessageBox("No matching footprint pairs found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Get the layers
        layer_id = None
        via_layer_id = None
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            name = board.GetLayerName(i)
            if name == layer_name:
                layer_id = i
            if name == via_layer_name:
                via_layer_id = i

        if layer_id is None:
            wx.MessageBox(f"Layer '{layer_name}' not found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        if use_via_transition and via_layer_id is None:
            wx.MessageBox(f"Via layer '{via_layer_name}' not found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Create tracks between matched pads
        tracks_created = 0
        vias_created = 0
        errors = []
        width_iu = pcbnew.FromMM(track_width)
        via_size_iu = pcbnew.FromMM(via_size)
        via_drill_iu = pcbnew.FromMM(via_drill)
        stub_length_iu = pcbnew.FromMM(stub_length)

        for num, (source_fp, target_fp) in pairs.items():
            source_pad = source_fp.FindPadByNumber(source_pad_num)
            if not source_pad:
                errors.append(f"{source_fp.GetReference()}: pad {source_pad_num} not found")
                continue

            target_pad = target_fp.FindPadByNumber(target_pad_num)
            if not target_pad:
                errors.append(f"{target_fp.GetReference()}: pad {target_pad_num} not found")
                continue

            start_pos = source_pad.GetPosition()
            end_pos = target_pad.GetPosition()
            net = source_pad.GetNet()

            if use_via_transition:
                # Create via transition route
                count, via_count = self._create_via_transition_route(
                    board, start_pos, end_pos, width_iu, layer_id, via_layer_id,
                    net, via_size_iu, via_drill_iu, stub_length_iu, use_45deg
                )
                tracks_created += count
                vias_created += via_count
            elif use_45deg:
                # Create 45°/90° route with two segments
                tracks_created += self._create_45deg_route(board, start_pos, end_pos, width_iu, layer_id, net)
            else:
                # Direct diagonal track
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(start_pos)
                track.SetEnd(end_pos)
                track.SetWidth(width_iu)
                track.SetLayer(layer_id)
                track.SetNet(net)
                board.Add(track)
                tracks_created += 1

        pcbnew.Refresh()

        if errors:
            msg = f"Created {tracks_created} track segments"
            if vias_created > 0:
                msg += f" and {vias_created} vias"
            msg += f".\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more errors"
            wx.MessageBox(msg, "Completed with Errors", wx.OK | wx.ICON_WARNING)
        else:
            msg = f"Successfully created {tracks_created} track segments"
            if vias_created > 0:
                msg += f" and {vias_created} vias"
            msg += " between matched footprints!"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)

    def _create_45deg_route(self, board, start_pos, end_pos, width, layer_id, net):
        """Create a route using 45° and 90° segments only.

        Returns the number of track segments created.
        """
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y

        # If already aligned (horizontal, vertical, or 45°), use single track
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(start_pos)
            track.SetEnd(end_pos)
            track.SetWidth(width)
            track.SetLayer(layer_id)
            track.SetNet(net)
            board.Add(track)
            return 1

        # Determine the diagonal length (minimum of |dx| and |dy|)
        diag_len = min(abs(dx), abs(dy))

        # Calculate the midpoint where we transition from straight to diagonal
        # Strategy: go straight first (along longer axis), then 45° diagonal
        if abs(dx) > abs(dy):
            # Horizontal is longer - go horizontal first, then diagonal
            straight_len = abs(dx) - diag_len
            mid_x = start_pos.x + (straight_len if dx > 0 else -straight_len)
            mid_y = start_pos.y
        else:
            # Vertical is longer - go vertical first, then diagonal
            straight_len = abs(dy) - diag_len
            mid_x = start_pos.x
            mid_y = start_pos.y + (straight_len if dy > 0 else -straight_len)

        mid_pos = pcbnew.VECTOR2I(int(mid_x), int(mid_y))

        # Create first segment (straight)
        track1 = pcbnew.PCB_TRACK(board)
        track1.SetStart(start_pos)
        track1.SetEnd(mid_pos)
        track1.SetWidth(width)
        track1.SetLayer(layer_id)
        track1.SetNet(net)
        board.Add(track1)

        # Create second segment (45° diagonal)
        track2 = pcbnew.PCB_TRACK(board)
        track2.SetStart(mid_pos)
        track2.SetEnd(end_pos)
        track2.SetWidth(width)
        track2.SetLayer(layer_id)
        track2.SetNet(net)
        board.Add(track2)

        return 2

    def _create_via_transition_route(self, board, start_pos, end_pos, width, layer_id, via_layer_id,
                                      net, via_size, via_drill, stub_length, use_45deg):
        """Create a route with via transitions: stub → via → other layer → via → stub.

        Returns (track_count, via_count).
        """
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        total_dist = (dx * dx + dy * dy) ** 0.5

        # If distance is too short for via transition, just do direct route
        if total_dist < stub_length * 3:
            if use_45deg:
                return (self._create_45deg_route(board, start_pos, end_pos, width, layer_id, net), 0)
            else:
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(start_pos)
                track.SetEnd(end_pos)
                track.SetWidth(width)
                track.SetLayer(layer_id)
                track.SetNet(net)
                board.Add(track)
                return (1, 0)

        # Calculate direction unit vector
        if total_dist > 0:
            dir_x = dx / total_dist
            dir_y = dy / total_dist
        else:
            dir_x, dir_y = 1, 0

        # Calculate via positions (stub_length from each end)
        via1_x = start_pos.x + dir_x * stub_length
        via1_y = start_pos.y + dir_y * stub_length
        via1_pos = pcbnew.VECTOR2I(int(via1_x), int(via1_y))

        via2_x = end_pos.x - dir_x * stub_length
        via2_y = end_pos.y - dir_y * stub_length
        via2_pos = pcbnew.VECTOR2I(int(via2_x), int(via2_y))

        tracks_created = 0

        # Create first stub on start layer
        track1 = pcbnew.PCB_TRACK(board)
        track1.SetStart(start_pos)
        track1.SetEnd(via1_pos)
        track1.SetWidth(width)
        track1.SetLayer(layer_id)
        track1.SetNet(net)
        board.Add(track1)
        tracks_created += 1

        # Create first via
        via1 = pcbnew.PCB_VIA(board)
        via1.SetPosition(via1_pos)
        via1.SetWidth(via_size)
        via1.SetDrill(via_drill)
        via1.SetViaType(pcbnew.VIATYPE_THROUGH)
        via1.SetNet(net)
        board.Add(via1)

        # Create middle track on via layer (with optional 45° routing)
        if use_45deg:
            # Use simple 2-segment 45° routing for middle section
            mid_dx = via2_pos.x - via1_pos.x
            mid_dy = via2_pos.y - via1_pos.y

            if mid_dx != 0 and mid_dy != 0 and abs(mid_dx) != abs(mid_dy):
                diag_len = min(abs(mid_dx), abs(mid_dy))
                if abs(mid_dx) > abs(mid_dy):
                    straight_len = abs(mid_dx) - diag_len
                    mid_x = via1_pos.x + (straight_len if mid_dx > 0 else -straight_len)
                    mid_y = via1_pos.y
                else:
                    straight_len = abs(mid_dy) - diag_len
                    mid_x = via1_pos.x
                    mid_y = via1_pos.y + (straight_len if mid_dy > 0 else -straight_len)

                mid_pos = pcbnew.VECTOR2I(int(mid_x), int(mid_y))

                track2a = pcbnew.PCB_TRACK(board)
                track2a.SetStart(via1_pos)
                track2a.SetEnd(mid_pos)
                track2a.SetWidth(width)
                track2a.SetLayer(via_layer_id)
                track2a.SetNet(net)
                board.Add(track2a)
                tracks_created += 1

                track2b = pcbnew.PCB_TRACK(board)
                track2b.SetStart(mid_pos)
                track2b.SetEnd(via2_pos)
                track2b.SetWidth(width)
                track2b.SetLayer(via_layer_id)
                track2b.SetNet(net)
                board.Add(track2b)
                tracks_created += 1
            else:
                # Already aligned, single track
                track2 = pcbnew.PCB_TRACK(board)
                track2.SetStart(via1_pos)
                track2.SetEnd(via2_pos)
                track2.SetWidth(width)
                track2.SetLayer(via_layer_id)
                track2.SetNet(net)
                board.Add(track2)
                tracks_created += 1
        else:
            # Direct track on via layer
            track2 = pcbnew.PCB_TRACK(board)
            track2.SetStart(via1_pos)
            track2.SetEnd(via2_pos)
            track2.SetWidth(width)
            track2.SetLayer(via_layer_id)
            track2.SetNet(net)
            board.Add(track2)
            tracks_created += 1

        # Create second via
        via2 = pcbnew.PCB_VIA(board)
        via2.SetPosition(via2_pos)
        via2.SetWidth(via_size)
        via2.SetDrill(via_drill)
        via2.SetViaType(pcbnew.VIATYPE_THROUGH)
        via2.SetNet(net)
        board.Add(via2)

        # Create last stub on start layer
        track3 = pcbnew.PCB_TRACK(board)
        track3.SetStart(via2_pos)
        track3.SetEnd(end_pos)
        track3.SetWidth(width)
        track3.SetLayer(layer_id)
        track3.SetNet(net)
        board.Add(track3)
        tracks_created += 1

        return (tracks_created, 2)


class UnroutePadsPanel(wx.Panel):
    """Delete tracks connected to specific pads by reference pattern."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Unroute Pads")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Delete all tracks connected to specific pads. Use this to remove unwanted routes.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Reference pattern input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        pattern_label = wx.StaticText(self, label="Reference Pattern:")
        hbox1.Add(pattern_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.pattern_ctrl = wx.TextCtrl(self, value=_SETTINGS['unroute_pattern'])
        self.pattern_ctrl.Bind(wx.EVT_TEXT, self.OnPatternChange)
        hbox1.Add(self.pattern_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Pad number input
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        pad_label = wx.StaticText(self, label="Pad Number:")
        hbox2.Add(pad_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.pad_ctrl = wx.TextCtrl(self, value=_SETTINGS['unroute_pad'], size=(80, -1))
        hbox2.Add(self.pad_ctrl)
        vbox.Add(hbox2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Help text
        help_text = wx.StaticText(self, label="Use {} as placeholder for numbers (e.g., D{} matches D1, D2, ...)")
        help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Matched footprints display
        self.matched_label = wx.StaticText(self, label="Matched footprints: 0")
        vbox.Add(self.matched_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Follow traces checkbox
        self.follow_traces_check = wx.CheckBox(self, label="Remove all connected tracks (follow entire trace)")
        self.follow_traces_check.SetValue(_SETTINGS['unroute_follow_traces'])
        vbox.Add(self.follow_traces_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Buttons
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)

        select_btn = wx.Button(self, label="Select Pads")
        select_btn.Bind(wx.EVT_BUTTON, self.OnSelectPads)
        btn_hbox.Add(select_btn, flag=wx.RIGHT, border=10)

        unroute_btn = wx.Button(self, label="Delete Connected Tracks")
        unroute_btn.Bind(wx.EVT_BUTTON, self.OnUnroute)
        btn_hbox.Add(unroute_btn)

        vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.SetSizer(vbox)

        # Initial update
        self.OnPatternChange(None)

    def OnPatternChange(self, event):
        """Update matched footprints count when pattern changes."""
        pattern = self.pattern_ctrl.GetValue()
        footprints = self._find_matching_footprints(pattern)
        self.matched_label.SetLabel(f"Matched footprints: {len(footprints)}")

    def _find_matching_footprints(self, pattern):
        """Find all footprints matching the pattern."""
        if not pattern:
            return []

        board = pcbnew.GetBoard()
        matching = []

        if "{}" in pattern:
            # Use regex for pattern with placeholder
            regex = re.escape(pattern).replace(r"\{\}", r"(\d+)")
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if re.fullmatch(regex, ref):
                    matching.append(footprint)
        else:
            # Simple prefix match
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if ref.startswith(pattern):
                    matching.append(footprint)

        return matching

    def OnSelectPads(self, event):
        """Select the matching pads without deleting tracks."""
        board = pcbnew.GetBoard()
        pattern = self.pattern_ctrl.GetValue()
        pad_num = self.pad_ctrl.GetValue().strip()

        # Save settings
        _SETTINGS['unroute_pattern'] = pattern
        _SETTINGS['unroute_pad'] = pad_num

        footprints = self._find_matching_footprints(pattern)

        if not footprints:
            wx.MessageBox("No matching footprints found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        pads_selected = 0
        for footprint in footprints:
            pad = footprint.FindPadByNumber(pad_num)
            if pad:
                pad.SetSelected()
                pads_selected += 1

        pcbnew.Refresh()
        wx.MessageBox(f"Selected {pads_selected} pads", "Success", wx.OK | wx.ICON_INFORMATION)

    def OnUnroute(self, event):
        """Delete all tracks connected to the matching pads."""
        board = pcbnew.GetBoard()
        pattern = self.pattern_ctrl.GetValue()
        pad_num = self.pad_ctrl.GetValue().strip()
        follow_traces = self.follow_traces_check.GetValue()

        # Save settings
        _SETTINGS['unroute_pattern'] = pattern
        _SETTINGS['unroute_pad'] = pad_num
        _SETTINGS['unroute_follow_traces'] = follow_traces

        footprints = self._find_matching_footprints(pattern)

        if not footprints:
            wx.MessageBox("No matching footprints found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Collect all pad positions and nets
        pad_positions = set()

        for footprint in footprints:
            pad = footprint.FindPadByNumber(pad_num)
            if pad:
                pos = pad.GetPosition()
                pad_positions.add((pos.x, pos.y))

        if not pad_positions:
            wx.MessageBox(f"No pads with number '{pad_num}' found on matching footprints!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Build a map of all tracks and vias for efficient lookup
        all_tracks = []
        for track in board.GetTracks():
            all_tracks.append(track)

        if follow_traces:
            # Find all connected tracks recursively
            tracks_to_delete = set()
            vias_to_delete = set()

            # Start with positions from our pads
            positions_to_check = set(pad_positions)
            checked_positions = set()

            while positions_to_check:
                current_pos = positions_to_check.pop()
                if current_pos in checked_positions:
                    continue
                checked_positions.add(current_pos)

                for track in all_tracks:
                    if track in tracks_to_delete or track in vias_to_delete:
                        continue

                    start = track.GetStart()
                    end = track.GetEnd()
                    start_tuple = (start.x, start.y)
                    end_tuple = (end.x, end.y)

                    # Check if this track connects to current position
                    if start_tuple == current_pos or end_tuple == current_pos:
                        if isinstance(track, pcbnew.PCB_VIA):
                            vias_to_delete.add(track)
                            # Add via position to check for more connections
                            via_pos = (start.x, start.y)
                            if via_pos not in checked_positions:
                                positions_to_check.add(via_pos)
                        else:
                            tracks_to_delete.add(track)
                            # Add the other end to check for more connections
                            if start_tuple == current_pos:
                                if end_tuple not in checked_positions:
                                    positions_to_check.add(end_tuple)
                            else:
                                if start_tuple not in checked_positions:
                                    positions_to_check.add(start_tuple)

            # Delete tracks and vias
            for track in tracks_to_delete:
                board.Remove(track)
            for via in vias_to_delete:
                board.Remove(via)

            pcbnew.Refresh()
            msg = f"Deleted {len(tracks_to_delete)} tracks"
            if vias_to_delete:
                msg += f" and {len(vias_to_delete)} vias"
            msg += f" connected to {len(pad_positions)} pads"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            # Only delete tracks directly touching the pads
            tracks_to_delete = []

            for track in all_tracks:
                # Skip vias
                if isinstance(track, pcbnew.PCB_VIA):
                    continue

                start = track.GetStart()
                end = track.GetEnd()
                start_tuple = (start.x, start.y)
                end_tuple = (end.x, end.y)

                # Check if either end touches any of our pads
                if start_tuple in pad_positions or end_tuple in pad_positions:
                    tracks_to_delete.append(track)

            # Delete the tracks
            for track in tracks_to_delete:
                board.Remove(track)

            pcbnew.Refresh()
            wx.MessageBox(f"Deleted {len(tracks_to_delete)} tracks connected to {len(pad_positions)} pads",
                         "Success", wx.OK | wx.ICON_INFORMATION)


