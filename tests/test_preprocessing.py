"""Regression checks against raw timestamps and an isolated notebook execution."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import nbformat
from nbclient import NotebookClient
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TARGET = "target_Appliances_t_plus_60m"
DATES = ["observation_time", "forecast_timestamp"]


class PreprocessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        raw_dir = root / "data" / "raw"
        raw_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "data/raw/energydata_complete.csv", raw_dir)
        cls.raw = pd.read_csv(raw_dir / "energydata_complete.csv", parse_dates=["date"])
        cls.notebook = nbformat.read(ROOT / "notebooks/01_data_preparation.ipynb", as_version=4)
        nbformat.validate(cls.notebook)
        client = NotebookClient(cls.notebook, timeout=180, resources={"metadata": {"path": str(root)}})
        client.create_kernel_manager()
        client.km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
        client.execute()
        cls.output = root / "data" / "processed"
        cls.frames = {
            name: pd.read_csv(cls.output / f"energy_forecasting_h1_{name}.csv", parse_dates=DATES)
            for name in ("full", "train", "validation", "test")
        }
        cls.summary = json.loads((cls.output / "data_quality_summary.json").read_text(encoding="utf-8"))

    def test_raw_bytes_unchanged(self):
        expected = "2820bf712ad0275cb18b85a05250926100d8e65ebb9f4d2d016ca91ea152a25d"
        for root in (ROOT, Path(self.temp.name)):
            self.assertEqual(hashlib.sha256((root / "data/raw/energydata_complete.csv").read_bytes()).hexdigest(), expected)
        self.assertEqual(self.summary["source_sha256"], expected)

    def test_target_matches_raw_at_exact_future_timestamp(self):
        frame = self.frames["full"]
        raw_by_time = self.raw.set_index("date")
        np.testing.assert_array_equal(frame[TARGET], raw_by_time.loc[frame.forecast_timestamp, "Appliances"])
        np.testing.assert_array_equal(frame.Appliances_lag_0, raw_by_time.loc[frame.observation_time, "Appliances"])
        self.assertTrue(((frame.forecast_timestamp - frame.observation_time) == pd.Timedelta(hours=1)).all())
        self.assertEqual(len(frame), len(self.raw) - 6)

    def test_sensor_features_use_only_observation_time(self):
        frame = self.frames["full"]
        sensors = self.raw.columns.drop(["date", "Appliances", "rv1", "rv2"])
        pd.testing.assert_frame_equal(frame[list(sensors)], self.raw.loc[:len(frame) - 1, sensors])
        self.assertNotIn("rv1", frame)
        self.assertNotIn("rv2", frame)
        self.assertFalse(frame.isna().any().any())
        self.assertTrue(np.isfinite(frame.select_dtypes(include="number").to_numpy()).all())

    def test_no_future_labels_cross_partition_boundaries(self):
        train, validation, test = [self.frames[name] for name in ("train", "validation", "test")]
        self.assertLess(train.forecast_timestamp.max(), validation.observation_time.min())
        self.assertLess(validation.forecast_timestamp.max(), test.observation_time.min())
        self.assertTrue(set(train.forecast_timestamp).isdisjoint(validation.observation_time))
        self.assertTrue(set(validation.forecast_timestamp).isdisjoint(test.observation_time))
        full = self.frames["full"]
        self.assertEqual((full.split == "gap").sum(), 12)
        self.assertEqual(self.summary["purged_boundary_rows"], 12)
        self.assertEqual(self.summary["split_rows"], {"train": 13804, "validation": 1967, "test": 3946})
        for name in ("train", "validation", "test"):
            pd.testing.assert_frame_equal(self.frames[name], full[full.split == name].reset_index(drop=True))

    def test_calendar_features_follow_forecast_time(self):
        frame = self.frames["full"]
        hour = frame.forecast_timestamp.dt.hour + frame.forecast_timestamp.dt.minute / 60
        weekday = frame.forecast_timestamp.dt.dayofweek
        for prefix, value, period in (("hour", hour, 24), ("weekday", weekday, 7)):
            for suffix, function in (("sin", np.sin), ("cos", np.cos)):
                np.testing.assert_allclose(frame[f"forecast_{prefix}_{suffix}"], function(2 * np.pi * value / period), atol=1e-15)

    def test_checked_in_artifacts_match_fresh_execution(self):
        for name, generated in self.frames.items():
            checked_in = pd.read_csv(ROOT / f"data/processed/energy_forecasting_h1_{name}.csv", parse_dates=DATES)
            pd.testing.assert_frame_equal(generated, checked_in)
        checked_in = json.loads((ROOT / "data/processed/data_quality_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(self.summary, checked_in)
        self.assertTrue((Path(self.temp.name) / "reports/figures/01_daily_weekly_cycles.png").is_file())

    def test_quality_gate_rejects_invalid_inputs(self):
        cells = [cell.source for cell in self.notebook.cells if cell.cell_type == "code"]
        validation_code = next(source for source in cells if source.startswith("expected_columns ="))
        missing = self.raw.copy()
        missing.loc[0, "T1"] = np.nan
        infinite = self.raw.copy()
        infinite.loc[0, "T1"] = np.inf
        negative = self.raw.copy()
        negative.loc[0, "Appliances"] = -1
        invalid_date = self.raw.copy()
        invalid_date["date"] = invalid_date["date"].astype(str)
        invalid_date.loc[0, "date"] = "not-a-date"
        cases = {
            "missing": missing,
            "infinite": infinite,
            "negative_energy": negative,
            "invalid_timestamp": invalid_date,
            "missing_column": self.raw.drop(columns="T1"),
            "empty": self.raw.iloc[:0],
            "too_short": self.raw.iloc[:6],
            "duplicate": pd.concat([self.raw.iloc[:1], self.raw], ignore_index=True),
            "missing_interval": self.raw.drop(index=10),
            "unsorted": self.raw.iloc[::-1],
        }
        for name, raw in cases.items():
            with self.subTest(name=name), contextlib.redirect_stdout(io.StringIO()):
                namespace = {"raw": raw, "pd": pd, "np": np, "HORIZON_STEPS": 6,
                             "FREQUENCY": pd.Timedelta(minutes=10), "display": lambda *args: None}
                with self.assertRaises(AssertionError):
                    exec(validation_code, namespace)


if __name__ == "__main__":
    unittest.main()
