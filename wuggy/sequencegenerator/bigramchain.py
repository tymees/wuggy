import codecs
import random
from collections import defaultdict, namedtuple

Link = namedtuple("Link", ["position", "value"])


class BigramChain(defaultdict):
    """A dictionary storing the next possible value, given a list of input sequences."""

    def __init__(
        self,
        plugin_module,
        data=None,
        size=100,
        cutoff=1,
        token=False,
    ):
        defaultdict.__init__(self, dict)
        self.plugin_module = plugin_module
        try:
            self.hidden_sequence = self.plugin_module.hidden_sequence
        except AttributeError:
            self.hidden_sequence = False
        if data != None:
            self.load(data, size=size, cutoff=cutoff, token=token)
        self.start_keys = {}
        self.status = {"message": "", "progress": 0}
        self.subscribers = []
        self.limit_frequencies = {}

    def set_status(self, message, progress):
        for receiver in [self] + self.subscribers:
            receiver.status["message"] = message
            receiver.status["progress"] = progress

    def clear_status(self):
        for receiver in [self] + self.subscribers:
            receiver.status["message"] = ""
            receiver.status["progress"] = 0

    def load(self, datafile, size=100, cutoff=1, token=False):
        lines = datafile.readlines()
        nlines = float(len(lines))

        for i, line in enumerate(lines):
            if i % 1000 == 0:
                self.set_status("Constructing Bigram Chain", i / nlines * 100)
            self._process_line(line, size, cutoff)

        datafile.close()
        self.clear_status()
        self.set_start_keys()

    def _process_line(self, line, size, cutoff):
        fields = line.strip("\n\t").split(self.plugin_module.separator)
        reference, input_sequence, _ = fields
        sequence = self.plugin_module.transform(input_sequence, frequency=1)

        if sequence.frequency >= cutoff and random.randint(1, 100) <= size:
            n = len(sequence.representation)
            for j in range(n):
                key = Link(j, sequence.representation[j])
                if j + 1 < n:
                    next_key = Link(j + 1, sequence.representation[j + 1])
                    self[key][next_key] = (
                        self[key].get(next_key, 0) + sequence.frequency
                    )

    def set_start_keys(self):
        self.start_keys = {key: 0 for key in self.keys() if key.position == 0}

    def get_frequencies(self, reference_sequence):
        frequencies = {}
        for position in range(len(reference_sequence) - 1):
            key = Link(position, reference_sequence[position])
            nextkey = Link(position + 1, reference_sequence[position + 1])
            try:
                frequency = self[key][nextkey]
            except KeyError:
                frequency = 0
            frequencies[position] = frequency
        return frequencies

    def build_limit_frequencies(self, fields):
        limits = defaultdict(dict)
        for key, nextkeys in self.items():
            position, value = key
            subkey_a = (
                position,
                tuple([value.__getattribute__(field) for field in fields]),
            )
            for nextkey, frequency in nextkeys.items():
                position, value = nextkey
                subkey_b = (
                    position,
                    tuple([value.__getattribute__(field) for field in fields]),
                )
                subkey = (subkey_a, subkey_b)
                minfrequency = limits[subkey].get("min", frequency)
                limits[subkey]["min"] = min(minfrequency, frequency)
                maxfrequency = limits[subkey].get("max", frequency)
                limits[subkey]["max"] = max(maxfrequency, frequency)
        self.limit_frequencies[tuple(fields)] = limits

    def frequency_filter(self, reference_sequence, lower, upper, kind="dev"):
        result = BigramChain(self.plugin_module)
        frequencies = self.get_frequencies(reference_sequence)
        for key, nextkeys in self.items():
            try:
                if kind == "dev":
                    minfreq = frequencies[key.position] - lower
                    maxfreq = frequencies[key.position] + upper
                elif kind == "limit":
                    minfreq = lower
                    maxfreq = upper
            except:
                pass
            else:
                for nextkey, frequency in nextkeys.items():
                    if minfreq <= frequency <= maxfreq:
                        result[key][nextkey] = frequency
                        # print 'set %s %s to %d because %d <= %d <= %d' % (key,nextkey,frequency,minfreq,frequency,maxfreq)
                        # print result
        result = result.clean(len(reference_sequence) - 1)
        result.set_start_keys()
        return result

    def segmentset_filter(self, reference_sequence, segmentset):
        segmentset = segmentset.union(set(("^", "$")))
        result = BigramChain(self.plugin_module)
        for key, nextkeys in self.items():
            if key.value.letters in segmentset:
                for nextkey, frequency in nextkeys.items():
                    if nextkey.value.letters in segmentset:
                        result[key][nextkey] = frequency
        result = result.clean(len(reference_sequence) - 1)
        result.set_start_keys()
        return result

    def attribute_filter(self, reference_sequence, attribute):
        result = BigramChain(self.plugin_module)
        if type(reference_sequence[0]) == self.plugin_module.Segment:
            for key, nextkeys in self.items():
                try:
                    if key.value.__getattribute__(attribute) == reference_sequence[
                        key.position
                    ].__getattribute__(attribute):
                        result[key] = self[key]
                except IndexError:
                    pass
        else:
            for key, nextkeys in self.items():
                try:
                    if (
                        key.value.__getattribute__(attribute)
                        == reference_sequence[key.position]
                    ):
                        result[key] = self[key]
                except IndexError:
                    pass
        return result

    def clean(self, maxpos):
        """Remove chains that can not be completed."""
        result = BigramChain(self.plugin_module)
        for key, nextkeys in self.items():
            for nextkey, frequency in nextkeys.items():
                if nextkey in self or nextkey.position == maxpos:
                    result[key][nextkey] = frequency
        if len(self) == len(result):
            return result
        else:
            return result.clean(maxpos)

    def generate(self, start_keys=None):
        if start_keys is None:
            start_keys = self.start_keys
        start_keys = list(start_keys.items())
        random.shuffle(start_keys)
        start_keys = dict(start_keys)
        if len(self) > 0:
            for key in start_keys:
                if key not in self:
                    yield (key.value,)
                else:
                    next_keys = self[key]
                    for result in self.generate(next_keys):
                        yield (key.value,) + result
        else:
            raise Exception("LinkError")

    def display(self):
        for key, nextkeys in sorted(self.items(), key=lambda x: x):
            print("***", key.position, key.value)
            for nextkey, frequency in nextkeys.items():
                print(nextkey.value, frequency)
