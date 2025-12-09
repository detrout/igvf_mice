from datetime import datetime, date, time
from unittest import TestCase
import numpy
from .. import models
from ..io.converters import (
    convert_plate_id_to_name,
    date_or_none,
    datetime_or_none,
    float_or_nan,
    float_or_none,
    int_or_none,
    int_or_0,
    str_or_empty,
    str_or_none,
    normalize_barcode_index,
    normalize_plate_name,
    normalize_mice_date,
    normalize_strain,
    normalize_subpool_submission_status,
    parse_mouse_age_sex,
    join_mouse_age_sex,
    parse_mouse_name,
    join_mouse_name,
    parse_mouse_tissue,
    join_mouse_tissue,
    get_genotype_from_mouse_tissue,
    instrument_name_to_platform_id,
)


class TestConverters(TestCase):
    def test_convert_plate_id_to_name(self):
        data = [
            ("008b", "IGVF_008B"),
            ("EX1", "IGVF_EX1"),
            ("IGVF_003", "IGVF_003"),
        ]

        for source, expected in data:
            self.assertEqual(
                convert_plate_id_to_name(source), expected)

    def test_date_or_none(self):
        self.assertIsNone(date_or_none(numpy.nan))
        self.assertIsNone(date_or_none(None))
        self.assertIsNone(date_or_none("-"))
        x = datetime(2022, 1, 2, 3, 4, 5)
        self.assertEqual(date_or_none(x), x.date())
        self.assertEqual(date_or_none("foo"), "foo")

    def test_datetime_or_none(self):
        self.assertIsNone(datetime_or_none(numpy.nan))
        self.assertIsNone(datetime_or_none(None))
        self.assertIsNone(datetime_or_none("-"))
        x = datetime(2022, 1, 2, 3, 4, 5)
        self.assertEqual(datetime_or_none(x), x)
        self.assertEqual(datetime_or_none("foo"), "foo")

    def test_float_or_nan(self):
        self.assertTrue(numpy.isnan(float_or_nan(numpy.nan)))
        for empty in ["N/A", "#VALUE!", "missing"]:
            self.assertTrue(numpy.isnan(float_or_nan(empty)))
        self.assertAlmostEqual(float_or_nan("4.0"), 4.0)

    def test_float_or_none(self):
        self.assertIsNone(float_or_none(numpy.nan))
        self.assertAlmostEqual(float_or_none("4.0"), 4.0)

    def test_int_or_none(self):
        for excelism in ["N/A", "#DIV/0!", "-", numpy.nan, None]:
            self.assertIsNone(int_or_none(excelism))
        # me using blanks as no value
        self.assertIsNone(int_or_none(""))
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

    def test_normalize_barcode_index(self):
        self.assertEqual(normalize_barcode_index("1"), "1")
        self.assertEqual(normalize_barcode_index(1), 1)
        self.assertEqual(normalize_barcode_index(""), "")
        self.assertEqual(normalize_barcode_index("UDI_WT_01"), "UDI01")

    def test_normalize_plate_name(self):
        self.assertEqual(normalize_plate_name("igvf_003"), "IGVF_003")
        self.assertEqual(normalize_plate_name("IGVF_008B"), "IGVF_008B")

    def test_normalize_mice_date_null(self):
        dates = [None, 123, None, "-", 123]
        times = [None, None, 123, 123, "-"]

        for i, dt in enumerate(normalize_mice_date(dates, times)):
            self.assertIs(dt, None, msg=f"Failed on step {i}")

    def test_normalize_mice_date_fail_types(self):
        dates = ["asdf"]
        times = [time(12, 30)]
        self.assertRaises(ValueError, list, normalize_mice_date(dates, times))

        dates = [time(12, 30)]
        times = [time(12, 30)]
        self.assertRaises(ValueError, list, normalize_mice_date(dates, times))

        dates = [date(1970, 1, 1)]
        times = ["asdf"]
        self.assertRaises(ValueError, list, normalize_mice_date(dates, times))

    def test_normalize_mice_date_valid_date_types(self):
        dates = [date(1970, 1, 1)]
        times = [time(12, 30)]
        expected = [datetime(1970, 1, 1, 12, 30)]

        self.assertEqual(list(normalize_mice_date(dates, times)), expected)

    def test_normalize_strain(self):
        # normalize strain now only works on the strain name and
        # doesn't support replacing arbitrary strings.
        self.assertEqual(normalize_strain("B6WSBF1/J"), "B6WSBF1J")
        self.assertEqual(normalize_strain("B6129SF1/J"), "B6129S1F1J")
        self.assertEqual(normalize_strain("TREM2R47HNSS_HO"), "TREM2")

    def test_normalize_subpool_submission_status(self):
        for falsy in (None, numpy.nan, 0, False, "no"):
            self.assertEqual(
                normalize_subpool_submission_status(falsy),
                str(models.RunStatusEnum.FAILED))

        for truthy in (1, True, "yes", "Yes"):
            self.assertEqual(
                normalize_subpool_submission_status(truthy),
                str(models.RunStatusEnum.PASS))

    def test_parse_mouse_age_sex(self):
        for name, split in [
                ("10M", ("10", "M")),
                ("10M", ("10", "M")),
                ("10F", ("10", "F")),
                ("6moF", ("6mo", "F"))]:
            self.assertEqual(parse_mouse_age_sex(name), split)
            self.assertEqual(join_mouse_age_sex(split), name)
            self.assertEqual(join_mouse_age_sex(parse_mouse_age_sex(name)), name)

    def test_parse_mouse_name(self):
        for name, split in [
                ("477_CC030_10M", ("477", "CC030", "10", "M")),
                ("239_TREM2_10M", ("239", "TREM2", "10", "M")),
                ("238_B6WSBF1J_10F", ("238", "B6WSBF1J", "10", "F")),
                ("656_B6NODF1J_6moF", ("656", "B6NODF1J", "6mo", "F"))]:
            self.assertEqual(parse_mouse_name(name), split)
            self.assertEqual(join_mouse_name(split), name)
            self.assertEqual(join_mouse_name(parse_mouse_name(name)), name)

    def test_parse_mouse_tissue(self):
        for name, split in [
                ("096_WSBJ_10F_15", ("096", "WSBJ", "10", "F", "15")),
                ("239_TREM2_10M_01", ("239", "TREM2", "10", "M", "01")),
                ("656_B6NODF1J_6moF_10", ("656", "B6NODF1J", "6mo", "F", "10"))]:
            self.assertEqual(parse_mouse_tissue(name), split)
            self.assertEqual(join_mouse_tissue(split), name)
            self.assertEqual(join_mouse_tissue(parse_mouse_tissue(name)), name)

    def test_get_genotype_from_mouse_tissue(self):
        for name, genotype in [
                ("016_B6J_10F_20", "C57BL/6J"),
                ("046_NZOJ_10F_03", "NZO/HlLtJ"),
                ("198_B6CASTF1J_10F_20", "B6CASTF1/J"),
                ("239_TREM2_10M_01", "TREM2R47HNSS_HO")]:
            self.assertEqual(get_genotype_from_mouse_tissue(name), genotype)

    def test_instrument_name_to_platform_id(self):
        for friendly, expected in [
                ("P2 Solo", "p2solo"),
                ("Promethion", "promethion"),
                ("MinION", "minion")]:
            self.assertEqual(
                instrument_name_to_platform_id(friendly), expected)
