import wx
"""@package imput_text_window
Creates pop-up window with text editor to input values.
"""
class SelectChoice(wx.App):
    def __init__(self,**kwargs):
        super(SelectChoice, self).__init__()
        
        if 'info' in list(kwargs.keys()):
            self.info = kwargs['info']
        else:
            self.info = 'Insert time window in seconds:'
            
    def on_click_or_close(self, event):
        self._result = self.textCtrl1.GetValue()
        self.frame.Destroy()

    @property
    def result(self):
        self.frame = wx.Frame(parent=None, size=(350,150))
        self.frame.Bind(wx.EVT_CLOSE, self.on_click_or_close)
        self.text = wx.StaticText(self.frame,label=self.info,pos=(50,20))
        self.textCtrl1 = wx.TextCtrl(name='textCtrl1', parent=self.frame, 
                                    pos=wx.Point(200, 56), size=wx.Size(100, 50),
                                    style=wx.TE_MULTILINE, value='100')
        self.button = wx.Button(parent=self.frame,pos=(50,80),label='OK')
        self.button.Bind(wx.EVT_BUTTON, self.on_click_or_close)
        self.frame.Show()
        self.MainLoop()
        return self._result

if __name__ == "__main__":
    result = SelectChoice().result
    print(result)
