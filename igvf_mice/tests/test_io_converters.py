from datetime import datetime
from unittest import TestCase
import numpy
import pandas
from .. import models
from ..io.converters import (
    date_or_none,
    datetime_or_none,
    float_or_none,
    int_or_none,
    int_or_0,
    str_or_empty,
    str_or_none,
    normalize_plate_name,
    normalize_strain,
    normalize_subpool_submission_status,
    parse_mouse_name,
    parse_mouse_tissue,
    get_genotype_from_mouse_tissue,
)


class TestConverters(TestCase):
    def test_date_or_none(self):
        self.assertIsNone(date_or_none(numpy.nan))
        self.assertIsNone(date_or_none(None))
        self.assertIsNone(date_or_none("-"))
        x = datetime(2022,1,2,3,4,5)
        self.assertEqual(date_or_none(x), x.date())
        self.assertEqual(date_or_none("foo"), "foo")
        
    def test_datetime_or_none(self):
        self.assertIsNone(datetime_or_none(numpy.nan))
        self.assertIsNone(datetime_or_none(None))
        self.assertIsNone(datetime_or_none("-"))
        x = datetime(2022,1,2,3,4,5)
        self.assertEqual(datetime_or_none(x), x)
        self.assertEqual(datetime_or_none("foo"), "foo")

    def test_float_or_none(self):
        self.assertIsNone(float_or_none(numpy.nan))
        self.assertAlmostEqual(float_or_none("4.0"), 4.0)

    def test_int_or_none(self):
        for excelism in ["N/A", "#DIV/0!", "-", numpy.nan, None]:
            self.assertIsNone(int_or_none(excelism))
        self.assertEqual(int_or_none("3"), 3)
        
    def test_int_or_0(self):
        for value in [numpy.nan, None]:
            self.assertEqual(int_or_0(value), 0)
        self.assertEqual(int_or_none("3"), 3)

    def test_str_or_empty(self):
        for value in [numpy.nan, None]:
            self.assertEqual(str_or_empty(value), "")
        self.assertEqual(str_or_empty("hello"), "hello")
        
    def test_str_or_none(self):
        for value in [numpy.nan, None]:
            self.assertIsNone(str_or_none(value))
        self.assertEqual(str_or_empty("hello"), "hello")

    def test_normalize_plate_name(self):
        self.assertEqual(normalize_plate_name("igvf_003"), "IGVF_003")
        self.assertEqual(normalize_plate_name("IGVF_008B"), "IGVF_008B")

    def test_normalize_strain(self):
        self.assertEqual(normalize_strain("B6WSBF1/J"), "B6WSBF1J")
        self.assertEqual(normalize_strain("195_B6CASTF1/J_10M_20"), "195_B6CASTF1J_10M_20")
        self.assertEqual(normalize_strain("B6129SF1/J"), "B6129S1F1J")

    def test_normalize_subpool_submission_status(self):
        for falsy in (None, numpy.nan, 0, False, "no"):
            self.assertEqual(normalize_subpool_submission_status(falsy), str(models.RunStatusEnum.FAILED))

        for truthy in (1, True, "yes", "Yes"):
            self.assertEqual(normalize_subpool_submission_status(truthy), str(models.RunStatusEnum.PASS))

    def test_parse_mouse_name(self):
        self.assertEqual(parse_mouse_name("477_CC030_10M"), ("477", "CC030", "10M"))
        self.assertEqual(parse_mouse_name("239_TREM2R47HNSS_HO_10M"), ("239", "TREM2R47HNSS_HO", "10M"))
        self.assertEqual(parse_mouse_name("238_B6WSBF1/J_10F"), ("238", "B6WSBF1J", "10F"))
        self.assertEqual(parse_mouse_name("656_B6NODF1/J_6moF"), ("656", "B6NODF1J", "6moF"))

    def test_parse_mouse_tissue(self):
        self.assertEqual(parse_mouse_tissue("096_WSBJ_10F_15"), ("096", "WSBJ", "10F", "15"))
        self.assertEqual(parse_mouse_tissue("239_TREM2R47HNSS_HO_10M_01"), ("239", "TREM2R47HNSS_HO", "10M", "01"))
        self.assertEqual(parse_mouse_tissue("656_B6NODF1/J_6moF_10"), ("656", "B6NODF1J", "6moF", "10"))

    def test_get_genotype_from_mouse_tissue(self):
        self.assertEqual(get_genotype_from_mouse_tissue("016_B6J_10F_20"), "B6J")
        self.assertEqual(get_genotype_from_mouse_tissue("046_NZOJ_10F_03"), "NZOJ")
        self.assertEqual(get_genotype_from_mouse_tissue("198_B6CASTF1/J_10F_20"), "B6CASTF1J")
        self.assertEqual(get_genotype_from_mouse_tissue("239_TREM2R47HNSS_HO_10M_01"), "TREM2R47HNSS_HO")
