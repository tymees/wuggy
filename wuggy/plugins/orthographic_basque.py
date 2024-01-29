# Orthographic Basque
public_name = "Orthographic Basque"
default_data = "orthographic_basque.txt"
default_neighbor_lexicon = "orthographic_basque.txt"
default_word_lexicon = "orthographic_basque.txt"
default_lookup_lexicon = "orthographic_basque.txt"
from .subsyllabic_common import *
from .. import plugins as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
