
"""
Tools for preprocessing text before parsing as PLSSDesc.
"""

from .rgxlib import *
from .unpackers import (
    unpack_twprge,
)
from .master_config import (
    MasterConfig,
)

SCRUBBER_REGEXES = (
    twprge_regex,
    pp_twprge_no_nswe,
    pp_twprge_no_nsr,
    pp_twprge_no_ewt,
    pp_twprge_pm,
    pp_twprge_comma_remove,
)

# Turn this one on with `ocr_scrub=True`
OCR_SCRUBBER = pp_twprge_ocr_scrub


class PLSSPreprocessor:
    """
    INTERNAL USE:

    A class for preprocessing text for the PLSSParser. Get the
    preprocessed text from the ``.text`` attribute, or the original text
    from the ``.orig_text`` attribute.  Get a list of Twp/Rge's that
    were fixed in the ``.fixed_twprges`` attribute.
    """

    def __init__(
            self,
            orig_text: str,
            default_ns=None,
            default_ew=None,
            ocr_scrub=False):
        """

        :param orig_text: The text to be preprocessed.
        :param default_ns: How to interpret townships for which N/S was
        not specified -- i.e. either 'n' or 's'. (Defaults to
        ``MasterConfig.default_ns``, which is 'n' unless otherwise
        specified.)
        :param default_ew: How to interpret ranges for which E/W was not
        specified -- i.e. either 'e' or 'w'. (Defaults to
        ``MasterConfig.default_ew``, which is 'w' unless otherwise
        specified.)
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to
        ``False``)
        """

        self.orig_text = orig_text
        self.ocr_scrub = ocr_scrub
        if not default_ns:
            default_ns = MasterConfig.default_ns
        if not default_ew:
            default_ew = MasterConfig.default_ew
        self.default_ns = default_ns
        self.default_ew = default_ew

        # These attributes are populated by `.preprocess()`:
        self.fixed_twprges = []
        self.text = ''

        self.preprocess(orig_text, default_ns, default_ew, ocr_scrub, commit=True)

    def preprocess(
            self,
            txt,
            default_ns=None,
            default_ew=None,
            ocr_scrub=None,
            commit=False):
        if default_ns is None:
            default_ns = self.default_ns
        if default_ew is None:
            default_ew = self.default_ew
        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub
        txt, fixed_twprges = plss_preprocess(
            txt, default_ns, default_ew, ocr_scrub)
        if commit:
            self.text = txt
            self.fixed_twprges = fixed_twprges
        return txt, fixed_twprges


def plss_preprocess(
        txt: str,
        default_ns: str = None,
        default_ew: str = None,
        ocr_scrub: bool = False):
    """
    Preprocess the PLSS description to iron out common kinks in
    the input data. Stores the results to ``.text`` attribute and
    a list of fixed Twp/Rges to ``.fixed_twprges``.

    :return: The preprocessed string, and a list of Twp/Rge's that were
    fixed (i.e. that had been missing N/S, E/W, or both).
    """

    if default_ns is None:
        default_ns = MasterConfig.default_ns
    if default_ew is None:
        default_ew = MasterConfig.default_ew

    # Look for Twp/Rge in original text, so that we can tell if any are
    # cleaned up during this process (so we can raise warning flags).
    orig_twprge_list = find_twprge(txt)

    # Iteratively run each of the preprocess regexes over the text,
    # swapping in the cleaned up Twp/Rge every time.
    pp_regexes = SCRUBBER_REGEXES
    if ocr_scrub:
        pp_regexes = list(SCRUBBER_REGEXES)
        pp_regexes.insert(0, OCR_SCRUBBER)
    for pp_rgx in pp_regexes:
        txt = sub_scrubber(pp_rgx, txt, default_ns, default_ew)

    txt = reduce_whitespace(txt)

    # Look for Twp/Rge's in the newly preprocessed text, to see if we've
    # found any new ones.
    processed_twprge_list = find_twprge(txt)

    # Remove from the post-preprocess TR list each of the elements
    # in the list generated from the original text.
    for twprge in orig_twprge_list:
        if twprge in processed_twprge_list:
            processed_twprge_list.remove(twprge)

    return txt, processed_twprge_list


def sub_scrubber(rgx, txt: str, default_ns: str, default_ew: str) -> str:
    # Only use ocr_scrub if the rgx being used is the ocr_scrub regex.
    ocr_scrub = rgx == pp_twprge_ocr_scrub
    matches = rgx.finditer(txt)
    for match in matches:
        clean_twprge = unpack_twprge(
            match,
            default_ns=default_ns,
            default_ew=default_ew,
            ocr_scrub=ocr_scrub)
        # Tack on a space at the end to maintain a gap between this
        # Twp/Rge and whatever comes after it.
        txt = txt.replace(match.group(0), clean_twprge + ' ')
    return txt


def reduce_whitespace(txt):
    """
    Reduce whitespace within a string.
    :param txt:
    :return:
    """
    txt = txt.strip()
    new_txt = ''
    while txt != new_txt:
        new_txt = txt
        txt = re.sub(r' +', ' ', txt)
        txt = re.sub(r'\t+', ' ', txt)
        txt = re.sub(r'\r', '\n', txt)
        txt = re.sub(r'\n{2,}', '\n\n', txt)
        txt = re.sub(r'^[ \t]', '', txt)
    return txt


def find_twprge(
        text,
        default_ns: str = None,
        default_ew: str = None,
        preprocess: bool = False,
        ocr_scrub: bool = False) -> list:
    """
    Returns a list of all Twp/Rge's in the text (formatted as '000n000w'
    or with fewer digits as needed).

    :param text: The text to scour for Twp/Rge's.
    :param default_ns: If N/S is not specified for the Twp, assume this
    direction.
    :param default_ew: If E/W is not specified for the Twp, assume this
    direction.
    :param preprocess: A bool, whether to preprocess the text before
    searching for Twp/Rge's. (Defaults to ``False``)
    :param ocr_scrub: Whether to pass the text through the ocr scrubber
    (defaults to ``False``).
    """
    if ocr_scrub:
        preprocess = True
    if preprocess:
        text, _ = plss_preprocess(text, default_ns, default_ew, ocr_scrub)
    tr_list = [
        unpack_twprge(mo, default_ns, default_ew)
        for mo in twprge_regex.finditer(text)
    ]
    return tr_list


__all__ = [
    'PLSSPreprocessor',
    'find_twprge',
    'reduce_whitespace',
]
