import unittest

import numpy as np
import pandas as pd

from antigravity_harness.indicators import ofi


class TestOFI(unittest.TestCase):
    def test_ofi_formula(self):
        # Create a mock order book sequence
        # Index | bid_price | bid_size | ask_price | ask_size
        # 0     | 100       | 10       | 101       | 10       -> OFI=0 initially
        # 1     | 100       | 15       | 101       | 10       (Bid size increases -> Delta Vb = 5, Delta Va = 0. OFI = 5)
        # 2     | 100       | 5        | 101       | 10       (Bid size decreases -> Delta Vb = -10, Delta Va = 0. OFI = -10)
        # 3     | 101       | 5        | 102       | 15       (Bid price increases -> Delta Vb = 5. Ask price increases -> Delta Va = 0. OFI = 5)
        # 4     | 100       | 20       | 101       | 5        (Bid price decreases -> Delta Vb = 0. Ask price decreases -> Delta Va = 5. OFI = -5)
        
        data = {
            "bid_price": [100.0, 100.0, 100.0, 101.0, 100.0],
            "bid_size":  [10.0,  15.0,  5.0,   5.0,   20.0],
            "ask_price": [101.0, 101.0, 101.0, 102.0, 101.0],
            "ask_size":  [10.0,  10.0,  10.0,  15.0,  5.0 ]
        }
        df = pd.DataFrame(data)
        
        # Calculate raw OFI (period=1)
        res_raw = ofi(df, period=1)
        expected_raw = [0.0, 5.0, -10.0, 5.0, -5.0]
        
        np.testing.assert_array_almost_equal(res_raw.values, expected_raw)
        
        # Calculate smoothed OFI (period=3)
        res_smooth = ofi(df, period=3)
        expected_smooth = [
            0.0, 
            np.mean([0.0, 5.0]), 
            np.mean([0.0, 5.0, -10.0]), 
            np.mean([5.0, -10.0, 5.0]), 
            np.mean([-10.0, 5.0, -5.0])
        ]
        
        np.testing.assert_array_almost_equal(res_smooth.values, expected_smooth)

if __name__ == "__main__":
    unittest.main()
