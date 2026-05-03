import unittest

from src.plot_probability_scale import format_percent, probability_tick_formatter


class PlotFormattingTests(unittest.TestCase):
    def test_format_percent_keeps_rare_events_visible(self) -> None:
        self.assertEqual(format_percent(69 / 1_374_687), "0.0050%")

    def test_probability_tick_formatter_avoids_zero_percent_ticks(self) -> None:
        self.assertEqual(probability_tick_formatter(0.00001, 0), "0.001%")


if __name__ == "__main__":
    unittest.main()
