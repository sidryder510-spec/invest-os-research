"""Studies 02, 05 and 06 on a synthetic trade_dump.csv (the frozen engine is not in the repo)."""
import contextlib, io, json, os, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import research_config
import research_utils as ru
import study_02_concentration as s02
import study_05_transaction_costs as s05
import study_06_walk_forward as s06


def dump(years=range(2015, 2025), alpha=3.0, star_share=0.0, seed=0):
    """Weekly snapshots of 5 distinct picks (as Study 00 requires). Each week holds
    EICHERMOT with probability 1-(1-star_share)^5."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.date_range("%d-01-05" % min(years), "%d-12-25" % max(years), freq="7D"):
        syms = ["S%03d" % i for i in rng.choice(200, 5, replace=False)]
        if rng.random() < 1 - (1 - star_share) ** 5:
            syms[0] = "EICHERMOT"
        for rank, sym in enumerate(syms, 1):
            nifty = rng.normal(2, 5)
            a = rng.normal(alpha, 8)
            rows.append({"date": d, "symbol": sym, "rank": rank, "score": 1.0,
                         "stock_return": nifty + a, "nifty_return": nifty, "alpha": a})
    return pd.DataFrame(rows)


class Costs(unittest.TestCase):
    def test_round_trip_cost_matches_hand_calc(self):
        # Rs 1L flat: buy 100 STT + 15 stamp + 3.07 exch + 0.1 SEBI + 0.57 GST = 118.74;
        # sell 100 + 15.34 DP + 3.07 + 0.1 + 0.57 = 119.08 -> 0.2378%, plus 0.1% slippage x2
        self.assertAlmostEqual(s05.round_trip_cost_pct("INFY", 0.0), 0.4378, places=3)
        self.assertAlmostEqual(s05.round_trip_cost_pct("EICHERMOT", 0.0), 0.7378, places=3)

    def test_net_alpha_is_gross_minus_cost(self):
        df = s05.add_net(dump(years=[2020]))
        np.testing.assert_allclose(df["alpha"] - df["net_alpha"], df["cost_pct"], atol=1e-9)

    def test_overlap_is_removed_for_t_stat(self):
        df = s05.add_net(dump(years=[2015, 2016, 2017]))
        n, _ = s05.non_overlapping_tstat(df)
        self.assertEqual(n, -(-df["date"].nunique() // 12))


class Verdicts(unittest.TestCase):
    def test_concentration_locked_criteria_cannot_fail(self):
        # EICHERMOT in ~95% of weeks still passes the locked tests: the protocol flaw the report warns about.
        _, s = s02.analyse(dump(star_share=0.45))
        self.assertEqual(s["top1_symbol"], "EICHERMOT")
        self.assertLessEqual(s["top1_share_pct"], 20.0)
        self.assertEqual(s["max_possible_share_pct"], 20.0)
        self.assertEqual(s02.determine_verdict(s), "PASS")
        self.assertGreater(s["top1_weeks_present_pct"], 90)
        _, s = s02.analyse(dump(star_share=0.0))
        self.assertLess(s["watch_weeks_present_pct"], 1)
        self.assertEqual(s02.determine_verdict(s), "PASS")

    def test_hhi_bands(self):
        base = {"hhi": 1500, "top1_share_pct": 10}
        self.assertEqual(s02.determine_verdict(dict(base, hhi=2500)), "CONDITIONAL")
        self.assertEqual(s02.determine_verdict(dict(base, hhi=3500)), "FAIL")

    def test_costs(self):
        base = {"mean_net_alpha": 2.5, "net_win_rate_pct": 60}
        self.assertEqual(s05.determine_verdict(base), "PASS")
        self.assertEqual(s05.determine_verdict(dict(base, net_win_rate_pct=52)), "CONDITIONAL")
        self.assertEqual(s05.determine_verdict(dict(base, mean_net_alpha=0.4)), "FAIL")
        self.assertEqual(s05.determine_verdict(dict(base, net_win_rate_pct=49)), "FAIL")

    def test_walk_forward(self):
        good = s06.summarise(s06.windows(s05.add_net(dump(alpha=4.0))))
        self.assertEqual(s06.determine_verdict(good), "PASS")
        bad = s06.summarise(s06.windows(s05.add_net(dump(alpha=0.0))))
        self.assertEqual(s06.determine_verdict(bad), "FAIL")
        gap = s06.summarise(s06.windows(s05.add_net(dump(years=range(2015, 2024), alpha=4.0))))
        self.assertEqual(gap["windows_with_data"], 9)
        self.assertEqual(gap["positive_windows"], 9)          # the empty year is not positive
        self.assertEqual(s06.determine_verdict(gap), "PASS")
        sparse = s06.summarise(s06.windows(s05.add_net(dump(years=range(2015, 2021), alpha=4.0))))
        self.assertEqual(s06.determine_verdict(sparse), "CONDITIONAL")  # 6 of 10 positive


class Study00(unittest.TestCase):
    def test_study00_noncritical_failure_is_conditional_not_fatal(self):
        import study_00_engine_validation as s00
        checks = {k: {"passed": True, "detail": ""} for k in s00.CRITICAL_CHECKS}
        checks["Weekly snapshot spacing"] = {"passed": False, "detail": "breadth gaps"}
        self.assertEqual(s00.determine_verdict(checks), "CONDITIONAL")
        checks["No duplicate trades"] = {"passed": False, "detail": "dupes"}
        self.assertEqual(s00.determine_verdict(checks), "FAIL")


class EndToEnd(unittest.TestCase):
    """Run each study's main() the way you would, in a temp folder."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        os.chdir(self.tmp)
        dump(alpha=3.0, star_share=0.3).to_csv("trade_dump.csv", index=False)
        self.real_hash = ru.verify_engine_hash
        ru.verify_engine_hash = lambda *a, **k: "0" * 64

    def tearDown(self):
        ru.verify_engine_hash = self.real_hash
        os.chdir(self.cwd)

    def test_all_three_write_artifacts(self):
        for mod in (s02, s05, s06):
            with contextlib.redirect_stdout(io.StringIO()):
                mod.main()
            meta = json.loads(Path(mod.OUTPUT_META).read_text(encoding="utf-8"))
            self.assertIn(meta["verdict"], {"PASS", "CONDITIONAL", "FAIL"}, mod.STUDY_ID)
            self.assertEqual(meta["config_version"], research_config.CONFIG_VERSION)
            self.assertTrue(Path(mod.OUTPUT_CSV).exists() and Path(mod.OUTPUT_REPORT).exists())

    def test_missing_dump_is_fatal(self):
        os.remove("trade_dump.csv")
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            s05.main()


if __name__ == "__main__":
    unittest.main()
