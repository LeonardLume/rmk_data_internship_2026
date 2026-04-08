import unittest

from stat_ee.pipeline import (
    TableRequest,
    build_query_payload,
    dimension,
    normalize_label,
    resolve_value_code,
    resolve_variable,
)


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metadata = {
            "title": "Example table",
            "variables": [
                {
                    "code": "Aasta",
                    "text": "Year",
                    "values": ["2024", "2025"],
                    "valueTexts": ["2024", "2025"],
                    "time": True,
                },
                {
                    "code": "Sugu",
                    "text": "Sex",
                    "values": ["T", "M", "F"],
                    "valueTexts": ["Males and females", "Males", "Females"],
                },
                {
                    "code": "Elukoht",
                    "text": "Place of residence",
                    "values": ["TOTAL", "37"],
                    "valueTexts": ["Whole country", "Harju county"],
                },
                {
                    "code": "Vanuseruhm",
                    "text": "Age group",
                    "values": ["0-4", "5-9"],
                    "valueTexts": ["0-4", "5-9"],
                },
            ],
        }

    def test_normalize_label_strips_punctuation(self) -> None:
        self.assertEqual(normalize_label("Child's birth weight, grams"), "child s birth weight grams")

    def test_resolve_variable_matches_text_alias(self) -> None:
        variable = resolve_variable(self.metadata, ["Year"])
        self.assertEqual(variable["code"], "Aasta")

    def test_resolve_variable_matches_code_alias(self) -> None:
        variable = resolve_variable(self.metadata, ["Elukoht"])
        self.assertEqual(variable["text"], "Place of residence")

    def test_resolve_value_code_matches_value_text(self) -> None:
        sex_variable = resolve_variable(self.metadata, ["Sex"])
        value_code = resolve_value_code(sex_variable, ["Both sexes", "Males and females"])
        self.assertEqual(value_code, "T")

    def test_build_query_payload_uses_resolved_codes(self) -> None:
        table_request = TableRequest(
            table_id="RV0282U",
            output_name="example.csv",
            description="Example",
            selections=(
                dimension(["Year"], "top", raw_values=["1"]),
                dimension(["Sex"], "item", value_alias_groups=[["Males and females"]]),
                dimension(
                    ["Place of residence"],
                    "item",
                    value_alias_groups=[["Whole country"], ["Harju county"]],
                ),
                dimension(["Age group"], "all", raw_values=["*"]),
            ),
        )

        payload = build_query_payload(self.metadata, table_request)

        self.assertEqual(payload[0]["code"], "Aasta")
        self.assertEqual(payload[0]["selection"]["filter"], "top")
        self.assertEqual(payload[1]["code"], "Sugu")
        self.assertEqual(payload[1]["selection"]["values"], ["T"])
        self.assertEqual(payload[2]["code"], "Elukoht")
        self.assertEqual(payload[2]["selection"]["values"], ["TOTAL", "37"])
        self.assertEqual(payload[3]["code"], "Vanuseruhm")
        self.assertEqual(payload[3]["selection"]["values"], ["*"])


if __name__ == "__main__":
    unittest.main()
