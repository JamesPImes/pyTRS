
"""
Tests for the regex patterns in pytrs.parser.parser.rgxlib
"""

import unittest

try:
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

        # lot regexes
        acreage_subpattern,
        lot_regex,
        multilot_regex,

        # aliquot regexes
        ne_clean,
        nw_clean,
        se_clean,
        sw_clean,
        ne_regex,
        nw_regex,
        se_regex,
        sw_regex,
        n2_regex,
        s2_regex,
        e2_regex,
        w2_regex,
        all_regex,
        half_plus_q_regex,

        # misc regexes
        through_regex,
        intervener_regex,
    )
except ImportError:
    import sys
    sys.path.append('../')
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

        # lot regexes
        acreage_subpattern,
        lot_regex,
        multilot_regex,

        # aliquot regexes
        ne_clean,
        nw_clean,
        se_clean,
        sw_clean,
        ne_regex,
        nw_regex,
        se_regex,
        sw_regex,
        n2_regex,
        s2_regex,
        e2_regex,
        w2_regex,
        all_regex,
        half_plus_q_regex,

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


class LotUnitTest(unittest.TestCase):

    def test_acreage_subpattern(self):
        txts = (
            '(12.34)',
            '[12.34]',
            '(1.0)',
            '[1.0]',
            '(123.456789)',
            '[123.456789]',
        )
        for txt in txts:
            self.assertRegex(txt, acreage_subpattern)

    def test_lot_regex(self):
        txts = (
            'Lot 1',
            'Lots 1',
            'L. 1',
            'L1',
        )
        for txt in txts:
            self.assertRegex(txt, lot_regex)
            mo = lot_regex.search(txt)
            self.assertEqual('1', mo['lotnum'])

    def test_multilot_regex_through(self):
        txts = (
            'Lot 1 - 8',
            'Lot 1 - Lot 8',
            'Lots 1 - 8',
            'L. 1 - L. 8',
            'L1 thru L8',
            'L1 through L8'
        )
        for txt in txts:
            self.assertRegex(txt, multilot_regex)
            mo = multilot_regex.search(txt)
            groups = mo.groupdict()
            self.assertEqual('1', groups['lotnum'])
            self.assertEqual('8', groups['lotnum_rightmost'])
            self.assertIsNotNone(groups['thru'])

    def test_multilot_regex_and(self):
        txts = (
            'Lot 1 and 8',
            'Lot 1 and Lot 8',
            'Lots 1 - 3, and 8',
            'L. 1 - 3, and L. 8',
            'L1 thru L3, and L8',
            'L1 through L3, and L8'
        )
        for txt in txts:
            self.assertRegex(txt, multilot_regex)
            mo = multilot_regex.search(txt)
            groups = mo.groupdict()
            self.assertEqual('1', groups['lotnum'])
            self.assertEqual('8', groups['lotnum_rightmost'])
            self.assertIsNotNone(groups['and'])


class AliquotUnitTest(unittest.TestCase):

    def _test_aliquot_basic(self, txts, rgx):
        for txt in txts:
            self.assertRegex(txt, rgx)

    def _test_aliquot_none(self, txts, rgx):
        for txt in txts:
            self.assertNotRegex(txt, rgx)

    def test_n2_regex(self):
        txts = (
            'North Half',
            'N2',
            'N/2',
            'N1/2',
            'North 1/2',
            'N 1/2',
            'N½',
        )
        self._test_aliquot_basic(txts, n2_regex)

    def test_s2_regex(self):
        txts = (
            'South Half',
            'S2',
            'S/2',
            'S1/2',
            'South 1/2',
            'S 1/2',
            'S½',
        )
        self._test_aliquot_basic(txts, s2_regex)

    def test_e2_regex(self):
        txts = (
            'East Half',
            'E2',
            'E/2',
            'E1/2',
            'East 1/2',
            'E 1/2',
            'E½',
        )
        self._test_aliquot_basic(txts, e2_regex)

    def test_w2_regex(self):
        txts = (
            'West Half',
            'W2',
            'W/2',
            'W1/2',
            'West 1/2',
            'W 1/2',
            'W½',
        )
        self._test_aliquot_basic(txts, w2_regex)

    def test_ne_regex(self):
        txts = (
            'Northeast Quarter',
            'Northeast One Quarter',
            'North East Quarter',
            'North East One Quarter',
            'NE Quarter',
            'NE/4',
            'NE4',
            'NE1/4',
            'NE 1/4',
        )
        self._test_aliquot_basic(txts, ne_regex)

        # Avoid clean_qq matches.
        no_good = (
            'NE',
            'asdfNE/4',
            'One Quarter',  # Dangerous edge case.
        )
        self._test_aliquot_none(no_good, ne_regex)

    def test_nw_regex(self):
        txts = (
            'Northwest Quarter',
            'Northwest One Quarter',
            'North West Quarter',
            'North West One Quarter',
            'NW Quarter',
            'NW/4',
            'NW4',
            'NW1/4',
            'NW 1/4',
        )
        self._test_aliquot_basic(txts, nw_regex)

        # Avoid clean_qq matches.
        no_good = (
            'NW',
            'asdfNW/4',
        )
        self._test_aliquot_none(no_good, nw_regex)

    def test_se_regex(self):
        txts = (
            'Southeast Quarter',
            'Southeast One Quarter',
            'South East Quarter',
            'South East One Quarter',
            'SE Quarter',
            'SE/4',
            'SE4',
            'SE1/4',
            'SE 1/4',
        )
        self._test_aliquot_basic(txts, se_regex)

        # Avoid clean_qq matches.
        no_good = (
            'SE',
            'asdfSE/4',
        )
        self._test_aliquot_none(no_good, se_regex)

    def test_sw_regex(self):
        txts = (
            'Southwest Quarter',
            'Southwest One Quarter',
            'South West Quarter',
            'South West One Quarter',
            'SW Quarter',
            'SW/4',
            'SW4',
            'SW1/4',
            'SW 1/4',
        )
        self._test_aliquot_basic(txts, sw_regex)

        # Avoid clean_qq matches.
        no_good = (
            'SW',
            'asdfSW/4',
        )
        self._test_aliquot_none(no_good, sw_regex)

    def test_ne_clean(self):
        txts = (
            'Northeast Quarter',
            'Northeast One Quarter',
            'North East Quarter',
            'North East One Quarter',
            'NE Quarter',
            'NE/4',
            'NE4',
            'NE1/4',
            'NE 1/4',
            'NE',
            'asdfNE/4',
        )
        self._test_aliquot_basic(txts, ne_clean)

    def test_nw_clean(self):
        txts = (
            'Northwest Quarter',
            'Northwest One Quarter',
            'North West Quarter',
            'North West One Quarter',
            'NW Quarter',
            'NW/4',
            'NW4',
            'NW1/4',
            'NW 1/4',
            'NW',
            'asdfNW/4',
        )
        self._test_aliquot_basic(txts, nw_clean)

    def test_se_clean(self):
        txts = (
            'Southwest Quarter',
            'Southwest One Quarter',
            'South West Quarter',
            'South West One Quarter',
            'SW Quarter',
            'SW/4',
            'SW4',
            'SW1/4',
            'SW 1/4',
            'SW',
            'asdfSW/4',
        )
        self._test_aliquot_basic(txts, sw_clean)

    def test_sw_clean(self):
        txts = (
            'Southwest Quarter',
            'Southwest One Quarter',
            'South West Quarter',
            'South West One Quarter',
            'SW Quarter',
            'SW/4',
            'SW4',
            'SW1/4',
            'SW 1/4',
            'SW',
            'asdfSW/4'
        )
        self._test_aliquot_basic(txts, sw_clean)

    def test_all_regex(self):
        txts_no_context = (
            'all',
            'ALL',
        )
        for txt in txts_no_context:
            self.assertRegex(txt, all_regex)
            mo = all_regex.search(txt)
            self.assertEqual('all', mo['all'].lower())
            self.assertIsNone(mo['context'])

        txts_with_context = (
            'All of',
            'All of the '
        )
        for txt in txts_with_context:
            self.assertRegex(txt, all_regex)
            mo = all_regex.search(txt)
            self.assertEqual('all', mo['all'].lower())
            self.assertIsNotNone(mo['context'])

    def _test_half_plus_q(self, txts, rightmost):
        """
        Test half_plus_q_regex with specified rightmost quarter.
        (Note that this regex is only intended for partially
        preprocessed text, with halves already turned to '½' symbols.)
        """
        quarters = {
            'ne': 'ne_found',
            'nw': 'nw_found',
            'se': 'se_found',
            'sw': 'sw_found',
        }
        for txt in txts:
            self.assertRegex(txt, half_plus_q_regex)
            # Ensure the target quarter was found at rightmost position.
            mo = half_plus_q_regex.search(txt)
            self.assertIsNotNone(mo[quarters[rightmost]])

    def test_half_plus_q_regex_ne(self):
        """
        Test half_plus_q_regex with rightmost: NE/4.
        """
        txts = (
            'N½NE/4',
            'N½NE4',
            'N½NE',
            'N½ NE',
            'N½ of NE',
            'N½ of the NE',
            'S½N½ NE',
            'S½N½ of NE',
            'S½N½ of the NE',
            'N½ NE4',
            'N½ of NE4',
            'N½ of the NE4',
            'N½ NE/4',
            'N½ of NE/4',
            'N½ of the NE/4',
            'N½ NE 1/4',
            'N½ of NE 1/4',
            'N½ of the NE 1/4',
            'N½ Northeast',
            'N½ of Northeast',
            'N½ of the Northeast',
            # Allow intervening aliquot, but check rightmost.
            'N½ Southwest Northeast',
            'N½ of Southwest of Northeast',
            'N½ of the Southwest of the Northeast',
        )
        self._test_half_plus_q(txts, 'ne')

    def test_half_plus_q_regex_nw(self):
        """
        Test half_plus_q_regex with rightmost: NW/4.
        """
        txts = (
            'N½NW/4',
            'N½NW4',
            'N½NW',
            'N½ NW',
            'N½ of NW',
            'N½ of the NW',
            'S½N½ NW',
            'S½N½ of NW',
            'S½N½ of the NW',
            'N½ NW4',
            'N½ of NW4',
            'N½ of the NW4',
            'N½ NW/4',
            'N½ of NW/4',
            'N½ of the NW/4',
            'N½ NW 1/4',
            'N½ of NW 1/4',
            'N½ of the NW 1/4',
            'N½ Northwest',
            'N½ of Northwest',
            'N½ of the Northwest',
            # Allow intervening aliquot, but check rightmost.
            'N½ Southwest Northwest',
            'N½ of Southwest of Northwest',
            'N½ of the Southwest of the Northwest',
        )
        self._test_half_plus_q(txts, 'nw')

    def test_half_plus_q_regex_se(self):
        """
        Test half_plus_q_regex with rightmost: SE/4.
        """
        txts = (
            'N½SE/4',
            'N½SE4',
            'N½SE',
            'N½ SE',
            'N½ of SE',
            'N½ of the SE',
            'S½N½ SE',
            'S½N½ of SE',
            'S½N½ of the SE',
            'N½ SE4',
            'N½ of SE4',
            'N½ of the SE4',
            'N½ SE/4',
            'N½ of SE/4',
            'N½ of the SE/4',
            'N½ SE 1/4',
            'N½ of SE 1/4',
            'N½ of the SE 1/4',
            'N½ Southeast',
            'N½ of Southeast',
            'N½ of the Southeast',
            # Allow intervening aliquot, but check rightmost.
            'N½ Southwest Southeast',
            'N½ of Southwest of Southeast',
            'N½ of the Southwest of the Southeast',
        )
        self._test_half_plus_q(txts, 'se')

    def test_half_plus_q_regex_sw(self):
        """
        Test half_plus_q_regex with rightmost: SW/4.
        """
        txts = (
            'N½SW/4',
            'N½SW4',
            'N½SW',
            'N½ SW',
            'N½ of SW',
            'N½ of the SW',
            'S½N½ SW',
            'S½N½ of SW',
            'S½N½ of the SW',
            'N½ SW4',
            'N½ of SW4',
            'N½ of the SW4',
            'N½ SW/4',
            'N½ of SW/4',
            'N½ of the SW/4',
            'N½ SW 1/4',
            'N½ of SW 1/4',
            'N½ of the SW 1/4',
            'N½ Southwest',
            'N½ of Southwest',
            'N½ of the Southwest',
            # Allow intervening aliquot, but check rightmost.
            'N½ Northeast Southwest',
            'N½ of Northeast of Southwest',
            'N½ of the Northeast of the Southwest',
        )
        self._test_half_plus_q(txts, 'sw')


if __name__ == '__main__':
    unittest.main()
