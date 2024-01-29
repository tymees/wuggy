import wx

from ui.wx.main_window import MainWindow



class WuggyApp(wx.App):
    def __init__(self, *args, data_path=None, **kwargs):
        self.data_path = data_path
        super().__init__(*args, **kwargs)

    def OnInit(self):
        # Parse command line arguments

        self.SetAppDisplayName("Wuggy")
        # Initialize the application
        # wx.InitAllImageHandlers()
        mainwindow = MainWindow(None, -1, "", data_path=self.data_path)
        self.SetTopWindow(mainwindow)
        mainwindow.Show()
        return 1