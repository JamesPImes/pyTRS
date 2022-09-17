
"""
Tests for pytrs.parser.unpackers submodule.
"""

import unittest

try:
    from pytrs.parser.rgxlib import *
    from pytrs.parser.unpackers import (
        # lot/multilot functions
        is_multi_lot,
        get_rightmost_lot,
        get_rightmost_acreage,
        first_lot_is_plural,

        # sec/multisec functions
        is_multi_sec,
        get_rightmost_sec,

        # twprge functions
        unpack_twprge,
        twprge_natural_to_short,
        twprge_short_to_natural,

        # general functions
        thru_rightmost,
        get_rightmost,
        start_of_rightmost,
        get_leading_aliquot,
    )
    from pytrs.parser.config import (
        DefaultNSError,
        DefaultEWError,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.rgxlib import *
    from pytrs.parser.unpackers import (
        # lot/multilot functions
        is_multi_lot,
        get_rightmost_lot,
        get_rightmost_acreage,
        first_lot_is_plural,

        # sec/multisec functions
        is_multi_sec,
        get_rightmost_sec,

        # twprge functions
        unpack_twprge,
        twprge_natural_to_short,
        twprge_short_to_natural,

        # general functions
        thru_rightmost,
        get_rightmost,
        start_of_rightmost,
        get_leading_aliquot,
    )
    from pytrs.parser.config import (
        DefaultNSError,
        DefaultEWError,
    )


class LotUnpackersTests(unittest.TestCase):

    def test_is_multi_lot(self):
        no = 'Lot 1'
        yes = 'Lots 1 and 3 - 5'
        no_with_aliquot = 'W½ of Lot 8'
        yes_with_aliquot = 'W½ of Lots 8 - 10'

        yes_mo = multilot_regex.search(yes)
        self.assertTrue(is_multi_lot(yes_mo))
        yes_aq_mo = multilot_with_aliquot_regex.search(yes_with_aliquot)
        self.assertTrue(is_multi_lot(yes_aq_mo))

        no_mo = multilot_regex.search(no)
        self.assertFalse(is_multi_lot(no_mo))
        no_aq_mo = multilot_with_aliquot_regex.search(no_with_aliquot)
        self.assertFalse(is_multi_lot(no_aq_mo))

    def test_get_rightmost(self):
        multis = (
            '{} 1 and 3 - 5',
            '{} 1 - 5',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
            '{} 5',
            '{} 1 and 5',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
        )

        singles = (
            '{} 5',
        )

        for txt in multis:
            # Test lots
            test = txt.format('Lot')
            mo = multilot_regex.search(test)
            self.assertTrue(get_rightmost_lot(mo))

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            mo = multilot_with_aliquot_regex.search(test)
            self.assertEqual('5', get_rightmost_lot(mo))

        for txt in singles:
            # Test lots
            test = txt.format('Lot')
            yes_mo_lot = multilot_regex.search(test)
            self.assertEqual('5', get_rightmost_lot(yes_mo_lot))

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            mo = multilot_with_aliquot_regex.search(test)
            self.assertEqual('5', get_rightmost_lot(mo))

    def test_get_rightmost_acreage(self):

        multis_yes = (
            'Lot 1(31.09), 2(31.13), 3(34.13), and 5(35.99)',
            'Lot 1(35.99)',
            'Lot 1 - 3, and 5(35.99)'
        )
        multis_no = (
            'Lot 1(31.09), 2(31.13), 3(34.13), and 5',
            'Lot 1',
            'Lot 1 - 3, and 5',
        )
        singles_yes = (
            'Lot 1(35.99)',
        )
        singles_no = (
            'Lot 1',
        )

        for txt in multis_yes:
            mo = multilot_regex.search(txt)
            self.assertEqual('35.99', get_rightmost_acreage(mo))

        for txt in multis_no:
            mo = multilot_regex.search(txt)
            self.assertIsNone(get_rightmost_acreage(mo))

        for txt in singles_yes:
            mo = lot_regex.search(txt)
            self.assertEqual('35.99', get_rightmost_acreage(mo))

        for txt in singles_no:
            mo = lot_regex.search(txt)
            self.assertIsNone(get_rightmost_acreage(mo))

    def test_first_lot_is_plural(self):
        """
        Check first_lot_is_plural()
        """
        multis_yes = (
            'Lots 1 - 3',
            'Lots 1 - 3 and Lot 5',
            'Lots 1',
        )
        multis_no = (
            'Lot 1 - 3',
            'Lot 1 - 3 and Lots 5 - 7',
            'L1',
            'L1 - L3',
            'L1, L2'
        )
        singles_yes = (
            'Lots 1',
            # These are weird, but would match:
            'Lt.s 1',
            'L.s 1',
        )
        singles_no = (
            'Lot 1',
            'L1',
            'Lt. 1',
            'Lt.1',
        )
        for txt in multis_yes:
            mo = multilot_regex.search(txt)
            self.assertTrue(first_lot_is_plural(mo))
        for txt in multis_no:
            mo = multilot_regex.search(txt)
            self.assertFalse(first_lot_is_plural(mo))
        for txt in singles_yes:
            mo = lot_regex.search(txt)
            self.assertTrue(first_lot_is_plural(mo))
        for txt in singles_no:
            mo = lot_regex.search(txt)
            self.assertFalse(first_lot_is_plural(mo))

    def test_get_leading_aliquot(self):
        aliquots = (
            'W½',
            'N½NE¼',
            'E½E½SE¼',
            'S½NE¼NW¼',
            'S½N½SW¼SW¼',
        )
        lots = (
            'Lot 1',
            'Lots 1',
            'L. 1',
            'L1',
        )
        # Test where leading aliquot exists.
        txts_expected = {}
        # Construct pairs of '<aliquot> <lots>' (and '<aliquot> of <lots>').
        for aq in aliquots:
            for lot in lots:
                txts_expected[f"{aq} {lot}"] = aq
                txts_expected[f"{aq} of {lot}"] = aq
        for txt, expected in txts_expected.items():
            mo = multilot_with_aliquot_regex.search(txt)
            self.assertEqual(expected, get_leading_aliquot(mo))

        # Test where no leading aliquot exists.
        for txt in lots:
            mo = multilot_with_aliquot_regex.search(txt)
            self.assertEqual('', get_leading_aliquot(mo))


class SecUnpackersTests(unittest.TestCase):

    def test_is_multi_sec(self):
        no = 'Sec 1'
        yes = 'Sec 1 and 3 - 5'

        yes_mo = multisec_regex.search(yes)
        self.assertTrue(is_multi_sec(yes_mo))

        no_mo = multisec_regex.search(no)
        self.assertFalse(is_multi_sec(no_mo))

    def test_get_rightmost(self):
        multis = (
            '{} 1 and 3 - 5',
            '{} 1 - 5',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
            '{} 1',
            '{} 1 and 3',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
        )
        singles = (
            '{} 5',
        )
        for txt in multis:
            # Test sections
            test = txt.format('Sec')
            mo = multisec_regex.search(test)
            self.assertTrue(get_rightmost_sec(mo))
        for txt in singles:
            # Test sections
            test = txt.format('Sec')
            mo = sec_regex.search(test)
            self.assertEqual('5', get_rightmost_sec(mo))


class TwpRgeUnpackersTests(unittest.TestCase):

    def test_unpack_twprge(self):
        # Test n/w.
        nw = (
            'T154N-R97W',
            'Township 154 North, Range 97 West',
            'Twp. 154 N., Rge. 97 W.',
            'T-154-N-R-97-W',
            't154nr97w',
            '154N-97W',
        )
        expected_nw = 'T154N-R97W'
        # Test s/e.
        se = (
            'T154S-R97E',
            'Township 154 South, Range 97 East',
            'Twp. 154 S., Rge. 97 E.',
            'T-154-S-R-97-E',
            't154sr97e',
            '154S-97E'
        )
        expected_se = 'T154S-R97E'

        for txt in nw:
            self.assertRegex(txt, twprge_regex)
            mo = twprge_regex.search(txt)
            self.assertEqual(expected_nw, unpack_twprge(mo))

        for txt in se:
            self.assertRegex(txt, twprge_regex)
            mo = twprge_regex.search(txt)
            self.assertEqual(expected_se, unpack_twprge(mo))

    def test_unpack_twprge_defaults(self):
        txt = 'T154-R97'
        self.assertRegex(txt, pp_twprge_no_nswe)
        mo = pp_twprge_no_nswe.search(txt)

        # Test master default_ns and default_ew
        self.assertEqual('T154N-R97W', unpack_twprge(mo))
        # Test explicit.
        self.assertEqual(
            'T154N-R97W', unpack_twprge(mo, default_ns='n', default_ew='w'))
        self.assertEqual(
            'T154N-R97E', unpack_twprge(mo, default_ns='n', default_ew='e'))
        self.assertEqual(
            'T154S-R97W', unpack_twprge(mo, default_ns='s', default_ew='w'))
        self.assertEqual(
            'T154S-R97E', unpack_twprge(mo, default_ns='s', default_ew='e'))

        # Check proper error when passing illegal default_ns or default_ew.
        with self.assertRaises(DefaultNSError):
            unpack_twprge(mo, default_ns='asdf')
        with self.assertRaises(DefaultEWError):
            unpack_twprge(mo, default_ew='asdf')

    def test_unpack_twprge_ocr_scrub(self):
        txts = (
            'TISlN-RIL0W',
            'Township ISl North, Range IL0 West',
            'T0wnship ISl North, Range IL0 West',
            'T0wnshlp ISl North, Range IL0 West',
            'T0wn5h1p ISl North, Range IL0 West',
            'Twp. ISl N., Rge. IL0 W.',
            'T-ISl-N-R-IL0-W'
        )
        expected = 'T151N-R110W'
        for txt in txts:
            self.assertRegex(txt, pp_twprge_ocr_scrub)
            mo = pp_twprge_ocr_scrub.search(txt)
            self.assertEqual(expected, unpack_twprge(mo, ocr_scrub=True))

    def test_twprge_natural_to_short(self):
        natural_short = {
            'T154N-R97W': '154n97w',
            'T1N-R7E': '1n7e',
            'T154S-R97W': '154s97w',
            'T1S-R7W': '1s7w',
        }
        for natural, short in natural_short.items():
            self.assertEqual(short, twprge_natural_to_short(natural))

    def test_twprge_short_to_natural(self):
        natural_short = {
            'T154N-R97W': '154n97w',
            'T1N-R7E': '1n7e',
            'T154S-R97W': '154s97w',
            'T1S-R7W': '1s7w',
        }
        for natural, short in natural_short.items():
            self.assertEqual(natural, twprge_short_to_natural(short))


class GeneralUnpackersTests(unittest.TestCase):

    def test_thru_rightmost(self):
        """
        Check if 'through' or equivalent abbreviations/symbol appears
        just before the rightmost element in a 'multi' regex pattern.
        :return:
        """
        yes_txts = (
            '{} 1 and 3 - 5',
            '{} 1 - 5',
            '{} 1 - 3 and 5 - 7',
            '{} 1 - 3, 5, 6, 8 - 10',
        )
        no_txts = (
            '{} 1',
            '{} 1 and 3',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
        )
        for txt in yes_txts:
            # Test sections
            test = txt.format('Sec')
            mo = multisec_regex.search(test)
            self.assertTrue(thru_rightmost(mo))

            # Test lots
            test = txt.format('Lot')
            mo = multilot_regex.search(test)
            self.assertTrue(thru_rightmost(mo))

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            mo = multilot_with_aliquot_regex.search(test)
            self.assertTrue(thru_rightmost(mo))

        for txt in no_txts:
            # Test sections
            test = txt.format('Sec')
            mo = multisec_regex.search(test)
            self.assertFalse(thru_rightmost(mo))

            # Test lots
            test = txt.format('Lot')
            yes_mo_lot = multilot_regex.search(test)
            self.assertFalse(thru_rightmost(yes_mo_lot))

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            mo = multilot_with_aliquot_regex.search(test)
            self.assertFalse(thru_rightmost(mo))

    def test_start_of_rightmost(self):
        # 'Lot' or 'Sec' will be added to the start of each.
        multis = (
            '{} 1 and 3 - 5',
            '{} 1 - 5',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
            '{} 1',
            '{} 1 and 3',
            '{} 1 - 3 and 5',
            '{} 1 - 3, 5',
        )
        singles = (
            '{} 5',
        )

        for txt in multis:
            # 'intervener' named group always matches at the left of the
            # rightmost target group (if it exists).

            # Test sections
            test = txt.format('Sec')
            mo = multisec_regex.search(test)
            i = start_of_rightmost(mo)
            expected = 0
            if mo['intervener'] is not None:
                expected = mo.start('intervener')
            self.assertEqual(expected, i)

            # Test lots
            test = txt.format('Lot')
            mo = multilot_regex.search(test)
            i = start_of_rightmost(mo)
            expected = 0
            if mo['intervener'] is not None:
                expected = mo.start('intervener')
            self.assertEqual(expected, i)

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            mo = multilot_with_aliquot_regex.search(test)
            i = start_of_rightmost(mo)
            expected = 0
            if mo['intervener'] is not None:
                expected = mo.start('intervener')
            self.assertEqual(expected, i)

        leading_nonsense = 'asdf '
        expected_start = len(leading_nonsense)
        for txt in singles:
            # Test sections
            test = txt.format('Sec')
            test = f"{leading_nonsense}{test}"
            mo = multisec_regex.search(test)
            self.assertEqual(expected_start, start_of_rightmost(mo))

            # Test lots
            test = txt.format('Lot')
            test = f"{leading_nonsense}{test}"
            mo = multilot_regex.search(test)
            i = start_of_rightmost(mo)
            self.assertEqual(expected_start, start_of_rightmost(mo))

            # Test lots with aliquots
            test = txt.format('Lot')
            test = f"NE¼ of {test}"
            test = f"{leading_nonsense}{test}"
            mo = multilot_with_aliquot_regex.search(test)
            i = start_of_rightmost(mo)
            self.assertEqual(expected_start, start_of_rightmost(mo))


if __name__ == '__main__':
    unittest.main()
