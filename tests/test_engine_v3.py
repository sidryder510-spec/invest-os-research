"""Engine v3 on a synthetic market, then every study end to end with the real hash check."""
import contextlib, importlib, io, json, os, shutil, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import research_config as rc

N_STOCKS = 60


def market(seed=1, late=("LATE",)):
    """Upward-drifting stocks (so breadth often clears 80%), one listed late, plus ^NSEI."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", "2016-12-30")
    drift = rng.uniform(0.0006, 0.0016, N_STOCKS)
    cols = {}
    for i in range(N_STOCKS):
        r = rng.normal(drift[i], 0.008, len(idx))
        cols["S%02d.NS" % i] = 100 * np.exp(np.cumsum(r))
    for name in late:
        s = 100 * np.exp(np.cumsum(rng.normal(0.004, 0.01, len(idx))))   # best momentum once listed
        s[:900] = np.nan
        cols[name + ".NS"] = s
    cols["^NSEI"] = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, len(idx))))
    return pd.DataFrame(cols, index=idx)


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        for f in ["historical_backtest_v3.py"]:
            shutil.copy(ROOT / f, self.tmp)
        os.chdir(self.tmp)
        Path("data").mkdir()
        self.closes = market()
        self.closes.to_csv("data/market_cache.csv.gz")
        sys.modules.pop("historical_backtest_v3", None)
        self.e = importlib.import_module("historical_backtest_v3")
        self.stock, self.nifty, self.st = self.e.load_market_data()

    def tearDown(self):
        os.chdir(self.cwd)
        sys.modules.pop("historical_backtest_v3", None)

    def test_snapshots_trade_only_when_breadth_passes(self):
        snaps = self.e.get_snapshot_dates(self.nifty)
        self.assertGreater(len(snaps), 20)
        self.assertTrue((self.st["breadth"].reindex(snaps) >= rc.BREADTH_THRESHOLD).all())
        pos = [self.nifty.index.get_loc(s) for s in snaps]
        self.assertTrue(all((p - rc.MIN_HISTORY) % rc.SNAPSHOT_INTERVAL == 0 for p in pos))
        self.assertLessEqual(max(pos) + 1 + rc.HOLDING_DAYS, len(self.nifty) - 1)

    def test_candidates_ranked_eligible_and_late_listing_waits(self):
        for snap in self.e.get_snapshot_dates(self.nifty):
            c = self.e.generate_historical_candidates(snap, self.stock, self.nifty)
            self.assertEqual(len(c), rc.TOP_N)
            scores = [x["score"] for x in c]
            self.assertEqual(scores, sorted(scores, reverse=True))
            for x in c:
                self.assertGreaterEqual(int((self.stock[x["symbol"]].index <= snap).sum()), rc.MIN_HISTORY)

    def test_no_look_ahead(self):
        snap = self.e.get_snapshot_dates(self.nifty)[10]
        before = self.e.generate_historical_candidates(snap, self.stock, self.nifty)
        future = self.closes.copy()
        future.loc[future.index > snap, [c for c in future.columns if c != "^NSEI"]] *= np.random.default_rng(9).uniform(
            0.2, 5, (int((future.index > snap).sum()), N_STOCKS + 1))
        future.to_csv("data/market_cache.csv.gz")
        stock, nifty, _ = self.e.load_market_data()
        self.assertEqual(before, self.e.generate_historical_candidates(snap, stock, nifty))

    def test_trade_dump_uses_next_day_entry(self):
        df = self.e.export_trade_dump("trade_dump.csv")
        row = df.iloc[0]
        i = self.nifty.index.get_loc(pd.Timestamp(row["date"]))
        entry, exit_ = self.nifty.index[i + 1], self.nifty.index[i + 1 + rc.HOLDING_DAYS]
        px = self.closes[row["symbol"] + ".NS"]
        self.assertAlmostEqual(row["stock_return"], (px[exit_] / px[entry] - 1) * 100, places=3)
        n = self.closes["^NSEI"]
        self.assertAlmostEqual(row["nifty_return"], (n[exit_] / n[entry] - 1) * 100, places=3)
        self.assertAlmostEqual(row["alpha"], row["stock_return"] - row["nifty_return"], places=3)

    def test_full_pipeline_with_real_hash_check(self):
        for f in ["research_config.py", "research_utils.py", "study_00_engine_validation.py",
                  "study_01_eligibility.py", "study_02_concentration.py",
                  "study_05_transaction_costs.py", "study_06_walk_forward.py"]:
            shutil.copy(ROOT / f, self.tmp)
        shutil.copytree(ROOT / "nse_exec", Path(self.tmp) / "nse_exec")
        self.e.export_trade_dump("trade_dump.csv")
        sys.path.insert(0, self.tmp)
        try:
            for name in ["study_00_engine_validation", "study_01_eligibility", "study_02_concentration",
                         "study_05_transaction_costs", "study_06_walk_forward"]:
                for m in [name, "research_utils", "research_config"]:
                    sys.modules.pop(m, None)
                mod = importlib.import_module(name)
                with contextlib.redirect_stdout(io.StringIO()):
                    mod.main()
                meta = json.loads(Path(mod.OUTPUT_META).read_text(encoding="utf-8"))
                self.assertIn(meta["verdict"], {"PASS", "CONDITIONAL", "FAIL"}, name)
                self.assertEqual(meta["engine_version"], "3.0.0")
            s00 = json.loads(Path("research/metadata/study_00_metadata.json").read_text())
            s01 = json.loads(Path("research/metadata/study_01_metadata.json").read_text())
            self.assertEqual(s00["verdict"], "PASS", s00["summary"])
            self.assertEqual(s01["verdict"], "PASS", s01["summary"])
        finally:
            sys.path.remove(self.tmp)
            for m in ["research_utils", "research_config"]:
                sys.modules.pop(m, None)


if __name__ == "__main__":
    unittest.main()
