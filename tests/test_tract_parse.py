
"""
Tests for the pytrs.parser.tract.tract_parse submodule.
"""

import unittest

try:
    from pytrs.parser.tract.tract_parse import (
        TractParser,

    )
    from pytrs.parser.tract.aliquot_parse import parse_aliquot
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.tract.tract_parse import (
        TractParser,

    )
    from pytrs.parser.tract.aliquot_parse import parse_aliquot


class TractParseTests(unittest.TestCase):

    def test_basic(self):
        desc = 'Lots 1 - 3, S/2N/2, Lot 8(39.21), SE/4SE/4'
        expected_lots = ['L1', 'L2', 'L3', 'L8']
        expected_acres = {'L8': '39.21'}
        expected_qqs = ['SENE', 'SWNE', 'SENW', 'SWNW', 'SESE']
        parser = TractParser(text=desc)
        self.assertEqual(expected_lots, parser.lots)
        self.assertEqual(expected_acres, parser.lot_acres)
        self.assertEqual(expected_qqs, parser.qqs)


if __name__ == '__main__':
    unittest.main()
