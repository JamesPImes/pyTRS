
import unittest

try:
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )
    from pytrs.parser.regexlib2 import (
        twprge_regex,
        twprge_regex_rge2,
        pp_twprge_no_nswe,
    )
except ImportError:
    import sys
    sys.path.append('../')
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )
    from pytrs.parser.regexlib2 import (
        twprge_regex,
        twprge_regex_rge2,
        pp_twprge_no_nswe,
    )


class TwpRgeUnitTest(unittest.TestCase):
    BASIC_NW = (
        'T154N-R97W',
        'Township 154 North, Range 97 West',
        'Twp. 154 N., Rge. 97 W.',
        'T-154-N-R-97-W',
        't154nr97w',
        '154N-97W'
    )
    BASIC_NW_EXPECTED = {
        'twpnum': '154',
        'ns': 'n',
        'rgenum': '97',
        'ew': 'w'
    }
    BASIC_SE = (
        'T154S-R97E',
        'Township 154 South, Range 97 East',
        'Twp. 154 S., Rge. 97 E.',
        'T-154-S-R-97-E',
        't154sr97e',
        '154S-97E'
    )
    BASIC_SE_EXPECTED = {
        'twpnum': '154',
        'ns': 's',
        'rgenum': '97',
        'ew': 'e'
    }

    def _test_twprge(self, rgx, txts: tuple, expected: dict):
        """
        Test a Twp/Rge regex that matches all 4 components:
        twpnum, ns, rgenum, ew
        """
        for txt in txts:
            self.assertRegex(txt, rgx)
            mo = rgx.search(txt)
            if mo:
                groups = mo.groupdict()
                # We can compare lowercase values, since case won't matter.
                self.assertEqual(expected['twpnum'], groups['twpnum'].lower())
                self.assertEqual(expected['rgenum'], groups['rgenum'].lower())
                # Only first letter of N/S and E/W will matter, but check
                # if None is expected (e.g., in preprocessing regexes).
                if expected['ns'] is None:
                    self.assertEqual(None, groups['ns'])
                else:
                    self.assertEqual(expected['ns'], groups['ns'][0].lower())

                if expected['ew'] is None:
                    self.assertEqual(None, groups['ew'])
                else:
                    self.assertEqual(expected['ew'], groups['ew'][0].lower())

    def test_twprge_regex_nw(self):
        self._test_twprge(twprge_regex, self.BASIC_NW, self.BASIC_NW_EXPECTED)

    def test_twprge_regex_se(self):
        self._test_twprge(twprge_regex, self.BASIC_SE, self.BASIC_SE_EXPECTED)

    def test_twprge_regex_rge2_nw(self):
        """
        Test the edge-case Twp/Rge regex for Range 2 West (testing N/W).
        """
        no_good = '2N-2W'
        ok = '2N-R2W'
        expected = {
            'twpnum': '2',
            'ns': 'n',
            'rgenum': '2',
            'ew': 'w'
        }
        self.assertNotRegex(no_good, twprge_regex_rge2)
        self._test_twprge(twprge_regex_rge2, (ok,), expected)

    def test_twprge_regex_rge2_se(self):
        """
        Test the edge-case Twp/Rge regex for Range 2 East (testing S/E).
        """
        no_good = '2S-2E'
        ok = '2S-R2E'
        expected = {
            'twpnum': '2',
            'ns': 's',
            'rgenum': '2',
            'ew': 'e'
        }
        self.assertNotRegex(no_good, twprge_regex_rge2)
        self._test_twprge(twprge_regex_rge2, (ok,), expected)

    def test_pp_twprge_no_nswe(self):
        txts = (
            'T154-R97',
            'Township 154, Range 97',
            'Twp. 154, Rge. 97',
            'T-154-R-97',
        )
        expected = {
            'twpnum': '154',
            'ns': None,
            'rgenum': '97',
            'ew': None
        }
        self._test_twprge(pp_twprge_no_nswe, txts, expected)

if __name__ == '__main__':
    unittest.main()
