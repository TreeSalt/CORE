"""
Test: Regime Persistence (Hysteresis)
Verify that Router/Persistence layer requires N bars to confirm a regime switch.
"""

import unittest

from mantis_core.regimes import RegimeLabel, RegimePersistence, RegimeState


class TestRegimePersistence(unittest.TestCase):
    def test_persistence_logic(self):
        # min_bars = 3
        p = RegimePersistence(min_bars=3)

        # Initial: A — Vanguard Effective: should be UNKNOWN (no bootstrap)
        s1 = RegimeState(RegimeLabel.RANGE_LOW_VOL)
        out1 = p.update(s1)
        self.assertEqual(out1.label, RegimeLabel.UNKNOWN)  # No auto-confirm

        # 2nd bar of A → still UNKNOWN (need 3 consecutive)
        out2 = p.update(s1)
        self.assertEqual(out2.label, RegimeLabel.UNKNOWN, "Should still be UNKNOWN after 2 bars")

        # 3rd bar of A → should confirm to RANGE_LOW_VOL
        out3 = p.update(s1)
        self.assertEqual(out3.label, RegimeLabel.RANGE_LOW_VOL, "Should confirm on 3rd bar")

        # Switch to B (1st bar) → Should stay A
        s2 = RegimeState(RegimeLabel.TREND_HIGH_VOL)
        out4 = p.update(s2)
        self.assertEqual(out4.label, RegimeLabel.RANGE_LOW_VOL, "Should not switch on 1st bar of new regime")

        # Switch to B (2nd bar) → Should stay A
        out5 = p.update(s2)
        self.assertEqual(out5.label, RegimeLabel.RANGE_LOW_VOL, "Should not switch on 2nd bar")

        # Switch to B (3rd bar) → Should switch to B
        out6 = p.update(s2)
        self.assertEqual(out6.label, RegimeLabel.TREND_HIGH_VOL, "Should switch on 3rd bar")

    def test_interrupted_switch(self):
        # min_bars = 3
        p = RegimePersistence(min_bars=3)

        sA = RegimeState(RegimeLabel.RANGE_LOW_VOL)
        sB = RegimeState(RegimeLabel.TREND_HIGH_VOL)

        # Confirm A
        p.update(sA)
        p.update(sA)
        p.update(sA)
        self.assertEqual(p.confirmed_regime, RegimeLabel.RANGE_LOW_VOL)

        # B (1)
        p.update(sB)
        self.assertEqual(p.confirmed_regime, RegimeLabel.RANGE_LOW_VOL)

        # B (2)
        p.update(sB)
        self.assertEqual(p.confirmed_regime, RegimeLabel.RANGE_LOW_VOL)

        # A (Interrupt!)
        p.update(sA)
        self.assertEqual(p.confirmed_regime, RegimeLabel.RANGE_LOW_VOL)

        # B (1) - Start over
        p.update(sB)
        self.assertEqual(p.confirmed_regime, RegimeLabel.RANGE_LOW_VOL)


if __name__ == "__main__":
    unittest.main()
