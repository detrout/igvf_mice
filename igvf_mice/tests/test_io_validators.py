from unittest import TestCase

from ..io.validators import (
    validate_alias,
    validate_mouse_age_sex,
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
