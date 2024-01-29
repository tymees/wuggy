# encoding: utf-8

import re

single_letters = ["a", "i", "u", "o", "e"]
single_letter_pattern = "|".join(single_letters)
nucleuspattern = "%s" % (single_letter_pattern)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
