
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

    def test_clean_qq(self):
        txts_expected = {
            'Lot 1 of SE/4 of the NW/4': ['L1', 'SENW'],
            'Southeast Quarter of the Northeast Quarter': ['SENE'],
            'Lots 1 - 3, NENE': ['L1', 'L2', 'L3', 'NENE'],
            'S2NE': ['SENE', 'SWNE'],
            'S2NENW, Lot 7': ['L7', 'S2NENW'],
            'N2 of NE of NW, NW': ['N2NENW', 'NENW', 'NWNW', 'SENW', 'SWNW'],
            'S½N½ SW': ['S2NESW', 'S2NWSW']
        }
        for txt, expected in txts_expected.items():
            parser = TractParser(txt, clean_qq=True)
            self.assertEqual(expected, parser.lots + parser.qqs)

    def test_lot_divs(self):
        txts_expected = {
            'N/2 of Lot 1, Lot 3, E/2SW/4 of Lot 7': ['N2 of L1', 'L3', 'E2SW of L7'],
            'Lot 5, N/2 of Lots 1 - 3': ['L5', 'N2 of L1', 'N2 of L2', 'N2 of L3'],
        }
        for txt, expected in txts_expected.items():
            # Default include lot divisions.
            parser = TractParser(txt)
            self.assertEqual(expected, parser.lots)


class AliquotParseTests(unittest.TestCase):

    def test_aliquot_parse(self):
        desc = 'S/2N/2'
        expected_qqs = ['SENE', 'SWNE', 'SENW', 'SWNW']
        qqs = parse_aliquot(desc)
        self.assertEqual(expected_qqs, qqs)

        qqs2 = parse_aliquot('SE/4SE/4')
        self.assertEqual(['SESE'], qqs2)


if __name__ == '__main__':
    unittest.main()
