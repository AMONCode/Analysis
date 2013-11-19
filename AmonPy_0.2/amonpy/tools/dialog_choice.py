import wx
"""@package dialog_choice
Creates pop-up window with dialog choices.
"""
class SelectChoice(wx.App):
    def __init__(self, choices,**kwargs):
        super(SelectChoice, self).__init__()
        self.choices = choices
        if 'info' in kwargs.keys():
            self.info = kwargs['info']
        else:
            self.info = 'Select from one of the following:'
            
    def on_click_or_close(self, event):
        self._result = self.choice.GetStringSelection()
        self.frame.Destroy()

    @property
    def result(self):
        self.frame = wx.Frame(parent=None, size=(350,150))
        self.frame.Bind(wx.EVT_CLOSE, self.on_click_or_close)
        self.text = wx.StaticText(self.frame,label=self.info,pos=(50,20))
        self.choice = wx.Choice(parent=self.frame,pos=(50,50),
                                choices=self.choices)
        self.button = wx.Button(parent=self.frame,pos=(50,80),label='Select')
        self.button.Bind(wx.EVT_BUTTON, self.on_click_or_close)
        self.frame.Show()
        self.MainLoop()
        return self._result

if __name__ == "__main__":
    choices = ['Do not write to DB', 'Rewrite DB', 'Append to DB', 'Cancel']
    result = SelectChoice(choices).result
    print(result)

