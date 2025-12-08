from django.test import TestCase
from ..io.read_sheet import (
    normalize_mice_name,
    normalize_mice_strain_name,
    strain_code_to_name,
    strain_name_to_code,
)


class TestNormalizeMiceName(TestCase):
    fixtures = ["source", "mousestrain"]

    def test_normalize_mice_name_none(self):
        self.assertIs(normalize_mice_name(None), None)

    def test_normalzie_mice_name_sex(self):
        self.assertEqual(normalize_mice_name("018_B6J_10F"), "018_B6J_10F")

        self.assertRaises(ValueError, normalize_mice_name, "018_B6J_10bad")

    def test_normalize_mice_name_trem2(self):
        name = "239_TREM2_10M"
        self.assertEqual(normalize_mice_name(name), name)

        name = "239_TREM2R47HNSS_HO_10M"
        expected = "239_TREM2_10M"
        self.assertEqual(normalize_mice_name(name), expected)

    def test_normalize_mice_name_f1s(self):
        names = ["874_B6AF1_10F", "882_AB6F1_10F"]
        for n in names:
            self.assertEqual(normalize_mice_name(n), n)

    def test_normalize_mice_name_cc(self):
        names = ["381_CC012_10M", "575_CC065_10M"]
        for n in names:
            self.assertEqual(normalize_mice_name(n), n)

    def test_normalize_mice_old(self):
        names = ["634_B6AF1J_6moF", "697_B6WSBF1J_6moM"]
        for n in names:
            self.assertEqual(normalize_mice_name(n), n)

    def test_normalize_mice_name_circadian(self):
        names = ["781_B6J_L_12M", "799_CASTJ_D_12M"]

        for n in names:
            self.assertEqual(normalize_mice_name(n), n)

    def test_normalize_mice_name_reverse_cross(self):
        names = ["958_CASTB6F1_10F"]

        for n in names:
            self.assertEqual(normalize_mice_name(n), n)

