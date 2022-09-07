
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


class PLSSDescUnitTest(unittest.TestCase):

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
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4", config='n')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit s.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4", config='s')
        self.assertEqual(sw, d.tracts[0].trs)
        # Test default w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4", config='w')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit w.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4", config='e')
        self.assertEqual(ne, d.tracts[0].trs)
        # Test default n,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='n,w')
        self.assertEqual(nw, d.tracts[0].trs)
        # Test explicit n,e.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='n,e')
        self.assertEqual(ne, d.tracts[0].trs)
        # Test explicit s,e.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='s,e')
        self.assertEqual(se, d.tracts[0].trs)
        # Test explicit s,w.
        d = pytrs.PLSSDesc("T154-R97 Sec 14: NE/4", config='s,w')
        self.assertEqual(sw, d.tracts[0].trs)

        # Test master NS.
        pytrs.PLSSDesc.MASTER_DEFAULT_NS = 's'
        # Confirm default s.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(sw, d.tracts[0].trs)
        # Reset master NS.
        pytrs.PLSSDesc.MASTER_DEFAULT_NS = 'n'
        # Confirm reset.
        d = pytrs.PLSSDesc("T154-R97W Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)

        # Test master EW.
        pytrs.PLSSDesc.MASTER_DEFAULT_EW = 'e'
        # Confirm default e.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(ne, d.tracts[0].trs)
        # Reset master EW.
        pytrs.PLSSDesc.MASTER_DEFAULT_EW = 'w'
        # Confirm reset.
        d = pytrs.PLSSDesc("T154N-R97 Sec 14: NE/4")
        self.assertEqual(nw, d.tracts[0].trs)


class PLSSPreprocessorUnitTest(unittest.TestCase):

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
        """Identify QQ's with default behavior."""
        t = pytrs.Tract(desc=self.TRACT_DESC_1, parse_qq=True)
        expected = ['NENE', 'NWNE', 'SENE', 'SWNE', 'SESE', 'SWSE']
        self.assertEqual(expected, t.qqs)

    def test_lots_basic(self):
        """Identify lots with default behavior."""
        t = pytrs.Tract(desc=self.TRACT_DESC_1, parse_qq=True)
        expected = ['L1', 'L2', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'S2 of L13']
        self.assertEqual(expected, t.lots)

    def test_lots_discard_halves(self):
        """Identify lots and discard halves."""
        t = pytrs.Tract(
            desc=self.TRACT_DESC_1,
            parse_qq=True,
            config='include_lot_divs.False')
        expected = ['L1', 'L2', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L13']
        self.assertEqual(expected, t.lots)

    def test_clean_qq(self):
        """Identify QQ's with clean_qq."""
        desc = 'Lot 1, NE, Lot 2'
        # Without clean_qq, should identify no QQ's.
        t1 = pytrs.Tract(desc, parse_qq=True)
        self.assertEqual([], t1.qqs)

        # With clean_qq, should identify NE/4.
        t2 = pytrs.Tract(desc, parse_qq=True, config='clean_qq')
        self.assertEqual(['NENE', 'NWNE', 'SENE', 'SWNE'], t2.qqs)


class TRSUnitTest(unittest.TestCase):

    def test_trs_basic(self):
        """Basic TRS parsing."""

        sources = [
            {'twp': '154n', 'rge': '97w', 'sec': '14'},
            {'twp': '9s', 'rge': '67e', 'sec': '01'},
            {'twp': '154n', 'rge': '97e', 'sec': '14'},
            {'twp': '9n', 'rge': '67w', 'sec': '01'},
        ]
        for source in sources:
            twp = source['twp']
            rge = source['rge']
            sec = source['sec']
            unparsed = f"{twp}{rge}{sec}"
            trs = pytrs.TRS(unparsed)
            self.assertEqual(unparsed, trs.trs)
            self.assertEqual(twp, trs.twp)
            self.assertEqual(rge, trs.rge)
            self.assertEqual(sec, trs.sec)
            self.assertEqual(twp + rge, trs.twprge)
            self.assertEqual(int(sec), trs.sec_num)

    def test_trs_undef(self):
        """Undefined TRS."""

        undef_expected = '___z___z__'

        # Create Tract without specifying TRS.
        t = pytrs.Tract(desc='NE/4')
        self.assertEqual(undef_expected, t.trs)

        # Create TRS without specifying.
        trs_undef = pytrs.TRS('')
        self.assertEqual(undef_expected, trs_undef.trs)

        # Each component undefined.
        trs_undef = pytrs.TRS.from_twprgesec('', '', '')
        self.assertEqual(undef_expected, trs_undef.trs)

        # Specify twp and rge, but not sec.
        pt_undef = pytrs.TRS.from_twprgesec('154n', '97w')
        self.assertEqual('154n97w__', pt_undef.trs)

        # Specify twp and sec, but not rge.
        pt_undef = pytrs.TRS.from_twprgesec(twp='154n', rge=None, sec=14)
        self.assertEqual('154n___z14', pt_undef.trs)

        # Specify rge and sec, but not twp.
        pt_undef = pytrs.TRS.from_twprgesec(twp=None, rge='97w', sec=14)
        self.assertEqual('___z97w14', pt_undef.trs)

        # Specify sec only.
        pt_undef = pytrs.TRS.from_twprgesec(twp=None, rge=None, sec=14)
        self.assertEqual('___z___z14', pt_undef.trs)

    def test_trs_error(self):
        """Error TRS parsing."""

        error_expected = 'XXXzXXXzXX'

        # Create Tract without specifying TRS.
        t = pytrs.Tract(desc='NE/4', trs='asdf')
        self.assertEqual(error_expected, t.trs)

        # Create TRS without specifying.
        trs_error = pytrs.TRS('asdf')
        self.assertEqual(error_expected, trs_error.trs)

        # Each component is error.
        trs_error = pytrs.TRS.from_twprgesec('asdf', 'asdf', 'asdf')
        self.assertEqual(error_expected, trs_error.trs)

        # Specify twp and rge, and error sec.
        pt_undef = pytrs.TRS.from_twprgesec('154n', '97w', 'asdf')
        self.assertEqual('154n97wXX', pt_undef.trs)

    def test_from_twprgesec(self):
        """TRS.from_twprgesec() and default_ns and default_ew."""

        sources = [
            {'twp': '154', 'rge': '97', 'sec': '01'},
            {'twp': 154, 'rge': 97, 'sec': 1},
        ]
        nsew_combos = [
            (None, None),
            ('n', 'w'),
            ('n', 'e'),
            ('s', 'w'),
            ('s', 'e')
        ]
        for source in sources:
            twp = source['twp']
            rge = source['rge']
            sec = source['sec']
            for (ns, ew) in nsew_combos:
                exp_twp = f"{twp}{ns}"
                if ns is None:
                    # If default_ns is specified, will expect 'n'.
                    exp_twp = f"{twp}n"
                exp_rge = f"{rge}{ew}"
                if ew is None:
                    # If default_ns is specified, will expect 'w'.
                    exp_rge = f"{rge}w"
                # Expect '01' regardless how `sec` is passed.
                exp_sec = "01"

                trs = pytrs.TRS.from_twprgesec(
                    twp, rge, sec, default_ns=ns, default_ew=ew)
                self.assertEqual(f"{exp_twp}{exp_rge}{exp_sec}", trs.trs)
                self.assertEqual(exp_twp, trs.twp)
                self.assertEqual(exp_rge, trs.rge)
                self.assertEqual(exp_sec, trs.sec)
                self.assertEqual(exp_twp + exp_rge, trs.twprge)
                self.assertEqual(int(sec), trs.sec_num)


if __name__ == '__main__':
    unittest.main()
