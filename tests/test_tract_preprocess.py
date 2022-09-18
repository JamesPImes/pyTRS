
"""
Tests for the pytrs.parser.tract_preprocess submodule (for tract
preprocessing).
"""

import unittest


try:
    from pytrs.parser.tract.tract_preprocess import (
        remove_aliquot_interveners,
        scrub_aliquots,
        TractPreprocessor,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.tract.tract_preprocess import (
        remove_aliquot_interveners,
        scrub_aliquots,
        TractPreprocessor,
    )


class PreprocessFuncTestCase(unittest.TestCase):

    def test_remove_aliquot_interveners(self):
        txts_expected = {
            'N½ of the S½': 'N½S½',
            'NE¼ of the SW¼': 'NE¼SW¼',
            'NE¼ of SW¼': 'NE¼SW¼',
            'NE¼ SW¼': 'NE¼SW¼',
            'N½ of NE¼ of the SW¼': 'N½NE¼SW¼',
            'N½ of the NE¼ of SW¼': 'N½NE¼SW¼',
            'N½ NE¼ SW¼': 'N½NE¼SW¼',
        }
        for txt, expected in txts_expected.items():
            self.assertEqual(expected, remove_aliquot_interveners(txt))

    def test_scrub_aliquots(self):
        txts_expected = {
            'Lot 1 of SE/4 of the NW/4': 'Lot 1 of SE¼NW¼',
            'Southeast Quarter of the Northeast Quarter': 'SE¼NE¼',
            'One Hundred Feet': 'One Hundred Feet',
            'NENE': 'NENE',
            'S2NE': 'S½NE¼',
            'S2NENW': 'S½NE¼NW¼',
            'N2 of NE of NW, NW': 'N½NE¼NW¼, NW',
        }
        for txt, expected in txts_expected.items():
            self.assertEqual(expected, scrub_aliquots(txt))

    def test_scrub_aliquots_clean_qq(self):
        txts_expected = {
            'Lot 1 of SE/4 of the NW/4': 'Lot 1 of SE¼NW¼',
            'Southeast Quarter of the Northeast Quarter': 'SE¼NE¼',
            'NENE': 'NE¼NE¼',
            'S2NE': 'S½NE¼',
            'S2NENW': 'S½NE¼NW¼',
            'N2 of NE of NW, NW': 'N½NE¼NW¼, NW¼',
            'S½N½ SW': 'S½N½SW¼'
        }
        for txt, expected in txts_expected.items():
            self.assertEqual(expected, scrub_aliquots(txt, clean_qq=True))


class TractPreprocessorTests(unittest.TestCase):
    """
    Tests for the TractPreprocessor class.
    """

    def test_basic(self):
        """
        Basic preprocessing (not configured with ``clean_qq=True``).
        """
        txts_expected = {
            'Lot 1 of SE/4 of the NW/4': 'Lot 1 of SE¼NW¼',
            'Southeast Quarter of the Northeast Quarter': 'SE¼NE¼',
            'One Hundred Feet': 'One Hundred Feet',
            'NENE': 'NENE',
            'S2NE': 'S½NE¼',
            'S2NENW': 'S½NE¼NW¼',
            'N2 of NE of NW, NW': 'N½NE¼NW¼, NW',
            'S½N½ SW': 'S½N½SW¼',
        }
        for txt, expected in txts_expected.items():
            preprocessor = TractPreprocessor(txt)
            self.assertEqual(expected, preprocessor.text)

    def test_clean_qq(self):
        """
        Preprocessing when configured with ``clean_qq=True``.
        :return:
        """
        txts_expected = {
            'Lot 1 of SE/4 of the NW/4': 'Lot 1 of SE¼NW¼',
            'Southeast Quarter of the Northeast Quarter': 'SE¼NE¼',
            'NENE': 'NE¼NE¼',
            'S2NE': 'S½NE¼',
            'S2NENW': 'S½NE¼NW¼',
            'N2 of NE of NW, NW': 'N½NE¼NW¼, NW¼',
            'S½N½ SW': 'S½N½SW¼',
        }
        for txt, expected in txts_expected.items():
            preprocessor = TractPreprocessor(txt, clean_qq=True)
            self.assertEqual(expected, preprocessor.text)


if __name__ == '__main__':
    unittest.main()
