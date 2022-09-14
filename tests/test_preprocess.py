
import unittest

try:
    import pytrs
    from pytrs.parser.parser import (
        PLSSPreprocessor,
    )
except ImportError:
    import sys
    sys.path.append('../')
    import pytrs
    from pytrs.parser.parser import (
        PLSSPreprocessor,
    )


class PreprocessTest(unittest.TestCase):

    def test_basic_preprocess(self):
        txts = (
            'Township 154 North, Range 97 West Sec 14: NE/4',
            'T154N-R97W Sec 14: NE/4',
            '154N-97W Sec 14: NE/4',
            'T154-R97 Sec 14: NE/4',
            '154N-R97 Sec 14: NE/4',
        )
        # Note: Following is only the expected result for some of the
        # test cases because default n/s and e/w are 'n' and 'w'.
        expected = 'T154N-R97W Sec 14: NE/4'
        for txt in txts:
            self.assertEqual(expected, PLSSPreprocessor(txt).text)

    def test_principal_meridian_preprocess(self):
        txt = 'T154N-R97W, 5th P.M., Sec 14: NE/4'
        expected = 'T154N-R97W Sec 14: NE/4'
        self.assertEqual(expected, PLSSPreprocessor(txt).text)

    # TODO: test_ocr_scrub


if __name__ == '__main__':
    unittest.main()
