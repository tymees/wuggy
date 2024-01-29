# Orthographic English
public_name = "Orthographic English"
default_data = "orthographic_english.txt"
default_neighbor_lexicon = "orthographic_english.txt"
default_word_lexicon = "orthographic_english.txt"
default_lookup_lexicon = "orthographic_english.txt"
from .subsyllabic_common import *
import plugins.orth.en as language
import plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
