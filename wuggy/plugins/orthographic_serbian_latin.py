# Orthographic Serbian (Latin)
public_name = "Orthographic Serbian (Latin)"
default_data = "orthographic_serbian_latin.txt"
default_neighbor_lexicon = "orthographic_serbian_latin.txt"
default_word_lexicon = "orthographic_serbian_latin.txt"
default_lookup_lexicon = "orthographic_serbian_latin.txt"
from .subsyllabic_common import *
import wuggy.plugins.orth.sr_latin as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
