
from .rgxlib import *
from .unpackers import *


def remove_aliquot_interveners(txt):
    """
    INTERNAL USE:

    Remove whitespace, 'of', and 'of the' between otherwise preprocessed
    aliquot components -- e.g., 'N½ of NE¼ of the SW¼' -> 'N½NE¼SW¼'.
    :param txt: An otherwise preprocessed string with aliquots already
    converted to their abbreviations with appropriate fractions.
    :return: The aliquots joined into a string with no spaces.
    """
    new_txt = ''
    while txt != new_txt:
        new_txt = txt
        txt = re.sub(
            aliquot_intervener_remover_regex,
            r"\g<aliquot1>\g<aliquot2>",
            txt)

    return txt
