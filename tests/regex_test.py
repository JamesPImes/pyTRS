
import unittest

try:
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )
    from pytrs.parser.rgxlib import (
        # twprge regexes
        twprge_regex,
        pp_twprge_no_nswe,
        pp_twprge_no_nsr,
        pp_twprge_no_ewt,
        pp_twprge_ocr_scrub,
        pp_twprge_pm,
        pp_twprge_comma_remove,
        # section regexes
        sec_regex,
        multisec_regex,
        # misc regexes
        through_regex,
        intervener_regex,
    )
except ImportError:
    import sys
    sys.path.append('../')
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )
    from pytrs.parser.rgxlib import (
        # twprge regexes
        twprge_regex,
        pp_twprge_no_nswe,
        pp_twprge_no_nsr,
        pp_twprge_no_ewt,
        pp_twprge_ocr_scrub,
        pp_twprge_pm,
        pp_twprge_comma_remove,
        # section regexes
        sec_regex,
        multisec_regex,
        # misc regexes
        through_regex,
        intervener_regex,
    )


class TwpRgeUnitTest(unittest.TestCase):

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

    def _test_range2_edgecase(self, rgx, txts: tuple, expected: dict):
        """
        'Range 2' is an edge case, where the twprge_regex pattern does
        NOT match 'T2S-2E' unless 'R' (or 'Range') is included in the
        string, thus: 'T2S-R2E'. This was done to prevent over-matching
        "Lot 2, N2 W2" as <'T2N-R2W'> (for example).
        """
        for txt in txts:
            self.assertRegex(txt, rgx)
            mo = rgx.search(txt)
            if mo:
                groups = mo.groupdict()
                # We can compare lowercase values, since case won't matter.
                self.assertEqual(expected['twpnum'], groups['twpnum'].lower())
                # rgenum should be None.
                self.assertEqual(expected['rgenum'], groups['rgenum'])
                # rgenum_edgecase_rge2 will be '2'.
                self.assertEqual(
                    expected['rgenum_edgecase_rge2'],
                    groups['rgenum_edgecase_rge2'])

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
        txts = (
            'T154N-R97W',
            'Township 154 North, Range 97 West',
            'Twp. 154 N., Rge. 97 W.',
            'T-154-N-R-97-W',
            't154nr97w',
            '154N-97W'
        )
        expected = {
            'twpnum': '154',
            'ns': 'n',
            'rgenum': '97',
            'ew': 'w'
        }
        self._test_twprge(twprge_regex, txts, expected)

    def test_twprge_regex_se(self):
        txts = (
            'T154S-R97E',
            'Township 154 South, Range 97 East',
            'Twp. 154 S., Rge. 97 E.',
            'T-154-S-R-97-E',
            't154sr97e',
            '154S-97E'
        )
        expected = {
            'twpnum': '154',
            'ns': 's',
            'rgenum': '97',
            'ew': 'e'
        }
        self._test_twprge(twprge_regex, txts, expected)

    def test_range2_edgecase_nw(self):
        """
        Test the edge case Twp/Rge regex for Range 2 West (testing N/W).
        """
        no_good = '2N-2W'
        ok = '2N-R2W'
        expected = {
            'twpnum': '2',
            'ns': 'n',
            'rgenum': None,
            'rgenum_edgecase_rge2': '2',
            'ew': 'w'
        }
        self.assertNotRegex(no_good, twprge_regex)
        self._test_range2_edgecase(twprge_regex, (ok,), expected)

    def test_range2_edgecase_se(self):
        """
        Test the edge case Twp/Rge regex for Range 2 East (testing S/E).
        """
        no_good = '2S-2E'
        ok = '2S-R2E'
        expected = {
            'twpnum': '2',
            'ns': 's',
            'rgenum': None,
            'rgenum_edgecase_rge2': '2',
            'ew': 'e'
        }
        self.assertNotRegex(no_good, twprge_regex)
        self._test_range2_edgecase(twprge_regex, (ok,), expected)

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

    def test_pp_twprge_no_nsr_west(self):
        txts = (
            'T154-97W',
            'Township 154, 97 West',
            'Twp. 154, 97 W.',
            'T-154-97-W',
        )
        expected = {
            'twpnum': '154',
            'ns': None,
            'rgenum': '97',
            'ew': 'w'
        }
        self._test_twprge(pp_twprge_no_nsr, txts, expected)

    def test_pp_twprge_no_nsr_east(self):
        txts = (
            'T154-97E',
            'Township 154, 97 East',
            'Twp. 154, 97 E.',
            'T-154-97-E',
        )
        expected = {
            'twpnum': '154',
            'ns': None,
            'rgenum': '97',
            'ew': 'e'
        }
        self._test_twprge(pp_twprge_no_nsr, txts, expected)

    def test_pp_twprge_no_ewt_north(self):
        txts = (
            '154N-R97',
            '154 North, Range 97',
            '154 N., Rge. 97',
            '154-N-R-97'
        )
        expected = {
            'twpnum': '154',
            'ns': 'n',
            'rgenum': '97',
            'ew': None
        }
        self._test_twprge(pp_twprge_no_ewt, txts, expected)

    def test_pp_twprge_no_ewt_south(self):
        txts = (
            '154S-R97',
            '154 South, Range 97',
            '154 S., Rge. 97',
            '154-S-R-97'
        )
        expected = {
            'twpnum': '154',
            'ns': 's',
            'rgenum': '97',
            'ew': None
        }
        self._test_twprge(pp_twprge_no_ewt, txts, expected)

    def test_pp_twprge_ocr_scrub(self):
        # Will be equivalent to T151N-R110W, after preprocessing.
        txts = (
            'TISlN-RIL0W',
            'Township ISl North, Range IL0 West',
            'T0wnship ISl North, Range IL0 West',
            'T0wnshlp ISl North, Range IL0 West',
            'T0wn5h1p ISl North, Range IL0 West',
            'Twp. ISl N., Rge. IL0 W.',
            'T-ISl-N-R-IL0-W'
        )
        expected = {
            'twpnum': 'isl',
            'ns': 'n',
            'rgenum': 'il0',
            'ew': 'w'
        }
        self._test_twprge(pp_twprge_ocr_scrub, txts, expected)

    def test_pp_twprge_pm(self):
        txts = (
            'T154N-R97W, 5th P.M.',
            'Township 154 North, Range 97 West, Fifth Principal Meridian',
            'Twp. 154 N., Rge. 97 W., 5th P. M.',
            'T-154-N-R-97-W-5-PM',
            't154nr97w,5PM',
            '154N-97W-5 P.M.'
        )
        expected = {
            'twpnum': '154',
            'ns': 'n',
            'rgenum': '97',
            'ew': 'w'
        }
        self._test_twprge(pp_twprge_pm, txts, expected)

    def test_pp_twprge_comma_remove(self):
        """
        Preprocessing twprge regex pattern for identifying and removing
        trailing commas and similar characters.
        :return:
        """
        txts = (
            'T154N-R97W,',
            'Township 154 North, Range 97 West ---- ,',
            'Twp. 154 N., Rge. 97 W. ;',
            'T-154-N-R-97-W  -',
            't154nr97w  :, ',
            '154N-97W,'
        )
        expected = {
            'twpnum': '154',
            'ns': 'n',
            'rgenum': '97',
            'ew': 'w'
        }
        self._test_twprge(pp_twprge_comma_remove, txts, expected)
        # Confirm entire string is matched in each case.
        for txt in txts:
            mo = pp_twprge_comma_remove.search(txt)
            self.assertEqual(txt, mo.group(0))


class SecUnitTest(unittest.TestCase):

    def _test_sec(self, rgx, txts, expected):
        """
                Test a Twp/Rge regex that matches all 4 components:
                twpnum, ns, rgenum, ew
                """
        for txt in txts:
            self.assertRegex(txt, rgx)
            mo = rgx.search(txt)
            if mo:
                groups = mo.groupdict()
                for group, value in expected.items():
                    self.assertEqual(value, groups[group])

    def test_sec_regex_singular(self):
        """
        Test sec_regex with singular 'section' and equivalent
        abbreviations.
        """
        txts = (
            'Section 14',
            'Seciton 14',
            'Sec 14',
            'Sec. 14',
            'Sect. 14',
            '§14'
        )
        expected = {
            'secnum': '14',
            'plural': None
        }
        self._test_sec(sec_regex, txts, expected)

    def test_sec_regex_plural(self):
        """
        Test sec_regex with plural 'sections' and equivalent
        abbreviations.
        """
        txts = (
            'Sections 14',
            'Secitons 14',
            'Secs 14',
        )
        expected = {
            'secnum': '14',
            'plural': 's'
        }
        self._test_sec(sec_regex, txts, expected)

    def test_multisec_through(self):
        """
        Test multisec_regex with rightmost section set off by 'through'.
        """
        txts = (
            'Section 14 - 20',
            'Seciton 14 through 20',
            'Sections 14 and 16 to 20',
            'Sec. 14, 15, and 16 - 20',
            'Sect. 14 and Section 16 to 20',
            '§14-§20'
        )
        for txt in txts:
            self.assertRegex(txt, multisec_regex)
            mo = multisec_regex.search(txt)
            if mo:
                self.assertEqual('14', mo['secnum'])
                self.assertEqual('20', mo['secnum_rightmost'])
                self.assertIsNotNone(mo['thru'])

    def test_multisec_and(self):
        """
        Test multisec_regex with rightmost section set off by 'and'.
        """
        txts = (
            'Section 14 and 20',
            'Seciton 14 through 16 and 20',
            'Sections 14 to 16 and 20',
            'Sec. 14, 15 - 16, and 20',
            'Sect. 14 and Sections 16 and 20',
            '§14 & §20'
        )
        for txt in txts:
            self.assertRegex(txt, multisec_regex)
            mo = multisec_regex.search(txt)
            if mo:
                self.assertEqual('14', mo['secnum'])
                self.assertEqual('20', mo['secnum_rightmost'])
                self.assertIsNotNone(mo['and'])

    def test_multisec_single(self):
        """
        Test multisec_regex but with only a single section.
        (multisec_regex should also match single sections, but with
        secnum_rightmost and plural_rightmost as None.)
        """
        txts = (
            'Section 14',
            'Seciton 14',
            'Sections 14',
            'Sec. 14,',
            'Sect. 14 and ',
            '§14 &'
        )
        for txt in txts:
            self.assertRegex(txt, multisec_regex)
            mo = multisec_regex.search(txt)
            if mo:
                self.assertEqual('14', mo['secnum'])
                self.assertIsNone(mo['secnum_rightmost'])
                self.assertIsNone(mo['plural_rightmost'])


class MiscUnitTest(unittest.TestCase):
    """
    Test .misc regexes in the .rgxlib.
    """

    def test_through_regex(self):
        txts = (
            'a - b',
            'a – b',
            'a — b',
            'a through b',
            'a thru b',
            'a thru. b',
        )
        for txt in txts:
            self.assertRegex(txt, through_regex)

    def test_intervener_regex_through(self):
        """
        Test the intervener_regex (which goes in elided lists of
        multi-sections and multi-lots). Look for 'through' specifically.
        """
        txts = (
            'a - b',
            'a – b',
            'a — b',
            'a through b',
            'a thru b',
            'a thru. b',
        )
        for txt in txts:
            self.assertRegex(txt, intervener_regex)
            mo = intervener_regex.search(txt)
            groups = mo.groupdict()
            self.assertIsNotNone(groups.get('thru'))
            self.assertIsNone(groups.get('and'))

    def test_intervener_regex_and(self):
        """
        Test the intervener_regex (which goes in elided lists of
        multi-sections and multi-lots). Look for 'and' specifically.
        """
        txts = (
            'a and b',
            'a & b',
        )
        for txt in txts:
            self.assertRegex(txt, intervener_regex)
            mo = intervener_regex.search(txt)
            groups = mo.groupdict()
            self.assertIsNotNone(groups.get('and'))
            self.assertIsNone(groups.get('thru'))

    def test_intervener_regex_neither(self):
        """
        Test the intervener_regex (which goes in elided lists of
        multi-sections and multi-lots). Look for neither 'through' nor
        'and'.
        """
        txts = (
            'a; b',
            'a, b, c',
            'a: d'
        )
        for txt in txts:
            self.assertRegex(txt, intervener_regex)
            mo = intervener_regex.search(txt)
            groups = mo.groupdict()
            self.assertIsNone(groups.get('and'))
            self.assertIsNone(groups.get('through'))


if __name__ == '__main__':
    unittest.main()
