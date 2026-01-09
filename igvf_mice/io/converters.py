"""Cast pandas values to django database semantics

The way that pandas and django represent missing data needs a bits of
conversion.
"""

from collections import namedtuple
from collections.abc import Sequence
import datetime
import numpy
import pandas
import zoneinfo

from .validators import validate_mouse_age_sex


def convert_plate_id_to_name(value):
    if pandas.notnull(value):
        value = normalize_plate_name(value)
        if value.startswith("IGVF_"):
            return value
        else:
            return "IGVF_{}".format(value)


def date_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in ("-",):
        return None
    elif isinstance(x, (datetime.datetime, datetime.date)):
        return x.date()
    else:
        return x


def datetime_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in ("-",):
        return None
    elif isinstance(x, datetime.datetime):
        return x
    else:
        return x


def float_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in (
        "N/A",
        "#DIV/0!",
        "#VALUE!",
        "-",
    ):
        return None
    else:
        return float(x)


def float_or_nan(x):
    if pandas.isnull(x):
        return numpy.nan
    elif isinstance(x, str) and x.strip() in (
        "N/A",
        "#DIV/0!",
        "#VALUE!",
        "-",
        "",
        "missing",
    ):
        return numpy.nan
    else:
        return float(x)


def is_excel_null(x):
    if pandas.isnull(x):
        return True
    elif x in ("#DIV/0!", "#VALUE!"):
        return True
    else:
        return False


def int_or_none(x):
    if isinstance(x, str) and x.strip() in ("N/A", "#DIV/0!", "#VALUE!", "-", ""):
        return None
    elif pandas.isnull(x):
        return None
    elif isinstance(x, str) and len(x) == 0:
        return None
    else:
        return int(x)


def positive_int_or_none(x):
    if isinstance(x, str) and x.strip() in ("N/A", "#DIV/0!", "#VALUE!", "-", ""):
        return None
    elif pandas.isnull(x):
        return None
    else:
        x = int(x)
        if x < 0:
            return None
        else:
            return x


def int_or_0(x):
    if pandas.isnull(x):
        return 0
    else:
        return int(x)


def str_or_empty(x):
    if pandas.isnull(x):
        return ""
    else:
        return x


def str_or_none(x):
    if pandas.isnull(x):
        return None
    else:
        return x


def normalize_barcode_index(value):
    if isinstance(value, str):
        if value.startswith("UDI_WT_"):
            return "UDI{}".format(value[len("UDI_WT_") :])

    return value


def normalize_plate_name(name):
    name = name.upper()

    return name


def normalize_mice_date(date_column, time_column):
    for i, (date, time) in enumerate(zip(date_column, time_column)):
        if pandas.isnull(date):
            yield None
        elif pandas.isnull(time):
            yield None
        elif date == "-" or time == "-":
            yield None
        elif isinstance(date, str):
            raise ValueError(f"Invalid type in date row {i} {date} {type(date)}")
            yield None
        elif isinstance(date, datetime.time):
            raise ValueError(f"Time in date field on row {i} {date} {type(date)}")
            yield None
        elif isinstance(time, str):
            raise ValueError(f"Invalid type in time row {i} {time} {type(time)}")
            yield None
        else:
            yield datetime.datetime.combine(date, time)


genotype_to_strain = {
    "129S1/SvImJ": "129S1J",
    "B6129SF1/J": "B6129S1F1J",
    "B6CASTF1/J": "B6CASTF1J",
    "B6NODF1/J": "B6NODF1J",
    "B6PWKF1/J": "B6PWKF1J",
    "B6WSBF1/J": "B6WSBF1J",
    "CAST/EiJ": "CASTJ",
    "C57BL/6J": "B6J",
    "NOD/ShiLtJ": "NODJ",
    "NZO/HlLtJ": "NZOJ",
    "PWK/PhJ": "PWKJ",
    "TREM2R47HNSS_HO": "TREM2",
    "WSB/EiJ": "WSBJ",
    "CASTB6F1": "CASTB6F1",
}


def normalize_strain(strain):
    """Adapter to convert name"""
    return genotype_to_strain.get(strain, strain)


strain_to_genotype = {genotype_to_strain[k]: k for k in genotype_to_strain}


def get_genotype_from_mouse_tissue(mouse_tissue):
    fields = parse_mouse_tissue(mouse_tissue)
    strain = fields[1]
    return strain_to_genotype.get(strain, strain)


def normalize_subpool_submission_status(value):
    from ..models import RunStatusEnum

    if pandas.isnull(value):
        return str(RunStatusEnum.FAILED)
    elif value in (0, False, "no", "No"):
        return str(RunStatusEnum.FAILED)
    elif value in (1, True, "yes", "Yes"):
        return str(RunStatusEnum.PASS)


mouse_age_sex_tuple = namedtuple("mouse_age_sex_tuple", ["mouse_age", "mouse_sex"])
mouse_age_sex_tuple_lens = {len(mouse_age_sex_tuple._fields)}


mouse_name_tuple = namedtuple(
    "mouse_name_tuple",
    ["mouse_id", "mouse_strain", "light_status", "mouse_age", "mouse_sex"],
)
mouse_name_tuple_lens = {
    len(mouse_name_tuple._fields) - 1,
    len(mouse_name_tuple._fields),
}


mouse_tissue_tuple = namedtuple(
    "mouse_tissue_tuple",
    ["mouse_id", "mouse_strain", "light_status", "mouse_age", "mouse_sex", "tissue_id"],
)
mouse_tissue_tuple_lens = {
    len(mouse_tissue_tuple._fields) - 1,
    len(mouse_tissue_tuple._fields),
}


def parse_mouse_age_sex(mouse_age_sex):
    """Parse age/sex combined files like 10F or 6moM"""
    from ..models import SexEnum

    sex = mouse_age_sex[-1]
    age = mouse_age_sex[0:-1]

    if sex not in SexEnum.values:
        raise ValueError(
            "Invalid sex value {}. Allowed values {}".format(sex, SexEnum.values)
        )

    valid_ages = ("6mo",)
    if not (age in valid_ages or isinstance(int(age), int)):
        raise ValueError("Age must be an integer or in {}".format(valid_ages))

    return mouse_age_sex_tuple(age, sex)


def join_mouse_age_sex(value):
    if isinstance(value, mouse_age_sex_tuple):
        mouse_age = str(value.mouse_age)
        mouse_sex = str(value.mouse_sex)
    elif isinstance(value, Sequence) and len(value) in mouse_age_sex_tuple_lens:
        mouse_age = str(value[0])
        mouse_sex = str(value[1])
    else:
        raise ValueError(
            "Value {} not compatible with mouse_age_sex_tuple".format(value)
        )

    # TODO: Could probably add validators here too
    return mouse_age + mouse_sex


def parse_mouse_name(mouse_name):
    # mouse_id_end = mouse_name.find("_")
    # mouse_age_sex_start = mouse_name.rfind("_") + 1

    # mouse_id = mouse_name[0:mouse_id_end]
    # mouse_strain = normalize_strain(mouse_name[mouse_id_end+1:mouse_age_sex_start-1])
    # mouse_age, mouse_sex = parse_mouse_age_sex(mouse_name[mouse_age_sex_start:])
    # return mouse_name_tuple(mouse_id, mouse_strain, mouse_age, mouse_sex)

    fields = mouse_name.split("_")

    mouse_id = fields.pop(0)
    mouse_strain = fields.pop(0)
    mouse_strain = normalize_strain(mouse_strain)
    if fields[0] in ("L", "D"):
        light_status = fields.pop(0)
    else:
        light_status = None
    mouse_age_sex = fields.pop(0)
    mouse_age, mouse_sex = parse_mouse_age_sex(mouse_age_sex)
    validate_mouse_age_sex(mouse_age_sex)
    assert len(fields) == 0

    return mouse_name_tuple(mouse_id, mouse_strain, light_status, mouse_age, mouse_sex)


def join_mouse_name(value):
    fields = []
    all_mouse_tuple_lens = mouse_name_tuple_lens.union(mouse_tissue_tuple_lens)
    if isinstance(value, mouse_name_tuple):
        fields.append(value.mouse_id)
        fields.append(value.mouse_strain)
        if value.light_status is not None:
            fields.append(value.light_status)
        fields.append(join_mouse_age_sex((value.mouse_age, value.mouse_sex)))
    elif isinstance(value, mouse_tissue_tuple):
        fields.append(value.mouse_id)
        fields.append(value.mouse_strain)
        if value.light_status is not None:
            fields.append(value.light_status)
        fields.append(join_mouse_age_sex((value.mouse_age, value.mouse_sex)))
    elif isinstance(value, Sequence) and len(value) in all_mouse_tuple_lens:
        value_fields = list(value)
        fields.append(value_fields.pop(0))
        fields.append(value_fields.pop(0))
        # optional light status
        if value_fields[0] is None:
            value_fields.pop(0)
        elif value_fields[0] in {"L", "D"}:
            fields.append(value_fields.pop(0))
        mouse_age = value_fields.pop(0)
        mouse_sex = value_fields.pop(0)
        fields.append(join_mouse_age_sex((mouse_age, mouse_sex)))
    else:
        raise ValueError("{} does not look like a parsed mouse_name".format(value))

    return "_".join(fields)


def parse_mouse_tissue(mouse_tissue):
    fields = mouse_tissue.split("_")

    mouse_id = fields.pop(0)
    mouse_strain = fields.pop(0)
    mouse_strain = normalize_strain(mouse_strain)
    if fields[0] in ("L", "D"):
        light_status = fields.pop(0)
    else:
        light_status = None
    mouse_age_sex = fields.pop(0)
    mouse_age, mouse_sex = parse_mouse_age_sex(mouse_age_sex)
    validate_mouse_age_sex(mouse_age_sex)
    tissue_id = fields.pop(0)
    assert len(fields) == 0

    return mouse_tissue_tuple(
        mouse_id, mouse_strain, light_status, mouse_age, mouse_sex, tissue_id
    )


def join_mouse_tissue(value):
    """Covert a set of mouse tissue attributes into a formatted string"""
    fields = []
    if isinstance(value, mouse_tissue_tuple):
        fields.append(value.mouse_id)
        fields.append(value.mouse_strain)
        if value.light_status is not None:
            fields.append(value.light_status)
        fields.append(join_mouse_age_sex((value.mouse_age, value.mouse_sex)))
        fields.append(value.tissue_id)
    elif isinstance(value, Sequence) and len(value) in mouse_tissue_tuple_lens:
        value_fields = list(value)
        fields.append(value_fields.pop(0))
        fields.append(value_fields.pop(0))
        if value_fields[0] is None:
            value_fields.pop(0)
        elif value_fields[0] in {"L", "D"}:
            fields.append(value_fields.pop(0))
        mouse_age = value_fields.pop(0)
        mouse_sex = value_fields.pop(0)
        fields.append(join_mouse_age_sex((mouse_age, mouse_sex)))
        fields.append(value_fields.pop(0))
    else:
        raise ValueError("{} does not look like a parsed mouse_name".format(value))

    return "_".join(fields)


def get_strain_from_mouse_tissue(mouse_tissue):
    fields = parse_mouse_tissue(mouse_tissue)

    return fields[1]


def uci_tz_or_none(value):
    los_angeles_tz = zoneinfo.ZoneInfo("America/Los_Angeles")

    if pandas.isnull(value):
        return None
    elif isinstance(value, pandas.Timestamp):
        return value.tz_localize("America/Los_Angeles")
    elif isinstance(value, datetime.datetime):
        return value.astimezone(los_angeles_tz)


def instrument_name_to_platform_id(value):
    """Convert human friendly nanopore machine names to platform ids"""
    if pandas.isnull(value):
        return None

    return value.replace(" ", "").lower()
