"""
Tests for the pytrs.parser.containers module (TractList and TRSList).
"""

import unittest

try:
    from pytrs import Tract, PLSSDesc
    from pytrs.parser.containers import (
        TractList,
        TRSList,
    )
except ImportError:
    import sys

    sys.path.append('../')
    from pytrs import Tract, PLSSDesc
    from pytrs.parser.containers import (
        TractList,
        TRSList,
    )

SAMPLE_PLSSDESC_1 = PLSSDesc(
    'T154N-R97W Sec 14: NE/4, Sec 16 - 20: ALL',
    parse_qq=True)
SAMPLE_PLSSDESC_2 = PLSSDesc(
    'T154N-R97W Sec 1: Lots 1 - 3, S/2N/2, T88S-R3E Sec 2: N/2NE/4, Sec 18 - 20: ALL',
    parse_qq=True)
SAMPLE_TRACT_1 = Tract('Lots 4 - 9, SW/4SW/4', '89s3e03', parse_qq=True)
SAMPLE_TRACT_2 = Tract('E/2E/2', '89s3e03', parse_qq=True)
SAMPLE_TRACT_3 = Tract('Lot 9, SW/4NE/4, N/2SE/4', '88s3e02', parse_qq=True)
SAMPLE_TRACT_4 = Tract('NE/4', trs='asdf', parse_qq=True)  # Error Twp/Rge
ALL_SAMPLES = [
    SAMPLE_PLSSDESC_1,
    SAMPLE_PLSSDESC_2,
    SAMPLE_TRACT_1,
    SAMPLE_TRACT_2,
    SAMPLE_TRACT_3,
    SAMPLE_TRACT_4,
]
GROUPED_BY_TWPRGE = {
    '154n97w': [
         '154n97w14: NE/4',
         '154n97w16: ALL',
         '154n97w17: ALL',
         '154n97w18: ALL',
         '154n97w19: ALL',
         '154n97w20: ALL',
         '154n97w01: Lots 1 - 3, S/2N/2'
    ],
    '88s3e': [
        '88s3e02: N/2NE/4',
        '88s3e18: ALL',
        '88s3e19: ALL',
        '88s3e20: ALL',
        '88s3e02: Lot 9, SW/4NE/4, N/2SE/4'
    ],
    '89s3e': [
        '89s3e03: Lots 4 - 9, SW/4SW/4',
        '89s3e03: E/2E/2'
    ],
    'XXXzXXXz': [
        'XXXzXXXzXX: NE/4'
    ]
}


class TractListTests(unittest.TestCase):

    def test_init(self):
        tl = TractList(SAMPLE_PLSSDESC_1)
        for i, tract in enumerate(SAMPLE_PLSSDESC_1):
            self.assertEqual(tract, tl[i])

    def test_from_multiple(self):
        tl = TractList.from_multiple(ALL_SAMPLES)
        for sample in ALL_SAMPLES:
            if isinstance(sample, PLSSDesc):
                # check each Tract in the PLSSDesc
                for tract in sample:
                    self.assertEqual(tract, tl.pop(0))
            else:
                # sample is itself a Tract
                self.assertEqual(sample, tl.pop(0))

    def test_concat(self):
        tl1 = TractList(SAMPLE_PLSSDESC_1)
        tl2 = TractList(SAMPLE_PLSSDESC_2)
        tl3 = tl1 + tl2
        self.assertIsInstance(tl3, TractList)

        vanilla_list = []
        for tract in SAMPLE_PLSSDESC_1:
            vanilla_list.append(tract)
        for tract in SAMPLE_PLSSDESC_2:
            vanilla_list.append(tract)

        self.assertTrue(len(vanilla_list) == len(tl3))
        for tract in vanilla_list:
            self.assertEqual(tract, tl3.pop(0))
        self.assertTrue(0 == len(tl3))

    def test_group(self):
        tl = TractList.from_multiple(ALL_SAMPLES)
        grouped = tl.group_by(attribute=['twprge'])
        for twprge, expected_tract_strs in GROUPED_BY_TWPRGE.items():
            tl_tracts = grouped[twprge]
            # We're comparing stringified tracts, rather than Tract objects,
            # to simplify the creation of test data.
            stringified_tracts = [str(tr) for tr in tl_tracts]
            for tract_str in expected_tract_strs:
                # Verify all expected tracts are in the list within the new group.
                self.assertIn(tract_str, stringified_tracts)
            # Verify they're the same length (i.e. nothing in grouped[twprge]
            # that is not also in the list of expected tracts).
            self.assertEqual(len(expected_tract_strs), len(stringified_tracts))


class TRSListTests(unittest.TestCase):

    def test_init(self):
        tl = TRSList(SAMPLE_PLSSDESC_1)
        for i, tract in enumerate(SAMPLE_PLSSDESC_1):
            self.assertEqual(tract.trs, tl[i].trs)

    def test_from_tractlist(self):
        """
        Creation of TRSList from a TractList.
        """
        tractlist = TractList(SAMPLE_PLSSDESC_1)
        trslist = TRSList(tractlist)
        self.assertEqual(6, len(trslist))
        for tract in tractlist:
            self.assertEqual(tract.trs, trslist.pop(0).trs)
        self.assertTrue(len(trslist) == 0)

    def test_from_multiple(self):
        tl = TRSList.from_multiple(ALL_SAMPLES)
        for sample in ALL_SAMPLES:
            if isinstance(sample, PLSSDesc):
                # check each Tract in the PLSSDesc
                for tract in sample:
                    self.assertEqual(tract.trs, tl.pop(0).trs)
            else:
                # sample is itself a Tract
                self.assertEqual(sample.trs, tl.pop(0).trs)

    def test_concat(self):
        tl1 = TRSList(SAMPLE_PLSSDESC_1)
        tl2 = TRSList(SAMPLE_PLSSDESC_2)
        tl3 = tl1 + tl2
        self.assertIsInstance(tl3, TRSList)

        vanilla_list = []
        for tract in SAMPLE_PLSSDESC_1:
            vanilla_list.append(tract)
        for tract in SAMPLE_PLSSDESC_2:
            vanilla_list.append(tract)

        self.assertTrue(len(vanilla_list) == len(tl3))
        for tract in vanilla_list:
            self.assertEqual(tract.trs, tl3.pop(0).trs)
        self.assertTrue(len(tl3) == 0)

    def test_group(self):
        tl = TRSList.from_multiple(ALL_SAMPLES)
        grouped = tl.group_by(attribute=['twprge'])
        for twprge, expected_tract_strs in GROUPED_BY_TWPRGE.items():
            tl_trses = grouped[twprge]
            # We're comparing stringified TRS's, rather than TRS objects,
            # to simplify the creation of test data.
            stringified_trses = [str(trs) for trs in tl_trses]
            for tract_str in expected_tract_strs:
                # Extract just the Twp/Rge/Sec from this string.
                expected_trs_str = tract_str.split(':')[0]
                # Verify all expected tracts are in the list within the new group.
                self.assertIn(expected_trs_str, stringified_trses)
            # Verify they're the same length (i.e. nothing in grouped[twprge]
            # that is not also in the list of expected tracts).
            self.assertEqual(len(expected_tract_strs), len(stringified_trses))
