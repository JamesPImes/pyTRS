
from .unpackers import *

# Clean aliquot abbreviations with fraction.
NE_FRAC = 'NE¼'
NW_FRAC = 'NW¼'
SE_FRAC = 'SE¼'
SW_FRAC = 'SW¼'
N2_FRAC = 'N½'
S2_FRAC = 'S½'
E2_FRAC = 'E½'
W2_FRAC = 'W½'

# Define what should replace matches of each regex that is used in the
# scrub_aliquots() method.
QQ_SCRUBBER_DEFINITIONS = {
    ne_regex: NE_FRAC,
    nw_regex: NW_FRAC,
    se_regex: SE_FRAC,
    sw_regex: SW_FRAC,
    n2_regex: N2_FRAC,
    s2_regex: S2_FRAC,
    e2_regex: E2_FRAC,
    w2_regex: W2_FRAC,
    ne_clean: NE_FRAC,
    nw_clean: NW_FRAC,
    se_clean: SE_FRAC,
    sw_clean: SW_FRAC,
}

# The basic scrubbing regexes.
SCRUBBER_REGEXES = (
    ne_regex,
    nw_regex,
    se_regex,
    sw_regex,
    n2_regex,
    s2_regex,
    e2_regex,
    w2_regex,
)

# Optionally addable scrubbing regexes.
CLEAN_QQ_REGEXES = (
    ne_clean,
    nw_clean,
    se_clean,
    sw_clean,
)


class TractPreprocessor:
    """
    INTERNAL USE:

    A class for preprocessing text for the ``TractParser``. Get the
    preprocessed text from the ``.text`` attribute, or the original text
    from the ``.orig_text`` attribute.
    """

    def __init__(self, orig_text, clean_qq=False):
        self.orig_text = orig_text
        self.clean_qq = clean_qq
        self.text = self.preprocess(orig_text)

    def preprocess(self, text, clean_qq=None, commit=True) -> str:
        if clean_qq is None:
            clean_qq = self.clean_qq
        if commit:
            self.text = scrub_aliquots(text, clean_qq)
        return scrub_aliquots(text, clean_qq)


def sub_scrubber(txt, scrubber_rgx):
    """
    Convert the raw aliquots to cleaner components, using the
    specified scrubber_rgx.
    """
    replace_with = QQ_SCRUBBER_DEFINITIONS[scrubber_rgx]
    # Make substitutions until there are no changes.
    new_txt = ''
    while txt != new_txt:
        new_txt = txt
        txt = re.sub(scrubber_rgx, replace_with, txt)
    return new_txt


def half_plus_q_scrubber(txt):
    """
    Scrub patterns like 'E½NENW' into 'E½NE¼NW¼', even without clean_qq.
    (Requires a leading half with fraction.)
    """
    new_txt = ''
    while txt != new_txt:
        new_txt = txt
        mo = half_plus_q_regex.search(txt)
        if mo is None:
            continue
        rightmost_comparer = mo['quarter_aliquot_rightmost']
        rightmost_quarter = ''
        if mo['ne_found'] == rightmost_comparer:
            rightmost_quarter = 'NE¼'
        elif mo['nw_found'] == rightmost_comparer:
            rightmost_quarter = 'NW¼'
        elif mo['se_found'] == rightmost_comparer:
            rightmost_quarter = 'SE¼'
        elif mo['sw_found'] == rightmost_comparer:
            rightmost_quarter = 'SW¼'
        i = mo.start('quarter_aliquot_rightmost')
        replace_with = f"{mo.group(0)[:i]}{rightmost_quarter}"
        txt = re.sub(half_plus_q_regex, replace_with, txt)
    return txt


def scrub_aliquots(txt, clean_qq=False):
    """
    INTERNAL USE:

    Convert non-standard aliquots into standard abbreviations with
    appropriate fractions.

    For example, 'Northeast Quarter' or 'NE/4' -> 'NE¼'.

    :param txt:
    :param clean_qq: Whether to apply the so-called ``clean_qq`` regex
    preprocessing (e.g., interpret 'NE' as 'NE¼'.)
    :return: The original string, with aliquots converted to standard
    abbreviations with appropriate fractions.
    """
    for rgx in SCRUBBER_REGEXES:
        txt = sub_scrubber(txt, rgx)
    if clean_qq:
        for rgx in CLEAN_QQ_REGEXES:
            txt = sub_scrubber(txt, rgx)
    # Scrub 'E½NENW' -> 'E½NE¼NW¼'.
    txt = half_plus_q_scrubber(txt)
    # Remove any intervening 'of the' and whitespace.
    txt = remove_aliquot_interveners(txt)
    return txt


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


__all__ = [
    'TractPreprocessor'
]
