import unittest

from src.common import canonical_age_group, canonical_place, canonical_sex


class CommonTests(unittest.TestCase):
    def test_canonical_age_group_preserves_ranges(self) -> None:
        self.assertEqual(canonical_age_group("25-29"), "25-29")
        self.assertEqual(canonical_age_group("100 and older"), "100_plus")

    def test_canonical_sex_maps_bilingual_values(self) -> None:
        self.assertEqual(canonical_sex("Boys and girls"), "total")
        self.assertEqual(canonical_sex("Females"), "female")

    def test_canonical_place_maps_estonian_and_english(self) -> None:
        self.assertEqual(canonical_place("Kogu Eesti"), "whole_country")
        self.assertEqual(canonical_place("HARJU COUNTY"), "harju_county")


if __name__ == "__main__":
    unittest.main()
