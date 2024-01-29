# encoding: utf-8

import re

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
accented_letters = ["á", "à", "ê", "è", "é", "í", "ó", "â", "ô", "ú", "ü", "ö"]
double_letter_pattern = "|".join(double_letters)
single_letter_pattern = "|".join(single_letters)
accented_letter_pattern = "|".join(accented_letters)
nucleuspattern = "%s|%s|%s" % (
    double_letter_pattern,
    accented_letter_pattern,
    single_letter_pattern,
)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
