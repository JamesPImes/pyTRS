
import unittest

try:
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )
except ImportError:
    import sys
    sys.path.append('../')
    import pytrs
    from pytrs.parser.parser import (
        PLSSParser,
        PLSSPreprocessor,
    )


class UnitTest(unittest.TestCase):

    TEST_DESC_1 = "T154N-R97W Sec 1: Lots 1 - 3, S/2N/2"

    # All four of these have the same tracts.
    TEST_DESC_MULTI_TRS_DESC = (
        "T154N-R97W Sec 20: W/2, Sec 24 - 27: S/2, Sec 28: N/2")
    TEST_DESC_MULTI_S_DESC_TR = (
        "Sec 20: W/2, Sec 24 - 27: S/2, Sec 28: N/2 of T154N-R97W")
    TEST_DESC_MULTI_DESC_STR = (
        "W/2 of Sec 20, S/2 of Sec 24 - 27: N/2 of Sec 28, T154N-R97W")
    TEST_DESC_MULTI_TR_DESC_S = (
        "T154N-R97W W/2 of Sec 20, S/2 of Sec 24 - 27, N/2 of Sec 28")

    def _test_multisec(self, desc):
        """
        Confirm proper unpacking of multi-sections, alongside single
        sections. (Called on different descriptions to test the proper
        unpacking in the different layouts.)
        """
        d = pytrs.PLSSDesc(desc)
        # Test first and last tracts.
        tract = d.tracts.pop(0)
        self.assertEqual(tract.trs, '154n97w20')
        self.assertEqual(tract.desc, 'W/2')
        tract = d.tracts.pop(-1)
        self.assertEqual(tract.trs, '154n97w28')
        self.assertEqual(tract.desc, 'N/2')
        # Test the multi-section.
        trs_expected = [f"154n97w{sec:02d}" for sec in range(24, 28)]
        i = -2
        for i, tract in enumerate(d.tracts):
            compare_trs = trs_expected[i]
            self.assertEqual(tract.trs, compare_trs)
            self.assertEqual(tract.desc, 'S/2')
        # Ensure all TRS were found.
        self.assertTrue(len(trs_expected) == i + 1)
        return None

    def test_multisec_trs_desc(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(self.TEST_DESC_MULTI_TRS_DESC)

    def test_multisec_desc_str(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(self.TEST_DESC_MULTI_DESC_STR)

    def test_multisec_s_desc_tr(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(self.TEST_DESC_MULTI_S_DESC_TR)

    def test_multisec_tr_desc_s(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(self.TEST_DESC_MULTI_TR_DESC_S)

    def test_plssdesc_default_nsew(self):
        """Verify default_ns and default_ew in PLSSDesc objects."""
        nw = '154n97w14'
        ne = '154n97e14'
        sw = '154s97w14'
        se = '154s97e14'

        # Test default n.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit n.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4", config='n')
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit s.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4", config='s')
        self.assertEqual(d.tracts[0].trs, sw)
        # Test default w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4", config='w')
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4", config='e')
        self.assertEqual(d.tracts[0].trs, ne)
        # Test default n,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit n,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='n,w')
        self.assertEqual(d.tracts[0].trs, nw)
        # Test explicit n,e.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='n,e')
        self.assertEqual(d.tracts[0].trs, ne)
        # Test explicit s,e.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='s,e')
        self.assertEqual(d.tracts[0].trs, se)
        # Test explicit s,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='s,w')
        self.assertEqual(d.tracts[0].trs, sw)

        # Test master NS.
        pytrs.PLSSDesc.MASTER_DEFAULT_NS = 's'
        # Confirm default s.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, sw)
        # Reset master NS.
        pytrs.PLSSDesc.MASTER_DEFAULT_NS = 'n'
        # Confirm reset.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, nw)

        # Test master EW.
        pytrs.PLSSDesc.MASTER_DEFAULT_EW = 'e'
        # Confirm default e.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, ne)
        # Reset master EW.
        pytrs.PLSSDesc.MASTER_DEFAULT_EW = 'w'
        # Confirm reset.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(d.tracts[0].trs, nw)

    def test_preprocess_trs(self):
        """PLSSPreprocessor TRS standardizing."""
        raw = '154n-97w Sec 14: NE/4, 155n 97w Sec 19: W/2'
        intended = 'T154N-R97W Sec 14: NE/4 T155N-R97W Sec 19: W/2'
        pp = PLSSPreprocessor(raw, default_ns='n', default_ew='w')
        self.assertEqual(intended, pp.text)

        raw2 = 'Township 154 North, Range 97 West, 5th P.M. Sec 14: NE/4'
        intended2 = 'T154N-R97W Sec 14: NE/4'
        pp = PLSSPreprocessor(raw2, default_ns='n', default_ew='w')
        self.assertEqual(intended2, pp.text)
        return None


class TractUnitTest(unittest.TestCase):

    TRACT_DESC_1 = (
        'NE/4, Lots 1, 2, and 4 - 9, S/2SE/4, S/2 of Lot 13, '
        'and that part lying south of the railroad'
    )

    def test_qqs_basic(self):
        t = pytrs.Tract(desc=self.TRACT_DESC_1, parse_qq=True)
        expected = ['NENE', 'NWNE', 'SENE', 'SWNE', 'SESE', 'SWSE']
        self.assertEqual(t.qqs, expected)

    def test_lots_basic(self):
        t = pytrs.Tract(desc=self.TRACT_DESC_1, parse_qq=True)
        expected = ['L1', 'L2', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'S2 of L13']
        self.assertEqual(t.lots, expected)

    def test_lots_discard_halves(self):
        t = pytrs.Tract(
            desc=self.TRACT_DESC_1,
            parse_qq=True,
            config='include_lot_divs.False')
        expected = ['L1', 'L2', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L13']
        self.assertEqual(t.lots, expected)


if __name__ == '__main__':
    unittest.main()
