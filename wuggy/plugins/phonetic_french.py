# Phonetic French
public_name = "Phonetic French"
default_data = "phonetic_french.txt"
default_neighbor_lexicon = "phonetic_french.txt"
default_word_lexicon = "phonetic_french.txt"
default_lookup_lexicon = "phonetic_french.txt"
from .subsyllabic_common import *
import wuggy.plugins.phon.fr as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
