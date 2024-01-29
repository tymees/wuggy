# encoding:utf-8
import re

double_letters = [
    "aa",
    "au",
    "ee",
    "ie",
    "oo",
    "ui",
    "ei",
    "ea",
    "ae",
    "ey",
    "oa",
    "ua",
]
single_letters = ["a", "e", "i", "o", "y"]
accented_letters = ["à", "ê", "è", "é", "â", "ä", "ô", "ü", "ö"]
double_letter_pattern = "|".join(double_letters)
single_letter_pattern = "|".join(single_letters)
accented_letter_pattern = "|".join(accented_letters)
nucleuspattern = "%s|%s|%s" % (
    double_letter_pattern,
    accented_letter_pattern,
    single_letter_pattern,
)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)