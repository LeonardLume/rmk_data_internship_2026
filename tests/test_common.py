import unittest

from src.common import (
    canonical_age_group,
    canonical_place,
    canonical_sex,
    format_odds_label,
    format_probability,
)


class CommonTests(unittest.TestCase):
    def test_canonical_age_group_preserves_ranges(self) -> None:
        self.assertEqual(canonical_age_group("25-29"), "25-29")
        self.assertEqual(canonical_age_group("100 and older"), "100_plus")

    def test_canonical_age_group_85_plus(self) -> None:
        self.assertEqual(canonical_age_group("85 and older"), "85_plus")

    def test_canonical_sex_maps_bilingual_values(self) -> None:
        self.assertEqual(canonical_sex("Boys and girls"), "total")
        self.assertEqual(canonical_sex("Females"), "female")

    def test_canonical_place_maps_estonian_and_english(self) -> None:
        self.assertEqual(canonical_place("Kogu Eesti"), "whole_country")
        self.assertEqual(canonical_place("HARJU COUNTY"), "harju_county")

    def test_format_probability_does_not_round_small_values_to_zero(self) -> None:
        self.assertEqual(format_probability(0.00005), "0.00005")

    def test_format_odds_label_reads_like_language(self) -> None:
        self.assertEqual(format_odds_label(1.96), "about 1 in 2")
        self.assertEqual(format_odds_label(25.7), "about 1 in 26")
        self.assertEqual(format_odds_label(19_923), "about 1 in 19,923")


if __name__ == "__main__":
    unittest.main()
