# orthographic Turkish
public_name = "Orthographic Turkish"
default_data = "orthographic_turkish.txt"
default_neighbor_lexicon = "orthographic_turkish.txt"
default_word_lexicon = "orthographic_turkish.txt"
default_lookup_lexicon = "orthographic_turkish.txt"
from wuggy.plugins.subsyllabic_common import *
import wuggy.plugins.orth.tr as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
