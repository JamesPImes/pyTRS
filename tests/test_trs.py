
"""
Tests for the pytrs.parser.trs module.
"""

import unittest

try:
    from pytrs.parser.trs import (
        TRS,
        trs_to_dict,
    )
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser.trs import (
        TRS,
        trs_to_dict,
    )


class TRSTests(unittest.TestCase):
    """
    Tests for ``TRS`` class.
    """

    def test_from_twprgesec(self):
        # Test n/w (default).
        components_nw = [
            ('154n', '97w', '1'),
            ('154', '97', '1'),
            (154, 97, 1),
        ]
        for twp, rge, sec in components_nw:
            test_trs = TRS.from_twprgesec(twp, rge, sec)
            # Relies on standard default_ns='w' and default_ew='w' values.
            self.assertEqual('154n97w01', test_trs.trs)

        # Test s/e.
        components_se = [
            ('154s', '97e', '1'),
            ('154', '97', '1'),
            (154, 97, 1),
        ]
        for twp, rge, sec in components_se:
            test_trs = TRS.from_twprgesec(twp, rge, sec, default_ns='s', default_ew='e')
            self.assertEqual('154s97e01', test_trs.trs)

    def test_trs_components(self):
        """
        Check that the Twp/Rge/Sec attributes/properties are correct.
        :return:
        """
        # Do not specify Twp/Rge/Sec initially.
        test_trs = TRS()

        # '___z___z__' is the undefined Twp/Rge/Sec.
        self.assertEqual('___z___z__', test_trs.trs)
        self.assertTrue(test_trs.twp_undef)
        self.assertTrue(test_trs.rge_undef)
        self.assertTrue(test_trs.sec_undef)
        self.assertIsNone(test_trs.twp_num)
        self.assertIsNone(test_trs.rge_num)
        self.assertIsNone(test_trs.sec_num)
        self.assertTrue(test_trs.is_undef())
        self.assertFalse(test_trs.is_error())

        # Assign a Twp/Rge/Sec that cannot be understood by the parser.
        test_trs.trs = 'asdf'
        # 'XXXzXXXzXX' is the error Twp/Rge/Sec.
        self.assertEqual('XXXzXXXzXX', test_trs.trs)
        # These are no longer undefined, even though they are nonsense.
        self.assertFalse(test_trs.twp_undef)
        self.assertFalse(test_trs.rge_undef)
        self.assertFalse(test_trs.sec_undef)
        # But these are still None.
        self.assertIsNone(test_trs.twp_num)
        self.assertIsNone(test_trs.rge_num)
        self.assertIsNone(test_trs.sec_num)
        self.assertFalse(test_trs.is_undef())
        self.assertTrue(test_trs.is_error())

        # Assign a valid Twp/Rge/Sec.
        test_trs.trs = '154n97w01'
        self.assertEqual('154n97w01', test_trs.trs)
        self.assertEqual('154n', test_trs.twp)
        self.assertEqual(154, test_trs.twp_num)
        self.assertEqual('n', test_trs.twp_ns)
        self.assertEqual('n', test_trs.ns)
        self.assertEqual('97w', test_trs.rge)
        self.assertEqual(97, test_trs.rge_num)
        self.assertEqual('w', test_trs.rge_ew)
        self.assertEqual('w', test_trs.ew)
        self.assertEqual('01', test_trs.sec)
        self.assertEqual(1, test_trs.sec_num)
        self.assertFalse(test_trs.twp_undef)
        self.assertFalse(test_trs.rge_undef)
        self.assertFalse(test_trs.sec_undef)
        self.assertFalse(test_trs.is_undef())
        self.assertFalse(test_trs.is_error())

    def test_pretty_twprge(self):
        custom_pretty_settings = {
            't': 'Twp ',
            'r': 'Rge ',
            'delim': ', ',
            'n': ' North',
            's': ' South',
            'e': ' East',
            'w': ' West',
            'undef': '___X'
        }

        test_trs = TRS('154n97w14')
        # Default.
        self.assertEqual('T154N-R97W', test_trs.pretty_twprge())
        # Custom.
        prettified = test_trs.pretty_twprge(**custom_pretty_settings)
        self.assertEqual('Twp 154 North, Rge 97 West', prettified)

        test_trs = TRS('154s97e14')
        # Default.
        self.assertEqual('T154S-R97E', test_trs.pretty_twprge())
        # Custom.
        prettified = test_trs.pretty_twprge(**custom_pretty_settings)
        self.assertEqual('Twp 154 South, Rge 97 East', prettified)

        # Undefined
        test_trs = TRS()
        # Default.
        self.assertEqual('T---X-R---X', test_trs.pretty_twprge())
        # Custom.
        prettified = test_trs.pretty_twprge(**custom_pretty_settings)
        self.assertEqual('Twp ___X, Rge ___X', prettified)

    def test_dunder_str(self):
        """Test the str() representation of a Tract object."""
        test_trs = TRS('154n97w01')
        self.assertEqual('154n97w01', str(test_trs))

    def test_trs_to_dict(self):
        trs = '154n97w01'
        expected = {
            'trs': '154n97w01',
            'twp': '154n',
            'twp_num': 154,
            'twp_ns': 'n',
            'twp_undef': False,
            'rge': '97w',
            'rge_num': 97,
            'rge_ew': 'w',
            'rge_undef': False,
            'sec': '01',
            'sec_num': 1,
            'sec_undef': False
        }
        # Test the TRS method.
        self.assertEqual(expected, TRS.trs_to_dict(trs))
        # Test the equivalent function.
        self.assertEqual(expected, trs_to_dict(trs))
