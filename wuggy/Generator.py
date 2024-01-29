import sys
import time
import re
import os
import operator
from fractions import Fraction

import wx

import config
from wuggy.sequencegenerator.generator import SequenceGenerator

if config.cl_plugin_path != None:  # a command line argument was given
    sys.path.append(plugin.path)
elif sys.platform.startswith("win"):
    sys.path.append(os.curdir)
elif sys.platform == "darwin":
    sys.path.append(os.curdir)

from wuggy import plugins

# TODO: what the hell is this override doing?

class Generator(SequenceGenerator):
    def __init__(self):
        super().__init__()
        if config.cl_data_path != None:  # a data_path was given on the command line
            self.data_path = config.cl_data_path
        else:
            self.data_path = os.path.join(os.path.abspath(os.curdir), "data")
        self._loaded = False
        self._plugin_modules = {}
        self.get_plugins()

    def get_plugins(self):
        for module_name in dir(plugins):
            module_object = eval("plugins.%s" % module_name) # TODO: EVIL
            try:
                self._plugin_modules[module_object.public_name] = module_object
            except AttributeError:
                pass

    def load(self, plugin_module, size=100, cutoff=1, token=False):
        self._load(plugin_module, size=size, cutoff=cutoff, token=token)
        self._loaded = True

    def run(self, options, reference_sequence, match_expression, outputwindow):
        # set the output window
        self.outputwindow = outputwindow
        # clear previous results
        self.clear_sequence_cache()
        self.clear_statistics()
        self.clear_filters()
        # get some general options
        self.maxtime = int(options["search_time"])
        self.maxcandidates = int(options["ncandidates"])
        # which statistics were required by the user?
        statistics = ("lexicality", "old20", "ned1", "overlap_ratio")
        active_statistics = [stat for stat in statistics if options[stat] == True]
        # set the reference sequence
        self.raw_reference_sequence = reference_sequence
        self.set_reference_sequence(reference_sequence)
        limit_frequencies = self.get_limit_frequencies(["sequence_length"])
        # set segment length filter if required
        if options["match_segment_length"] == True:
            self.set_attribute_filters(("segment_length",))
        # some options require computation of statistics
        required_statistics = []
        if options["overlapping_segments"] == True:
            required_statistics.append("overlap_ratio")
        if options["output_type"] != "Both":
            required_statistics.append("lexicality")
        if options["maxdeviation"] == True:
            required_statistics.append("transition_frequencies")
        if (
            options["match_segment_length"] == False
            and options["match_plain_length"] == True
        ):
            required_statistics.append("plain_length")
        self.set_statistics(required_statistics)
        # set output mode (also transform reference sequence if necessary)
        if options["output_mode"] == "Syllables":
            self.set_output_mode("syllabic")
        elif options["output_mode"] == "Segments":
            self.set_output_mode("segmental")
        else:
            self.set_output_mode("plain")
            reference_sequence = reference_sequence.replace("-", "")
        # compile the matching expression if required (matching is always done on specified output mode!)
        if match_expression != "":
            regex = re.compile(match_expression)
        # initialize variables for the main loop
        exponent = 1  # frequency matching exponent
        self.ncandidates = 0
        self.nchecked = 0
        self.starttime = time.time()
        self.stopgenerator = False

        # the while loop is only relevant for concentric search
        while 1:
            self.update_status()
            if self.stopgenerator == True or self.elapsed_time > self.maxtime:
                break
            if options["concentric"] == True:
                self.set_frequency_filter(2**exponent, 2**exponent)
                exponent = exponent + 1
            # this is the loop where the main work is done
            # as concentric search would always find the same sequences
            # we have to keep the found sequences in a cache
            for sequence in self.generate(clear_cache=False):
                # break if required
                if self.stopgenerator == True:
                    break
                # matching routine #
                # initially, match is True (since all conditions have
                # to be fulfilled we can reject on one False)
                match = True
                # add code for less or more overlapping segments using options['overlapping_segments_comparison']
                if options["overlapping_segments"] == True:
                    observed_fraction = self.statistics["overlap_ratio"]
                    requested_fraction = Fraction(
                        int(options["overlap_numerator"]),
                        int(options["overlap_denominator"]),
                    )
                    string2operator = {
                        "Exactly": operator.eq,
                        "Maximum": operator.le,
                        "Minimum": operator.ge,
                    }
                    requested_operation = string2operator[
                        options["overlapping_segments_comparison"]
                    ]
                    if not requested_operation(observed_fraction, requested_fraction):
                        match = False
                if (
                    options["match_segment_length"] == False
                    and options["match_plain_length"] == True
                    and self.difference_statistics["plain_length"] != 0
                ):
                    match = False
                if (
                    options["output_type"] == "Only pseudowords"
                    and self.statistics["lexicality"] == "W"
                ):
                    match = False
                if (
                    options["output_type"] == "Only words"
                    and self.statistics["lexicality"] == "N"
                ):
                    match = False
                if match_expression != "":
                    if regex.match(sequence) == None:
                        match = False
                # what to do if we found a matching candidate
                if match == True:
                    self.ncandidates = self.ncandidates + 1
                    # compute statistics required only for output
                    for statistic in active_statistics:
                        self.set_statistic(statistic)
                    self.apply_statistics()
                    # prepare the output #
                    output = []
                    # append reference sequence and generated sequence (always)
                    output.append(reference_sequence)
                    output.append(sequence)
                    # append all required statistics
                    for statistic in active_statistics:
                        output.append(self.statistics[statistic])
                        if statistic in ["old20", "ned1"]:
                            output.append(self.difference_statistics[statistic])
                    # compute maximal deviation statistic if required
                    if options["maxdeviation"] == True:
                        reference_frequencies = self.reference_statistics[
                            "transition_frequencies"
                        ]
                        differences = self.difference_statistics[
                            "transition_frequencies"
                        ]
                        maxindex, maxdev = max(
                            differences.items(), key=lambda x: abs(x[1])
                        )
                        sumdev = sum((abs(d) for d in differences.values()))
                        # maximal deviation
                        output.append(maxdev)
                        # summed deviation
                        output.append(sumdev)
                        # the maximally deviating transition
                        segments = [
                            element.letters for element in self.current_sequence
                        ]
                        visual = segments
                        visual[maxindex] = "[%s" % visual[maxindex]
                        visual[maxindex + 1] = "%s]" % visual[maxindex + 1]
                        output.append(
                            "".join(visual).replace("^", "_").replace("$", "_")
                        )
                    # display the result in the outputwindow
                    output = [element for element in output]
                    self.outputwindow.grid.DisplayRow(output)
                # make sure only required statistics are computed on the next yield
                self.clear_statistics()
                self.set_statistics(required_statistics)
                self.nchecked = self.nchecked + 1
                self.update_status()
                if (
                    self.elapsed_time >= self.maxtime
                    or self.ncandidates >= self.maxcandidates
                ):
                    self.stopgenerator = True
        if options["concentric"] == False:
            self.stopgenerator = True
        self.outputwindow.ClearStatus()

    def get_elapsed_time(self):
        return time.time() - self.starttime

    elapsed_time = property(get_elapsed_time)

    def update_status(self):
        time_left = self.maxtime - self.elapsed_time
        self.outputwindow.SetStatus("%s" % (self.raw_reference_sequence), 0)
        self.outputwindow.SetStatus("%.00f seconds left" % (time_left), 1)
        self.outputwindow.SetStatus("%d sequences checked" % (self.nchecked), 2)
        wx.Yield() # TODO: move!

    def stop(self):
        self.stopgenerator = True