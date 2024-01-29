# encoding: utf-8

import re

double_letters = ["ia", "ie", "io", "iu"]
single_letters = ["a", "e", "i", "o", "u", "y"]
accented_letters = ["ą", "ę"]
double_letter_pattern = "|".join(double_letters)
single_letter_pattern = "|".join(single_letters)
accented_letter_pattern = "|".join(accented_letters)
nucleuspattern = "%s|%s|%s" % (
    double_letter_pattern,
    accented_letter_pattern,
    single_letter_pattern,
)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
