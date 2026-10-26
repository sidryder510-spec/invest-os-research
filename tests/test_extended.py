"""Extended tests (monkey, robustness) and the point-in-time bhavcopy pipeline, offline."""
import importlib, io, os, shutil, sys, tempfile, unittest, zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import research_config as rc
import extended_tests as xt
import pit_backtest as pit
from test_engine_v3 import market


class OnSyntheticMarket(unittest.TestCase):
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
        cls.e = importlib.import_module("historical_backtest_v3")
        cls.stock, cls.nifty, cls.st = cls.e.load_market_data()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.cwd)
        sys.path.remove(cls.tmp)

    def args(self):
        return self.st["px"], self.st["exit_px"], self.st["rows"], self.st["breadth"], self.nifty["Close"]

    def test_12_1_with_breadth_reproduces_the_engine(self):
        dump = self.e.export_trade_dump("trade_dump.csv")
        _, picks, _, _, _ = xt.monkey_section(*self.args())
        mine = picks.assign(date=picks["date"].dt.strftime("%Y-%m-%d")).groupby("date")["symbol"].apply(set)
        theirs = dump.groupby("date")["symbol"].apply(set)
        self.assertEqual(mine.to_dict(), theirs.to_dict())

    def test_monkey_cannot_be_beaten_by_luck_but_an_oracle_beats_it(self):
        px, exit_px, rows, breadth, nifty = self.args()
        fwd = xt.forward_returns(px, exit_px)
        nfwd = (nifty.shift(-(1 + rc.HOLDING_DAYS)) / nifty.shift(-1) - 1) * 100
        pos = xt.snapshot_positions(len(px), breadth, True)
        elig = xt.eligibility(px, rows, xt.momentum(px, 252))
        oracle, _ = xt.run(fwd, elig, fwd, nfwd, pos)              # picks the future winners
        p, sims = xt.monkey(elig, fwd, nfwd, pos, oracle["alpha"].mean())
        self.assertEqual(p, 0.0)
        self.assertEqual(len(sims), rc.MONKEY_RUNS)
        median_alpha = float(np.median(sims))                      # a typical monkey sits mid-pack
        p_mid, _ = xt.monkey(elig, fwd, nfwd, pos, median_alpha)
        self.assertAlmostEqual(p_mid, 0.5, delta=0.05)

    def test_robustness_has_six_variants_and_a_verdict(self):
        table, positive, verdict = xt.robustness(*self.args())
        self.assertEqual(len(table), 6)
        self.assertIn(verdict, {"PASS", "CONDITIONAL", "FAIL"})
        self.assertEqual(positive, int((table["selection_edge"] > 0).sum()))

    def test_report_renders(self):
        text, v, snaps, picks = xt.report("synthetic", *self.args())
        self.assertIn("Random-monkey test", text)
        self.assertEqual(len(picks), len(snaps) * rc.TOP_N)


def zipped(name, text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, text)
    return buf.getvalue()


class Bhavcopy(unittest.TestCase):
    def test_parse_old_format(self):
        raw = zipped("cm01JAN2015bhav.csv",
                     "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,\n"
                     "INFY,EQ,1,1,1,100,1,98,10,1000,01-JAN-2015,5,X,\n"
                     "INFY,N1,1,1,1,5,1,5,10,9,01-JAN-2015,5,X,\n"
                     "WEAK,BE,1,1,1,20,1,21,10,50,01-JAN-2015,5,X,\n")
        df = pit.parse(raw).set_index("symbol")
        self.assertEqual(sorted(df.index), ["INFY", "WEAK"])        # N1 (bond) series dropped, BE kept
        self.assertEqual(df.at["INFY", "close"], 100)

    def test_parse_udiff_format(self):
        raw = zipped("BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv",
                     "TradDt,TckrSymb,SctySrs,ClsPric,PrvsClsgPric,TtlTrfVal\n"
                     "2024-07-08,INFY,EQ,1650,1640,5000000\n2024-07-08,GOLDBEES,EQ,60,59,100\n")
        df = pit.parse(raw).set_index("symbol")
        self.assertEqual(df.at["INFY", "prevclose"], 1640)

    def test_urls_switch_format_on_the_cutover_date(self):
        self.assertIn("/historical/EQUITIES/2015/JAN/cm02JAN2015bhav", pit.urls(pd.Timestamp("2015-01-02"))[0])
        self.assertIn("BhavCopy_NSE_CM_0_0_0_20240708", pit.urls(pd.Timestamp("2024-07-08"))[0])


class Panels(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        os.chdir(tempfile.mkdtemp())
        pit.BHAV_DIR.mkdir(parents=True)
        self.dates = pd.bdate_range("2020-01-01", periods=300)
        for i, d in enumerate(self.dates):
            rows = []
            split = 1 if i < 150 else 0.5                          # SPLIT: 1:2 split on day 150
            rows.append(("SPLIT", 100 * split * (1.001 ** i), 100 * split * (1.001 ** (i - 1)), 1e9))
            if i < 200:                                              # GONE: stops trading on day 200
                rows.append(("GONE", 50 - 0.1 * i, 50 - 0.1 * (i - 1), 5e8))
            if i >= 100:                                             # LATE: listed on day 100
                rows.append(("LATE", 10.0, 9.0 if i == 100 else 10.0, 1e10 if i >= 120 else 1.0))
            pd.DataFrame(rows, columns=["symbol", "close", "prevclose", "value"]).to_csv(
                pit.BHAV_DIR / (d.strftime("%Y%m%d") + ".csv"), index=False)

    def tearDown(self):
        os.chdir(self.cwd)

    def test_split_is_adjusted_and_delisted_exits_at_last_price(self):
        old = pit.PIT_UNIVERSE_SIZE
        pit.PIT_UNIVERSE_SIZE = 2
        try:
            px, exit_px, rows, member, breadth, big, n = pit.panels(list(self.dates))
        finally:
            pit.PIT_UNIVERSE_SIZE = old
        s = px["SPLIT"]
        self.assertAlmostEqual(s.iloc[150] / s.iloc[149], 1.001, places=6)   # no fake -50% day
        self.assertEqual(big, 0)
        self.assertAlmostEqual(exit_px["GONE"].iloc[-1], exit_px["GONE"].iloc[199])
        self.assertTrue(np.isnan(px["GONE"].iloc[-1]))                        # not buyable after it stops
        self.assertTrue(np.isnan(px["LATE"].iloc[99]))
        self.assertEqual(px["LATE"].iloc[100], 1.0)                           # listing day anchors the chain
        self.assertEqual(n, 3)
        # LATE's traded value jumps on day 120; with a lagged average it can't be a member that same day
        self.assertFalse(member["LATE"].iloc[120])
        self.assertTrue(member["LATE"].iloc[-1])
        self.assertFalse(member["GONE"].iloc[-1])


if __name__ == "__main__":
    unittest.main()
