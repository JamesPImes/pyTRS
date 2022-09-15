
"""
Tests for pytrs.parser.unpackers submodule.
"""

import unittest

try:
    from pytrs.parser.rgxlib import *
    from pytrs.parser.unpackers import (
        # lot/multilot functions
        is_multi_lot,

        # sec/multisec functions
        is_multi_sec,

        # general functions
        thru_rightmost,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.rgxlib import *
    from pytrs.parser.unpackers import (
        # lot/multilot functions
        is_multi_lot,

        # sec/multisec functions
        is_multi_sec,

        # general functions
        thru_rightmost,
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


class SecUnpackersTests(unittest.TestCase):

    def test_is_multi_sec(self):
        no = 'Sec 1'
        yes = 'Sec 1 and 3 - 5'

        yes_mo = multisec_regex.search(yes)
        self.assertTrue(is_multi_sec(yes_mo))

        no_mo = multisec_regex.search(no)
        self.assertFalse(is_multi_sec(no_mo))


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


if __name__ == '__main__':
    unittest.main()
