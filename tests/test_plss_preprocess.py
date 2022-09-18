
"""
Tests for the pytrs.parser.plssdesc.plss_preprocess submodule.
"""

import unittest

try:
    from pytrs.parser.plssdesc.plss_preprocess import (
        PLSSPreprocessor,
        find_twprge,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.plssdesc.plss_preprocess import (
        PLSSPreprocessor,
        find_twprge,
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

    def test_ocr_scrub(self):
        txt = """Township lS4 North, Range 97 West
        Section 14: NE/4
        Township 1SS North, Range 97 West
        Sec 22: ALL"""
        expected = """T154N-R97W Section 14: NE/4
        T155N-R97W Sec 22: ALL"""

        # Get rid of indentation in multi-line strings.
        txt = txt.replace(' ' * 8, '')
        expected = expected.replace(' ' * 8, '')
        self.assertEqual(expected, PLSSPreprocessor(txt, ocr_scrub=True).text)

    def test_find_twprge_basic(self):
        txt = """Township 154 North, Range 97 West
            Section 14: NE/4
            T 155 N, R 97 W
            Section 22: ALL
            156N-97W
            Sec 1: Lots 1 - 3
            T1S-R9E"""
        expected = [
            'T154N-R97W',
            'T155N-R97W',
            'T156N-R97W',
            'T1S-R9E'
        ]
        self.assertEqual(expected, find_twprge(txt))

    def test_find_twprge_preprocess_default(self):
        txt = """Township 154, Range 97 West
            Section 14: NE/4
            T 155 N, R 97
            Section 22: ALL
            T156-R97
            Sec 1: Lots 1 - 3
            T1S-R9E"""
        expected = [
            'T154N-R97W',
            'T155N-R97W',
            'T156N-R97W',
            'T1S-R9E'
        ]
        self.assertEqual(expected, find_twprge(txt, preprocess=True))

    def test_find_twprge_preprocess_se(self):
        txt = """Township 154, Range 97 West
            Section 14: NE/4
            T 155 N, R 97
            Section 22: ALL
            T156-R97
            Sec 1: Lots 1 - 3
            T1S-R9E"""
        expected = [
            'T154S-R97W',
            'T155N-R97E',
            'T156S-R97E',
            'T1S-R9E'
        ]
        self.assertEqual(expected, find_twprge(
            txt, default_ns='s', default_ew='e', preprocess=True))


if __name__ == '__main__':
    unittest.main()
