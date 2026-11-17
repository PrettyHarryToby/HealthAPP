import unittest
from datetime import date, datetime

from sqlalchemy import and_

from database import _expression_filter, _model_document, _model_from_document, _to_storage
from models import Patient, VitaminLevels


class MongoDatabaseTests(unittest.TestCase):
    def test_date_fields_round_trip_as_iso_strings(self):
        patient = Patient(
            id=3,
            patient_id="P-003",
            first_name="Ada",
            last_name="Lovelace",
            date_of_birth=date(1815, 12, 10),
            created_at=datetime(2026, 1, 2, 3, 4, 5),
        )

        document = _model_document(patient)
        restored = _model_from_document(Patient, document)

        self.assertEqual(document["date_of_birth"], "1815-12-10")
        self.assertEqual(document["created_at"], "2026-01-02T03:04:05")
        self.assertEqual(restored.date_of_birth, patient.date_of_birth)
        self.assertEqual(restored.created_at, patient.created_at)

    def test_date_and_boolean_filters_translate_to_mongo(self):
        cutoff = date(2026, 1, 1)
        expression = and_(
            VitaminLevels.patient_id == 12,
            VitaminLevels.test_date >= cutoff,
        )

        self.assertEqual(
            _expression_filter(VitaminLevels, expression),
            {"$and": [
                {"patient_id": 12},
                {"test_date": {"$gte": "2026-01-01"}},
            ]},
        )

    def test_datetime_default_for_date_column_is_normalized(self):
        created_at = datetime(2026, 4, 5, 6, 7, 8)

        self.assertEqual(_to_storage(VitaminLevels, "test_date", created_at), "2026-04-05")

    def test_unsupported_filter_operator_fails_explicitly(self):
        with self.assertRaises(TypeError):
            _expression_filter(VitaminLevels, VitaminLevels.patient_id.in_([1, 2]))


if __name__ == "__main__":
    unittest.main()
