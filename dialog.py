import wx


class RotateDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Rotate Items Individually", size=(350, 200))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Angle input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label="Rotation Angle (degrees):")
        hbox1.Add(label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        
        self.angle_ctrl = wx.SpinCtrlDouble(panel, value="90", min=-360, max=360, initial=90, inc=15)
        self.angle_ctrl.SetDigits(2)
        hbox1.Add(self.angle_ctrl, proportion=1)
        
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        # Quick angle buttons
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_90 = wx.Button(panel, label="90°")
        btn_90.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(90))
        hbox2.Add(btn_90, flag=wx.RIGHT, border=5)
        
        btn_180 = wx.Button(panel, label="180°")
        btn_180.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(180))
        hbox2.Add(btn_180, flag=wx.RIGHT, border=5)
        
        btn_270 = wx.Button(panel, label="270°")
        btn_270.Bind(wx.EVT_BUTTON, lambda e: self.angle_ctrl.SetValue(270))
        hbox2.Add(btn_270)
        
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        # OK/Cancel buttons
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Rotate")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        hbox3.Add(ok_btn, flag=wx.RIGHT, border=5)
        hbox3.Add(cancel_btn)
        
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
    def GetAngle(self):
        return self.angle_ctrl.GetValue()
