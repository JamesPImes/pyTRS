
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

        # sec/multisec functions
        is_multi_sec,
        get_rightmost_sec,

        # general functions
        thru_rightmost,
        get_rightmost,
        start_of_rightmost,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.rgxlib import *
    from pytrs.parser.unpackers import (
        # lot/multilot functions
        is_multi_lot,
        get_rightmost_lot,

        # sec/multisec functions
        is_multi_sec,
        get_rightmost_sec,

        # general functions
        thru_rightmost,
        get_rightmost,
        start_of_rightmost,
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
