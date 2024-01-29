import time
import re
import operator
from fractions import Fraction

from wuggy.sequencegenerator.generator import SequenceGenerator

from wuggy import plugins


class Wuggy:
    def __init__(self, data_path=None):
        self._generator = SequenceGenerator(data_path=data_path)
        self.raw_reference_sequence = ""
        self._active_statistics = []
        self._required_statistics = []
        self._max_candidates = None
        self._max_time = None
        self._loaded = False
        self._plugin_modules = {}
        self._get_plugins()

    def _get_plugins(self):
        for module_name in dir(plugins):
            module_object = eval("plugins.%s" % module_name)  # TODO: EVIL
            try:
                self._plugin_modules[module_object.public_name] = module_object
            except AttributeError:
                pass

    def load(self, plugin_module, size=100, cutoff=1, token=False):
        self._generator._load(plugin_module, size=size, cutoff=cutoff, token=token)
        self._loaded = True

    def _set_run_options(self, options):
        # get some general options
        self._max_time = int(options["search_time"])
        self._max_candidates = int(options["ncandidates"])

        self._generator.get_limit_frequencies(["sequence_length"])

        # set output mode (also transform reference sequence if necessary)
        if options["output_mode"] == "Syllables":
            self._generator.set_output_mode("syllabic")
        elif options["output_mode"] == "Segments":
            self._generator.set_output_mode("segmental")
        else:
            self._generator.set_output_mode("plain")

        # set segment length filter if required
        if options["match_segment_length"] == True:
            self._generator.set_attribute_filters(("segment_length",))

    def _resolve_required_statistics(self, options):
        required_statistics = []

        if options["overlapping_segments"] is True:
            required_statistics.append("overlap_ratio")

        if options["output_type"] != "Both":
            required_statistics.append("lexicality")

        if options["maxdeviation"] is True:
            required_statistics.append("transition_frequencies")

        if (
            options["match_segment_length"] is False
            and options["match_plain_length"] is True
        ):
            required_statistics.append("plain_length")

        self._required_statistics = required_statistics

    def _set_reference_sequence(self, options, reference_sequence):
        # set the reference sequence
        self.raw_reference_sequence = reference_sequence
        self._generator.set_reference_sequence(reference_sequence)

        if options["output_type"] == "Plain":
            reference_sequence = reference_sequence.replace("-", "")

        self._reference_sequence = reference_sequence

    def _set_statistics(self, options):
        # some options require computation of statistics
        self._resolve_required_statistics(options)
        self._generator.set_statistics(self._required_statistics)

        # which statistics were required by the user?
        statistics = ("lexicality", "old20", "ned1", "overlap_ratio")
        self.active_statistics = [stat for stat in statistics if options[stat] is True]

    def _compile_regex(self, match_expression):
        # compile the matching expression if required (matching is always done on specified output mode!)
        if match_expression != "":
            return re.compile(match_expression)

    def run(self, options, reference_sequence, match_expression):
        # TODO: make this return a self-contained generator
        # clear previous results
        self._generator.clear_sequence_cache()
        self._generator.clear_statistics()
        self._generator.clear_filters()

        # TODO: type options
        self._set_reference_sequence(options, reference_sequence)
        self._set_run_options(options)
        self._set_statistics(options)

        regex = self._compile_regex(match_expression)

        return self._run(options, regex, reference_sequence)

    def _run(self, options, regex, reference_sequence):
        # initialize variables for the main loop
        exponent = 1  # frequency matching exponent
        self.n_candidates = 0
        self.n_checked = 0
        self.start_time = time.time()
        self.stop_generator = False  # TODO: find a better name/way

        # the while loop is only relevant for concentric search
        while 1:
            if self.stop_generator is True or self.elapsed_time > self._max_time:
                break

            if options["concentric"] is True:
                self._generator.set_frequency_filter(2**exponent, 2**exponent)
                exponent += 1

            # this is the loop where the main work is done
            # as concentric search would always find the same sequences
            # we have to keep the found sequences in a cache
            for sequence in self._generator.generate(clear_cache=False):
                # break if required
                if self.stop_generator:
                    break

                output = None
                # what to do if we found a matching candidate
                if self._is_match(options, regex, sequence):
                    self.n_candidates += 1
                    # compute statistics required only for output
                    output = self._process_match(options, reference_sequence, sequence)

                    # TODO: move this
                    # self.output_window.grid.DisplayRow(output)

                # make sure only required statistics are computed on the next yield
                self._generator.clear_statistics()
                self._generator.set_statistics(self._required_statistics)
                self.n_checked += 1

                if (
                    self.elapsed_time >= self._max_time
                    or self.n_candidates >= self._max_candidates
                ):
                    self.stop_generator = True

                if output:
                    yield output

    def _is_match(self, options, regex, sequence):
        # TODO: A lot of the code here is referencing the generator and options, not the sequence we retrieved. Smelly?
        # matching routine #
        # initially, match is True (since all conditions have
        # to be fulfilled we can reject on one False)
        match = True

        # add code for less or more overlapping segments using options['overlapping_segments_comparison']
        if options["overlapping_segments"]:
            observed_fraction = self._generator.statistics["overlap_ratio"]
            requested_fraction = Fraction(
                int(options["overlap_numerator"]),
                int(options["overlap_denominator"]),
            )

            requested_operation = {
                "Exactly": operator.eq,
                "Maximum": operator.le,
                "Minimum": operator.ge,
            }[options["overlapping_segments_comparison"]]

            if not requested_operation(observed_fraction, requested_fraction):
                match = False

        if (
            options["match_segment_length"] is False
            and options["match_plain_length"] is True
            and self._generator.difference_statistics["plain_length"] != 0
        ):
            match = False

        if (
            options["output_type"] == "Only pseudowords"
            and self._generator.statistics["lexicality"] == "W"
        ):
            match = False

        if (
            options["output_type"] == "Only words"
            and self._generator.statistics["lexicality"] == "N"
        ):
            match = False

        if regex and regex.match(sequence) is None:
            match = False

        return match

    def _process_match(self, options, reference_sequence, sequence):
        # TODO: we seem to be calling set_statistic a lot, why?
        for statistic in self._active_statistics:
            self._generator.set_statistic(statistic)

        self._generator.apply_statistics()

        # prepare the output #
        output = [reference_sequence, sequence]
        # append reference sequence and generated sequence (always)
        # append all required statistics
        for statistic in self._active_statistics:
            output.append(self._generator.statistics[statistic])
            if statistic in ["old20", "ned1"]:
                output.append(self._generator.difference_statistics[statistic])

        # compute maximal deviation statistic if required
        if options["maxdeviation"]:
            differences = self._generator.difference_statistics[
                "transition_frequencies"
            ]
            max_index, max_deviation = max(differences.items(), key=lambda x: abs(x[1]))
            sum_deviation = sum((abs(d) for d in differences.values()))
            # maximal deviation
            output.append(max_deviation)
            # summed deviation
            output.append(sum_deviation)
            # the maximally deviating transition
            segments = [element.letters for element in self._generator.current_sequence]
            visual = segments
            visual[max_index] = "[%s" % visual[max_index]
            visual[max_index + 1] = "%s]" % visual[max_index + 1]
            output.append("".join(visual).replace("^", "_").replace("$", "_"))

        return output

    @property
    def elapsed_time(self):
        return time.time() - self.start_time

    @property
    def time_left(self):
        return self._max_time - self.elapsed_time

    @property
    def generator(self):
        return self._generator

    @property
    def status(self):
        # TODO: evaluate
        return self._generator.status

    def stop(self):
        self.stop_generator = True
