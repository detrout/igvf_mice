from unittest import TestCase

from ..io.validators import (
    validate_alias,
    validate_mouse_age_sex,
    validate_splitseq_cap_label,
)

class TestIoValidators(TestCase):
    def test_validate_alias(self):
        self.assertTrue(validate_alias("ali-mortazavi:abcdef"))
        self.assertRaises(ValueError, validate_alias, "ali-mortazavi:194_B6CASTF1/J_10F_20")

    def test_validate_mouse_age_sex(self):
        self.assertTrue(validate_mouse_age_sex("10F"))
        self.assertTrue(validate_mouse_age_sex("6moM"))
        self.assertRaises(ValueError, validate_mouse_age_sex, "ABF")
        self.assertRaises(ValueError, validate_mouse_age_sex, "5moF")

    def test_validate_splitseq_cap_label(self):
        # Valid cases
        expected = [
                ("268_01", "268_CC001_10F_01", True),
                ("016_03", "016_B6J_10F_03", True),
                ("268_03", "268_CC001_10F", False),
                ("016_10", "016_B6J_10F_03", False),
        ]

        for tube, sample, result in expected:
            self.assertEqual(validate_splitseq_cap_label(tube, sample), result)
