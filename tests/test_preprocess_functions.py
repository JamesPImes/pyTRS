
import unittest


try:
    from pytrs.parser.preprocess import (
        remove_aliquot_interveners,
        scrub_aliquots,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.preprocess import (
        remove_aliquot_interveners,
        scrub_aliquots,
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
        }
        for txt, expected in txts_expected.items():
            self.assertEqual(expected, scrub_aliquots(txt, clean_qq=True))


if __name__ == '__main__':
    unittest.main()
