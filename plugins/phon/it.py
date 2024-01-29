import re

single_letters = ["a", "A", "E", "i", "O", "u", "o", "e"]
single_letter_pattern = "|".join(single_letters)
nucleuspattern = "%s" % (single_letter_pattern)
oncpattern = re.compile("(.*?)(%s)(.*)" % nucleuspattern)
