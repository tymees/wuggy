# -*- coding: utf-8 -*-
import os.path
import threading
import re

import wx
import wx.lib.dialogs
import wx.adv

from .frame import Frame
from .results_window import ResultsWindow
from .grid import InputGrid
from wuggy.wuggy import Wuggy
import info

import wx.grid


class MainWindow(Frame):
    def __init__(self, *args, data_path=None, **kwds):
        # default options required for choice elements because we can't
        # get their value from the interface if they are not user-changed
        self.options = {
            "output_type": "Only pseudowords",
            "output_mode": "Plain",
            "overlapping_segments_comparison": "Maximum",
        }
        self.output_window = None
        self.wuggy = Wuggy(data_path=data_path)
        self.stop = False
        # begin wxGlade: MainWindow.__init__
        kwds["style"] = (
            wx.CAPTION
            | wx.CLOSE_BOX
            | wx.MINIMIZE_BOX
            | wx.MAXIMIZE_BOX
            | wx.SYSTEM_MENU
            | wx.RESIZE_BORDER
            | wx.CLIP_CHILDREN
        )
        super().__init__(*args, **kwds)
        self.splitterwindow = wx.SplitterWindow(self, -1, style=wx.SP_3D | wx.SP_BORDER)
        self.splitterwindow_rightpanel = wx.Panel(self.splitterwindow, -1)
        self.generalsettings_sizer_staticbox = wx.StaticBox(
            self.splitterwindow_rightpanel, -1, "General Settings"
        )
        self.filter_sizer_staticbox = wx.StaticBox(
            self.splitterwindow_rightpanel, -1, "Output Restrictions"
        )
        self.outputopts_sizer_staticbox = wx.StaticBox(
            self.splitterwindow_rightpanel, -1, "Output Options"
        )
        self.splitterwindow_leftpanel = wx.Panel(self.splitterwindow, -1)

        # Menu Bar
        self.menubar = wx.MenuBar()
        self.menu_file = wx.Menu()
        self.menu_open = wx.MenuItem(
            self.menu_file,
            wx.NewId(),
            "&Open Input Sequences\tCtrl+O",
            "",
            wx.ITEM_NORMAL,
        )
        self.menu_file.Append(self.menu_open)
        self.menu_save = wx.MenuItem(
            self.menu_file,
            wx.NewId(),
            "&Save Input Sequences\tCtrl+S",
            "",
            wx.ITEM_NORMAL,
        )
        self.menu_file.Append(self.menu_save)
        self.menu_save_output = wx.MenuItem(
            self.menu_file,
            wx.NewId(),
            "Save &Output Sequences\tCtrl+Shift+S",
            "",
            wx.ITEM_NORMAL,
        )
        self.menu_file.Append(self.menu_save_output)
        self.menu_quit = wx.MenuItem(
            self.menu_file, wx.ID_EXIT, "Quit\tCtrl+Q", "", wx.ITEM_NORMAL
        )
        self.menu_file.Append(self.menu_quit)
        self.menubar.Append(self.menu_file, "&File")
        self.menu_edit = wx.Menu()
        self.menu_cut = wx.MenuItem(
            self.menu_edit, wx.ID_CUT, "&Cut\tCtrl+X", "", wx.ITEM_NORMAL
        )
        self.menu_edit.Append(self.menu_cut)
        self.menu_copy = wx.MenuItem(
            self.menu_edit, wx.ID_COPY, "Cop&y\tCtrl+C", "", wx.ITEM_NORMAL
        )
        self.menu_edit.Append(self.menu_copy)
        self.menu_paste = wx.MenuItem(
            self.menu_edit, wx.ID_PASTE, "&Paste\tCtrl+V", "", wx.ITEM_NORMAL
        )
        self.menu_edit.Append(self.menu_paste)
        self.menubar.Append(self.menu_edit, "&Edit")
        self.menu_generate = wx.Menu()
        self.menu_run = wx.MenuItem(
            self.menu_generate, wx.NewId(), "&Run\tCtrl+R", "", wx.ITEM_NORMAL
        )
        self.menu_generate.Append(self.menu_run)
        self.menu_stop = wx.MenuItem(
            self.menu_generate, wx.NewId(), "&Stop\tCtrl+B", "", wx.ITEM_NORMAL
        )
        self.menu_generate.Append(self.menu_stop)
        self.menubar.Append(self.menu_generate, "&Generate")
        self.menu_tools = wx.Menu()
        self.menu_autosegment = wx.MenuItem(
            self.menu_tools,
            wx.NewId(),
            "Segmentation (Syllabify)\tCtrl+Y",
            "",
            wx.ITEM_NORMAL,
        )
        self.menu_tools.Append(self.menu_autosegment)
        self.menu_verify = wx.MenuItem(
            self.menu_tools,
            wx.NewId(),
            "Verify Input\tCtrl+Shift+V",
            "",
            wx.ITEM_NORMAL,
        )
        self.menu_tools.Append(self.menu_verify)
        self.menubar.Append(self.menu_tools, "&Tools")
        self.menu_help = wx.Menu()
        self.menu_help.Append(wx.ID_ABOUT, "About Wuggy", "", wx.ITEM_NORMAL)
        self.menubar.Append(self.menu_help, "&Help")
        self.SetMenuBar(self.menubar)
        # Menu Bar end
        self.statusbar = self.CreateStatusBar(1, wx.STB_SIZEGRIP)

        # Tool Bar
        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL)
        self.SetToolBar(self.toolbar)
        # Tool Bar end
        self.grid = InputGrid(self.splitterwindow_leftpanel)
        self.grid.SetNumberRows(100000)
        self.label_generator = wx.StaticText(
            self.splitterwindow_rightpanel, -1, "Language module:  "
        )
        self.choice_language = wx.Choice(
            self.splitterwindow_rightpanel, -1, choices=["Choose a language"]
        )
        self.label_output_type = wx.StaticText(
            self.splitterwindow_rightpanel, -1, "Output type: "
        )
        self.choice_output_type = wx.Choice(
            self.splitterwindow_rightpanel,
            -1,
            choices=["Only pseudowords", "Only words", "Both"],
        )
        self.label_ncandidates = wx.StaticText(
            self.splitterwindow_rightpanel, -1, "Maximal number of candidates: "
        )
        self.choice_ncandidates = wx.SpinCtrl(
            self.splitterwindow_rightpanel, -1, "10", min=0, max=10000
        )
        self.label_per_word = wx.StaticText(
            self.splitterwindow_rightpanel, -1, " per word"
        )
        self.label_search_time = wx.StaticText(
            self.splitterwindow_rightpanel,
            -1,
            "Maximal search time per word: ",
            style=wx.ST_NO_AUTORESIZE,
        )
        self.choice_search_time = wx.SpinCtrl(
            self.splitterwindow_rightpanel, -1, "10", min=0, max=3600
        )
        self.label_seconds = wx.StaticText(
            self.splitterwindow_rightpanel, -1, " seconds"
        )
        self.choice_match_segment_length = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Match length of subsyllabic segments"
        )
        self.choice_match_plain_length = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Match letter length"
        )
        self.choice_concentric_matching = wx.CheckBox(
            self.splitterwindow_rightpanel,
            -1,
            "Match transition frequencies (concentric search)",
        )
        self.choice_overlapping_segments = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Match segments: "
        )
        self.overlapping_segments_numerator = wx.SpinCtrl(
            self.splitterwindow_rightpanel, -1, "5"
        )
        self.fraction_label = wx.StaticText(
            self.splitterwindow_rightpanel, -1, " out of "
        )
        self.overlapping_segments_denominator = wx.SpinCtrl(
            self.splitterwindow_rightpanel, -1, "6"
        )
        self.choice_overlapping_segments_comparison = wx.Choice(
            self.splitterwindow_rightpanel,
            -1,
            choices=["Exactly", "Minimum", "Maximum"],
        )
        self.choice_output_mode = wx.Choice(
            self.splitterwindow_rightpanel,
            -1,
            choices=["Plain", "Syllables", "Segments"],
        )
        self.choice_output_lexicality = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Lexicality"
        )
        self.choice_output_old20 = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "OLD20"
        )
        self.choice_output_ned1 = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Neighbors at edit distance 1"
        )
        self.choice_output_overlap = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Number of overlapping segments"
        )
        self.choice_output_max_deviation = wx.CheckBox(
            self.splitterwindow_rightpanel, -1, "Deviation statistics"
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.OnMenuOpen, self.menu_open)
        self.Bind(wx.EVT_MENU, self.OnMenuSave, self.menu_save)
        self.Bind(wx.EVT_MENU, self.OnMenuSaveOutput, self.menu_save_output)
        # self.Bind(wx.EVT_MENU, self.OnMenuCut, self.menu_cut)
        # self.Bind(wx.EVT_MENU, self.OnMenuCopy, self.menu_copy)
        # self.Bind(wx.EVT_MENU, self.OnMenuPaste, self.menu_paste)
        self.Bind(wx.EVT_MENU, self.OnMenuRun, self.menu_run)
        self.Bind(wx.EVT_MENU, self.OnMenuStop, self.menu_stop)
        self.Bind(wx.EVT_MENU, self.OnMenuSegment, self.menu_autosegment)
        self.Bind(wx.EVT_MENU, self.OnMenuVerify, self.menu_verify)
        self.Bind(wx.EVT_MENU, self.OnMenuAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceModule, self.choice_language)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceOutputType, self.choice_output_type)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceOutputMode, self.choice_output_mode)
        self.Bind(
            wx.EVT_CHOICE,
            self.OnChoiceOverlappingSegmentsComparison,
            self.choice_overlapping_segments_comparison,
        )

        # end wxGlade
        self.Bind(wx.EVT_MENU, self.OnMenuQuit, id=wx.ID_EXIT)

        for module_name in sorted(self.wuggy._plugin_modules.keys()):
            self.choice_language.Append(module_name)

    def __set_properties(self):
        # begin wxGlade: MainWindow.__set_properties
        self.SetTitle("Input Sequences")
        self.SetSize((1280, 800))
        self.statusbar.SetStatusWidths([-1])
        # statusbar fields
        statusbar_fields = [""]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)
        self.toolbar.SetToolBitmapSize((30, 29))
        self.toolbar.SetMargins((5, 5))
        self.toolbar.SetToolSeparation(5)
        self.toolbar.Realize()
        self.grid.EnableDragGridSize(0)
        self.grid.SetColLabelValue(0, "Word")
        self.grid.SetColSize(0, 100)
        self.grid.SetColLabelValue(1, "Segments")
        self.grid.SetColSize(1, 120)
        self.grid.SetColLabelValue(2, "Matching Expression")
        self.grid.SetColSize(2, 150)
        self.grid.SetMinSize((400, 200))
        self.choice_language.SetSelection(0)
        self.choice_output_type.SetSelection(0)
        self.choice_match_segment_length.SetValue(1)
        self.choice_match_plain_length.SetValue(1)
        self.choice_concentric_matching.SetValue(1)
        self.choice_overlapping_segments.SetValue(1)
        self.choice_overlapping_segments_comparison.SetSelection(2)
        self.choice_output_overlap.SetValue(1)

        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MainWindow.__do_layout
        mainwindow_sizer = wx.BoxSizer(wx.VERTICAL)
        settingspanel_sizer = wx.BoxSizer(wx.VERTICAL)
        outputopts_sizer = wx.StaticBoxSizer(
            self.outputopts_sizer_staticbox, wx.VERTICAL
        )
        filter_sizer = wx.StaticBoxSizer(self.filter_sizer_staticbox, wx.VERTICAL)
        segmentmatch_sizer = wx.BoxSizer(wx.HORIZONTAL)
        generalsettings_sizer = wx.StaticBoxSizer(
            self.generalsettings_sizer_staticbox, wx.VERTICAL
        )
        searchtime_sizer = wx.GridSizer(1, 2, 0, 0)
        searchtime_subsizer = wx.BoxSizer(wx.HORIZONTAL)
        ncandidates_sizer = wx.GridSizer(1, 2, 0, 0)
        ncandidates_subsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1 = wx.GridSizer(1, 2, 0, 0)
        languagemodule_sizer = wx.GridSizer(1, 2, 0, 0)
        splitter_window_leftpanel_sizer = wx.BoxSizer(wx.VERTICAL)
        splitter_window_leftpanel_sizer.Add(self.grid, 1, wx.EXPAND, 0)
        self.splitterwindow_leftpanel.SetSizer(splitter_window_leftpanel_sizer)
        languagemodule_sizer.Add(
            self.label_generator, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0
        )
        languagemodule_sizer.Add(
            self.choice_language, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0
        )
        generalsettings_sizer.Add(languagemodule_sizer, 1, wx.EXPAND, 0)
        sizer_1.Add(self.label_output_type, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add(self.choice_output_type, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0)
        generalsettings_sizer.Add(sizer_1, 1, wx.EXPAND, 0)
        ncandidates_sizer.Add(
            self.label_ncandidates, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0
        )
        ncandidates_subsizer.Add(
            self.choice_ncandidates, 0, wx.ALIGN_CENTER_VERTICAL, 0
        )
        ncandidates_subsizer.Add(self.label_per_word, 0, wx.EXPAND, 0)
        ncandidates_sizer.Add(ncandidates_subsizer, 1, wx.EXPAND, 0)
        generalsettings_sizer.Add(ncandidates_sizer, 1, wx.EXPAND, 0)
        searchtime_sizer.Add(
            self.label_search_time, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0
        )
        searchtime_subsizer.Add(self.choice_search_time, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        searchtime_subsizer.Add(self.label_seconds, 0, wx.EXPAND, 0)
        searchtime_sizer.Add(searchtime_subsizer, 1, wx.EXPAND, 0)
        generalsettings_sizer.Add(searchtime_sizer, 1, wx.EXPAND, 0)
        settingspanel_sizer.Add(
            generalsettings_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20
        )
        filter_sizer.Add(self.choice_match_segment_length, 1, wx.EXPAND, 0)
        filter_sizer.Add(self.choice_match_plain_length, 1, wx.EXPAND, 0)
        filter_sizer.Add(self.choice_concentric_matching, 1, wx.EXPAND, 0)

        segmentmatch_sizer.Add(self.choice_overlapping_segments, 0, wx.EXPAND, 0)
        segmentmatch_sizer.Add(
            self.overlapping_segments_numerator,
            1,
            wx.EXPAND,
            0,
        )
        segmentmatch_sizer.Add(self.fraction_label, 1, wx.EXPAND, 0)
        segmentmatch_sizer.Add(
            self.overlapping_segments_denominator,
            1,
            wx.EXPAND,
            0,
        )
        segmentmatch_sizer.Add(
            self.choice_overlapping_segments_comparison,
            0,
            wx.EXPAND,
            0,
        )

        filter_sizer.Add(segmentmatch_sizer, 0, wx.EXPAND, 0)
        settingspanel_sizer.Add(filter_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
        outputopts_sizer.Add(self.choice_output_mode, 1, wx.EXPAND, 0)
        outputopts_sizer.Add(self.choice_output_lexicality, 1, wx.EXPAND, 0)
        outputopts_sizer.Add(self.choice_output_old20, 1, wx.EXPAND, 0)
        outputopts_sizer.Add(self.choice_output_ned1, 1, wx.EXPAND, 0)
        outputopts_sizer.Add(self.choice_output_overlap, 1, wx.EXPAND, 0)
        outputopts_sizer.Add(self.choice_output_max_deviation, 1, wx.EXPAND, 0)
        settingspanel_sizer.Add(outputopts_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
        self.splitterwindow_rightpanel.SetSizer(settingspanel_sizer)
        self.splitterwindow.SplitVertically(
            self.splitterwindow_leftpanel, self.splitterwindow_rightpanel, 480
        )
        mainwindow_sizer.Add(self.splitterwindow, 1, wx.EXPAND, 0)
        self.SetSizer(mainwindow_sizer)
        mainwindow_sizer.SetSizeHints(self)
        self.Layout()
        self.Centre()
        # end wxGlade

    def OnMenuOpen(self, event):  # wxGlade: MainWindow.<event_handler>
        self.grid.ImportData()

    def OnMenuSave(self, event):  # wxGlade: MainWindow.<event_handler>
        self.grid.SaveData()

    def OnMenuSaveOutput(self, event):  # wxGlade: MainWindow.<event_handler>
        self.output_window.grid.SaveData(headers=True)

    def OnChangeCell(self, event):  # wxGlade: MainWindow.<event_handler>
        print("Event handler `OnChangeCell' not implemented!")
        event.Skip()

    def OnSelectNewCell(self, event):  # wxGlade: MainWindow.<event_handler>
        print("Event handler `OnSelectNewCell' not implemented!")
        event.Skip()

    def OnChoiceOutputType(self, event):  # wxGlade: MainWindow.<event_handler>
        self.options["output_type"] = event.GetString()

    def OnChoiceOutputMode(self, event):  # wxGlade: MainWindow.<event_handler>
        self.options["output_mode"] = event.GetString()

    def OnChoiceOverlappingSegmentsComparison(
        self, event
    ):  # wxGlade: MainWindow.<event_handler>
        self.options["overlapping_segments_comparison"] = event.GetString()

    def OnMenuNew(self, event):  # wxGlade: MainWindow.<event_handler>
        print("Event handler `OnMenuNewInput' not implemented")
        event.Skip()

    def OnMenuClose(self, event):  # wxGlade: MainWindow.<event_handler>
        self.OnMenuSave()

    def OnChoiceModule(self, event):  # wxGlade: MainWindow.<event_handler>
        module_name = event.GetString()
        if module_name.startswith("Choose"):
            pass
        else:
            plugin_module = self.wuggy._plugin_modules[module_name]
            t = threading.Thread(
                target=self.wuggy.load, args=[plugin_module, 100, 1, False]
            )
            t.start()
            message = "Loading %s language module\n\n" % module_name
            dialog = wx.ProgressDialog("Progress", message + "\n", 100, self)
            while 1:
                t.join(0.1)
                if t.is_alive():
                    value = self.wuggy.status["progress"]
                    if isinstance(value, float):
                        value = round(value)
                    dialog.Update(
                        value,
                        message + self.wuggy.status["message"],
                    )
                    self.SetStatus(self.wuggy.status["message"], 0)
                else:
                    break
            self.ClearStatus()
            dialog.Destroy()

    # def OnMenuCut(self, event): # wxGlade: MainWindow.<event_handler>
    #     self.OnMenuCopy(event)
    #     self.grid.Clear()
    #
    # def OnMenuCopy(self, event): # wxGlade: MainWindow.<event_handler>
    #     print self.grid._selected
    #     self.grid.Copy()
    #
    # def OnMenuPaste(self, event): # wxGlade: MainWindow.<event_handler>
    #     self.grid.Paste()

    def OnMenuRun(self, event):  # wxGlade: MainWindow.<event_handler>
        if self.VerifyModuleLoaded() == False:
            return False
        warnings = self.grid.Segment(self.wuggy.generator, replace=False)
        if self.VerifyInput() == False:
            return False
        self.CollectOptions()
        colnames = ("lexicality", "old20", "ned1", "overlap_ratio", "maxdeviation")
        columns = []
        for colname in colnames:
            if self.options[colname] == True:
                columns.append(colname)
                if colname in ["old20", "ned1"]:
                    columns.append("%s_diff" % colname)
                if colname in ["maxdeviation"]:
                    columns.append("summed_deviation")
                    columns.append("maxdeviation_transition")
        if self.output_window != None:
            self.wuggy.stop()
            self.output_window.Destroy()
        self.output_window = ResultsWindow(self, columns=columns)
        self.output_window.Show()
        self.stop = False
        array = self.grid.MakeArray()
        for word, segments, expression in array:
            if segments == "":
                pass
            else:
                for output in self.wuggy.run(self.options, segments, expression):
                    self.output_window.grid.DisplayRow(output)
                    self.update_status(self.wuggy.time_left, word, self.wuggy.n_checked)
                    if self.stop:
                        break
                self.output_window.ClearStatus()

                if self.stop:
                    break

    def update_status(self, time_left, word, n_checked):
        self.output_window.SetStatus("%s" % word, 0)
        self.output_window.SetStatus("%.00f seconds left" % time_left, 1)
        self.output_window.SetStatus("%d sequences checked" % n_checked, 2)
        wx.Yield()

    def OnMenuStop(self, event):  # wxGlade: MainWindow.<event_handler>
        self.wuggy.stop()
        self.stop = True

    def CollectOptions(self):
        self.options["ncandidates"] = self.choice_ncandidates.GetValue()
        self.options["search_time"] = self.choice_search_time.GetValue()
        self.options["match_segment_length"] = (
            self.choice_match_segment_length.GetValue()
        )
        self.options["match_plain_length"] = self.choice_match_plain_length.GetValue()
        self.options["concentric"] = self.choice_concentric_matching.GetValue()
        self.options["overlapping_segments"] = (
            self.choice_overlapping_segments.GetValue()
        )
        self.options["overlap_numerator"] = (
            self.overlapping_segments_numerator.GetValue()
        )
        self.options["overlap_denominator"] = (
            self.overlapping_segments_denominator.GetValue()
        )
        self.options["lexicality"] = self.choice_output_lexicality.GetValue()
        self.options["old20"] = self.choice_output_old20.GetValue()
        self.options["ned1"] = self.choice_output_ned1.GetValue()
        self.options["overlap_ratio"] = self.choice_output_overlap.GetValue()
        self.options["maxdeviation"] = self.choice_output_max_deviation.GetValue()

    def OnMenuSegment(self, event):  # wxGlade: MainWindow.<event_handler>
        if self.VerifyModuleLoaded() == False:
            return False
        choices = ["replace everything", "fill only empty fields", "cancel"]
        dialog = wx.SingleChoiceDialog(
            self,
            "",
            "Segmentation",
            choices,
        )
        if wx.ID_OK == dialog.ShowModal():
            result = dialog.GetStringSelection()
            dialog.Destroy()
            if result == "cancel":
                pass
            else:
                replace = True if result == "replace everything" else False
                # TODO: provide API on wuggy object
                warnings = self.grid.Segment(self.wuggy.generator, replace=replace)
                if len(warnings) > 0:
                    dialog = wx.lib.dialogs.ScrolledMessageDialog(
                        self, "\n".join(warnings), "Warnings"
                    )
                    dialog.ShowModal()
                    dialog.Destroy()

    def OnMenuVerify(self, event):  # wxGlade: MainWindow.<event_handler>
        self.VerifyInput(quiet=False)

    def VerifyInput(self, quiet=True):
        array = self.grid.MakeArray()
        errors = []
        warnings = []
        for rownum, (word, segments, expression) in enumerate(array):
            if expression != "":
                try:
                    re.compile(expression)
                except:
                    errors.append(
                        "error: invalid expression on row %d: %s"
                        % (rownum + 1, expression)
                    )
            if segments == "":
                warnings.append(
                    "warning: no segmentation found on row %d" % (rownum + 1)
                )
        message_text = "\n".join(errors + warnings)
        if len(errors + warnings) > 0:
            dialog = wx.lib.dialogs.ScrolledMessageDialog(
                self, message_text, "Verify Input"
            )
            dialog.ShowModal()
            dialog.Destroy()
            if len(errors) > 0:
                return False
            else:
                return True  # only warnings (we can continue)
        elif quiet == False:
            dialog = wx.MessageDialog(self, "No problems found", "Verify Input")
            dialog.ShowModal()
            dialog.Destroy()
            return True
        else:
            return True

    def VerifyModuleLoaded(self):
        if self.wuggy._loaded == False:
            dialog = wx.MessageDialog(self, "No language module loaded", "Warning")
            dialog.ShowModal()
            dialog.Destroy()
            return False
        else:
            return True

    def OnMenuAbout(self, event):  # wxGlade: MainWindow.<event_handler>
        # On OS X some of the info seems to beread from info.plist
        # Need to see what it does on Win and Linux
        about = wx.adv.AboutDialogInfo()
        about.Name = info.Name
        about.Version = info.Version
        about.Copyright = info.Copyright
        about.Description = info.Description
        about.WebSite = info.WebSite
        # about.Developers = info.Developers
        wx.adv.AboutBox(about)

    def OnMenuQuit(self, event):
        self.Close()


# end of class MainWindow
