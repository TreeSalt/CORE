import unittest
import pandas as pd

from mantis_core.portfolio_policies import CrossSectionMeanReversionPolicy, PolicyConfig
from mantis_core.portfolio_router import PortfolioRouter
from mantis_core.regimes import RegimeConfig, RegimeFlag, RegimeLabel, RegimeState


class TestPhase9EHardening(unittest.TestCase):
    def setUp(self):
        self.dates = pd.date_range("2021-01-01", periods=100, freq="D")
        self.cfg = RegimeConfig(trend_th_entry=0.6, trend_th_exit=0.3)

    def test_schmitt_trigger_behavior(self):
        print("Entering test_schmitt_trigger_behavior")
        """
        Verify Schmitt Trigger uses different thresholds based on state.
        Entry requires 0.6, Exit requires 0.3.
        """
        from mantis_core.regimes import _infer_single_regime

        # Case 1: Was not trending. Z=0.45 (< 0.6). Should stay in RANGE.
        label, _, _, is_trending, _ = _infer_single_regime(
            dz=0.45, vr=1.0, dd=0.0, disp=1.0, td=1.0, rv=0.15,
            avg_corr=0.0, corr_z=0.0, was_trending=False, was_high_vol=False, cfg=self.cfg
        )
        self.assertIn("RANGE", label)
        self.assertFalse(is_trending)

        # Case 2: Was trending. Z=0.45 (> 0.3). Should stay in TREND.
        label, _, _, is_trending, _ = _infer_single_regime(
            dz=0.45, vr=1.0, dd=0.0, disp=1.0, td=1.0, rv=0.15,
            avg_corr=0.0, corr_z=0.0, was_trending=True, was_high_vol=False, cfg=self.cfg
        )
        self.assertIn("TREND", label)
        self.assertTrue(is_trending)

    def test_persistence_delay(self):
        print("Entering test_persistence_delay")
        """
        Router should not switch regime until N bars confirm it.
        """
        router = PortfolioRouter()
        # Mock the persistence
        router.persistence.min_bars = 3

        # Initial: Feed 'TREND_LOW_VOL' for 10 bars -> Confirmed TREND
        state_trend = RegimeState(RegimeLabel.TREND_LOW_VOL)
        for _ in range(5):
            res = router.persistence.update(state_trend)
        self.assertEqual(res.label, RegimeLabel.TREND_LOW_VOL)

        # Switch: Feed 'PANIC' for 1 bar
        state_panic = RegimeState(RegimeLabel.PANIC, flags={RegimeFlag.PANIC})
        res = router.persistence.update(state_panic)
        # Should still be TREND (1/3 confirmed)
        self.assertEqual(res.label, RegimeLabel.TREND_LOW_VOL)

        # Feed 2nd bar PANIC
        res = router.persistence.update(state_panic)
        self.assertEqual(res.label, RegimeLabel.TREND_LOW_VOL)  # 2/3

        # Feed 3rd bar PANIC
        res = router.persistence.update(state_panic)
        self.assertEqual(res.label, RegimeLabel.PANIC)  # 3/3 -> Switch!

    def test_falling_knife_guard(self):
        print("Entering test_falling_knife_guard")
        """
        MeanRev policy should return empty weights if returns < crash_floor.
        """
        pol = CrossSectionMeanReversionPolicy()
        pcfg = PolicyConfig(crash_floor=-0.20, top_k=3, min_positions=1)

        # Create crash data: 3 assets, all down -30%
        dates = pd.date_range("2021-01-01", periods=30, freq="D")
        df = pd.DataFrame(index=dates, columns=["A", "B", "C"])
        df.iloc[:] = 100.0
        # Last day crash
        df.iloc[-1] = 70.0  # -30% return

        asof = dates[-1]

        # Run policy
        weights = pol.compute_target_weights(df, asof, pcfg)

        # Expect all zeros because all returns (-0.30) < crash_floor (-0.20)
        self.assertEqual(sum(weights.values()), 0.0)

        # Case 2: One asset valid
        df.iloc[-1, 0] = 95.0  # A is -5% (valid fallback)
        weights_2 = pol.compute_target_weights(df, asof, pcfg)
        self.assertEqual(weights_2["A"], 1.0)  # A is 100% (since B,C excluded)
        self.assertEqual(weights_2["B"], 0.0)


if __name__ == "__main__":
    unittest.main()
