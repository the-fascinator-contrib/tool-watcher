
import clr
import sys
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("IronPython")
#form System.Windows.Forms import *
from System.Windows.Forms import Application
from System.Windows.Forms import BorderStyle, Button, ButtonState
from System.Windows.Forms import CheckBox, CheckState, CheckedListBox, ComboBox
from System.Windows.Forms import CommonDialog, ContextMenu, Control, Cursors
from System.Windows.Forms import DialogResult, DockStyle, DragAction
from System.Windows.Forms import Form, FileDialog, FolderBrowserDialog, FontDialog
from System.Windows.Forms import FormBorderStyle, FlowLayoutPanel, FlowDirection
from System.Windows.Forms import GroupBox, HScrollBar, ImageList, ImageLayout, Keys
from System.Windows.Forms import Label, Layout, LinkLabel, ListBox, ListView, ListControl
from System.Windows.Forms import ListViewItem, MainMenu, MaskedTextBox, Menu, MenuItem
from System.Windows.Forms import MouseButtons, MessageBox, MessageBoxIcon, NotifyIcon
from System.Windows.Forms import OpenFileDialog, Orientation, Padding, Panel, PictureBox
from System.Windows.Forms import PrintDialog, PrintPreviewDialog, ProgressBar
from System.Windows.Forms import RadioButton, RichTextBox, RichTextBoxScrollBars
from System.Windows.Forms import SaveFileDialog, Screen, ScrollBar, ScrollBars, ScrollButton
from System.Windows.Forms import SendKeys, Splitter, StatusBar, StatusBarPanel, StatusBarPanelStyle
from System.Windows.Forms import StatusStrip, SystemInformation
from System.Windows.Forms import TabControl, TabPage, TextBox, TableLayoutPanel, Timer
from System.Windows.Forms import ToolBar, ToolBarButton, ToolStrip, ToolStripDropDown
from System.Windows.Forms import ToolStripItem, ToolStripMenuItem, ToolStripLabel
from System.Windows.Forms import ToolTip, ToolTipIcon, TreeView
from System.Windows.Forms import VScrollBar, View, VisualStyles
from System.Windows.Forms import WebBrowser
from System.Drawing import Brushes, Color, Font, FontFamily, FontStyle, Icon
from System.Drawing import Image, Pens, Point, Rectangle, Size, Text
from System.Drawing import SystemBrushes, SystemColors, SystemFonts, SystemIcons, SystemPens

from System.Threading import Thread, ThreadStart, AutoResetEvent
import IronPython

from watchDirectory import WatchDirectory


class ConfigForm(Form):
    def __init__(self, watcher=None):
        #
        self.__watcher = watcher
        self.Text = "FileWatcher configuration"
        self.__table = TableLayoutPanel()
        self.MinimumSize = Size(520, 360)
        self.Size = Size(640, 360)
        self.MaximizeBox = False
        self.Icon = Icon("watcher.ico")
        p = Panel()
        p.Padding = Padding(10, 0, 10, 10)
        exitBut = Button(Text="E&xit")
        p.Height = exitBut.Height + 10
        p.Controls.Add(exitBut)
        exitBut.Dock = DockStyle.Right
        p.Dock = DockStyle.Bottom
        def exit(s, e):
            self.Dispose()
        exitBut.Click += exit
        self.Controls.Add(p)
        self.Controls.Add(self.__table)
        label = Label(Text="Watch Directories")
        self.__table.Controls.Add(label)
        self.__list = ListBox()
        self.__list.Width = 500
        self.__table.Dock = DockStyle.Fill
        try:
            for wd in watcher.controller.watchDirectories.itervalues():
                self.__list.Items.Add(wd)
        except Exception, e:
            self.__list.Items.Add(str(e))
        self.__table.Controls.Add(self.__list)

        def fClick(s, e):
            self.__list.SelectedIndex = -1
        self.__table.Click += fClick

        addBut = Button(Text="&Add")
        addBut.Click += self.__addButClick
        self.__table.Controls.Add(addBut)

        #self.__list.

        self.Show()

    def __addButClick(self, s, e):
        f = FolderBrowserDialog()
        r = f.ShowDialog()
        if str(r)=="OK":
            path = f.SelectedPath
            wd = WatchDirectory(path)
            self.__list.Items.Add(wd)

    def __listItemSelected(self, s, e):
        pass





def testRun():
    autoResetEvent = AutoResetEvent(False)
    data = {}
    if hasattr(clr, "SetCommandDispatcher"):    # for IP 2.x
        def setCommandDispatcher(cmd):
            clr.SetCommandDispatcher(cmd)
    else:                                       # for IP 1.x
        def setCommandDispatcher(cmd):
            IronPython.Hosting.PythonEngine.ConsoleCommandDispatcher = cmd

    def threadProc():
        try:
            dispatcher = Form(Size=Size(0,0))
            dispatcher.Show()       # create a dummy control (for invoking commands from)
            dispatcher.Hide()       #   and show & hide to initialise it.
            data["dispatcher"] = dispatcher
            autoResetEvent.Set()    # indicate that we are ready
            Application.Run()       # start the message loop
        finally:
            setCommandDispatcher(None)

    def dispatchConsoleCommand(consoleCommand):
        dispatcher = data.get("dispatcher")
        if consoleCommand:
            dispatcher.Invoke(consoleCommand)
        else:
            Application.Exit()

    t = Thread(ThreadStart(threadProc))
    t.IsBackground = True
    t.Start()
    autoResetEvent.WaitOne()    # Wait until the alt input execution
    setCommandDispatcher(dispatchConsoleCommand)
appRun = testRun

def exit():
    sys.exit()

