import wx
import pcbnew
import re
import json
import os
import math
import random


# Settings file path (in same directory as this script)
_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'layout_tools_settings.json')

# Default settings
_DEFAULT_SETTINGS = {
    'rotate_angle': 90.0,
    'chain_ref_prefix': 'LED',
    'chain_output_pad': '2',
    'chain_input_pad': '3',
    'chain_track_width': 0.20,
    'chain_layer': 'B.Cu',
    'chain_use_45deg': True,
    'chain_max_distance': 30.0,
    'chain_use_via_transition': True,
    'chain_via_layer': 'F.Cu',
    'chain_via_size': 0.45,
    'chain_via_drill': 0.20,
    'chain_stub_length': 1.50,
    'via_ref_prefix': 'D',
    'via_pad_num': '2',
    'via_size': 0.8,
    'via_drill': 0.4,
    'via_type': 0,
    'via_selected_only': False,
    'via_offset_x': 0.0,
    'via_offset_y': 0.0,
    'via_auto_route': False,
    'via_track_width': 0.25,
    'via_track_layer': 'F.Cu',
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
    # Select Footprints settings
    'selfp_ref_prefix': 'HE',
    # Nudge Ref Des settings
    'refdes_prefix': 'HE',
    'refdes_nudge_amount': 0.5,
    'refdes_text_size': 1.0,
    'refdes_text_thickness': 0.15,
    # Via Stitching settings
    'vstitch_net': 'GND',
    'vstitch_via_size': 0.8,
    'vstitch_via_drill': 0.4,
    'vstitch_spacing': 5.0,
    'vstitch_mode': 0,
    'vstitch_randomize': False,
    'vstitch_random_amount': 0.5,
    'vstitch_edge_offset': 1.0,
    'vstitch_clearance': 0.5,
    # Connect Footprint Pads settings
    'cfp_ref_prefix': 'HE',
    'cfp_mode_selected': False,
    'cfp_max_distance': 2.0,
    'cfp_track_width': 0.25,
    'cfp_layer': 'F.Cu',
    'cfp_layer_auto': True,
}


def _load_settings():
    """Load settings from file, merging with defaults."""
    settings = _DEFAULT_SETTINGS.copy()
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                # Only update keys that exist in defaults (ignore obsolete keys)
                for key in settings:
                    if key in saved:
                        settings[key] = saved[key]
    except Exception:
        pass  # Use defaults if file can't be read
    return settings


def _save_settings():
    """Save current settings to file."""
    try:
        with open(_SETTINGS_FILE, 'w') as f:
            json.dump(_SETTINGS, f, indent=2)
    except Exception:
        pass  # Silently fail if can't write


# Load settings on module import
_SETTINGS = _load_settings()


class LayoutToolsDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Layout Tools", size=(650, 600),
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        
        # Create notebook (tabbed interface) with multi-row tabs
        notebook = wx.Notebook(self, style=wx.NB_MULTILINE)
        
        # Add tabs
        self.rotate_panel = RotatePanel(notebook)
        self.flip_panel = FlipPanel(notebook)
        self.chain_route_panel = ChainRoutePanel(notebook)
        self.pad_to_pad_route_panel = PadToPadRoutePanel(notebook)
        self.connect_fp_pads_panel = ConnectFootprintPadsPanel(notebook)
        self.unroute_pads_panel = UnroutePadsPanel(notebook)
        self.select_pads_panel = SelectPadsPanel(notebook)
        self.select_footprints_panel = SelectFootprintsPanel(notebook)
        self.select_refdes_panel = SelectRefDesPanel(notebook)
        self.via_panel = AddViasPanel(notebook)
        self.via_stitch_panel = ViaStitchPanel(notebook)
        self.pin_label_panel = PinLabelPanel(notebook)
        self.relative_offset_panel = RelativeOffsetPanel(notebook)

        notebook.AddPage(self.rotate_panel, "Rotate Items")
        notebook.AddPage(self.flip_panel, "Flip Items")
        notebook.AddPage(self.chain_route_panel, "Chain Route LEDs")
        notebook.AddPage(self.pad_to_pad_route_panel, "Pad-to-Pad Route")
        notebook.AddPage(self.connect_fp_pads_panel, "Connect FP Pads")
        notebook.AddPage(self.unroute_pads_panel, "Unroute Pads")
        notebook.AddPage(self.select_pads_panel, "Select Pads")
        notebook.AddPage(self.select_footprints_panel, "Select Footprints")
        notebook.AddPage(self.select_refdes_panel, "Nudge Ref Des")
        notebook.AddPage(self.via_panel, "Add Vias to Pads")
        notebook.AddPage(self.via_stitch_panel, "Via Stitching")
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
        _save_settings()

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
        self._last_created_items = []  # Store items for undo

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

        # Via transition checkbox and options
        self.use_via_check = wx.CheckBox(self, label="Use via transition (stub → via → other layer → via → stub)")
        self.use_via_check.SetValue(_SETTINGS['chain_use_via_transition'])
        vbox.Add(self.use_via_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Via options row
        via_hbox = wx.BoxSizer(wx.HORIZONTAL)
        via_hbox.Add(wx.StaticText(self, label="Via layer:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_layer_choice = wx.Choice(self, choices=layers, size=(80, -1))
        if _SETTINGS['chain_via_layer'] in layers:
            self.via_layer_choice.SetStringSelection(_SETTINGS['chain_via_layer'])
        elif "B.Cu" in layers:
            self.via_layer_choice.SetStringSelection("B.Cu")
        via_hbox.Add(self.via_layer_choice, flag=wx.RIGHT, border=10)

        via_hbox.Add(wx.StaticText(self, label="Via Pad:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['chain_via_size']), min=0.2, max=3.0,
                                                initial=_SETTINGS['chain_via_size'], inc=0.1, size=(80, -1))
        self.via_size_ctrl.SetDigits(2)
        via_hbox.Add(self.via_size_ctrl, flag=wx.RIGHT, border=8)

        via_hbox.Add(wx.StaticText(self, label="Via Hole:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.via_drill_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['chain_via_drill']), min=0.1, max=2.0,
                                                 initial=_SETTINGS['chain_via_drill'], inc=0.1, size=(80, -1))
        self.via_drill_ctrl.SetDigits(2)
        via_hbox.Add(self.via_drill_ctrl, flag=wx.RIGHT, border=8)

        via_hbox.Add(wx.StaticText(self, label="Stub:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.stub_length_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['chain_stub_length']), min=0.1, max=10.0,
                                                   initial=_SETTINGS['chain_stub_length'], inc=0.25, size=(80, -1))
        self.stub_length_ctrl.SetDigits(2)
        via_hbox.Add(self.stub_length_ctrl)
        via_hbox.Add(wx.StaticText(self, label="mm"), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=3)

        vbox.Add(via_hbox, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=25)

        # Max distance setting
        hbox_max = wx.BoxSizer(wx.HORIZONTAL)
        hbox_max.Add(wx.StaticText(self, label="Max Route Distance (mm):"),
                    flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        self.max_distance_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['chain_max_distance']),
                                                    min=1.0, max=500.0,
                                                    initial=_SETTINGS['chain_max_distance'], inc=5.0, size=(80, -1))
        self.max_distance_ctrl.SetDigits(1)
        hbox_max.Add(self.max_distance_ctrl)
        vbox.Add(hbox_max, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_max = wx.StaticText(self, label="(Skip routing if distance exceeds this value)")
        help_max.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_max, flag=wx.LEFT | wx.TOP, border=10)

        # Buttons
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        route_btn = wx.Button(self, label="Create Chain Tracks")
        route_btn.Bind(wx.EVT_BUTTON, self.OnChainRoute)
        btn_hbox.Add(route_btn, flag=wx.RIGHT, border=10)

        self.undo_btn = wx.Button(self, label="Undo Last")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        btn_hbox.Add(self.undo_btn)

        vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.SetSizer(vbox)

        # Bind change events to save settings on change
        self.ref_prefix_ctrl.Bind(wx.EVT_TEXT, self._on_setting_change)
        self.output_pad_ctrl.Bind(wx.EVT_TEXT, self._on_setting_change)
        self.input_pad_ctrl.Bind(wx.EVT_TEXT, self._on_setting_change)
        self.track_width_ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_setting_change)
        self.layer_choice.Bind(wx.EVT_CHOICE, self._on_setting_change)
        self.use_45deg_check.Bind(wx.EVT_CHECKBOX, self._on_setting_change)
        self.use_via_check.Bind(wx.EVT_CHECKBOX, self._on_setting_change)
        self.via_layer_choice.Bind(wx.EVT_CHOICE, self._on_setting_change)
        self.via_size_ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_setting_change)
        self.via_drill_ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_setting_change)
        self.stub_length_ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_setting_change)
        self.max_distance_ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_setting_change)

    def _on_setting_change(self, event):
        """Save settings whenever a control value changes."""
        _SETTINGS['chain_ref_prefix'] = self.ref_prefix_ctrl.GetValue()
        _SETTINGS['chain_output_pad'] = self.output_pad_ctrl.GetValue()
        _SETTINGS['chain_input_pad'] = self.input_pad_ctrl.GetValue()
        _SETTINGS['chain_track_width'] = self.track_width_ctrl.GetValue()
        _SETTINGS['chain_layer'] = self.layer_choice.GetStringSelection()
        _SETTINGS['chain_use_45deg'] = self.use_45deg_check.GetValue()
        _SETTINGS['chain_use_via_transition'] = self.use_via_check.GetValue()
        _SETTINGS['chain_via_layer'] = self.via_layer_choice.GetStringSelection()
        _SETTINGS['chain_via_size'] = self.via_size_ctrl.GetValue()
        _SETTINGS['chain_via_drill'] = self.via_drill_ctrl.GetValue()
        _SETTINGS['chain_stub_length'] = self.stub_length_ctrl.GetValue()
        _SETTINGS['chain_max_distance'] = self.max_distance_ctrl.GetValue()
        _save_settings()
        event.Skip()

    def OnChainRoute(self, event):
        board = pcbnew.GetBoard()

        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        output_pad = self.output_pad_ctrl.GetValue().strip()
        input_pad = self.input_pad_ctrl.GetValue().strip()
        track_width = self.track_width_ctrl.GetValue()
        layer_name = self.layer_choice.GetStringSelection()
        use_45deg = self.use_45deg_check.GetValue()
        use_via_transition = self.use_via_check.GetValue()
        via_layer_name = self.via_layer_choice.GetStringSelection()
        via_size = self.via_size_ctrl.GetValue()
        via_drill = self.via_drill_ctrl.GetValue()
        stub_length = self.stub_length_ctrl.GetValue()
        max_distance = self.max_distance_ctrl.GetValue()

        # Save settings
        _SETTINGS['chain_ref_prefix'] = ref_prefix
        _SETTINGS['chain_output_pad'] = output_pad
        _SETTINGS['chain_input_pad'] = input_pad
        _SETTINGS['chain_track_width'] = track_width
        _SETTINGS['chain_layer'] = layer_name
        _SETTINGS['chain_use_45deg'] = use_45deg
        _SETTINGS['chain_max_distance'] = max_distance
        _SETTINGS['chain_use_via_transition'] = use_via_transition
        _SETTINGS['chain_via_layer'] = via_layer_name
        _SETTINGS['chain_via_size'] = via_size
        _SETTINGS['chain_via_drill'] = via_drill
        _SETTINGS['chain_stub_length'] = stub_length
        _save_settings()

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

        # Create tracks between consecutive LEDs
        self._last_created_items = []  # Clear for undo
        tracks_created = 0
        vias_created = 0
        skipped_distance = 0
        errors = []
        width_iu = pcbnew.FromMM(track_width)
        via_size_iu = pcbnew.FromMM(via_size)
        via_drill_iu = pcbnew.FromMM(via_drill)
        stub_length_iu = pcbnew.FromMM(stub_length)
        max_distance_iu = pcbnew.FromMM(max_distance)

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

            # Check distance
            dx = end_pos.x - start_pos.x
            dy = end_pos.y - start_pos.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance > max_distance_iu:
                skipped_distance += 1
                continue

            if use_via_transition:
                # Create via transition route
                count, via_count, items = self._create_via_transition_route(
                    board, start_pos, end_pos, width_iu, layer_id, via_layer_id,
                    net, via_size_iu, via_drill_iu, stub_length_iu, use_45deg
                )
                tracks_created += count
                vias_created += via_count
                self._last_created_items.extend(items)
            elif use_45deg:
                # Create 45°/90° route with diagonal in middle
                count, items = self._create_45deg_middle_route(board, start_pos, end_pos, width_iu, layer_id, net)
                tracks_created += count
                self._last_created_items.extend(items)
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
                self._last_created_items.append(track)

        pcbnew.Refresh()

        # Enable undo button if items were created
        self.undo_btn.Enable(len(self._last_created_items) > 0)

        if errors:
            msg = f"Created {tracks_created} track segments"
            if vias_created > 0:
                msg += f" and {vias_created} vias"
            if skipped_distance > 0:
                msg += f" (skipped {skipped_distance} routes exceeding {max_distance}mm)"
            msg += f".\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more errors"
            wx.MessageBox(msg, "Completed with Errors", wx.OK | wx.ICON_WARNING)
        else:
            msg = f"Successfully created {tracks_created} track segments"
            if vias_created > 0:
                msg += f" and {vias_created} vias"
            if skipped_distance > 0:
                msg += f" (skipped {skipped_distance} routes exceeding {max_distance}mm)"
            msg += f" between {len(matching_footprints)} LEDs!"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)

    def OnUndo(self, event):
        """Remove items created by the last operation."""
        if not self._last_created_items:
            wx.MessageBox("Nothing to undo!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        board = pcbnew.GetBoard()
        count = len(self._last_created_items)

        for item in self._last_created_items:
            board.Remove(item)

        self._last_created_items = []
        self.undo_btn.Enable(False)
        pcbnew.Refresh()

        wx.MessageBox(f"Removed {count} items.", "Undo Complete", wx.OK | wx.ICON_INFORMATION)

    def _create_45deg_middle_route(self, board, start_pos, end_pos, width, layer_id, net):
        """Create a route with 45° diagonal in the middle.

        Pattern: straight → 45° diagonal → straight
        Returns (segments_created, items_list).
        """
        items = []
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
            items.append(track)
            return (1, items)

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
            items.append(track1)
            segments_created += 1

        # Middle segment (45° diagonal)
        track2 = pcbnew.PCB_TRACK(board)
        track2.SetStart(mid1_pos)
        track2.SetEnd(mid2_pos)
        track2.SetWidth(width)
        track2.SetLayer(layer_id)
        track2.SetNet(net)
        board.Add(track2)
        items.append(track2)
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
            items.append(track3)
            segments_created += 1

        return (segments_created, items)

    def _create_via_transition_route(self, board, start_pos, end_pos, width, layer_id, via_layer_id,
                                      net, via_size, via_drill, stub_length, use_45deg):
        """Create a route with via transitions: stub → via → other layer → via → stub.

        Returns (track_count, via_count, items_list).
        """
        items = []
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        total_dist = (dx * dx + dy * dy) ** 0.5

        # If distance is too short for via transition, just do direct route
        if total_dist < stub_length * 3:
            if use_45deg:
                count, sub_items = self._create_45deg_middle_route(board, start_pos, end_pos, width, layer_id, net)
                return (count, 0, sub_items)
            else:
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(start_pos)
                track.SetEnd(end_pos)
                track.SetWidth(width)
                track.SetLayer(layer_id)
                track.SetNet(net)
                board.Add(track)
                return (1, 0, [track])

        # Calculate via positions - stub comes straight out from pad center
        # If LEDs are more horizontal, stub goes horizontal; if more vertical, stub goes vertical
        if abs(dx) >= abs(dy):
            # More horizontal arrangement - stubs go horizontal (left/right)
            via1_x_offset = stub_length if dx >= 0 else -stub_length
            via1_x = start_pos.x + via1_x_offset
            via1_y = start_pos.y
            via2_x = end_pos.x - via1_x_offset
            via2_y = end_pos.y
        else:
            # More vertical arrangement - stubs go vertical (up/down)
            via1_y_offset = stub_length if dy >= 0 else -stub_length
            via1_x = start_pos.x
            via1_y = start_pos.y + via1_y_offset
            via2_x = end_pos.x
            via2_y = end_pos.y - via1_y_offset

        via1_pos = pcbnew.VECTOR2I(int(via1_x), int(via1_y))
        via2_pos = pcbnew.VECTOR2I(int(via2_x), int(via2_y))

        tracks_created = 0

        # Create first stub: straight out from pad center (purely horizontal or vertical)
        track1 = pcbnew.PCB_TRACK(board)
        track1.SetStart(start_pos)
        track1.SetEnd(via1_pos)
        track1.SetWidth(width)
        track1.SetLayer(layer_id)
        track1.SetNet(net)
        board.Add(track1)
        items.append(track1)
        tracks_created += 1

        # Create first via
        via1 = pcbnew.PCB_VIA(board)
        via1.SetPosition(via1_pos)
        via1.SetWidth(via_size)
        via1.SetDrill(via_drill)
        via1.SetViaType(pcbnew.VIATYPE_THROUGH)
        via1.SetNet(net)
        board.Add(via1)
        items.append(via1)

        # Create middle track on via layer (with optional 45° routing)
        # For 45° mode: straight from via1, diagonal in middle, straight to via2
        if use_45deg:
            mid_dx = via2_pos.x - via1_pos.x
            mid_dy = via2_pos.y - via1_pos.y

            if mid_dx != 0 and mid_dy != 0 and abs(mid_dx) != abs(mid_dy):
                # Need 3-segment routing: straight -> diagonal -> straight
                diag_len = min(abs(mid_dx), abs(mid_dy))
                straight_len = abs(abs(mid_dx) - abs(mid_dy)) / 2  # Split straight portion

                # Calculate mid points for 3-segment path
                if abs(mid_dx) > abs(mid_dy):
                    # More horizontal: straight-x, diagonal, straight-x
                    mid1_x = via1_pos.x + (straight_len if mid_dx > 0 else -straight_len)
                    mid1_y = via1_pos.y
                    mid2_x = mid1_x + (diag_len if mid_dx > 0 else -diag_len)
                    mid2_y = mid1_y + (diag_len if mid_dy > 0 else -diag_len)
                else:
                    # More vertical: straight-y, diagonal, straight-y
                    mid1_x = via1_pos.x
                    mid1_y = via1_pos.y + (straight_len if mid_dy > 0 else -straight_len)
                    mid2_x = mid1_x + (diag_len if mid_dx > 0 else -diag_len)
                    mid2_y = mid1_y + (diag_len if mid_dy > 0 else -diag_len)

                mid1_pos = pcbnew.VECTOR2I(int(mid1_x), int(mid1_y))
                mid2_pos = pcbnew.VECTOR2I(int(mid2_x), int(mid2_y))

                # First segment: straight from via1 (90°)
                track2a = pcbnew.PCB_TRACK(board)
                track2a.SetStart(via1_pos)
                track2a.SetEnd(mid1_pos)
                track2a.SetWidth(width)
                track2a.SetLayer(via_layer_id)
                track2a.SetNet(net)
                board.Add(track2a)
                items.append(track2a)
                tracks_created += 1

                # Second segment: diagonal in middle (45°)
                track2b = pcbnew.PCB_TRACK(board)
                track2b.SetStart(mid1_pos)
                track2b.SetEnd(mid2_pos)
                track2b.SetWidth(width)
                track2b.SetLayer(via_layer_id)
                track2b.SetNet(net)
                board.Add(track2b)
                items.append(track2b)
                tracks_created += 1

                # Third segment: straight to via2 (90°)
                track2c = pcbnew.PCB_TRACK(board)
                track2c.SetStart(mid2_pos)
                track2c.SetEnd(via2_pos)
                track2c.SetWidth(width)
                track2c.SetLayer(via_layer_id)
                track2c.SetNet(net)
                board.Add(track2c)
                items.append(track2c)
                tracks_created += 1
            else:
                # Already aligned (0°, 45°, or 90°), single track
                track2 = pcbnew.PCB_TRACK(board)
                track2.SetStart(via1_pos)
                track2.SetEnd(via2_pos)
                track2.SetWidth(width)
                track2.SetLayer(via_layer_id)
                track2.SetNet(net)
                board.Add(track2)
                items.append(track2)
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
            items.append(track2)
            tracks_created += 1

        # Create second via
        via2 = pcbnew.PCB_VIA(board)
        via2.SetPosition(via2_pos)
        via2.SetWidth(via_size)
        via2.SetDrill(via_drill)
        via2.SetViaType(pcbnew.VIATYPE_THROUGH)
        via2.SetNet(net)
        board.Add(via2)
        items.append(via2)

        # Create last stub: straight from via to pad center (perpendicular)
        track3 = pcbnew.PCB_TRACK(board)
        track3.SetStart(via2_pos)
        track3.SetEnd(end_pos)
        track3.SetWidth(width)
        track3.SetLayer(layer_id)
        track3.SetNet(net)
        board.Add(track3)
        items.append(track3)
        tracks_created += 1

        return (tracks_created, 2, items)


class AddViasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._last_created_items = []  # Store items for undo

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

        # Via Offset
        hbox_offset = wx.BoxSizer(wx.HORIZONTAL)
        hbox_offset.Add(wx.StaticText(self, label="Via Offset X (mm):"),
                       flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.offset_x_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['via_offset_x']),
                                                min=-10.0, max=10.0,
                                                initial=_SETTINGS['via_offset_x'], inc=0.1, size=(70, -1))
        self.offset_x_ctrl.SetDigits(2)
        hbox_offset.Add(self.offset_x_ctrl)

        hbox_offset.Add(wx.StaticText(self, label="Y (mm):"),
                       flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        self.offset_y_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['via_offset_y']),
                                                min=-10.0, max=10.0,
                                                initial=_SETTINGS['via_offset_y'], inc=0.1, size=(70, -1))
        self.offset_y_ctrl.SetDigits(2)
        hbox_offset.Add(self.offset_y_ctrl)
        vbox.Add(hbox_offset, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_offset = wx.StaticText(self, label="(Offset from pad center, positive X = right, positive Y = down)")
        help_offset.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_offset, flag=wx.LEFT | wx.TOP, border=10)

        # Auto route checkbox
        self.auto_route_check = wx.CheckBox(self, label="Auto route from pad to via (when offset)")
        self.auto_route_check.SetValue(_SETTINGS['via_auto_route'])
        self.auto_route_check.Bind(wx.EVT_CHECKBOX, self.OnAutoRouteCheck)
        vbox.Add(self.auto_route_check, flag=wx.LEFT | wx.TOP, border=10)

        # Track settings (for auto route)
        hbox_track = wx.BoxSizer(wx.HORIZONTAL)
        hbox_track.Add(wx.StaticText(self, label="Track Width (mm):"),
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.track_width_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['via_track_width']),
                                                   min=0.1, max=5.0,
                                                   initial=_SETTINGS['via_track_width'], inc=0.05, size=(70, -1))
        self.track_width_ctrl.SetDigits(2)
        hbox_track.Add(self.track_width_ctrl)

        hbox_track.Add(wx.StaticText(self, label="Layer:"),
                      flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        self.track_layer_choice = wx.Choice(self, choices=['F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'])
        layer_idx = ['F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'].index(_SETTINGS['via_track_layer']) if _SETTINGS['via_track_layer'] in ['F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'] else 0
        self.track_layer_choice.SetSelection(layer_idx)
        hbox_track.Add(self.track_layer_choice)
        vbox.Add(hbox_track, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Enable/disable track settings based on auto route checkbox
        self._update_track_controls()

        # Buttons
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        
        select_btn = wx.Button(self, label="Select Pads")
        select_btn.Bind(wx.EVT_BUTTON, self.OnSelectPads)
        hbox_btns.Add(select_btn, flag=wx.RIGHT, border=10)
        
        via_btn = wx.Button(self, label="Create Vias in Pads")
        via_btn.Bind(wx.EVT_BUTTON, self.OnCreateVias)
        hbox_btns.Add(via_btn, flag=wx.RIGHT, border=10)

        self.undo_btn = wx.Button(self, label="Undo Last")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        hbox_btns.Add(self.undo_btn)

        vbox.Add(hbox_btns, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=15)

        self.SetSizer(vbox)

    def OnAutoRouteCheck(self, event):
        """Enable/disable track controls based on auto route checkbox."""
        self._update_track_controls()

    def _update_track_controls(self):
        """Enable track controls only when auto route is checked."""
        enabled = self.auto_route_check.GetValue()
        self.track_width_ctrl.Enable(enabled)
        self.track_layer_choice.Enable(enabled)

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
        _save_settings()

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
        offset_x = self.offset_x_ctrl.GetValue()
        offset_y = self.offset_y_ctrl.GetValue()
        auto_route = self.auto_route_check.GetValue()
        track_width = self.track_width_ctrl.GetValue()
        track_layer_name = self.track_layer_choice.GetStringSelection()

        # Save settings for next time
        _SETTINGS['via_ref_prefix'] = ref_prefix
        _SETTINGS['via_pad_num'] = pad_num
        _SETTINGS['via_size'] = via_size
        _SETTINGS['via_drill'] = via_drill
        _SETTINGS['via_type'] = via_type
        _SETTINGS['via_selected_only'] = selected_only
        _SETTINGS['via_offset_x'] = offset_x
        _SETTINGS['via_offset_y'] = offset_y
        _SETTINGS['via_auto_route'] = auto_route
        _SETTINGS['via_track_width'] = track_width
        _SETTINGS['via_track_layer'] = track_layer_name
        _save_settings()

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

        # Get layer ID for tracks
        layer_id = board.GetLayerID(track_layer_name)

        # Convert offset to internal units
        offset_x_iu = pcbnew.FromMM(offset_x)
        offset_y_iu = pcbnew.FromMM(offset_y)
        has_offset = offset_x != 0 or offset_y != 0

        # Create vias
        self._last_created_items = []  # Clear for undo
        vias_created = 0
        tracks_created = 0

        for ref, pad in matching_pads:
            pad_pos = pad.GetPosition()

            # Calculate via position with offset
            via_pos = pcbnew.VECTOR2I(pad_pos.x + offset_x_iu, pad_pos.y + offset_y_iu)

            # Create a via
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(via_pos)
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
            self._last_created_items.append(via)
            vias_created += 1

            # Create track from pad to via if auto route is enabled and there's an offset
            if auto_route and has_offset:
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(pad_pos)
                track.SetEnd(via_pos)
                track.SetWidth(pcbnew.FromMM(track_width))
                track.SetLayer(layer_id)
                track.SetNet(pad.GetNet())
                board.Add(track)
                self._last_created_items.append(track)
                tracks_created += 1

        pcbnew.Refresh()

        # Enable undo button if items were created
        self.undo_btn.Enable(len(self._last_created_items) > 0)

        msg = f"Successfully created {vias_created} vias"
        if tracks_created > 0:
            msg += f" and {tracks_created} tracks"
        if ref_prefix:
            msg += f" on {ref_prefix}* footprints"
        msg += f" at pad {pad_num}!"

        wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)

    def OnUndo(self, event):
        """Remove items created by the last operation."""
        if not self._last_created_items:
            wx.MessageBox("Nothing to undo!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        board = pcbnew.GetBoard()
        count = len(self._last_created_items)

        for item in self._last_created_items:
            board.Remove(item)

        self._last_created_items = []
        self.undo_btn.Enable(False)
        pcbnew.Refresh()

        wx.MessageBox(f"Removed {count} items.", "Undo Complete", wx.OK | wx.ICON_INFORMATION)


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
        _save_settings()

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


class SelectFootprintsPanel(wx.Panel):
    """Select footprints by reference prefix."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Select Footprints")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Select all footprints matching a reference prefix (e.g., select all HE* footprints).")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['selfp_ref_prefix'])
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_text = wx.StaticText(self, label="(e.g., 'HE' for hall effect switches, 'C' for capacitors, blank for all)")
        help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text, flag=wx.LEFT | wx.TOP, border=10)

        # Action buttons
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)

        select_btn = wx.Button(self, label="Select Footprints")
        select_btn.Bind(wx.EVT_BUTTON, self.OnSelectFootprints)
        hbox_btns.Add(select_btn, flag=wx.RIGHT, border=10)

        deselect_btn = wx.Button(self, label="Deselect All")
        deselect_btn.Bind(wx.EVT_BUTTON, self.OnDeselectAll)
        hbox_btns.Add(deselect_btn)

        vbox.Add(hbox_btns, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.SetSizer(vbox)

    def OnSelectFootprints(self, event):
        board = pcbnew.GetBoard()

        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()

        # Save settings
        _SETTINGS['selfp_ref_prefix'] = ref_prefix
        _save_settings()

        # Find and select all matching footprints
        fps_selected = 0

        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if not ref_prefix or ref.startswith(ref_prefix):
                footprint.SetSelected()
                fps_selected += 1

        pcbnew.Refresh()

        if fps_selected > 0:
            msg = f"Selected {fps_selected} footprints"
            if ref_prefix:
                msg += f" matching {ref_prefix}*"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No matching footprints found!", "Error", wx.OK | wx.ICON_ERROR)

    def OnDeselectAll(self, event):
        board = pcbnew.GetBoard()

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


class SelectRefDesPanel(wx.Panel):
    """Highlight and nudge reference designator text by prefix."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._undo_stack = []  # list of [(ref_field, old_pos), ...]
        self._redo_stack = []

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Nudge Ref Des")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Select and nudge reference designator text for matching footprints.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['refdes_prefix'])
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_text = wx.StaticText(self, label="(e.g., 'HE' to highlight all HE* ref des text)")
        help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text, flag=wx.LEFT | wx.TOP, border=10)

        # Highlight button
        highlight_btn = wx.Button(self, label="Highlight Ref Des")
        highlight_btn.Bind(wx.EVT_BUTTON, self.OnHighlight)
        vbox.Add(highlight_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=10)

        # Status label
        self.status_label = wx.StaticText(self, label="")
        vbox.Add(self.status_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        vbox.AddSpacer(10)

        # Arrow pad with nudge amount in center
        #         [ Up ]
        # [Left] [amount] [Right]
        #        [ Down ]
        arrow_grid = wx.GridBagSizer(5, 5)

        btn_size = (60, 30)

        up_btn = wx.Button(self, label="\u2191 Up", size=btn_size)
        up_btn.Bind(wx.EVT_BUTTON, lambda e: self._nudge(0, -1))
        arrow_grid.Add(up_btn, pos=(0, 1), flag=wx.ALIGN_CENTER)

        left_btn = wx.Button(self, label="\u2190", size=(40, 30))
        left_btn.Bind(wx.EVT_BUTTON, lambda e: self._nudge(-1, 0))
        arrow_grid.Add(left_btn, pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        self.nudge_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['refdes_nudge_amount']),
                                             min=0.01, max=50.0,
                                             initial=_SETTINGS['refdes_nudge_amount'],
                                             inc=0.1, size=(70, -1))
        self.nudge_ctrl.SetDigits(2)
        arrow_grid.Add(self.nudge_ctrl, pos=(1, 1), flag=wx.ALIGN_CENTER)

        right_btn = wx.Button(self, label="\u2192", size=(40, 30))
        right_btn.Bind(wx.EVT_BUTTON, lambda e: self._nudge(1, 0))
        arrow_grid.Add(right_btn, pos=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        down_btn = wx.Button(self, label="\u2193 Down", size=btn_size)
        down_btn.Bind(wx.EVT_BUTTON, lambda e: self._nudge(0, 1))
        arrow_grid.Add(down_btn, pos=(2, 1), flag=wx.ALIGN_CENTER)

        nudge_label = wx.StaticText(self, label="Nudge amount (mm)")
        nudge_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        arrow_grid.Add(nudge_label, pos=(3, 0), span=(1, 3), flag=wx.ALIGN_CENTER | wx.TOP, border=2)

        vbox.Add(arrow_grid, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        vbox.AddSpacer(5)

        # Text size and thickness
        hbox_size = wx.BoxSizer(wx.HORIZONTAL)
        hbox_size.Add(wx.StaticText(self, label="Text Size (mm):"),
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.text_size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['refdes_text_size']),
                                                 min=0.1, max=10.0,
                                                 initial=_SETTINGS['refdes_text_size'],
                                                 inc=0.1, size=(70, -1))
        self.text_size_ctrl.SetDigits(2)
        hbox_size.Add(self.text_size_ctrl, flag=wx.RIGHT, border=15)

        hbox_size.Add(wx.StaticText(self, label="Thickness (mm):"),
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.text_thickness_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['refdes_text_thickness']),
                                                      min=0.01, max=5.0,
                                                      initial=_SETTINGS['refdes_text_thickness'],
                                                      inc=0.05, size=(70, -1))
        self.text_thickness_ctrl.SetDigits(2)
        hbox_size.Add(self.text_thickness_ctrl)

        vbox.Add(hbox_size, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        apply_text_btn = wx.Button(self, label="Apply Size/Thickness")
        apply_text_btn.Bind(wx.EVT_BUTTON, self.OnApplyTextSize)
        vbox.Add(apply_text_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        vbox.AddSpacer(5)

        # Undo / Redo buttons
        hbox_undo = wx.BoxSizer(wx.HORIZONTAL)

        self.undo_btn = wx.Button(self, label="Undo")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        hbox_undo.Add(self.undo_btn, flag=wx.RIGHT, border=10)

        self.redo_btn = wx.Button(self, label="Redo")
        self.redo_btn.Bind(wx.EVT_BUTTON, self.OnRedo)
        self.redo_btn.Enable(False)
        hbox_undo.Add(self.redo_btn)

        vbox.Add(hbox_undo, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        vbox.AddSpacer(10)

        # Hide/Show ref des text
        vis_label = wx.StaticText(self, label="Visibility (hides ref des text on board):")
        vis_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(vis_label, flag=wx.LEFT | wx.TOP, border=10)

        hbox_vis = wx.BoxSizer(wx.HORIZONTAL)

        hide_highlighted_btn = wx.Button(self, label="Hide Highlighted")
        hide_highlighted_btn.Bind(wx.EVT_BUTTON, self.OnHideHighlighted)
        hbox_vis.Add(hide_highlighted_btn, flag=wx.RIGHT, border=5)

        hide_selected_btn = wx.Button(self, label="Hide Selected")
        hide_selected_btn.Bind(wx.EVT_BUTTON, self.OnHideSelected)
        hbox_vis.Add(hide_selected_btn, flag=wx.RIGHT, border=5)

        show_highlighted_btn = wx.Button(self, label="Show Highlighted")
        show_highlighted_btn.Bind(wx.EVT_BUTTON, self.OnShowHighlighted)
        hbox_vis.Add(show_highlighted_btn)

        vbox.Add(hbox_vis, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        self.SetSizer(vbox)

    def _get_matching_ref_fields(self):
        """Get reference text fields for footprints matching the prefix."""
        board = pcbnew.GetBoard()
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        fields = []
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if not ref_prefix or ref.startswith(ref_prefix):
                # In KiCad 9, Reference() returns the reference field (PCB_FIELD)
                ref_field = fp.Reference()
                fields.append(ref_field)
        return fields

    def OnHighlight(self, event):
        """Select/highlight matching ref des text on the board."""
        board = pcbnew.GetBoard()
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()

        _SETTINGS['refdes_prefix'] = ref_prefix
        _save_settings()

        # Deselect everything first
        for fp in board.GetFootprints():
            fp.ClearSelected()
            fp.Reference().ClearSelected()
            fp.Value().ClearSelected()
            for pad in fp.Pads():
                pad.ClearSelected()
        for drawing in board.GetDrawings():
            drawing.ClearSelected()
        for track in board.GetTracks():
            track.ClearSelected()

        # Select matching ref des text
        count = 0
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if not ref_prefix or ref.startswith(ref_prefix):
                fp.Reference().SetSelected()
                count += 1

        pcbnew.Refresh()
        self.status_label.SetLabel(f"Highlighted {count} ref des text items")

    def OnApplyTextSize(self, event):
        """Apply text size and thickness to all matching ref des text."""
        text_size = self.text_size_ctrl.GetValue()
        text_thickness = self.text_thickness_ctrl.GetValue()

        _SETTINGS['refdes_text_size'] = text_size
        _SETTINGS['refdes_text_thickness'] = text_thickness
        _save_settings()

        fields = self._get_matching_ref_fields()
        if not fields:
            wx.MessageBox("No matching ref des found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        size_iu = pcbnew.FromMM(text_size)
        thickness_iu = pcbnew.FromMM(text_thickness)

        # Save old values for undo
        undo_entry = []
        for field in fields:
            old_size = field.GetTextSize()
            old_thickness = field.GetTextThickness()
            undo_entry.append(('text_props', field,
                               pcbnew.VECTOR2I(old_size.x, old_size.y), old_thickness))
            field.SetTextSize(pcbnew.VECTOR2I(int(size_iu), int(size_iu)))
            field.SetTextThickness(int(thickness_iu))

        self._undo_stack.append(undo_entry)
        self._redo_stack.clear()
        self._update_undo_redo_buttons()

        pcbnew.Refresh()
        self.status_label.SetLabel(f"Applied size {text_size}mm / thickness {text_thickness}mm to {len(fields)} ref des")

    def _nudge(self, dx_sign, dy_sign):
        """Nudge all matching ref des text by the nudge amount."""
        amount = self.nudge_ctrl.GetValue()
        _SETTINGS['refdes_nudge_amount'] = amount
        _save_settings()

        fields = self._get_matching_ref_fields()
        if not fields:
            wx.MessageBox("No matching ref des found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        dx = pcbnew.FromMM(amount * dx_sign)
        dy = pcbnew.FromMM(amount * dy_sign)

        # Save old positions for undo
        undo_entry = []
        for field in fields:
            old_pos = field.GetPosition()
            undo_entry.append(('pos', field, pcbnew.VECTOR2I(old_pos.x, old_pos.y)))
            new_pos = pcbnew.VECTOR2I(old_pos.x + dx, old_pos.y + dy)
            field.SetPosition(new_pos)

        self._undo_stack.append(undo_entry)
        self._redo_stack.clear()
        self._update_undo_redo_buttons()

        pcbnew.Refresh()

    def _apply_undo_redo(self, from_stack, to_stack):
        """Generic undo/redo: pop from one stack, save current state to the other."""
        if not from_stack:
            return

        entry = from_stack.pop()
        reverse_entry = []

        for item in entry:
            if item[0] == 'pos':
                _, field, saved_pos = item
                cur_pos = field.GetPosition()
                reverse_entry.append(('pos', field, pcbnew.VECTOR2I(cur_pos.x, cur_pos.y)))
                field.SetPosition(saved_pos)
            elif item[0] == 'text_props':
                _, field, saved_size, saved_thickness = item
                cur_size = field.GetTextSize()
                cur_thickness = field.GetTextThickness()
                reverse_entry.append(('text_props', field,
                                      pcbnew.VECTOR2I(cur_size.x, cur_size.y), cur_thickness))
                field.SetTextSize(saved_size)
                field.SetTextThickness(saved_thickness)
            elif item[0] == 'visible':
                _, field, saved_visible = item
                cur_visible = field.IsVisible()
                reverse_entry.append(('visible', field, cur_visible))
                field.SetVisible(saved_visible)

        to_stack.append(reverse_entry)
        self._update_undo_redo_buttons()
        pcbnew.Refresh()

    def OnUndo(self, event):
        self._apply_undo_redo(self._undo_stack, self._redo_stack)

    def OnRedo(self, event):
        self._apply_undo_redo(self._redo_stack, self._undo_stack)

    def _update_undo_redo_buttons(self):
        self.undo_btn.Enable(len(self._undo_stack) > 0)
        self.redo_btn.Enable(len(self._redo_stack) > 0)

    def _set_visibility(self, fields, visible):
        """Set visibility on fields and record undo entry."""
        if not fields:
            wx.MessageBox("No matching ref des found!", "Error", wx.OK | wx.ICON_ERROR)
            return 0

        undo_entry = []
        count = 0
        for field in fields:
            old_visible = field.IsVisible()
            if old_visible != visible:
                undo_entry.append(('visible', field, old_visible))
                field.SetVisible(visible)
                count += 1

        if undo_entry:
            self._undo_stack.append(undo_entry)
            self._redo_stack.clear()
            self._update_undo_redo_buttons()

        pcbnew.Refresh()
        return count

    def OnHideHighlighted(self, event):
        """Hide all ref des text matching the prefix."""
        fields = self._get_matching_ref_fields()
        count = self._set_visibility(fields, False)
        if count:
            self.status_label.SetLabel(f"Hidden {count} ref des")

    def OnHideSelected(self, event):
        """Hide only currently selected ref des text."""
        board = pcbnew.GetBoard()
        fields = []
        for fp in board.GetFootprints():
            ref_field = fp.Reference()
            if ref_field.IsSelected():
                fields.append(ref_field)
        count = self._set_visibility(fields, False)
        if count:
            self.status_label.SetLabel(f"Hidden {count} selected ref des")
        elif not fields:
            wx.MessageBox("No ref des text is selected on the board!", "Error", wx.OK | wx.ICON_ERROR)

    def OnShowHighlighted(self, event):
        """Show all ref des text matching the prefix."""
        fields = self._get_matching_ref_fields()
        count = self._set_visibility(fields, True)
        if count:
            self.status_label.SetLabel(f"Shown {count} ref des")


class ViaStitchPanel(wx.Panel):
    """Generate via stitching across a board area or along board edges."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._last_created_items = []

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Via Stitching Generator")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Generate via stitching across the board area or along board edges.")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Net selection
        hbox_net = wx.BoxSizer(wx.HORIZONTAL)
        hbox_net.Add(wx.StaticText(self, label="Net:"),
                     flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)

        board = pcbnew.GetBoard()
        net_names = []
        for name in board.GetNetInfo().NetsByName():
            if name:
                net_names.append(str(name))
        net_names.sort()

        self.net_choice = wx.Choice(self, choices=net_names, size=(150, -1))
        if _SETTINGS['vstitch_net'] in net_names:
            self.net_choice.SetStringSelection(_SETTINGS['vstitch_net'])
        elif 'GND' in net_names:
            self.net_choice.SetStringSelection('GND')
        elif net_names:
            self.net_choice.SetSelection(0)
        hbox_net.Add(self.net_choice)

        refresh_btn = wx.Button(self, label="Refresh", size=(60, -1))
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_nets)
        hbox_net.Add(refresh_btn, flag=wx.LEFT, border=5)

        vbox.Add(hbox_net, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Mode selection
        mode_box = wx.StaticBox(self, label="Stitching Mode")
        mode_sizer = wx.StaticBoxSizer(mode_box, wx.VERTICAL)

        self.mode_grid = wx.RadioButton(self, label="Grid Fill (fill board area with vias)", style=wx.RB_GROUP)
        self.mode_edge = wx.RadioButton(self, label="Edge Stitch (vias along board outline)")
        self.mode_grid.SetValue(_SETTINGS['vstitch_mode'] == 0)
        self.mode_edge.SetValue(_SETTINGS['vstitch_mode'] == 1)

        mode_sizer.Add(self.mode_grid, flag=wx.ALL, border=5)
        mode_sizer.Add(self.mode_edge, flag=wx.ALL, border=5)

        vbox.Add(mode_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Via size and drill
        hbox_via = wx.BoxSizer(wx.HORIZONTAL)
        hbox_via.Add(wx.StaticText(self, label="Via Size (mm):"),
                     flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.via_size_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_via_size']),
                                                min=0.2, max=3.0,
                                                initial=_SETTINGS['vstitch_via_size'],
                                                inc=0.1, size=(70, -1))
        self.via_size_ctrl.SetDigits(2)
        hbox_via.Add(self.via_size_ctrl, flag=wx.RIGHT, border=15)

        hbox_via.Add(wx.StaticText(self, label="Drill (mm):"),
                     flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.via_drill_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_via_drill']),
                                                 min=0.1, max=2.0,
                                                 initial=_SETTINGS['vstitch_via_drill'],
                                                 inc=0.1, size=(70, -1))
        self.via_drill_ctrl.SetDigits(2)
        hbox_via.Add(self.via_drill_ctrl)

        vbox.Add(hbox_via, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Spacing
        hbox_spacing = wx.BoxSizer(wx.HORIZONTAL)
        hbox_spacing.Add(wx.StaticText(self, label="Spacing (mm):"),
                         flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.spacing_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_spacing']),
                                               min=0.5, max=50.0,
                                               initial=_SETTINGS['vstitch_spacing'],
                                               inc=0.5, size=(70, -1))
        self.spacing_ctrl.SetDigits(2)
        hbox_spacing.Add(self.spacing_ctrl)
        vbox.Add(hbox_spacing, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Edge offset (for edge mode)
        hbox_edge = wx.BoxSizer(wx.HORIZONTAL)
        hbox_edge.Add(wx.StaticText(self, label="Edge Offset (mm):"),
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.edge_offset_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_edge_offset']),
                                                    min=0.1, max=20.0,
                                                    initial=_SETTINGS['vstitch_edge_offset'],
                                                    inc=0.25, size=(70, -1))
        self.edge_offset_ctrl.SetDigits(2)
        hbox_edge.Add(self.edge_offset_ctrl)
        vbox.Add(hbox_edge, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_edge = wx.StaticText(self, label="(Distance inward from board edge for edge stitch mode)")
        help_edge.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_edge, flag=wx.LEFT | wx.TOP, border=10)

        # Randomize
        hbox_rand = wx.BoxSizer(wx.HORIZONTAL)
        self.randomize_check = wx.CheckBox(self, label="Randomize positions")
        self.randomize_check.SetValue(_SETTINGS['vstitch_randomize'])
        hbox_rand.Add(self.randomize_check, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)

        hbox_rand.Add(wx.StaticText(self, label="Amount (mm):"),
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.random_amount_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_random_amount']),
                                                      min=0.01, max=10.0,
                                                      initial=_SETTINGS['vstitch_random_amount'],
                                                      inc=0.1, size=(70, -1))
        self.random_amount_ctrl.SetDigits(2)
        hbox_rand.Add(self.random_amount_ctrl)

        vbox.Add(hbox_rand, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Clearance
        hbox_clear = wx.BoxSizer(wx.HORIZONTAL)
        hbox_clear.Add(wx.StaticText(self, label="Clearance (mm):"),
                       flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.clearance_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['vstitch_clearance']),
                                                  min=0.1, max=10.0,
                                                  initial=_SETTINGS['vstitch_clearance'],
                                                  inc=0.1, size=(70, -1))
        self.clearance_ctrl.SetDigits(2)
        hbox_clear.Add(self.clearance_ctrl)
        vbox.Add(hbox_clear, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_clear = wx.StaticText(self, label="(Min distance from pads, traces, vias, board edge, NPTH, components)")
        help_clear.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_clear, flag=wx.LEFT | wx.TOP, border=10)

        # Status label
        self.status_label = wx.StaticText(self, label="")
        vbox.Add(self.status_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Buttons
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        gen_btn = wx.Button(self, label="Generate")
        gen_btn.Bind(wx.EVT_BUTTON, self.OnGenerate)
        btn_hbox.Add(gen_btn, flag=wx.RIGHT, border=10)

        self.undo_btn = wx.Button(self, label="Undo Last")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        btn_hbox.Add(self.undo_btn)

        vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP, border=10)

        self.SetSizer(vbox)

    def _on_refresh_nets(self, event):
        """Refresh the net dropdown from the board."""
        board = pcbnew.GetBoard()
        current = self.net_choice.GetStringSelection()
        net_names = []
        for name in board.GetNetInfo().NetsByName():
            if name:
                net_names.append(str(name))
        net_names.sort()
        self.net_choice.Set(net_names)
        if current in net_names:
            self.net_choice.SetStringSelection(current)
        elif net_names:
            self.net_choice.SetSelection(0)

    def _save_settings(self):
        """Save current control values to settings."""
        _SETTINGS['vstitch_net'] = self.net_choice.GetStringSelection()
        _SETTINGS['vstitch_via_size'] = self.via_size_ctrl.GetValue()
        _SETTINGS['vstitch_via_drill'] = self.via_drill_ctrl.GetValue()
        _SETTINGS['vstitch_spacing'] = self.spacing_ctrl.GetValue()
        _SETTINGS['vstitch_mode'] = 0 if self.mode_grid.GetValue() else 1
        _SETTINGS['vstitch_randomize'] = self.randomize_check.GetValue()
        _SETTINGS['vstitch_random_amount'] = self.random_amount_ctrl.GetValue()
        _SETTINGS['vstitch_edge_offset'] = self.edge_offset_ctrl.GetValue()
        _SETTINGS['vstitch_clearance'] = self.clearance_ctrl.GetValue()
        _save_settings()

    def _get_net(self, board):
        """Get the NETINFO_ITEM for the selected net name."""
        net_name = self.net_choice.GetStringSelection()
        if not net_name:
            return None
        nets_by_name = board.GetNetInfo().NetsByName()
        if net_name in nets_by_name:
            return nets_by_name[net_name]
        return None

    def _get_board_edge_segments(self, board):
        """Get line segments on Edge.Cuts layer as list of (start, end) VECTOR2I pairs."""
        edge_cuts_id = board.GetLayerID("Edge.Cuts")
        segments = []

        def _collect_from_drawing(drawing):
            shape = drawing.GetShape()
            if shape == pcbnew.SHAPE_T_SEGMENT:
                segments.append((drawing.GetStart(), drawing.GetEnd()))
            elif shape == pcbnew.SHAPE_T_RECT:
                s = drawing.GetStart()
                e = drawing.GetEnd()
                segments.append((pcbnew.VECTOR2I(s.x, s.y), pcbnew.VECTOR2I(e.x, s.y)))
                segments.append((pcbnew.VECTOR2I(e.x, s.y), pcbnew.VECTOR2I(e.x, e.y)))
                segments.append((pcbnew.VECTOR2I(e.x, e.y), pcbnew.VECTOR2I(s.x, e.y)))
                segments.append((pcbnew.VECTOR2I(s.x, e.y), pcbnew.VECTOR2I(s.x, s.y)))
            elif shape == pcbnew.SHAPE_T_ARC:
                segments.extend(self._approximate_arc(drawing))
            elif shape == pcbnew.SHAPE_T_CIRCLE:
                # Approximate circle with segments
                center = drawing.GetCenter()
                start = drawing.GetStart()
                dx = start.x - center.x
                dy = start.y - center.y
                radius = math.sqrt(dx * dx + dy * dy)
                num_segs = 36
                for i in range(num_segs):
                    a1 = 2 * math.pi * i / num_segs
                    a2 = 2 * math.pi * (i + 1) / num_segs
                    p1 = pcbnew.VECTOR2I(int(center.x + radius * math.cos(a1)),
                                          int(center.y + radius * math.sin(a1)))
                    p2 = pcbnew.VECTOR2I(int(center.x + radius * math.cos(a2)),
                                          int(center.y + radius * math.sin(a2)))
                    segments.append((p1, p2))
            elif shape == pcbnew.SHAPE_T_POLY:
                # Polygon outline
                try:
                    poly = drawing.GetPolyShape()
                    for outline_idx in range(poly.OutlineCount()):
                        outline = poly.Outline(outline_idx)
                        pts = outline.PointCount()
                        for i in range(pts):
                            p1 = outline.CPoint(i)
                            p2 = outline.CPoint((i + 1) % pts)
                            segments.append((
                                pcbnew.VECTOR2I(p1.x, p1.y),
                                pcbnew.VECTOR2I(p2.x, p2.y)
                            ))
                except Exception:
                    pass

        # Board-level drawings
        for drawing in board.GetDrawings():
            if drawing.GetLayer() == edge_cuts_id:
                _collect_from_drawing(drawing)

        # Footprint-level edge cuts (cutouts, mounting holes, etc.)
        for fp in board.GetFootprints():
            for item in fp.GraphicalItems():
                if item.GetLayer() == edge_cuts_id:
                    _collect_from_drawing(item)

        return segments

    def _approximate_arc(self, arc_drawing):
        """Approximate an arc with short line segments."""
        center = arc_drawing.GetCenter()
        start = arc_drawing.GetStart()
        # Calculate radius and angles
        dx = start.x - center.x
        dy = start.y - center.y
        radius = math.sqrt(dx * dx + dy * dy)
        start_angle = math.atan2(dy, dx)

        arc_angle_eda = arc_drawing.GetArcAngle()
        # GetArcAngle returns EDA_ANGLE; convert to radians
        arc_angle_deg = arc_angle_eda.AsDegrees()
        arc_angle_rad = math.radians(arc_angle_deg)

        # Number of segments based on arc length
        num_segs = max(8, int(abs(arc_angle_deg) / 5))
        step = arc_angle_rad / num_segs

        segments = []
        for i in range(num_segs):
            a1 = start_angle + step * i
            a2 = start_angle + step * (i + 1)
            p1 = pcbnew.VECTOR2I(int(center.x + radius * math.cos(a1)),
                                  int(center.y + radius * math.sin(a1)))
            p2 = pcbnew.VECTOR2I(int(center.x + radius * math.cos(a2)),
                                  int(center.y + radius * math.sin(a2)))
            segments.append((p1, p2))
        return segments

    def _is_inside_board(self, board, point):
        """Check if a point is inside the board outline using ray casting."""
        edge_segments = self._get_board_edge_segments(board)
        if not edge_segments:
            return True  # No edge defined, allow all points

        # Ray casting algorithm: count intersections with a horizontal ray
        px, py = point.x, point.y
        crossings = 0
        for seg_start, seg_end in edge_segments:
            x1, y1 = seg_start.x, seg_start.y
            x2, y2 = seg_end.x, seg_end.y
            # Check if ray from (px, py) going right crosses this segment
            if (y1 <= py < y2) or (y2 <= py < y1):
                # Calculate x intersection
                if y1 != y2:
                    x_intersect = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
                    if px < x_intersect:
                        crossings += 1

        return crossings % 2 == 1

    def _point_to_segment_dist(self, px, py, x1, y1, x2, y2):
        """Return distance from point (px,py) to line segment (x1,y1)-(x2,y2)."""
        dx = x2 - x1
        dy = y2 - y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            # Zero-length segment
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        # Project point onto segment, clamped to [0,1]
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    def _build_collision_cache(self, board):
        """Pre-build lists of obstacles for fast collision checking."""
        cache = {
            'pads': [],       # (x, y, radius)
            'vias': [],       # (x, y, radius)
            'tracks': [],     # (x1, y1, x2, y2, half_width)
            'edges': [],      # (x1, y1, x2, y2)
        }

        # Pads (including NPTH)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                p = pad.GetPosition()
                # Use pad bounding box half-diagonal as radius
                bb = pad.GetBoundingBox()
                rx = bb.GetWidth() / 2
                ry = bb.GetHeight() / 2
                radius = math.sqrt(rx * rx + ry * ry)
                cache['pads'].append((p.x, p.y, radius))

        # Vias and tracks
        for track in board.GetTracks():
            if isinstance(track, pcbnew.PCB_VIA):
                p = track.GetPosition()
                cache['vias'].append((p.x, p.y, track.GetWidth() / 2))
            else:
                s = track.GetStart()
                e = track.GetEnd()
                cache['tracks'].append((s.x, s.y, e.x, e.y, track.GetWidth() / 2))

        # Board edge segments
        for seg_start, seg_end in self._get_board_edge_segments(board):
            cache['edges'].append((seg_start.x, seg_start.y, seg_end.x, seg_end.y))

        return cache

    def _check_collision(self, board, pos, clearance_iu, cache=None):
        """Check if position is too close to any obstacle."""
        if cache is None:
            cache = self._build_collision_cache(board)

        px, py = pos.x, pos.y

        # Check pads (including NPTH)
        for x, y, radius in cache['pads']:
            dx = px - x
            dy = py - y
            if dx * dx + dy * dy < (clearance_iu + radius) ** 2:
                return True

        # Check existing vias
        for x, y, radius in cache['vias']:
            dx = px - x
            dy = py - y
            if dx * dx + dy * dy < (clearance_iu + radius) ** 2:
                return True

        # Check traces
        for x1, y1, x2, y2, half_w in cache['tracks']:
            dist = self._point_to_segment_dist(px, py, x1, y1, x2, y2)
            if dist < clearance_iu + half_w:
                return True

        # Check board edge
        for x1, y1, x2, y2 in cache['edges']:
            dist = self._point_to_segment_dist(px, py, x1, y1, x2, y2)
            if dist < clearance_iu:
                return True

        return False

    def _generate_grid(self, board, net, via_size_iu, via_drill_iu, spacing_iu,
                       randomize, random_iu, clearance_iu):
        """Generate vias on a grid across the board area."""
        bbox = board.GetBoardEdgesBoundingBox()
        if bbox.GetWidth() == 0 or bbox.GetHeight() == 0:
            wx.MessageBox("No board outline found! Draw an Edge.Cuts outline first.",
                          "Error", wx.OK | wx.ICON_ERROR)
            return []

        cache = self._build_collision_cache(board)

        items = []
        x = bbox.GetLeft() + spacing_iu // 2
        while x < bbox.GetRight():
            y = bbox.GetTop() + spacing_iu // 2
            while y < bbox.GetBottom():
                vx, vy = x, y
                if randomize:
                    vx += int(random.uniform(-random_iu, random_iu))
                    vy += int(random.uniform(-random_iu, random_iu))

                pos = pcbnew.VECTOR2I(int(vx), int(vy))

                # Check if inside board outline
                if not self._is_inside_board(board, pos):
                    y += spacing_iu
                    continue

                # Check collision with everything
                if self._check_collision(board, pos, clearance_iu, cache):
                    y += spacing_iu
                    continue

                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pos)
                via.SetWidth(via_size_iu)
                via.SetDrill(via_drill_iu)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetNet(net)
                board.Add(via)
                items.append(via)

                y += spacing_iu
            x += spacing_iu

        return items

    def _generate_edge(self, board, net, via_size_iu, via_drill_iu, spacing_iu,
                       edge_offset_iu, randomize, random_iu, clearance_iu):
        """Generate vias along the board edge."""
        edge_segments = self._get_board_edge_segments(board)
        if not edge_segments:
            wx.MessageBox("No board outline found! Draw an Edge.Cuts outline first.",
                          "Error", wx.OK | wx.ICON_ERROR)
            return []

        cache = self._build_collision_cache(board)
        items = []

        for seg_start, seg_end in edge_segments:
            dx = seg_end.x - seg_start.x
            dy = seg_end.y - seg_start.y
            seg_len = math.sqrt(dx * dx + dy * dy)
            if seg_len < 1:
                continue

            # Unit vector along segment
            ux = dx / seg_len
            uy = dy / seg_len

            # Normal vector pointing inward (perpendicular, rotated 90 CW)
            # We'll use the board center to determine inward direction
            bbox = board.GetBoardEdgesBoundingBox()
            cx = bbox.GetCenter().x
            cy = bbox.GetCenter().y

            # Two possible normals
            nx1, ny1 = -uy, ux
            nx2, ny2 = uy, -ux

            # Pick the one pointing toward board center
            mid_x = (seg_start.x + seg_end.x) / 2
            mid_y = (seg_start.y + seg_end.y) / 2
            d1 = (mid_x + nx1 * edge_offset_iu - cx) ** 2 + (mid_y + ny1 * edge_offset_iu - cy) ** 2
            d2 = (mid_x + nx2 * edge_offset_iu - cx) ** 2 + (mid_y + ny2 * edge_offset_iu - cy) ** 2
            if d1 < d2:
                nx, ny = nx1, ny1
            else:
                nx, ny = nx2, ny2

            # Place vias along segment
            num_vias = max(1, int(seg_len / spacing_iu))
            for i in range(num_vias):
                t = (i + 0.5) / num_vias  # Centered in each segment interval
                px = seg_start.x + dx * t + nx * edge_offset_iu
                py = seg_start.y + dy * t + ny * edge_offset_iu

                if randomize:
                    px += random.uniform(-random_iu, random_iu)
                    py += random.uniform(-random_iu, random_iu)

                pos = pcbnew.VECTOR2I(int(px), int(py))

                if self._check_collision(board, pos, clearance_iu, cache):
                    continue

                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pos)
                via.SetWidth(via_size_iu)
                via.SetDrill(via_drill_iu)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetNet(net)
                board.Add(via)
                items.append(via)

        return items

    def OnGenerate(self, event):
        """Generate via stitching."""
        board = pcbnew.GetBoard()
        self._save_settings()

        net = self._get_net(board)
        if not net:
            wx.MessageBox("Selected net not found!", "Error", wx.OK | wx.ICON_ERROR)
            return

        via_size = self.via_size_ctrl.GetValue()
        via_drill = self.via_drill_ctrl.GetValue()
        spacing = self.spacing_ctrl.GetValue()
        edge_offset = self.edge_offset_ctrl.GetValue()
        randomize = self.randomize_check.GetValue()
        random_amount = self.random_amount_ctrl.GetValue()
        clearance = self.clearance_ctrl.GetValue()
        is_grid = self.mode_grid.GetValue()

        via_size_iu = pcbnew.FromMM(via_size)
        via_drill_iu = pcbnew.FromMM(via_drill)
        spacing_iu = pcbnew.FromMM(spacing)
        edge_offset_iu = pcbnew.FromMM(edge_offset)
        random_iu = pcbnew.FromMM(random_amount)
        clearance_iu = pcbnew.FromMM(clearance)

        self._last_created_items = []

        if is_grid:
            items = self._generate_grid(board, net, via_size_iu, via_drill_iu,
                                        spacing_iu, randomize, random_iu, clearance_iu)
        else:
            items = self._generate_edge(board, net, via_size_iu, via_drill_iu,
                                        spacing_iu, edge_offset_iu, randomize, random_iu,
                                        clearance_iu)

        self._last_created_items = items
        self._last_created_group = None

        if items:
            # Add all vias to a group
            group = pcbnew.PCB_GROUP(board)
            group.SetName("Via Stitching")
            board.Add(group)
            for via in items:
                group.AddItem(via)
            self._last_created_group = group

            # Select all created vias
            for via in items:
                via.SetSelected()

        self.undo_btn.Enable(len(items) > 0)
        pcbnew.Refresh()

        mode_str = "grid fill" if is_grid else "edge stitch"
        self.status_label.SetLabel(f"Created {len(items)} vias ({mode_str})")
        if items:
            wx.MessageBox(f"Created {len(items)} stitching vias ({mode_str}), added to group 'Via Stitching'.",
                          "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No vias created. Check board outline and clearances.",
                          "Info", wx.OK | wx.ICON_INFORMATION)

    def OnUndo(self, event):
        """Remove vias and group created by the last operation."""
        if not self._last_created_items:
            wx.MessageBox("Nothing to undo!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        board = pcbnew.GetBoard()
        count = len(self._last_created_items)

        # Remove group first (releases items), then remove vias
        if self._last_created_group:
            board.Remove(self._last_created_group)
            self._last_created_group = None

        for item in self._last_created_items:
            board.Remove(item)

        self._last_created_items = []
        self.undo_btn.Enable(False)
        pcbnew.Refresh()

        self.status_label.SetLabel(f"Removed {count} vias")
        wx.MessageBox(f"Removed {count} vias and group.", "Undo Complete", wx.OK | wx.ICON_INFORMATION)


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
        _save_settings()

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
        _save_settings()

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
        self._last_created_items = []  # Store items for undo

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Pad-to-Pad Route")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Route tracks between corresponding pads on matched footprint pairs (e.g., connect LED VDD pads to capacitor pads).")
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

        led_cap_btn = wx.Button(self, label="LED/Cap")
        led_cap_btn.Bind(wx.EVT_BUTTON, self.OnLedCapPreset)
        preset_hbox.Add(led_cap_btn, flag=wx.RIGHT, border=5)

        vbox.Add(preset_hbox, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Matched pairs display
        self.matched_label = wx.StaticText(self, label="Matched pairs: 0")
        vbox.Add(self.matched_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Buttons
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        route_btn = wx.Button(self, label="Create Tracks")
        route_btn.Bind(wx.EVT_BUTTON, self.OnCreateTracks)
        btn_hbox.Add(route_btn, flag=wx.RIGHT, border=10)

        self.undo_btn = wx.Button(self, label="Undo Last")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        btn_hbox.Add(self.undo_btn)

        vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP, border=15)

        self.SetSizer(vbox)

        # Initial update of matched pairs
        self.OnPatternChange(None)

    def OnLedCapPreset(self, event):
        """Fill in LED/Capacitor preset values for VDD connection."""
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
        _save_settings()

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
        self._last_created_items = []  # Clear for undo
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
                count, via_count, items = self._create_via_transition_route(
                    board, start_pos, end_pos, width_iu, layer_id, via_layer_id,
                    net, via_size_iu, via_drill_iu, stub_length_iu, use_45deg
                )
                tracks_created += count
                vias_created += via_count
                self._last_created_items.extend(items)
            elif use_45deg:
                # Create 45°/90° route with two segments
                count, items = self._create_45deg_route(board, start_pos, end_pos, width_iu, layer_id, net)
                tracks_created += count
                self._last_created_items.extend(items)
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
                self._last_created_items.append(track)

        pcbnew.Refresh()

        # Enable undo button if items were created
        self.undo_btn.Enable(len(self._last_created_items) > 0)

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

    def OnUndo(self, event):
        """Remove items created by the last operation."""
        if not self._last_created_items:
            wx.MessageBox("Nothing to undo!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        board = pcbnew.GetBoard()
        count = len(self._last_created_items)

        for item in self._last_created_items:
            board.Remove(item)

        self._last_created_items = []
        self.undo_btn.Enable(False)
        pcbnew.Refresh()

        wx.MessageBox(f"Removed {count} items.", "Undo Complete", wx.OK | wx.ICON_INFORMATION)

    def _create_45deg_route(self, board, start_pos, end_pos, width, layer_id, net):
        """Create a route using 45° and 90° segments only.

        Returns (segments_created, items_list).
        """
        items = []
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
            items.append(track)
            return (1, items)

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
        items.append(track1)

        # Create second segment (45° diagonal)
        track2 = pcbnew.PCB_TRACK(board)
        track2.SetStart(mid_pos)
        track2.SetEnd(end_pos)
        track2.SetWidth(width)
        track2.SetLayer(layer_id)
        track2.SetNet(net)
        board.Add(track2)
        items.append(track2)

        return (2, items)

    def _create_via_transition_route(self, board, start_pos, end_pos, width, layer_id, via_layer_id,
                                      net, via_size, via_drill, stub_length, use_45deg):
        """Create a route with via transitions: stub → via → other layer → via → stub.

        Returns (track_count, via_count, items_list).
        """
        items = []
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        total_dist = (dx * dx + dy * dy) ** 0.5

        # If distance is too short for via transition, just do direct route
        if total_dist < stub_length * 3:
            if use_45deg:
                count, sub_items = self._create_45deg_route(board, start_pos, end_pos, width, layer_id, net)
                return (count, 0, sub_items)
            else:
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(start_pos)
                track.SetEnd(end_pos)
                track.SetWidth(width)
                track.SetLayer(layer_id)
                track.SetNet(net)
                board.Add(track)
                return (1, 0, [track])

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

        # Create first stub on start layer: diagonal from pad, then straight to via (arrive at 90°)
        stub1_dx = via1_pos.x - start_pos.x
        stub1_dy = via1_pos.y - start_pos.y
        if use_45deg and stub1_dx != 0 and stub1_dy != 0 and abs(stub1_dx) != abs(stub1_dy):
            # 2-segment routing: diagonal first, then straight to via
            diag_len = min(abs(stub1_dx), abs(stub1_dy))
            # Mid point is after diagonal (covers diag_len in both x and y)
            stub1_mid_x = start_pos.x + (diag_len if stub1_dx > 0 else -diag_len)
            stub1_mid_y = start_pos.y + (diag_len if stub1_dy > 0 else -diag_len)
            stub1_mid_pos = pcbnew.VECTOR2I(int(stub1_mid_x), int(stub1_mid_y))

            # First segment: diagonal from pad
            track1a = pcbnew.PCB_TRACK(board)
            track1a.SetStart(start_pos)
            track1a.SetEnd(stub1_mid_pos)
            track1a.SetWidth(width)
            track1a.SetLayer(layer_id)
            track1a.SetNet(net)
            board.Add(track1a)
            items.append(track1a)
            tracks_created += 1

            # Second segment: straight to via (90°)
            track1b = pcbnew.PCB_TRACK(board)
            track1b.SetStart(stub1_mid_pos)
            track1b.SetEnd(via1_pos)
            track1b.SetWidth(width)
            track1b.SetLayer(layer_id)
            track1b.SetNet(net)
            board.Add(track1b)
            items.append(track1b)
            tracks_created += 1
        else:
            # Direct or already aligned stub
            track1 = pcbnew.PCB_TRACK(board)
            track1.SetStart(start_pos)
            track1.SetEnd(via1_pos)
            track1.SetWidth(width)
            track1.SetLayer(layer_id)
            track1.SetNet(net)
            board.Add(track1)
            items.append(track1)
            tracks_created += 1

        # Create first via
        via1 = pcbnew.PCB_VIA(board)
        via1.SetPosition(via1_pos)
        via1.SetWidth(via_size)
        via1.SetDrill(via_drill)
        via1.SetViaType(pcbnew.VIATYPE_THROUGH)
        via1.SetNet(net)
        board.Add(via1)
        items.append(via1)

        # Create middle track on via layer (with optional 45° routing)
        # For 45° mode: straight from via1, diagonal in middle, straight to via2
        if use_45deg:
            mid_dx = via2_pos.x - via1_pos.x
            mid_dy = via2_pos.y - via1_pos.y

            if mid_dx != 0 and mid_dy != 0 and abs(mid_dx) != abs(mid_dy):
                # Need 3-segment routing: straight -> diagonal -> straight
                diag_len = min(abs(mid_dx), abs(mid_dy))
                straight_len = abs(abs(mid_dx) - abs(mid_dy)) / 2  # Split straight portion

                # Calculate mid points for 3-segment path
                if abs(mid_dx) > abs(mid_dy):
                    # More horizontal: straight-x, diagonal, straight-x
                    mid1_x = via1_pos.x + (straight_len if mid_dx > 0 else -straight_len)
                    mid1_y = via1_pos.y
                    mid2_x = mid1_x + (diag_len if mid_dx > 0 else -diag_len)
                    mid2_y = mid1_y + (diag_len if mid_dy > 0 else -diag_len)
                else:
                    # More vertical: straight-y, diagonal, straight-y
                    mid1_x = via1_pos.x
                    mid1_y = via1_pos.y + (straight_len if mid_dy > 0 else -straight_len)
                    mid2_x = mid1_x + (diag_len if mid_dx > 0 else -diag_len)
                    mid2_y = mid1_y + (diag_len if mid_dy > 0 else -diag_len)

                mid1_pos = pcbnew.VECTOR2I(int(mid1_x), int(mid1_y))
                mid2_pos = pcbnew.VECTOR2I(int(mid2_x), int(mid2_y))

                # First segment: straight from via1 (90°)
                track2a = pcbnew.PCB_TRACK(board)
                track2a.SetStart(via1_pos)
                track2a.SetEnd(mid1_pos)
                track2a.SetWidth(width)
                track2a.SetLayer(via_layer_id)
                track2a.SetNet(net)
                board.Add(track2a)
                items.append(track2a)
                tracks_created += 1

                # Second segment: diagonal in middle (45°)
                track2b = pcbnew.PCB_TRACK(board)
                track2b.SetStart(mid1_pos)
                track2b.SetEnd(mid2_pos)
                track2b.SetWidth(width)
                track2b.SetLayer(via_layer_id)
                track2b.SetNet(net)
                board.Add(track2b)
                items.append(track2b)
                tracks_created += 1

                # Third segment: straight to via2 (90°)
                track2c = pcbnew.PCB_TRACK(board)
                track2c.SetStart(mid2_pos)
                track2c.SetEnd(via2_pos)
                track2c.SetWidth(width)
                track2c.SetLayer(via_layer_id)
                track2c.SetNet(net)
                board.Add(track2c)
                items.append(track2c)
                tracks_created += 1
            else:
                # Already aligned (0°, 45°, or 90°), single track
                track2 = pcbnew.PCB_TRACK(board)
                track2.SetStart(via1_pos)
                track2.SetEnd(via2_pos)
                track2.SetWidth(width)
                track2.SetLayer(via_layer_id)
                track2.SetNet(net)
                board.Add(track2)
                items.append(track2)
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
            items.append(track2)
            tracks_created += 1

        # Create second via
        via2 = pcbnew.PCB_VIA(board)
        via2.SetPosition(via2_pos)
        via2.SetWidth(via_size)
        via2.SetDrill(via_drill)
        via2.SetViaType(pcbnew.VIATYPE_THROUGH)
        via2.SetNet(net)
        board.Add(via2)
        items.append(via2)

        # Create last stub: straight from via (90°), then diagonal to pad
        stub2_dx = end_pos.x - via2_pos.x
        stub2_dy = end_pos.y - via2_pos.y
        if use_45deg and stub2_dx != 0 and stub2_dy != 0 and abs(stub2_dx) != abs(stub2_dy):
            # 2-segment routing: straight from via, then diagonal to pad
            diag_len = min(abs(stub2_dx), abs(stub2_dy))
            straight_len = abs(abs(stub2_dx) - abs(stub2_dy))
            # Mid point is after straight section (straight from via)
            if abs(stub2_dx) > abs(stub2_dy):
                stub2_mid_x = via2_pos.x + (straight_len if stub2_dx > 0 else -straight_len)
                stub2_mid_y = via2_pos.y
            else:
                stub2_mid_x = via2_pos.x
                stub2_mid_y = via2_pos.y + (straight_len if stub2_dy > 0 else -straight_len)
            stub2_mid_pos = pcbnew.VECTOR2I(int(stub2_mid_x), int(stub2_mid_y))

            # First segment: straight from via (90°)
            track3a = pcbnew.PCB_TRACK(board)
            track3a.SetStart(via2_pos)
            track3a.SetEnd(stub2_mid_pos)
            track3a.SetWidth(width)
            track3a.SetLayer(layer_id)
            track3a.SetNet(net)
            board.Add(track3a)
            items.append(track3a)
            tracks_created += 1

            # Second segment: diagonal to pad
            track3b = pcbnew.PCB_TRACK(board)
            track3b.SetStart(stub2_mid_pos)
            track3b.SetEnd(end_pos)
            track3b.SetWidth(width)
            track3b.SetLayer(layer_id)
            track3b.SetNet(net)
            board.Add(track3b)
            items.append(track3b)
            tracks_created += 1
        else:
            # Direct or already aligned stub
            track3 = pcbnew.PCB_TRACK(board)
            track3.SetStart(via2_pos)
            track3.SetEnd(end_pos)
            track3.SetWidth(width)
            track3.SetLayer(layer_id)
            track3.SetNet(net)
            board.Add(track3)
            items.append(track3)
            tracks_created += 1

        return (tracks_created, 2, items)


class ConnectFootprintPadsPanel(wx.Panel):
    """Route matching-numbered pads together within the same footprint."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._last_created_items = []

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Connect Pads in Footprint")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALL, border=10)

        # Description
        desc = wx.StaticText(self, label="Route matching-numbered pads together within the same footprint (e.g., connect SMD pad 1 to PTH pad 1).")
        desc.Wrap(400)
        vbox.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Selection mode
        mode_box = wx.StaticBox(self, label="Selection Mode")
        mode_sizer = wx.StaticBoxSizer(mode_box, wx.VERTICAL)

        self.mode_all = wx.RadioButton(self, label="All matching footprints", style=wx.RB_GROUP)
        self.mode_selected = wx.RadioButton(self, label="Only selected footprints")
        self.mode_all.SetValue(not _SETTINGS['cfp_mode_selected'])
        self.mode_selected.SetValue(_SETTINGS['cfp_mode_selected'])

        self.mode_all.Bind(wx.EVT_RADIOBUTTON, self._update_matched_count)
        self.mode_selected.Bind(wx.EVT_RADIOBUTTON, self._update_matched_count)

        mode_sizer.Add(self.mode_all, flag=wx.ALL, border=5)
        mode_sizer.Add(self.mode_selected, flag=wx.ALL, border=5)

        vbox.Add(mode_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(self, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(self, value=_SETTINGS['cfp_ref_prefix'])
        self.ref_prefix_ctrl.Bind(wx.EVT_TEXT, self._update_matched_count)
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_text1 = wx.StaticText(self, label="(e.g., 'HE' for hall effect switches, blank for all)")
        help_text1.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text1, flag=wx.LEFT | wx.TOP, border=10)

        # Max distance
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(self, label="Max Distance (mm):")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.max_distance_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['cfp_max_distance']),
                                                    min=0.1, max=50.0,
                                                    initial=_SETTINGS['cfp_max_distance'],
                                                    inc=0.5, size=(80, -1))
        self.max_distance_ctrl.SetDigits(2)
        hbox2.Add(self.max_distance_ctrl)
        vbox.Add(hbox2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        help_dist = wx.StaticText(self, label="(Skip pad pairs farther apart than this)")
        help_dist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_dist, flag=wx.LEFT | wx.TOP, border=10)

        # Track width
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(self, label="Track Width (mm):")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.track_width_ctrl = wx.SpinCtrlDouble(self, value=str(_SETTINGS['cfp_track_width']),
                                                    min=0.1, max=10.0,
                                                    initial=_SETTINGS['cfp_track_width'],
                                                    inc=0.05, size=(80, -1))
        self.track_width_ctrl.SetDigits(2)
        hbox3.Add(self.track_width_ctrl)
        vbox.Add(hbox3, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Auto-detect layer checkbox
        self.auto_layer_check = wx.CheckBox(self, label="Auto-detect layer from pad layers")
        self.auto_layer_check.SetValue(_SETTINGS['cfp_layer_auto'])
        self.auto_layer_check.Bind(wx.EVT_CHECKBOX, self._on_auto_layer_change)
        vbox.Add(self.auto_layer_check, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Layer selection
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.layer_label = wx.StaticText(self, label="Layer:")
        hbox4.Add(self.layer_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)

        board = pcbnew.GetBoard()
        layers = []
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            layer_name = board.GetLayerName(i)
            if layer_name and not layer_name.startswith("User."):
                layers.append(layer_name)

        self.layer_choice = wx.Choice(self, choices=layers, size=(100, -1))
        if _SETTINGS['cfp_layer'] in layers:
            self.layer_choice.SetStringSelection(_SETTINGS['cfp_layer'])
        elif "F.Cu" in layers:
            self.layer_choice.SetStringSelection("F.Cu")
        elif layers:
            self.layer_choice.SetSelection(0)

        hbox4.Add(self.layer_choice)
        vbox.Add(hbox4, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Disable layer choice when auto is checked
        self.layer_choice.Enable(not _SETTINGS['cfp_layer_auto'])
        self.layer_label.Enable(not _SETTINGS['cfp_layer_auto'])

        help_layer = wx.StaticText(self, label="(Used when auto-detect is off, or as preferred layer for auto)")
        help_layer.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_layer, flag=wx.LEFT | wx.TOP, border=10)

        # Matched footprints display
        self.matched_label = wx.StaticText(self, label="Matched footprints: 0")
        vbox.Add(self.matched_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Buttons
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        connect_btn = wx.Button(self, label="Connect Pads")
        connect_btn.Bind(wx.EVT_BUTTON, self.OnConnectPads)
        btn_hbox.Add(connect_btn, flag=wx.RIGHT, border=10)

        self.undo_btn = wx.Button(self, label="Undo Last")
        self.undo_btn.Bind(wx.EVT_BUTTON, self.OnUndo)
        self.undo_btn.Enable(False)
        btn_hbox.Add(self.undo_btn)

        vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP, border=15)

        self.SetSizer(vbox)

        # Initial count update
        self._update_matched_count(None)

    def _on_auto_layer_change(self, event):
        """Enable/disable layer choice based on auto-detect checkbox."""
        auto = self.auto_layer_check.GetValue()
        self.layer_choice.Enable(not auto)
        self.layer_label.Enable(not auto)

    def _update_matched_count(self, event):
        """Update the matched footprints label."""
        board = pcbnew.GetBoard()
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        selected_only = self.mode_selected.GetValue()

        count = 0
        pad_groups_total = 0
        for fp in board.GetFootprints():
            if selected_only and not fp.IsSelected():
                continue
            ref = fp.GetReference()
            if not ref_prefix or ref.startswith(ref_prefix):
                # Check if this footprint has any duplicate pad numbers
                pad_nums = {}
                for pad in fp.Pads():
                    num = pad.GetNumber()
                    if num:
                        pad_nums[num] = pad_nums.get(num, 0) + 1
                duplicates = sum(1 for c in pad_nums.values() if c >= 2)
                if duplicates > 0:
                    count += 1
                    pad_groups_total += duplicates

        self.matched_label.SetLabel(
            f"Matched footprints: {count} ({pad_groups_total} pad groups to connect)")

        if event:
            event.Skip()

    def _find_common_copper_layer(self, board, pad_a, pad_b, preferred_layer_name):
        """Find a copper layer accessible to both pads.

        Returns the layer ID, preferring preferred_layer_name.
        Returns None if no common copper layer exists.
        """
        layer_set_a = pad_a.GetLayerSet()
        layer_set_b = pad_b.GetLayerSet()

        # Check preferred layer first
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            if board.GetLayerName(i) == preferred_layer_name:
                if layer_set_a.Contains(i) and layer_set_b.Contains(i):
                    return i
                break

        # Fall back to any common copper layer
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            name = board.GetLayerName(i)
            if name and '.Cu' in name:
                if layer_set_a.Contains(i) and layer_set_b.Contains(i):
                    return i

        return None

    def OnConnectPads(self, event):
        """Create tracks between same-numbered pads within footprints."""
        board = pcbnew.GetBoard()

        # Read control values
        ref_prefix = self.ref_prefix_ctrl.GetValue().strip()
        selected_only = self.mode_selected.GetValue()
        max_distance = self.max_distance_ctrl.GetValue()
        track_width = self.track_width_ctrl.GetValue()
        auto_layer = self.auto_layer_check.GetValue()
        layer_name = self.layer_choice.GetStringSelection()

        # Save settings
        _SETTINGS['cfp_ref_prefix'] = ref_prefix
        _SETTINGS['cfp_mode_selected'] = selected_only
        _SETTINGS['cfp_max_distance'] = max_distance
        _SETTINGS['cfp_track_width'] = track_width
        _SETTINGS['cfp_layer_auto'] = auto_layer
        _SETTINGS['cfp_layer'] = layer_name
        _save_settings()

        # Resolve manual layer_id
        manual_layer_id = None
        if not auto_layer:
            for i in range(pcbnew.PCB_LAYER_ID_COUNT):
                if board.GetLayerName(i) == layer_name:
                    manual_layer_id = i
                    break
            if manual_layer_id is None:
                wx.MessageBox(f"Layer '{layer_name}' not found!", "Error",
                              wx.OK | wx.ICON_ERROR)
                return

        # Collect matching footprints
        footprints = []
        for fp in board.GetFootprints():
            if selected_only and not fp.IsSelected():
                continue
            ref = fp.GetReference()
            if not ref_prefix or ref.startswith(ref_prefix):
                footprints.append(fp)

        if not footprints:
            wx.MessageBox("No matching footprints found!", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        # Process each footprint
        self._last_created_items = []
        tracks_created = 0
        skipped_distance = 0
        skipped_layer = 0
        width_iu = pcbnew.FromMM(track_width)
        max_dist_iu = pcbnew.FromMM(max_distance)

        for fp in footprints:
            # Group pads by pad number
            pad_groups = {}
            for pad in fp.Pads():
                num = pad.GetNumber()
                if not num:
                    continue
                if num not in pad_groups:
                    pad_groups[num] = []
                pad_groups[num].append(pad)

            # For each group with 2+ pads, connect nearest pairs
            for pad_num, pads in pad_groups.items():
                if len(pads) < 2:
                    continue

                # Greedy nearest-neighbor pairing
                remaining = list(pads)
                while len(remaining) >= 2:
                    best_dist = float('inf')
                    best_i = 0
                    best_j = 1
                    for i in range(len(remaining)):
                        for j in range(i + 1, len(remaining)):
                            pi = remaining[i].GetPosition()
                            pj = remaining[j].GetPosition()
                            dx = pj.x - pi.x
                            dy = pj.y - pi.y
                            dist = (dx * dx + dy * dy) ** 0.5
                            if dist < best_dist:
                                best_dist = dist
                                best_i = i
                                best_j = j

                    # Check max distance
                    if best_dist > max_dist_iu:
                        skipped_distance += 1
                        break

                    pad_a = remaining[best_i]
                    pad_b = remaining[best_j]

                    # Determine layer
                    if auto_layer:
                        layer_id = self._find_common_copper_layer(
                            board, pad_a, pad_b, layer_name)
                        if layer_id is None:
                            skipped_layer += 1
                            remaining.pop(best_j)
                            remaining.pop(best_i)
                            continue
                    else:
                        layer_id = manual_layer_id

                    # Get net from first pad
                    net = pad_a.GetNet()

                    # Create direct track
                    start_pos = pad_a.GetPosition()
                    end_pos = pad_b.GetPosition()

                    track = pcbnew.PCB_TRACK(board)
                    track.SetStart(start_pos)
                    track.SetEnd(end_pos)
                    track.SetWidth(width_iu)
                    track.SetLayer(layer_id)
                    track.SetNet(net)
                    board.Add(track)
                    tracks_created += 1
                    self._last_created_items.append(track)

                    # Remove paired pads
                    remaining.pop(best_j)
                    remaining.pop(best_i)

        pcbnew.Refresh()
        self.undo_btn.Enable(len(self._last_created_items) > 0)

        # Report results
        msg = f"Created {tracks_created} tracks"
        if skipped_distance > 0:
            msg += f"\nSkipped {skipped_distance} pad groups exceeding {max_distance}mm"
        if skipped_layer > 0:
            msg += f"\nSkipped {skipped_layer} pad pairs with no common copper layer"
        if tracks_created > 0:
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        elif skipped_distance > 0 or skipped_layer > 0:
            wx.MessageBox(msg, "No Tracks Created", wx.OK | wx.ICON_WARNING)
        else:
            wx.MessageBox("No footprints with duplicate pad numbers found!", "Info",
                          wx.OK | wx.ICON_INFORMATION)

    def OnUndo(self, event):
        """Remove items created by the last operation."""
        if not self._last_created_items:
            wx.MessageBox("Nothing to undo!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        board = pcbnew.GetBoard()
        count = len(self._last_created_items)

        for item in self._last_created_items:
            board.Remove(item)

        self._last_created_items = []
        self.undo_btn.Enable(False)
        pcbnew.Refresh()

        wx.MessageBox(f"Removed {count} tracks.", "Undo Complete",
                      wx.OK | wx.ICON_INFORMATION)


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
        _save_settings()

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
        _save_settings()

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


