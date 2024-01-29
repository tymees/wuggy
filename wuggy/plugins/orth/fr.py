# encoding: utf-8

import re

triple_letters = ["eai", "iai"]
double_letters = [
    "aa",
    "au",
    "ai",
    "ea",
    "ee",
    "ia",
    "ie",
    "io",
    "oo",
    "oe",
    "oi",
    "ou",
    "ui",
    "ue",
    "ei",
    "eu",
    "ae",
    "oa",
]
single_letters = ["a", "e", "i", "o", "u", "y"]
accented_letters = ["à", "ê", "è", "é", "â", "ô", "ü", "ö"]
double_accented_letters = ["ée", "éo", "ué", "éé", "iè", "oï"]

triple_letter_pattern = "|".join(triple_letters)
double_letter_pattern = "|".join(double_letters)
single_letter_pattern = "|".join(single_letters)
accented_letter_pattern = "|".join(accented_letters)
double_accented_letter_pattern = "|".join(double_accented_letters)

nucleuspattern = "%s|%s|%s|%s|%s" % (
    triple_letter_pattern,
    double_accented_letter_pattern,
    double_letter_pattern,
    accented_letter_pattern,
    single_letter_pattern,
)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
