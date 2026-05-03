import unittest

from src.common import format_odds_label
from src.plot_probability_scale import (
    format_percent,
    odds_label_for_row,
    probability_tick_formatter,
)


class PlotTests(unittest.TestCase):
    def test_format_percent_keeps_rare_events_visible(self) -> None:
        self.assertEqual(format_percent(69 / 1_374_687), "0.0050%")

    def test_probability_tick_formatter_avoids_zero_percent_ticks(self) -> None:
        self.assertEqual(probability_tick_formatter(0.00001, 0), "0.001%")

    def test_odds_label_for_plot_is_human_readable(self) -> None:
        self.assertEqual(format_odds_label(637.61), "about 1 in 638")

    def test_plot_prefers_csv_odds_label(self) -> None:
        row = {"odds_1_in": "about 1 in 19,923"}
        self.assertEqual(odds_label_for_row(row, 0.00005), "about 1 in 19,923")


if __name__ == "__main__":
    unittest.main()
