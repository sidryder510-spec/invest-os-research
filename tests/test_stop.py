"""Stop-loss test (research_config 1.5.0), offline on synthetic panels."""
import importlib, os, shutil, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import research_config as rc
import extended_tests as xt
import pit_backtest as pit
import stop_test as st
from test_engine_v3 import market

H = rc.HOLDING_DAYS


def one_pick(path):
    """A single pick on day 0 whose closes from day 1 (entry) on are `path`."""
    dates = pd.bdate_range("2020-01-01", periods=len(path) + 1)
    px = pd.DataFrame({"X": [100.0] + list(path)}, index=dates)
    picks = pd.DataFrame([{"date": dates[0], "symbol": "X", "stock_return": np.nan, "nifty_return": 0.0}])
    return px, picks


class Mechanics(unittest.TestCase):
    def test_a_40pct_fall_is_stopped_near_minus_20_at_the_next_close(self):
        path = np.linspace(100, 60, H + 1)                     # steady slide to -40% over the hold
        px, picks = one_pick(path)
        out = st.apply_stop(picks, px, px, 0.20)
        k = int(np.argmax(path <= 80))                         # first close at or below -20%
        self.assertTrue(out["stopped"].iloc[0])
        self.assertAlmostEqual(out["stock_return"].iloc[0], (path[k + 1] / 100 - 1) * 100)
        self.assertLess(out["stock_return"].iloc[0], -20)
        self.assertGreater(out["stock_return"].iloc[0], -22)
        base = st.apply_stop(picks, px, px, None)
        self.assertAlmostEqual(base["stock_return"].iloc[0], -40)
        self.assertFalse(base["stopped"].iloc[0])

    def test_no_look_ahead(self):
        path = np.r_[np.full(10, 100.0), 79.0, np.linspace(90, 130, H - 10)]
        k = 10
        r, hit = st.stop_return(path, 0.20)
        self.assertTrue(hit)
        r_before, hit_before = st.stop_return(np.r_[path[:k], 100.0], 0.20)   # closes up to k-1 only
        self.assertFalse(hit_before)
        changed = path.copy()
        changed[k + 2:] = 1.0                                   # rewrite everything after the exit day
        self.assertEqual(st.stop_return(changed, 0.20), (r, True))
        self.assertAlmostEqual(r, (path[k + 1] / 100 - 1) * 100)

    def test_trigger_on_last_day_is_the_scheduled_exit(self):
        path = np.r_[np.full(H, 100.0), 50.0]
        self.assertEqual(st.stop_return(path, 0.20), (-50.0, False))

    def test_costs_are_applied(self):
        px, picks = one_pick(np.full(H + 1, 100.0))
        out = st.apply_stop(picks, px, px, 0.20)
        self.assertGreater(out["cost_pct"].iloc[0], 0.2)       # 0.1% STT each way plus slippage
        self.assertAlmostEqual(out["net_alpha"].iloc[0], -out["cost_pct"].iloc[0])


class Decision(unittest.TestCase):
    def row(self, mean, worst):
        return {"mean_net_alpha": mean, "worst_trade_net_return": worst}

    def test_widest_qualifying_stop_is_adopted(self):
        t = [self.row(5.0, -70), self.row(4.9, -30), self.row(4.6, -35), self.row(4.4, -40)]
        self.assertEqual(st.decide(t)[0], 0.25)                 # -30% costs 0.6 > 0.5

    def test_fallback_is_insurance(self):
        t = [self.row(5.0, -70), self.row(3.0, -30), self.row(4.0, -35), self.row(5.0, -70)]
        level, text = st.decide(t)
        self.assertEqual(level, rc.STOP_INSURANCE_LEVEL)
        self.assertIn("insurance", text)


class Baseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        cls.tmp = tempfile.mkdtemp()
        shutil.copy(ROOT / "historical_backtest_v3.py", cls.tmp)
        os.chdir(cls.tmp)
        Path("data").mkdir()
        market().to_csv("data/market_cache.csv.gz")
        sys.modules.pop("historical_backtest_v3", None)
        sys.path.insert(0, cls.tmp)
        e = importlib.import_module("historical_backtest_v3")
        _, nifty, s = e.load_market_data()
        cls.args = s["px"], s["exit_px"], s["rows"], s["breadth"], nifty["Close"]

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.cwd)
        sys.path.remove(cls.tmp)

    def test_no_stop_equals_extended_tests_12_1_breadth(self):
        px, exit_px, rows, breadth, nifty = self.args
        snaps, picks, _, _, mv = xt.monkey_section(*self.args)
        _, net, win, t, _ = pit.verdict_for(picks, snaps, mv)
        table, _ = st.run_all(*self.args)
        base = table[0]
        self.assertGreater(len(picks), 0)
        self.assertEqual(base["trades"], len(picks))
        self.assertAlmostEqual(base["mean_net_alpha"], round(net, 2))
        self.assertAlmostEqual(base["win_rate_pct"], round(win, 1))
        self.assertAlmostEqual(base["t_nonoverlap"], round(t, 2))
        self.assertEqual(base["stopped_pct"], 0)
        mine = st.apply_stop(st.baseline_picks(*self.args), px, exit_px, None)
        np.testing.assert_allclose(mine["stock_return"].values, picks["stock_return"].values)
        self.assertEqual(len(table), 1 + len(rc.STOP_LEVELS))


if __name__ == "__main__":
    unittest.main()
