import wx
import pcbnew


class ChainRouteDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Chain Route LEDs", size=(400, 350))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Reference prefix
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label1 = wx.StaticText(panel, label="Reference Prefix:")
        hbox1.Add(label1, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.ref_prefix_ctrl = wx.TextCtrl(panel, value="D")
        hbox1.Add(self.ref_prefix_ctrl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Add help text
        help_text1 = wx.StaticText(panel, label="(e.g., 'D' for D1, D2, D3...)")
        help_text1.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text1, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Output pad number
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        label2 = wx.StaticText(panel, label="Output Pad Number:")
        hbox2.Add(label2, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.output_pad_ctrl = wx.TextCtrl(panel, value="1")
        hbox2.Add(self.output_pad_ctrl, proportion=1)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Add help text
        help_text2 = wx.StaticText(panel, label="(Pad to connect FROM, e.g., DO/DOUT)")
        help_text2.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text2, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Input pad number
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label3 = wx.StaticText(panel, label="Input Pad Number:")
        hbox3.Add(label3, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.input_pad_ctrl = wx.TextCtrl(panel, value="3")
        hbox3.Add(self.input_pad_ctrl, proportion=1)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Add help text
        help_text3 = wx.StaticText(panel, label="(Pad to connect TO on next LED, e.g., DI/DIN)")
        help_text3.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        vbox.Add(help_text3, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Track width
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        label4 = wx.StaticText(panel, label="Track Width (mm):")
        hbox4.Add(label4, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.track_width_ctrl = wx.SpinCtrlDouble(panel, value="0.25", min=0.1, max=10, initial=0.25, inc=0.05)
        self.track_width_ctrl.SetDigits(2)
        hbox4.Add(self.track_width_ctrl, proportion=1)
        vbox.Add(hbox4, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Layer selection
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        label5 = wx.StaticText(panel, label="Layer:")
        hbox5.Add(label5, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        
        # Get layer names
        board = pcbnew.GetBoard()
        layers = []
        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            layer_name = board.GetLayerName(i)
            if layer_name and not layer_name.startswith("User."):
                layers.append(layer_name)
        
        self.layer_choice = wx.Choice(panel, choices=layers)
        # Default to F.Cu if available
        if "F.Cu" in layers:
            self.layer_choice.SetStringSelection("F.Cu")
        elif layers:
            self.layer_choice.SetSelection(0)
        
        hbox5.Add(self.layer_choice, proportion=1)
        vbox.Add(hbox5, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # OK/Cancel buttons
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Create Tracks")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        hbox6.Add(ok_btn, flag=wx.RIGHT, border=5)
        hbox6.Add(cancel_btn)
        
        vbox.Add(hbox6, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=15)
        
        panel.SetSizer(vbox)
        
    def GetRefPrefix(self):
        return self.ref_prefix_ctrl.GetValue().strip()
    
    def GetOutputPad(self):
        return self.output_pad_ctrl.GetValue().strip()
    
    def GetInputPad(self):
        return self.input_pad_ctrl.GetValue().strip()
    
    def GetTrackWidth(self):
        return self.track_width_ctrl.GetValue()
    
    def GetLayer(self):
        return self.layer_choice.GetStringSelection()
