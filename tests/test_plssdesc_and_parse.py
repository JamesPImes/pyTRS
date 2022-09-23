
"""
Tests for the pytrs.parser.plssdesc module and submodules (except the
.plss_preprocess submodule, which has its own tests).
"""

import unittest

try:
    from pytrs.parser import PLSSDesc
    from pytrs.parser.plssdesc.plss_parse import PLSSParser
    from pytrs.parser import Tract
    from pytrs.parser import MasterConfig
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser import PLSSDesc
    from pytrs.parser.plssdesc.plss_parse import PLSSParser
    from pytrs.parser import Tract
    from pytrs.parser import MasterConfig
    

# All four of these have the same tracts.
TEST_DESC_MULTI_TRS_DESC = (
    "T155N-R97W Sec 1: SW/4, T154N-R97W Sec 20: W/2, Sec 24 - 27: S/2, Sec 28: N/2")
TEST_DESC_MULTI_S_DESC_TR = (
    "Sec 1: SW/4 of T155N-R97W, Sec 20: W/2, Sec 24 - 27: S/2, Sec 28: N/2 of T154N-R97W")
TEST_DESC_MULTI_DESC_STR = (
    "SW/4 of Sec 1, T155N-R97W, W/2 of Sec 20, S/2 of Sec 24 - 27: N/2 of Sec 28, T154N-R97W")
TEST_DESC_MULTI_TR_DESC_S = (
    "T155N-R97W SW/4 of Sec 1, T154N-R97W W/2 of Sec 20, S/2 of Sec 24 - 27, N/2 of Sec 28")


class PLSSParseTests(unittest.TestCase):

    def _test_multisec(self, desc):
        """
        Confirm proper unpacking of multi-sections, alongside single
        sections. (Called on different descriptions to test the proper
        unpacking in the different layouts.)
        """
        d = PLSSDesc(desc)
        # Test first, second, and last tracts.
        tract = d.tracts.pop(0)
        self.assertEqual('155n97w01', tract.trs)
        self.assertEqual('SW/4', tract.desc)
        tract = d.tracts.pop(0)
        self.assertEqual('154n97w20', tract.trs)
        self.assertEqual('W/2', tract.desc)
        tract = d.tracts.pop(-1)
        self.assertEqual('154n97w28', tract.trs)
        self.assertEqual('N/2', tract.desc)
        # Test the multi-section.
        trs_expected = [f"154n97w{sec:02d}" for sec in range(24, 28)]
        i = -2
        for i, tract in enumerate(d.tracts):
            compare_trs = trs_expected[i]
            self.assertEqual(compare_trs, tract.trs)
            self.assertEqual('S/2', tract.desc)
        # Ensure all TRS were found.
        self.assertTrue(len(trs_expected) == i + 1)
        return None

    def test_multisec_trs_desc(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(TEST_DESC_MULTI_TRS_DESC)

    def test_multisec_desc_str(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(TEST_DESC_MULTI_DESC_STR)

    def test_multisec_s_desc_tr(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(TEST_DESC_MULTI_S_DESC_TR)

    def test_multisec_tr_desc_s(self):
        """
        Confirm proper unpacking of multi-sections in format TRS_Desc
        layout.
        """
        self._test_multisec(TEST_DESC_MULTI_TR_DESC_S)

    def test_plssdesc_default_nsew(self):
        """Verify default_ns and default_ew in PLSSDesc objects."""
        nw = '154n97w14'
        ne = '154n97e14'
        sw = '154s97w14'
        se = '154s97e14'

        # Test default n.
        d = PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n.
        d = PLSSDesc("T154-R97W Sec 14: NE/4", config='n')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit s.
        d = PLSSDesc("T154-R97W Sec 14: NE/4", config='s')
        self.assertEqual(sw, d.tracts[0].trs)
        # Test default w.
        d = PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit w.
        d = PLSSDesc("T154N-R97 Sec 14: NE/4", config='w')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit w.
        d = PLSSDesc("T154N-R97 Sec 14: NE/4", config='e')
        self.assertEqual(ne, d.tracts[0].trs)
        # Test default n,w.
        d = PLSSDesc("T154-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n,w.
        d = PLSSDesc("T154-R97 Sec 14: NE/4", config='n,w')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n,e.
        d = PLSSDesc("T154-R97 Sec 14: NE/4", config='n,e')
        self.assertEqual(ne, d.tracts[0].trs)
        # Test explicit s,e.
        d = PLSSDesc("T154-R97 Sec 14: NE/4", config='s,e')
        self.assertEqual(se, d.tracts[0].trs)
        # Test explicit s,w.
        d = PLSSDesc("T154-R97 Sec 14: NE/4", config='s,w')
        self.assertEqual(sw, d.tracts[0].trs)

        # Test master NS.
        MasterConfig.default_ns = 's'
        # Confirm default s.
        d = PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(sw, d.tracts[0].trs)
        # Reset master NS.
        MasterConfig.default_ns = 'n'
        # Confirm reset.
        d = PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)

        # Test master EW.
        MasterConfig.default_ew = 'e'
        # Confirm default e.
        d = PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(ne, d.tracts[0].trs)
        # Reset master EW.
        MasterConfig.default_ew = 'w'
        # Confirm reset.
        d = PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)

    def test_desc_is_flawed(self):
        error_desc = """Sec 22: W/2, T154N-R97W Sec 14: NE/4, Sec 15: S/2"""
        d = PLSSDesc(error_desc)
        self.assertTrue(d.desc_is_flawed)

    def test_sec_within(self):
        txts = (
            # Twp/Rge before
            'T154N-R97W: That part of the NE/4 of Sec 13 - 15 lying within RoW',
            'T154N-R97W\nThat part of the NE/4 of Sec 13 - 15 lying within RoW',
            # Twp/Rge within
            'That part of the NE/4 of Sec 13 - 15, T154N-R97W lying within RoW',
            # Twp/Rge after
            'That part of the NE/4 of Sec 13 - 15 lying within RoW, T154N-R97W'
        )
        expected_desc = 'That part of the NE/4 lying within RoW'
        expected_trs = ['154n97w13', '154n97w14', '154n97w15']
        expected_flag = "sec_within<{}>"  # To be filled in with .trx

        for txt in txts:
            d = PLSSDesc(txt, config='sec_within')
            for i, trs in enumerate(expected_trs):
                self.assertEqual(trs, d.tracts[i].trs)
                self.assertEqual(expected_desc, d.tracts[i].desc)
                # Check that the appropriate
                self.assertIn(expected_flag.format(trs), d.w_flags)


if __name__ == '__main__':
    unittest.main()
