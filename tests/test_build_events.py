import unittest

from src.build_events import Event, latest_common_year, matching_rows


class BuildEventsTests(unittest.TestCase):
    def test_latest_common_year_returns_max_overlap(self) -> None:
        self.assertEqual(latest_common_year({2022, 2023, 2024}, {2021, 2024}), 2024)

    def test_matching_rows_requires_exact_match(self) -> None:
        rows = [
            {"year": "2024", "age_group": "20-24", "value": "36"},
            {"year": "2024", "age_group": "20-29", "value": "100"},
        ]

        self.assertEqual(
            matching_rows(rows, year=2024, age_group="20-24"),
            [{"year": "2024", "age_group": "20-24", "value": "36"}],
        )

    def test_event_probability_calculation(self) -> None:
        row = Event(
            event_id="example",
            label="Example event",
            category="example",
            estimate_type="exact_probability",
            numerator=25,
            denominator=100,
            year=2024,
            notes="Small fixture.",
        ).as_row()

        self.assertEqual(row["probability"], "0.25")
        self.assertEqual(row["odds_1_in"], "about 1 in 4")
        self.assertEqual(row["estimate_type"], "exact_probability")


if __name__ == "__main__":
    unittest.main()
