# Orthographic French
public_name = "Orthographic French"
default_data = "orthographic_french.txt"
default_neighbor_lexicon = "orthographic_french.txt"
default_word_lexicon = "orthographic_french.txt"
default_lookup_lexicon = "orthographic_french.txt"
from .subsyllabic_common import *
import wuggy.plugins.orth.fr as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
