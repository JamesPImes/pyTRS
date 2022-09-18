
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
        txts_expected_with = {
            'N/2 of Lot 1, Lot 3, E/2SW/4 of Lot 7': ['N2 of L1', 'L3', 'E2SW of L7'],
            'Lot 5, N/2 of Lots 1 - 3': ['L5', 'N2 of L1', 'N2 of L2', 'N2 of L3'],
        }
        for txt, expected in txts_expected_with.items():
            # Default include lot divisions.
            parser = TractParser(txt)
            self.assertEqual(expected, parser.lots)
        txts_expected_without = {
            'N/2 of Lot 1, Lot 3, E/2SW/4 of Lot 7': ['L1', 'L3', 'L7'],
            'Lot 5, N/2 of Lots 1 - 3': ['L5', 'L1', 'L2', 'L3'],
        }
        for txt, expected in txts_expected_without.items():
            parser = TractParser(txt, include_lot_divs=False)
            self.assertEqual(expected, parser.lots)

    def test_qq_depth_min(self):
        txt = 'N2'
        expected_1 = ['NE', 'NW']
        expected_2 = ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']
        expected_3 = [
            'NENENE', 'NWNENE', 'SENENE', 'SWNENE',
            'NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE',
            'NESENE', 'NWSENE', 'SESENE', 'SWSENE',
            'NESWNE', 'NWSWNE', 'SESWNE', 'SWSWNE',
            'NENENW', 'NWNENW', 'SENENW', 'SWNENW',
            'NENWNW', 'NWNWNW', 'SENWNW', 'SWNWNW',
            'NESENW', 'NWSENW', 'SESENW', 'SWSENW',
            'NESWNW', 'NWSWNW', 'SESWNW', 'SWSWNW',
        ]
        to_1 = TractParser(txt, qq_depth_min=1)
        self.assertEqual(expected_1, to_1.qqs)
        to_2 = TractParser(txt, qq_depth_min=2)
        self.assertEqual(expected_2, to_2.qqs)
        to_3 = TractParser(txt, qq_depth_min=3)
        self.assertEqual(expected_3, to_3.qqs)

    def test_qq_depth_max(self):
        txt = 'S/2N/2NW/4SW/4, SE/4SE/4'
        # Do not do a qq_depth_max of 1.
        expected_2 = ['NWSW', 'SESE']
        expected_3 = ['N2NWSW', 'SESE']
        expected_4 = ['S2N2NWSW', 'SESE']
        to_2 = TractParser(txt, qq_depth_max=2)
        self.assertEqual(expected_2, to_2.qqs)
        to_3 = TractParser(txt, qq_depth_max=3)
        self.assertEqual(expected_3, to_3.qqs)
        to_4 = TractParser(txt, qq_depth_max=4)
        self.assertEqual(expected_4, to_4.qqs)

    def test_qq_depth_exact(self):
        txt = 'S/2N/2NW/4SW/4, SE/4SE/4'
        # Do not do a qq_depth_max of 1.
        expected_1 = ['SW', 'SE']
        expected_2 = ['NWSW', 'SESE']
        expected_3 = ['NENWSW', 'NWNWSW', 'NESESE', 'NWSESE', 'SESESE', 'SWSESE']
        to_1 = TractParser(txt, qq_depth=1)
        self.assertEqual(expected_1, to_1.qqs)
        to_2 = TractParser(txt, qq_depth=2)
        self.assertEqual(expected_2, to_2.qqs)
        to_3 = TractParser(txt, qq_depth=3)
        self.assertEqual(expected_3, to_3.qqs)

    def test_break_halves(self):
        txt = 'N/2NW/4SW/4, SE/4SE/4'
        expected_without_break = ['N2NWSW', 'SESE']
        expected_with_break = ['NENWSW', 'NWNWSW', 'SESE']

        # Default qq_depth_min=2; qq_depth_max=None; break_halves=False.
        without = TractParser(txt)
        self.assertEqual(expected_without_break, without.qqs)

        with_break_halves = TractParser(txt, break_halves=True)
        self.assertEqual(expected_with_break, with_break_halves.qqs)


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
