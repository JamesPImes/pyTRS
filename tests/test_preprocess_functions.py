
import unittest


try:
    from pytrs.parser.preprocess import (
        remove_aliquot_interveners,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.preprocess import (
        remove_aliquot_interveners,
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


if __name__ == '__main__':
    unittest.main()
