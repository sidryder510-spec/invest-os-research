"""Paper trading simulated week by week on the synthetic market from test_engine_v3."""
import importlib, os, shutil, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import research_config as rc
from test_engine_v3 import market


class PaperTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        shutil.copy(ROOT / "historical_backtest_v3.py", self.tmp)
        os.chdir(self.tmp)
        Path("data").mkdir()
        self.closes = market()
        self.closes.to_csv("data/market_cache.csv.gz")
        for m in ("historical_backtest_v3", "paper_trade"):
            sys.modules.pop(m, None)
        sys.path.insert(0, self.tmp)
        self.e = importlib.import_module("historical_backtest_v3")
        self.pt = importlib.import_module("paper_trade")
        self.pt.e = self.e
        self.stock, self.nifty, self.st = self.e.load_market_data()
        self.gen = lambda d: self.e.generate_historical_candidates(d, self.stock, self.nifty, rc.TOP_N)
        self.alerts = []

    def tearDown(self):
        os.chdir(self.cwd)
        sys.path.remove(self.tmp)

    def run_weeks(self, start, end, px=None):
        px = self.st["px"] if px is None else px
        for t in range(start, end, 5):   # cumulative breadth/score panels are causal, so slicing = running on that day
            before = self.pt.read(self.pt.LEDGER, self.pt.COLS)
            weekly = self.pt.read(self.pt.WEEKLY, self.pt.WEEKLY_COLS)
            ledger, weekly = self.pt.step(before, weekly, self.nifty.index[:t + 1], px, self.st["exit_px"],
                                          self.st["breadth"], self.nifty["Close"], self.gen)
            self.alerts.append(self.pt.alerts(before, ledger))
            rc.PAPER_DIR.mkdir(exist_ok=True)
            ledger.to_csv(self.pt.LEDGER, index=False)
            weekly.to_csv(self.pt.WEEKLY, index=False)
        return ledger, weekly

    def test_signals_fill_and_close_correctly(self):
        n = len(self.nifty)
        ledger, weekly = self.run_weeks(n - 400, n)
        self.assertEqual(weekly["signal_date"].nunique(), len(weekly))       # one signal per run
        closed = ledger[ledger["status"] == "CLOSED"]
        self.assertGreater(len(closed), 20)
        idx = self.nifty.index
        for _, r in closed.head(10).iterrows():
            i = idx.get_loc(pd.Timestamp(r["signal_date"]))
            entry, exit_ = idx[i + 1], idx[i + 1 + rc.HOLDING_DAYS]
            self.assertEqual(r["entry_date"], entry.strftime("%Y-%m-%d"))
            self.assertEqual(r["exit_date"], exit_.strftime("%Y-%m-%d"))
            px = self.closes[r["symbol"] + ".NS"]
            self.assertAlmostEqual(float(r["stock_return"]), (px[exit_] / px[entry] - 1) * 100, places=3)
            self.assertAlmostEqual(float(r["net_alpha"]),
                                   float(r["alpha"]) - float(r["cost_pct"]), places=3)
        text = "\n".join(a for a in self.alerts if a)
        self.assertEqual(text.count("BUY trigger"), weekly["traded"].eq("True").sum())
        self.assertEqual(text.count("SELL trigger"), len(closed))
        # nothing closes early: open trades are all younger than the holding period
        for _, r in ledger[ledger["status"] == "OPEN"].iterrows():
            self.assertGreater(idx.get_loc(pd.Timestamp(r["entry_date"])) + rc.HOLDING_DAYS, n - 5)

    def test_missing_price_stays_open(self):
        n = len(self.nifty)
        self.run_weeks(n - 200, n - 150)
        held = pd.read_csv(self.pt.LEDGER)["symbol"].iloc[0]
        px = self.st["px"].drop(columns=[held])
        ledger, _ = self.run_weeks(n - 145, n, px=px)
        self.assertFalse((ledger[ledger["symbol"] == held]["status"] == "CLOSED").any())

    def test_uat_replay_fires_both_triggers(self):
        n = len(self.nifty)
        start, end = self.nifty.index[n - 500], self.nifty.index[n - 300]
        self.pt.uat(str(start.date()), str(end.date()), Path("uat"))
        led = pd.read_csv("uat/ledger.csv")
        self.assertTrue((led["signal_date"] <= str(end.date())).all())     # no signals after the window
        self.assertFalse(led["status"].isin(["PENDING", "OPEN"]).any())    # replay ran until all closed
        log = Path("uat/trigger_log.md").read_text()
        self.assertGreater(log.count("[UAT] BUY trigger"), 0)
        self.assertEqual(log.count("[UAT] SELL trigger"), len(led))
        self.assertIn("UAT finished", Path("paper/alert.md").read_text())
        self.assertIn("functional test only", Path("uat/SCORECARD.md").read_text())

    def test_scorecard_rule(self):
        rows = lambda weeks, net: pd.DataFrame({
            "signal_date": ["2027-%02d-01" % (w % 12 + 1) + str(w) for w in range(weeks)],
            "status": "CLOSED", "net_alpha": [str(x) for x in net]})
        weekly = pd.DataFrame([["2027-01-04", "85.0", "True", "A B"]], columns=["signal_date", "breadth", "traded", "picks"])
        self.assertTrue(self.pt.scorecard(rows(10, [5] * 10), weekly)[0].startswith("TOO EARLY"))
        self.assertEqual(self.pt.scorecard(rows(30, [5] * 20 + [-3] * 10), weekly)[0], "PASS")
        self.assertEqual(self.pt.scorecard(rows(30, [5] * 15 + [-3] * 15), weekly)[0], "FAIL")   # 50% win rate


if __name__ == "__main__":
    unittest.main()
