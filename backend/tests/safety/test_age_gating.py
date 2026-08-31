import unittest
import datetime
from app.safety.age_policy import AgePolicy

class TestAgeGatingSafety(unittest.TestCase):
    """Verifies that age calculation, platform eligibility, and parental consent gating behave correctly."""

    def test_age_calculation(self):
        today = datetime.date.today()
        # Exactly 15 years old
        dob_15 = datetime.date(today.year - 15, today.month, today.day)
        self.assertEqual(AgePolicy.calculate_age(dob_15), 15)

        # 14 years old (birthday tomorrow)
        # Handle month boundary safely
        if today.month < 12:
            dob_14 = datetime.date(today.year - 15, today.month + 1, 1)
        else:
            dob_14 = datetime.date(today.year - 15, 12, 28)
        self.assertEqual(AgePolicy.calculate_age(dob_14), 14)

    def test_age_eligibility_and_consent_requirement(self):
        today = datetime.date.today()

        # Age 13: Eligible, requires guardian consent
        dob_13 = datetime.date(today.year - 13, today.month, today.day)
        res_13 = AgePolicy.validate_student_age(dob_13)
        self.assertTrue(res_13["is_eligible"])
        self.assertTrue(res_13["requires_guardian_consent"])
        self.assertEqual(AgePolicy.get_age_band(13), "BAND_13_15")

        # Age 17: Eligible, requires statutory guardian consent under DPDP Act 2023 (under 18)
        dob_17 = datetime.date(today.year - 17, today.month, today.day)
        res_17 = AgePolicy.validate_student_age(dob_17)
        self.assertTrue(res_17["is_eligible"])
        self.assertTrue(res_17["requires_guardian_consent"])
        self.assertEqual(AgePolicy.get_age_band(17), "BAND_16_17")

        # Age 8: Ineligible (under minimum platform age)
        dob_8 = datetime.date(today.year - 8, today.month, today.day)
        res_8 = AgePolicy.validate_student_age(dob_8)
        self.assertFalse(res_8["is_eligible"])

if __name__ == "__main__":
    unittest.main()
