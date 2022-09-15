
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


if __name__ == '__main__':
    unittest.main()
