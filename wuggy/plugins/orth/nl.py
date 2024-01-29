# encoding:utf-8
import re

double_letters = [
    "aa",
    "au",
    "ee",
    "ie",
    "oo",
    "oe",
    "ui",
    "ij",
    "ei",
    "eu",
    "ea",
    "ae",
    "ey",
    "oa",
    "ua",
    "ou",
]
single_letters = ["a", "e", "i", "o", "u", "y"]
accented_letters = ["à", "ê", "è", "é", "â", "ô", "ü", "ö", "ë"]
double_letter_pattern = "|".join(double_letters)
single_letter_pattern = "|".join(single_letters)
accented_letter_pattern = "|".join(accented_letters)
nucleuspattern = "%s|%s|%s" % (
    double_letter_pattern,
    accented_letter_pattern,
    single_letter_pattern,
)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
