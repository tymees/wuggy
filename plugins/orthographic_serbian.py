# Orthographic Serbian
public_name = "Orhographic Serbian"
default_data = "orthographic_serbian.txt"
default_neighbor_lexicon = "orthographic_serbian.txt"
default_word_lexicon = "orthographic_serbian.txt"
default_lookup_lexicon = "orthographic_serbian.txt"
from plugins.subsyllabic_common import *
import plugins.orth.sr as language
import plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
