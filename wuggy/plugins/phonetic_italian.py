# Phonetic Italian
public_name = "Phonetic Italian"
default_data = "phonetic_italian.txt"
default_neighbor_lexicon = "phonetic_italian.txt"
default_word_lexicon = "phonetic_italian.txt"
default_lookup_lexicon = "phonetic_italian.txt"
from .subsyllabic_common import *
import wuggy.plugins.phon.it as language
import wuggy.plugins.segment as segment

segment_function = segment.start_peak_end


def transform(input_sequence, frequency=1):
    return pre_transform(input_sequence, frequency=frequency, language=language)
